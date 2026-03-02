import uuid
from typing import List, Optional, Any, Dict, Mapping
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from types import MappingProxyType

class PipelineStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation: str
    params: Mapping[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parameter_checksum: Optional[str] = None
    previous_dtype: Optional[Dict[str, str]] = None
    new_dtype: Optional[Dict[str, str]] = None

    class Config:
        extra = "forbid"
        frozen = True

    @model_validator(mode='before')
    @classmethod
    def freeze_params(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'params' in data and isinstance(data['params'], dict):
                data['params'] = MappingProxyType(data['params'])
        return data

    @model_validator(mode='after')
    def enforce_mapping_proxy(self) -> 'PipelineStep':
        # Double check after validation because Pydantic might coerce back to dict
        if isinstance(self.params, dict):
             # Force conversion. Since model is frozen, we must use object.__setattr__
             object.__setattr__(self, 'params', MappingProxyType(self.params))
        return self

class PipelineBase(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_id: Optional[str] = None

class PipelineCreate(PipelineBase):
    steps: List[PipelineStep]
    
    @model_validator(mode='after')
    def validate_unique_step_ids(self) -> 'PipelineCreate':
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            from app.services.pipeline_service import DuplicateStepIDError
            raise DuplicateStepIDError("Pipeline contains duplicate step IDs")
        return self

class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[PipelineStep]] = None
    
    @model_validator(mode='after')
    def validate_unique_step_ids(self) -> 'PipelineUpdate':
        if self.steps:
            step_ids = [step.step_id for step in self.steps]
            if len(step_ids) != len(set(step_ids)):
                from app.services.pipeline_service import DuplicateStepIDError
                raise DuplicateStepIDError("Pipeline contains duplicate step IDs")
        return self

class Pipeline(PipelineBase):
    id: str
    created_at: datetime
    updated_at: datetime
    steps: str

    class Config:
        from_attributes = True

class PipelineExecuteResponse(BaseModel):
    pipeline_id: str
    execution_status: str
    rows_affected: int
    preview_data: Optional[str] = None  # JSON string of head(5)
