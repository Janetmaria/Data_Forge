import json
import re
from dateutil import parser
import pandas as pd
from typing import List, Dict, Any

from app import schemas
from word2number import w2n

def detect_encoding(file_path: str) -> str:
    # Basic encoding detection fallback
    return "utf-8"

def parse_json_to_dataframe(data) -> pd.DataFrame:
    def flatten_data(d, parent_key='', sep='.'):
        items = []
        if isinstance(d, dict):
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    items.extend(flatten_data(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        elif isinstance(d, list):
            for i, v in enumerate(d):
                new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                if isinstance(v, (dict, list)):
                    items.extend(flatten_data(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        else:
            items.append((parent_key, d))
        return dict(items)

    if isinstance(data, list):
        flat_data = [flatten_data(item) for item in data]
        df = pd.DataFrame(flat_data)
    elif isinstance(data, dict):
        df = pd.DataFrame([flatten_data(data)])
    else:
        df = pd.DataFrame(data)
        
    cols = df.columns.tolist()
    to_drop = set()
    for col in cols:
        if '.' in col:
            parts = col.split('.')
            for i in range(1, len(parts)):
                parent = '.'.join(parts[:i])
                if parent in cols:
                    to_drop.add(parent)
    if to_drop:
        df = df.drop(columns=list(to_drop))

    return df

def auto_format_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    date_keywords = ['date', 'time', 'dob', 'created', 'updated', 'stamp', 'history']
    
    def try_parse(val):
        if pd.isna(val) or not isinstance(val, str): return None
        try:
            if not re.search(r'[a-zA-Z]{3}|\d{2,4}', val):
                return None
            clean_val = re.sub(r'(?i)(Purchased on|Order #[0-9]+ - |Date:|Originally:|On)', '', str(val)).strip()
            
            # Stricter rejection rules
            if not re.search(r'[-/.,:]', clean_val) and not re.search(r'(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', clean_val):
                # Not a recognized format unless it's exactly 8 digits YYYYMMDD
                if not re.match(r'^\d{8}$', clean_val):
                    return None
                    
            # Reject things that look like pure alphanumeric IDs even if they have a dash (e.g. EMP-001)
            if re.match(r'^[A-Za-z]+[-_]?\d+$', clean_val):
                return None
                
            # Reject simple number values that are not 8 digits
            if re.match(r'^\d+$', clean_val) and len(clean_val) != 8:
                return None
                
            dt = parser.parse(clean_val, fuzzy=True)
            if 1900 < dt.year < 2100:
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
        return None

    for col in df.columns:
        if df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]):
            sample = df[col].dropna().head(20)
            if sample.empty: continue
                
            is_date_name = any(kw in col.lower() for kw in date_keywords)
            parsed_sample = sample.apply(try_parse)
            valid_pct = parsed_sample.notna().mean()
            
            if valid_pct > 0.5 or (is_date_name and valid_pct > 0.2):
                def parse_and_fallback(val):
                    parsed = try_parse(val)
                    return parsed if parsed is not None else val
                df[col] = df[col].apply(parse_and_fallback)
    return df

def parse_file(file_path: str, file_format: str, encoding: str = "utf-8") -> pd.DataFrame:
    if file_format == "csv":
        df = pd.read_csv(file_path, encoding=encoding)
    elif file_format in ["xlsx", "xls"]:
        df = pd.read_excel(file_path)
    elif file_format == "json":
        # Load the raw JSON and flatten it automatically
        with open(file_path, "r", encoding=encoding) as f:
            data = json.load(f)
        df = parse_json_to_dataframe(data)
    else:
        raise ValueError("Unsupported file format")
        
    df = auto_format_date_columns(df)
    return df

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
                # Unhashable objects will become NaT
                try:
                    converted = pd.to_datetime(sample, errors='coerce')
                    valid_date_count = converted.notna().sum()
                    if valid_date_count >= len(sample) * 0.5 and valid_date_count > 0:
                        return "Date"
                except Exception:
                    pass
                    
            try:
                unique_count = series.nunique()
            except TypeError:
                unique_count = series.astype(str).nunique()
                
            if unique_count < 20:
                return "Categorical"
                
        return "Text"

def classify_dataset_domain(columns: List[Any]) -> str:
    col_names = [c.name.lower() for c in columns]
    
    domains = {
        "Healthcare / Medical": ["patient", "diagnosis", "doctor", "blood", "medical", "treatment", "symptom", "hospital", "icd", "mrn", "disease", "health"],
        "Banking / Finance": ["account", "balance", "transaction", "credit", "debit", "loan", "mortgage", "interest", "card", "iban", "swift", "finance", "currency", "investment", "fund", "equity", "bond", "stock", "deposit", "saving", "portfolio"],
        "E-commerce / Retail": ["order", "cart", "product", "sku", "price", "checkout", "shipping", "customer", "inventory", "sales", "discount"],
        "Human Resources": ["employee", "salary", "department", "manager", "hire", "payroll", "title", "role", "leave", "bonus", "hr"],
        "Telecommunications": ["call", "duration", "plan", "data", "usage", "roaming", "churn", "subscriber", "telecom"],
        "Logistics": ["shipment", "tracking", "route", "vehicle", "driver", "freight", "warehouse", "delivery", "transport"],
        "Education": ["student", "grade", "course", "teacher", "enrollment", "gpa", "school", "university", "class"]
    }
    
    scores = {d: 0 for d in domains}
    for name in col_names:
        for domain, keywords in domains.items():
             if any(kw in name for kw in keywords):
                 scores[domain] += 1
                 
    best_domain = max(scores.items(), key=lambda x: x[1])
    if best_domain[1] > 0:
        return best_domain[0]
        
    return "Generic / General Domain"

def profile_dataset(df: pd.DataFrame) -> List[schemas.DatasetColumnCreate]:
    columns = []
    for i, col_name in enumerate(df.columns):
        series = df[col_name]
        col_type = infer_column_type(series)
        
        null_count = int(series.isnull().sum())
        total_count = len(series)
        null_pct = (null_count / total_count) * 100 if total_count > 0 else 0
        
        try:
            unique_count = series.nunique()
        except TypeError:
            unique_count = series.astype(str).nunique()
        
        min_val = None
        max_val = None
        mean_val = None
        
        if col_type == "Numeric":
            min_val = str(series.min())
            max_val = str(series.max())
            mean_val = float(series.mean())
        elif col_type == "Date":
            try:
                min_val = str(series.min())
                max_val = str(series.max())
            except Exception:
                pass
            
        try:
            top_values = series.value_counts().head(5).to_dict()
        except TypeError:
            top_values = series.astype(str).value_counts().head(5).to_dict()
            
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
            
            for val in df[col].dropna():
                total_valid += 1
                
                # Check numeric
                if isinstance(val, (int, float)):
                    numeric_count += 1
                    continue
                try:
                    float(val)
                    numeric_count += 1
                    continue
                except (ValueError, TypeError):
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

    # 3. Numeric Regex Validation (detect strings like "unknown" in generic numeric columns)
    import re
    numeric_pattern = re.compile(r"^\s*-?\d+(\.\d+)?\s*$")
    numeric_keywords = ['age', 'price', 'amount', 'count', 'total', 'salary', 'score', 'qty', 'quantity']
    
    for col in df.columns:
        if df[col].dtype == 'object':
            is_numeric_name = any(kw in col.lower() for kw in numeric_keywords)
            
            valid_numeric = 0
            invalid_numeric = 0
            total_non_null = 0
            
            for val in df[col].dropna():
                total_non_null += 1
                if isinstance(val, (int, float)):
                    valid_numeric += 1
                elif isinstance(val, str) and numeric_pattern.match(str(val)):
                    valid_numeric += 1
                else:
                    invalid_numeric += 1
                    
            if total_non_null > 0:
                if is_numeric_name or (valid_numeric / total_non_null) > 0.5:
                    if invalid_numeric > 0:
                        alerts.append({
                            "entity": col,
                            "type": "invalid_numeric_format",
                            "missing_pct": (invalid_numeric / len(df)) * 100,
                            "recommended_action": "Use validate_format (numeric) to drop invalid rows, or convert_type (numeric)"
                        })

    # 4. Date Regex Validation
    date_pattern = re.compile(r"^\s*(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})\s*(?:T| )?(?:\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[\+-]\d{2}:\d{2})?)?\s*$")
    date_keywords = ['date', 'time', 'dob', 'created', 'updated', 'stamp']
    
    for col in df.columns:
        if df[col].dtype == 'object':
            is_date_name = any(kw in col.lower() for kw in date_keywords)
            valid_date = 0
            invalid_date = 0
            total_non_null = 0
            
            for val in df[col].dropna():
                total_non_null += 1
                if isinstance(val, str):
                    if date_pattern.match(str(val)):
                        valid_date += 1
                    else:
                        invalid_date += 1
                elif hasattr(val, 'year'): # datetime
                    valid_date += 1
                else:
                    invalid_date += 1
                    
            if total_non_null > 0:
                if is_date_name or (valid_date / total_non_null) > 0.5:
                    if invalid_date > 0 and invalid_date < total_non_null: # Avoid flagging 100% invalid if it's just a normal string col
                        alerts.append({
                            "entity": col,
                            "type": "invalid_date_format",
                            "missing_pct": (invalid_date / len(df)) * 100,
                            "recommended_action": "Use validate_format (date) to drop invalid rows, or convert_type (date)"
                        })

    # 5. Constant Columns (Zero Variance / Only 1 value)
    for col in df.columns:
        if len(df) > 0 and df[col].nunique(dropna=True) == 1:
            alerts.append({
                "entity": col,
                "type": "constant_column",
                "missing_pct": 0,
                "recommended_action": "Drop column (provides no variance/information for ML)"
            })
            
    # 6. High Cardinality Categoricals (ID-like strings)
    for col in df.columns:
        if df[col].dtype == 'object':
            unique_count = df[col].nunique()
            non_null_count = df[col].count()
            if non_null_count > 100 and unique_count > non_null_count * 0.9:
                alerts.append({
                    "entity": col,
                    "type": "high_cardinality",
                    "missing_pct": 0,
                    "recommended_action": "Drop column (likely an ID or primary key, not useful for ML encoding)"
                })

    return alerts
