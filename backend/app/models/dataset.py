from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, unique=True, nullable=False)
    file_path = Column(String, nullable=False)
    file_format = Column(String, nullable=False)  # csv, xlsx, json
    encoding = Column(String, default="utf-8")
    row_count = Column(Integer, nullable=False)
    col_count = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    domain = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    pipelines = relationship("Pipeline", back_populates="dataset")
    exports = relationship("Export", back_populates="dataset")
    logs = relationship("TransformationLog", back_populates="dataset")
