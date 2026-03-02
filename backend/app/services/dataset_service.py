import os
import uuid
import json
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from num2words import num2words
from word2number import w2n

def detect_encoding(file_path: str) -> str:
    # Basic encoding detection fallback
    return "utf-8"

def parse_file(file_path: str, file_format: str, encoding: str = "utf-8") -> pd.DataFrame:
    if file_format == "csv":
        return pd.read_csv(file_path, encoding=encoding)
    elif file_format in ["xlsx", "xls"]:
        return pd.read_excel(file_path)
    elif file_format == "json":
        return pd.read_json(file_path)
    else:
        raise ValueError("Unsupported file format")

def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "Numeric"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "Date"
    elif pd.api.types.is_bool_dtype(series):
        return "Boolean"
    else:
        # If it's a string object, pandas might not have automatically caught dates
        if pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            sample = series.dropna().head(50)
            if not sample.empty:
                # Convert to datetime with coerce (invalid strings become NaT)
                converted = pd.to_datetime(sample, errors='coerce')
                # If more than 50% of the sample successfully converted to a Date
                valid_date_count = converted.notna().sum()
                if valid_date_count >= len(sample) * 0.5 and valid_date_count > 0:
                    return "Date"
                    
            if series.nunique() < 20:
                return "Categorical"
                
        return "Text"

def profile_dataset(df: pd.DataFrame) -> List[schemas.DatasetColumnCreate]:
    columns = []
    for i, col_name in enumerate(df.columns):
        series = df[col_name]
        col_type = infer_column_type(series)
        
        null_count = int(series.isnull().sum())
        total_count = len(series)
        null_pct = (null_count / total_count) * 100 if total_count > 0 else 0
        unique_count = series.nunique()
        
        min_val = None
        max_val = None
        mean_val = None
        
        if col_type == "Numeric":
            min_val = str(series.min())
            max_val = str(series.max())
            mean_val = float(series.mean())
        elif col_type == "Date":
            min_val = str(series.min())
            max_val = str(series.max())
            
        top_values = series.value_counts().head(5).to_dict()
        # Convert keys to string for JSON serialization
        top_values_str = {str(k): int(v) for k, v in top_values.items()}
        
        columns.append(schemas.DatasetColumnCreate(
            name=col_name,
            position=i,
            detected_type=col_type,
            null_count=null_count,
            null_pct=null_pct,
            unique_count=unique_count,
            min_val=min_val,
            max_val=max_val,
            mean_val=mean_val,
            top_values=json.dumps(top_values_str)
        ))
    return columns

def check_quality_alerts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    alerts = []
    
    # 1. Missing Values
    for col in df.columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            null_pct = (null_count / len(df)) * 100
            if null_pct >= 50:
                alerts.append({
                    "entity": col,
                    "type": "missing_values",
                    "missing_pct": float(null_pct),
                    "recommended_action": "Drop column or Fill with Constant"
                })
            elif null_pct > 0:
                 alerts.append({
                    "entity": col,
                    "type": "missing_values",
                    "missing_pct": float(null_pct),
                    "recommended_action": "Fill with Mean/Median or Impute"
                })

    # 2. Mixed Data Types (Numeric vs Worded Numbers)
    for col in df.columns:
        # Check if column is object type (potential mixed)
        if df[col].dtype == 'object':
            numeric_count = 0
            worded_count = 0
            total_valid = 0
            
            for val in df[col]:
                if pd.isnull(val): continue
                total_valid += 1
                
                # Check numeric
                if isinstance(val, (int, float)):
                    numeric_count += 1
                    continue
                try:
                    float(val)
                    numeric_count += 1
                    continue
                except ValueError:
                    pass
                
                # Check worded number
                try:
                    w2n.word_to_num(str(val))
                    worded_count += 1
                except ValueError:
                    pass
            
            if total_valid > 0:
                # Case A: Mostly Numeric, some Worded
                if numeric_count > worded_count and worded_count > 0:
                     alerts.append({
                        "entity": col,
                        "type": "mixed_type_numeric",
                        "missing_pct": 0, # Not missing, but malformed
                        "recommended_action": "Convert entire column to Numeric (Text to Numeric)"
                    })
                # Case B: Mostly Worded, some Numeric
                elif worded_count > numeric_count and numeric_count > 0:
                     alerts.append({
                        "entity": col,
                        "type": "mixed_type_worded",
                        "missing_pct": 0,
                        "recommended_action": "Convert entire column to Numeric (Text to Numeric)"
                    })

    return alerts
