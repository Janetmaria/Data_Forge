import shutil
import os
import uuid
import json
import pandas as pd
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.v1 import deps
from app.core.config import settings
from app.services.dataset_service import parse_file, infer_column_type, check_quality_alerts, classify_dataset_domain
from app.services.pipeline_service import execute_pipeline

router = APIRouter()

@router.delete("/{dataset_id}", response_model=schemas.Dataset)
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Delete a dataset and its associated file.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Delete physical file
    if os.path.exists(dataset.file_path):
        try:
            os.remove(dataset.file_path)
        except OSError as e:
            print(f"Error deleting file {dataset.file_path}: {e}")
            
    # Delete from DB
    db.delete(dataset)
    db.commit()
    return dataset

@router.post("/upload", response_model=schemas.DatasetUploadResponse)
def upload_dataset(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
) -> Any:
    # 1. Validate file extension
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls", ".json"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    # 2. Save file
    dataset_id = str(uuid.uuid4())
    stored_filename = f"{dataset_id}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. Parse and Profile
    try:
        df = parse_file(file_path, ext.lstrip("."))
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail=f"Could not parse file: {str(e)}")
    
    # 4. Create Dataset record
    dataset_in = schemas.DatasetCreate(
        original_filename=filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_format=ext.lstrip("."),
        encoding="utf-8",  # Detect later
        row_count=len(df),
        col_count=len(df.columns),
        size_bytes=os.path.getsize(file_path)
    )
    
    dataset = models.Dataset(
        id=dataset_id,
        **dataset_in.model_dump(),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # 5. Create Column records
    columns = []
    for i, col_name in enumerate(df.columns):
        series = df[col_name]
        col_type = infer_column_type(series)
        
        null_count = int(series.isnull().sum())
        total_count = len(series)
        null_pct = (null_count / total_count) * 100 if total_count > 0 else 0.0
        
        try:
            unique_count = series.nunique()
        except TypeError:
            unique_count = series.astype(str).nunique()
        
        min_val = None
        max_val = None
        mean_val = None
        
        # Simple profiling logic inline or use service
        if pd.api.types.is_numeric_dtype(series):
             min_val = str(series.min())
             max_val = str(series.max())
             mean_val = float(series.mean())
        
        try:
            top_values = series.value_counts().head(5).to_dict()
        except TypeError:
            top_values = series.astype(str).value_counts().head(5).to_dict()
            
        top_values_str = {str(k): int(v) for k, v in top_values.items()}
        
        col_obj = models.DatasetColumn(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            name=str(col_name),
            position=i,
            detected_type=col_type,
            null_count=null_count,
            null_pct=null_pct,
            unique_count=unique_count,
            min_val=min_val,
            max_val=max_val,
            mean_val=mean_val,
            top_values=json.dumps(top_values_str) # Store as JSON string
        )
        db.add(col_obj)
        columns.append(col_obj)
    
    # Set the dataset-level domain based on its columns
    dataset.domain = classify_dataset_domain(columns)
    db.commit()
    
    # 6. Check Quality Alerts
    alerts = check_quality_alerts(df)
    
    # Reload dataset with columns
    db.refresh(dataset)
    
    return {
        "dataset": dataset,
        "quality_alerts": alerts
    }

@router.get("/", response_model=List[schemas.Dataset])
def read_datasets(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve datasets.
    """
    datasets = db.query(models.Dataset).offset(skip).limit(limit).all()
    return datasets

@router.get("/{dataset_id}", response_model=schemas.DatasetDetail)
def read_dataset(
    dataset_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get dataset by ID with quality alerts.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Compute quality alerts on the fly
    try:
        df = parse_file(dataset.file_path, dataset.file_format)
        alerts = check_quality_alerts(df)
    except Exception:
        alerts = []
        
    return {
        "id": dataset.id,
        "original_filename": dataset.original_filename,
        "file_format": dataset.file_format,
        "encoding": dataset.encoding,
        "row_count": dataset.row_count,
        "col_count": dataset.col_count,
        "size_bytes": dataset.size_bytes,
        "domain": dataset.domain,
        "created_at": dataset.created_at,
        "columns": dataset.columns,
        "quality_alerts": alerts
    }

@router.get("/{dataset_id}/preview")
def preview_dataset(
    dataset_id: str,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a preview of the dataset rows.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # We need the entire dataset parsed correctly to avoid breaking json lists logic
        df = parse_file(dataset.file_path, dataset.file_format)
        df = df.head(limit)
            
        # Replace NaN with null for JSON serialization
        df = df.where(pd.notnull(df), None)
        
        return json.loads(df.to_json(orient="records"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read dataset: {str(e)}")

@router.post("/{dataset_id}/export")
def export_dataset(
    dataset_id: str,
    steps: List[schemas.PipelineStep],
    export_format: str = "csv",
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Execute pipeline and export dataset.
    """
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        # Load data
        df = parse_file(dataset.file_path, dataset.file_format)

        # Execute Pipeline
        pipeline_steps = [step.model_dump() for step in steps]
        df, _ = execute_pipeline(df, pipeline_steps)
        
        # Save to Export Dir
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"export_{dataset_id}_{timestamp}.{export_format}"
        file_path = os.path.join(settings.EXPORT_DIR, filename)
        
        if export_format == "csv":
            df.to_csv(file_path, index=False)
        elif export_format in ["xlsx", "xls"]:
            df.to_excel(file_path, index=False)
        elif export_format == "json":
            df.to_json(file_path, orient="records")
        else:
             raise HTTPException(status_code=400, detail="Unsupported export format")
             
        # Create Export Record
        export = models.Export(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            pipeline_id=None, # Ad-hoc export
            format=export_format,
            file_path=file_path
        )
        db.add(export)
        db.commit()

        return {"download_url": f"/api/v1/datasets/download/{filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/download/{filename}")
def download_file(
    filename: str,
    db: Session = Depends(deps.get_db),
):
    # Security check: Ensure filename is in EXPORT_DIR and not traversing up
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    file_path = os.path.join(settings.EXPORT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=filename)
