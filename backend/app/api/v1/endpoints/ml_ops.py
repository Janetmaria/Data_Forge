from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict
from app.api.v1 import deps
from app import models
from app.schemas.inference import InferenceReport
from app.services.inferencer import run_full_inference

router = APIRouter()

_inference_cache: Dict[str, InferenceReport] = {}

@router.get("/{dataset_id}/infer", response_model=InferenceReport)
def get_inference(
    dataset_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    # Check dataset auth/existence
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if dataset_id in _inference_cache:
        return _inference_cache[dataset_id]
        
    try:
        # Load the latest pipeline transformed preview directly
        from app.api.v1.endpoints.pipelines import execute_preview, get_or_create_draft_pipeline
        import json
        
        pipeline = get_or_create_draft_pipeline(db, dataset_id)
        if not pipeline.steps:
            steps = []
        else:
            try:
                steps = json.loads(pipeline.steps)
            except json.JSONDecodeError:
                steps = []
                
        # Run pipeline
        res = execute_preview(dataset, steps, db, limit=100000)
        df_full = res.get("preview_full_df")
        
        if df_full is None:
            from app.services.dataset_service import parse_file
            df_full = parse_file(dataset.file_path, dataset.file_format)
            
        report = run_full_inference(df_full)
        _inference_cache[dataset_id] = report
        return report
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
