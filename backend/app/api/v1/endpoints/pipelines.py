import json
import uuid
import pandas as pd
import numpy as np
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.v1 import deps
from app.services.pipeline_service import execute_pipeline
from app.services.dataset_service import check_quality_alerts
from app.services.nlp_service import parse_command
from app.core.config import settings

router = APIRouter()

# --- Helper Functions ---

def load_secondary_datasets(db: Session, steps: List[dict]) -> dict:
    context = {}
    for step in steps:
        op = step.get("operation")
        params = step.get("params", {})
        if op in ["merge", "concat"]:
            sec_id = params.get("secondary_dataset_id")
            if sec_id and sec_id not in context:
                ds = db.query(models.Dataset).filter(models.Dataset.id == sec_id).first()
                if ds:
                    try:
                        if ds.file_format == "csv":
                            context[sec_id] = pd.read_csv(ds.file_path)
                        elif ds.file_format in ["xlsx", "xls"]:
                            context[sec_id] = pd.read_excel(ds.file_path)
                        elif ds.file_format == "json":
                            context[sec_id] = pd.read_json(ds.file_path)
                    except Exception:
                        pass # Fail silently or log? For now silently skip invalid files
    return context

def get_or_create_draft_pipeline(db: Session, dataset_id: str) -> models.Pipeline:
    pipeline = db.query(models.Pipeline).filter(
        models.Pipeline.dataset_id == dataset_id,
        models.Pipeline.name == "Draft Pipeline",
    ).first()
    
    if not pipeline:
        pipeline = models.Pipeline(
            id=str(uuid.uuid4()),
            name="Draft Pipeline",
            description="Interactive workspace pipeline",
            steps="[]",
            dataset_id=dataset_id,
        )
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
    return pipeline

def execute_preview(dataset: models.Dataset, steps: List[dict], db: Session, limit: int = 100) -> dict:
    try:
        # Load data
        # Note: We must load the dataset completely to run accurate transformations (like fillna(mean))
        if dataset.file_format == "csv":
            df = pd.read_csv(dataset.file_path)
        elif dataset.file_format in ["xlsx", "xls"]:
            df = pd.read_excel(dataset.file_path)
        elif dataset.file_format == "json":
            df = pd.read_json(dataset.file_path)
        else:
            raise ValueError("Unsupported file format")

        # Load secondary datasets if needed
        context = load_secondary_datasets(db, steps)

        # Execute Pipeline on full dataset
        df_transformed = execute_pipeline(df, steps, context)
        
        # Determine columns
        columns = list(df_transformed.columns)
        
        from app.services.dataset_service import infer_column_type
        column_schemas = [
            {"name": col, "detected_type": infer_column_type(df_transformed[col])}
            for col in columns
        ]

        # Take preview (head)
        df_preview = df_transformed.head(limit)
        
        # Convert to dict for JSON response (Handle NaNs)
        # Using where(pd.notnull(df), None) is safer for mixed types than replace({np.nan: None})
        preview_data = df_preview.where(pd.notnull(df_preview), None).to_dict(orient="records")

        return {
            "preview": preview_data,
            "preview_full_df": df_transformed, # Return full DF for quality checks
            "row_count": len(df_transformed),
            "col_count": len(df_transformed.columns),
            "columns": columns,
            "column_schemas": column_schemas
        }
    except Exception as e:
        print(f"Pipeline Execution Error: {e}")
        raise HTTPException(status_code=422, detail=f"Pipeline execution failed: {str(e)}")

# --- Endpoints ---

@router.get("/", response_model=List[schemas.Pipeline])
def read_pipelines(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve pipelines.
    """
    pipelines = db.query(models.Pipeline).offset(skip).limit(limit).all()
    return pipelines

@router.post("/", response_model=schemas.Pipeline)
def create_pipeline(
    *,
    db: Session = Depends(deps.get_db),
    pipeline_in: schemas.PipelineCreate,
) -> Any:
    """
    Create a new pipeline.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == pipeline_in.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    pipeline = models.Pipeline(
        id=str(uuid.uuid4()),
        name=pipeline_in.name,
        description=pipeline_in.description,
        steps=json.dumps([step.model_dump() for step in pipeline_in.steps]),
        dataset_id=pipeline_in.dataset_id,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline

@router.post("/{pipeline_id}/clone", response_model=schemas.Pipeline)
def clone_pipeline(
    *,
    pipeline_id: str,
    pipeline_data: dict = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Clone a draft pipeline into a saved template.
    """
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    name = pipeline_data.get("name", f"Copy of {pipeline.name}")
    description = pipeline_data.get("description", pipeline.description)
    
    new_pipeline = models.Pipeline(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        steps=pipeline.steps,
        dataset_id=None, # Save as unattached template
    )
    db.add(new_pipeline)
    db.commit()
    db.refresh(new_pipeline)
    return new_pipeline

@router.put("/{pipeline_id}", response_model=schemas.Pipeline)
def update_pipeline(
    *,
    pipeline_id: str,
    pipeline_in: schemas.PipelineUpdate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Update a pipeline.
    """
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    update_data = pipeline_in.model_dump(exclude_unset=True)
    if "steps" in update_data:
        update_data["steps"] = json.dumps([step.model_dump() for step in pipeline_in.steps])
    for field, value in update_data.items():
        setattr(pipeline, field, value)
        
    pipeline.updated_at = pd.Timestamp.utcnow().to_pydatetime()
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline

@router.get("/{pipeline_id}/export")
def export_pipeline_json(
    pipeline_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Export pipeline steps as JSON.
    """
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    return {
        "pipeline_name": pipeline.name,
        "description": pipeline.description,
        "created_at": pipeline.created_at,
        "steps": json.loads(pipeline.steps)
    }

@router.post("/import")
def import_pipeline_json(
    pipeline_data: dict = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Import a pipeline from JSON.
    """
    # Create a new pipeline record
    new_pipeline = models.Pipeline(
        id=str(uuid.uuid4()),
        name=pipeline_data.get("pipeline_name", "Imported Pipeline") + f" (Imported {datetime.utcnow().strftime('%Y-%m-%d %H:%M')})",
        description=pipeline_data.get("description", "Imported from external file"),
        steps=json.dumps(pipeline_data.get("steps", [])),
        dataset_id=None, # Not attached to any dataset initially
    )
    db.add(new_pipeline)
    db.commit()
    db.refresh(new_pipeline)
    return new_pipeline

@router.post("/{pipeline_id}/execute", response_model=schemas.PipelineExecuteResponse)
def execute_pipeline_endpoint(
    *,
    pipeline_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Execute a pipeline on its dataset.
    """
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    dataset = db.query(models.Dataset).filter(models.Dataset.id == pipeline.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Load and Execute
    try:
        if dataset.file_format == "csv":
            df = pd.read_csv(dataset.file_path)
        elif dataset.file_format in ["xlsx", "xls"]:
            df = pd.read_excel(dataset.file_path)
        elif dataset.file_format == "json":
            df = pd.read_json(dataset.file_path)
        else:
            raise ValueError("Unsupported file format")
            
        steps = json.loads(pipeline.steps)
        context = load_secondary_datasets(db, steps)
        transformed_df = execute_pipeline(df, steps, context)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Execution failed: {str(e)}")

    preview = transformed_df.head(5).to_json()
    
    # Log execution
    log = models.TransformationLog(
        id=str(uuid.uuid4()),
        dataset_id=dataset.id,
        pipeline_id=pipeline.id,
        step_index=len(steps),
        operation="full_pipeline",
        parameters=json.dumps({"pipeline_name": pipeline.name}),
        rows_affected=len(transformed_df),
    )
    db.add(log)
    db.commit()

    return {
        "pipeline_id": pipeline.id,
        "execution_status": "success",
        "rows_affected": len(transformed_df),
        "preview_data": preview
    }

# --- Interactive Workspace Endpoints ---

@router.get("/interactive/{dataset_id}")
def get_interactive_state(
    dataset_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get current draft pipeline state and preview.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    pipeline = get_or_create_draft_pipeline(db, dataset_id)
    
    # Load steps safely
    if not pipeline.steps:
        steps = []
    else:
        try:
            steps = json.loads(pipeline.steps)
        except json.JSONDecodeError:
            steps = []
            
    # Execute pipeline to get current state
    result = execute_preview(dataset, steps, db)
    
    # Calculate quality alerts on the TRANSFORMED data (always use full dataset)
    alerts = []
    
    # Extract full DataFrame for accurate alert calculation
    df_full = result.pop("preview_full_df", None)
    
    if df_full is not None:
         try:
             alerts = check_quality_alerts(df_full)
         except Exception as e:
             print(f"Error calculating alerts on full DF: {e}")
             alerts = []
        
    return {
        "pipeline_id": pipeline.id,
        "steps": steps,
        "quality_alerts": alerts,
        **result
    }

@router.post("/interactive/{dataset_id}/command")
def execute_command(
    dataset_id: str,
    command: dict = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Execute a natural language command.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    cmd_text = command.get("text", "")
    step_data = parse_command(cmd_text)
    
    if not step_data:
        raise HTTPException(status_code=400, detail="Could not understand command")
    
    # Wrap in PipelineStep
    # Create step object first to get ID and timestamp
    step = schemas.PipelineStep(
        operation=step_data["operation"],
        params=step_data["params"]
    )
    
    # Calculate checksum
    import json
    import hashlib
    step.parameter_checksum = hashlib.sha256(json.dumps(step.params, sort_keys=True).encode()).hexdigest()
        
    pipeline = get_or_create_draft_pipeline(db, dataset_id)
    steps = json.loads(pipeline.steps)
    
    # Add step
    step_dict = step.model_dump()
    step_dict["timestamp"] = step_dict["timestamp"].isoformat()
    steps.append(step_dict)
    
    # Update pipeline
    pipeline.steps = json.dumps(steps)
    pipeline.updated_at = pd.Timestamp.utcnow().to_pydatetime()
    db.commit()
    
    # Execute and return preview
    result = execute_preview(dataset, steps, db)
    
    # Extract and REMOVE full DF before returning to prevent serialization error
    df_full = result.pop("preview_full_df", None)
    
    # Calculate quality alerts on full dataset
    alerts = []
    if df_full is not None:
         try:
             alerts = check_quality_alerts(df_full)
         except Exception:
             alerts = []
            
    return {
        "pipeline_id": pipeline.id,
        "steps": steps,
        "added_step": step_dict,
        "quality_alerts": alerts,
        **result
    }

@router.post("/interactive/{dataset_id}/steps")
def add_step(
    dataset_id: str,
    step: schemas.PipelineStep,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Add a step to the draft pipeline and return updated preview.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    pipeline = get_or_create_draft_pipeline(db, dataset_id)
    steps = json.loads(pipeline.steps)
    
    # Calculate checksum
    import hashlib
    # Convert MappingProxy to dict for JSON serialization
    params_dict = dict(step.params)
    checksum = hashlib.sha256(json.dumps(params_dict, sort_keys=True).encode()).hexdigest()
    
    # Since step is frozen, we must use object.__setattr__ to bypass Pydantic's frozen check
    # This is a legitimate backend operation to set the checksum before storage
    object.__setattr__(step, 'parameter_checksum', checksum)
    
    # Add step (schemas.PipelineStep handles UUID and timestamp)
    step_dict = step.model_dump()
    # Ensure JSON serializable (MappingProxy to Dict)
    if 'params' in step_dict and isinstance(step_dict['params'], dict) is False:
        step_dict['params'] = dict(step_dict['params'])
        
    step_dict["timestamp"] = step_dict["timestamp"].isoformat()
    steps.append(step_dict)
    
    # Update pipeline
    pipeline.steps = json.dumps(steps)
    pipeline.updated_at = pd.Timestamp.utcnow().to_pydatetime()
    db.commit()
    
    # Execute and return preview
    result = execute_preview(dataset, steps, db)
    
    # Remove non-serializable DataFrame from result
    df_full = result.pop("preview_full_df", None)
    
    # Calculate quality alerts on full dataset (already processed, no need for preview fallback)
    alerts = []
    if df_full is not None:
         try:
             alerts = check_quality_alerts(df_full)
         except Exception:
             alerts = []
        
    return {
        "pipeline_id": pipeline.id,
        "steps": steps,
        "quality_alerts": alerts,
        **result
    }

@router.post("/{pipeline_id}/apply/{dataset_id}")
def apply_pipeline_to_dataset(
    pipeline_id: str,
    dataset_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Apply an existing pipeline to a dataset (Validation & Replay).
    """
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Get current draft pipeline for this dataset
    draft = get_or_create_draft_pipeline(db, dataset_id)
    
    # Overwrite draft steps with imported steps
    # TODO: Add validation logic here (check columns existence)
    # For now, we assume user knows what they are doing or let it fail gracefully
    
    draft.steps = pipeline.steps
    draft.updated_at = pd.Timestamp.utcnow().to_pydatetime()
    db.commit()
    
    # Execute and return preview
    steps = json.loads(draft.steps)
    result = execute_preview(dataset, steps, db)
    
    # Remove non-serializable DataFrame
    df_full = result.pop("preview_full_df", None)
    
    # Calculate quality alerts on full dataset
    alerts = []
    if df_full is not None:
         try:
             alerts = check_quality_alerts(df_full)
         except Exception:
             alerts = []

    return {
        "pipeline_id": draft.id,
        "steps": steps,
        "message": "Pipeline applied successfully",
        "quality_alerts": alerts,
        **result
    }

@router.delete("/interactive/{dataset_id}/steps/{step_index}")
def remove_step(
    dataset_id: str,
    step_index: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Remove a step by index and return updated preview.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    pipeline = get_or_create_draft_pipeline(db, dataset_id)
    steps = json.loads(pipeline.steps)
    
    if 0 <= step_index < len(steps):
        steps.pop(step_index)
        pipeline.steps = json.dumps(steps)
        pipeline.updated_at = pd.Timestamp.utcnow().to_pydatetime()
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="Invalid step index")
        
    # Execute and return preview
    result = execute_preview(dataset, steps, db)
    
    # Remove non-serializable DataFrame from result
    df_full = result.pop("preview_full_df", None)
    
    # Calculate quality alerts on full dataset (already processed, no need for preview fallback)
    alerts = []
    if df_full is not None:
         try:
             alerts = check_quality_alerts(df_full)
         except Exception:
             alerts = []
        
    return {
        "pipeline_id": pipeline.id,
        "steps": steps,
        "quality_alerts": alerts,
        **result
    }

@router.post("/interactive/{dataset_id}/reset")
def reset_pipeline(
    dataset_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Clear all steps and return original preview.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    pipeline = get_or_create_draft_pipeline(db, dataset_id)
    
    pipeline.steps = "[]"
    pipeline.updated_at = pd.Timestamp.utcnow().to_pydatetime()
    db.commit()
    
    # Execute and return preview
    result = execute_preview(dataset, [], db)
    
    # Remove non-serializable DataFrame
    df_full = result.pop("preview_full_df", None)
    
    # Calculate alerts on full dataset (original data)
    alerts = []
    if df_full is not None:
        try:
            alerts = check_quality_alerts(df_full)
        except Exception:
            alerts = []
        
    return {
        "pipeline_id": pipeline.id,
        "steps": [],
        "quality_alerts": alerts,
        **result
    }
