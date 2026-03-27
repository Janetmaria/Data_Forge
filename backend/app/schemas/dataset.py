from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime

class DatasetColumnBase(BaseModel):
    name: str
    position: int
    detected_type: str
    overridden_type: Optional[str] = None
    null_count: int
    null_pct: float
    unique_count: int
    min_val: Optional[str] = None
    max_val: Optional[str] = None
    mean_val: Optional[float] = None
    top_values: Optional[str] = None  # JSON string

class DatasetColumnCreate(DatasetColumnBase):
    pass

class DatasetColumn(DatasetColumnBase):
    id: str
    dataset_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class DatasetBase(BaseModel):
    original_filename: str
    file_format: str
    encoding: str
    row_count: int
    col_count: int
    size_bytes: int
    domain: Optional[str] = None

class DatasetCreate(DatasetBase):
    stored_filename: str
    file_path: str

class Dataset(DatasetBase):
    id: str
    created_at: datetime
    columns: List[DatasetColumn] = []

    class Config:
        from_attributes = True

class DatasetDetail(Dataset):
    quality_alerts: List[Dict[str, Any]] = []

class DatasetUploadResponse(BaseModel):
    dataset: Dataset
    quality_alerts: List[Dict[str, Any]] = []
