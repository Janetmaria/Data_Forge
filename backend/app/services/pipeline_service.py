import pandas as pd
import numpy as np
import hashlib
import json
from sklearn.impute import KNNImputer
from typing import Dict, Any, List, Optional
from num2words import num2words
from word2number import w2n

from app.services.missingness_indicator import add_missingness_indicator
from app.services.encoder import encode_column
from app.services.outlier_handler import handle_outliers
from app.services.imbalance_handler import handle_imbalance
from app.services.binner import bin_column
from app.services.timeseries_features import extract_datetime_components, create_lag_features, create_rolling_features

STRICT_MODE = True

class TypeMutationError(Exception):
    pass

class InvalidColumnTypeError(Exception):
    pass

class ReplayConflictError(Exception):
    pass

class ChecksumMismatchError(Exception):
    pass

class DuplicateStepIDError(ValueError):
    pass

class PipelineSchemaError(ValueError):
    pass

class DeterminismMismatchError(Exception):
    pass

def execute_step(df: pd.DataFrame, step: Dict[str, Any], context: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
    # Support both old format (direct dict) and new format (nested in step object)
    operation = step.get("operation")
    params = step.get("params", {})
    
    # Checksum validation if present
    if "parameter_checksum" in step and step["parameter_checksum"]:
        current_checksum = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        if current_checksum != step["parameter_checksum"]:
            raise ChecksumMismatchError(f"Step {step.get('step_id')} integrity check failed")

    context = context or {}

    # Strict Column Validation
    target_columns = params.get("columns", [])
    if target_columns:
        # Check if columns is a list, if it's None or empty skip
        if isinstance(target_columns, list):
            # Attempt case-insensitive match for missing columns (helpful for NLP commands)
            lower_cols = {str(c).lower(): c for c in df.columns}
            for i, c in enumerate(target_columns):
                if c not in df.columns and str(c).lower() in lower_cols:
                    target_columns[i] = lower_cols[str(c).lower()]
            
            missing_cols = [c for c in target_columns if c not in df.columns]
            if missing_cols:
                 raise ReplayConflictError(f"Columns {missing_cols} missing for operation '{operation}'")
            
            # Update params with corrected column names
            params["columns"] = target_columns
        elif target_columns is None:
            # Some operations might send None for columns if optional
            pass

    # Capture types before
    types_before = df.dtypes.apply(lambda x: str(x)).to_dict()

    if operation == "drop_missing":
        columns = params.get("columns")
        if columns:
            df = df.dropna(subset=columns)
        else:
            df = df.dropna()
    
    elif operation == "fill_missing":
        columns = params.get("columns")
        value = params.get("value")
        method = params.get("method") # mean, median, mode, constant
        
        for col in columns:
            if method == "constant":
                df[col] = df[col].fillna(value)
            elif method == "mean":
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
            elif method == "median":
                 if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
            elif method == "mode":
                mode_val = df[col].mode()
                if not mode_val.empty:
                    df[col] = df[col].fillna(mode_val[0])

    elif operation == "knn_impute":
        columns = params.get("columns", [])
        n_neighbors = int(params.get("n_neighbors", 5))
        if columns:
            # KNN needs context (all available numeric columns) to find nearest neighbors
            # rather than just the target column.
            all_numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            
            # Ensure our target columns are actually numeric
            target_cols = [c for c in columns if c in all_numeric_cols]
            
            if target_cols and all_numeric_cols:
                imputer = KNNImputer(n_neighbors=n_neighbors)
                # Fit transform on ALL numeric columns to calculate distances
                imputed_data = imputer.fit_transform(df[all_numeric_cols])
                
                # Extract only the targeted columns back into the main DataFrame
                # We need to map the target column names to their index in all_numeric_cols
                for col in target_cols:
                    col_index = all_numeric_cols.index(col)
                    df[col] = imputed_data[:, col_index]

    elif operation == "drop_duplicates":
        subset = params.get("columns", None) # Optional subset of columns to check
        if subset == []: subset = None
        
        try:
            df = df.drop_duplicates(subset=subset)
        except TypeError:
            cols_to_check = df.columns if subset is None else subset
            mask = ~df[cols_to_check].astype(str).duplicated()
            df = df[mask]

    elif operation == "text_case":
        columns = params.get("columns", [])
        case_type = params.get("case", "lower") # lower, upper, title
        for col in columns:
            if col in df.columns and pd.api.types.is_string_dtype(df[col]):
                if case_type == "lower":
                    df[col] = df[col].str.lower()
                elif case_type == "upper":
                    df[col] = df[col].str.upper()
                elif case_type == "title":
                    df[col] = df[col].str.title()
                    
    elif operation == "extract_datetime":
        columns = params.get("columns", [])
        for col in columns:
            if col in df.columns:
                try:
                    # Convert to datetime if it isn't already
                    dt_series = pd.to_datetime(df[col], errors='coerce')
                    df[f"{col}_year"] = dt_series.dt.year
                    df[f"{col}_month"] = dt_series.dt.month
                    df[f"{col}_day"] = dt_series.dt.day
                except Exception:
                    pass

    elif operation == "time_series_fill":
        columns = params.get("columns", [])
        method = params.get("method", "ffill") # ffill (forward) or bfill (backward)
        for col in columns:
            if col in df.columns:
                if method == "ffill":
                    df[col] = df[col].ffill()
                elif method == "bfill":
                    df[col] = df[col].bfill()

    elif operation == "convert_type":
        columns = params.get("columns", [])
        target_type = params.get("type") # numeric, date, string, numeric_to_text, text_to_numeric
        for col in columns:
            if col in df.columns:
                if target_type == "numeric":
                    # More intelligent numeric conversion
                    def convert_to_numeric(x):
                        if pd.isnull(x): 
                            return np.nan
                        if isinstance(x, (int, float)): 
                            return x
                        if isinstance(x, str):
                            x = x.strip()
                            # Skip empty strings
                            if not x:
                                return np.nan
                            # Try to convert strings that look like numbers
                            try:
                                # Handle commas in numbers (e.g., "1,234.56")
                                if ',' in x:
                                    return float(x.replace(',', ''))
                                # Handle percentages (e.g., "50%")
                                if x.endswith('%'):
                                    return float(x.rstrip('%')) / 100
                                # Handle currency symbols (e.g., "$123.45")
                                if x.startswith('$') or x.startswith('€') or x.startswith('£'):
                                    return float(x[1:].replace(',', ''))
                                # Regular numeric conversion
                                return float(x)
                            except ValueError:
                                # If it can't be converted, replace with null
                                return np.nan
                        # For other types, try conversion but keep original if fails
                        try:
                            return float(x)
                        except (ValueError, TypeError):
                            return np.nan
                    
                    df[col] = df[col].apply(convert_to_numeric)
                elif target_type == "date":
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                elif target_type == "string":
                    df[col] = df[col].astype(str)
                elif target_type == "numeric_to_text":
                    # 1 -> "one", 30 -> "thirty", handles mixed columns
                    def convert_mixed_to_text(x):
                        if pd.isnull(x): 
                            return x
                        if isinstance(x, (int, float)): 
                            try:
                                result = num2words(int(x)) if x == int(x) else num2words(x)
                                print(f"Converting numeric {x} to words: {result}")
                                return result
                            except Exception as e:
                                print(f"Error converting {x} to words: {e}")
                                return str(x)
                        if isinstance(x, str):
                            x = x.strip()
                            if not x:
                                return x
                            # First try to convert string to number (handles "88", "25", etc.)
                            try:
                                num = float(x)
                                result = num2words(int(num)) if num == int(num) else num2words(num)
                                print(f"Converting string number '{x}' to words: {result}")
                                return result
                            except ValueError:
                                pass
                            # Try word to number to see if it's already words
                            try:
                                w2n.word_to_num(x.lower())
                                # If successful, it's already words, so return as-is
                                print(f"Keeping existing words: {x}")
                                return x
                            except ValueError:
                                pass
                            # If can't convert, return original string
                            print(f"Keeping original string: {x}")
                            return x
                        # For other types, convert to string
                        return str(x)

                    print(f"Applying numeric_to_text conversion to column: {col}")
                    df[col] = df[col].apply(convert_mixed_to_text)
                    print(f"Conversion completed for column: {col}")
                elif target_type == "text_to_numeric":
                    # "one" -> 1, "thirty" -> 30, handles mixed columns
                    def convert_mixed_to_numeric(x):
                        if pd.isnull(x): 
                            return np.nan
                        if isinstance(x, (int, float)): 
                            return x
                        if isinstance(x, str):
                            x = x.strip().lower()
                            if not x:
                                return np.nan
                            # Try word to number first (e.g., "thirty" -> 30)
                            try:
                                return w2n.word_to_num(x)
                            except ValueError:
                                pass
                            # Try simple numeric conversion (e.g., "30" -> 30.0)
                            try:
                                return float(x)
                            except ValueError:
                                pass
                            # If can't convert, return original string (or could return np.nan)
                            return x
                        # For other types, try conversion
                        try:
                            return float(x)
                        except (ValueError, TypeError):
                            return x

                    df[col] = df[col].apply(convert_mixed_to_numeric)

    elif operation == "round_numeric":
        columns = params.get("columns", [])
        decimals = int(params.get("decimals", 2))
        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].round(decimals)

    elif operation == "validate_format":
        columns = params.get("columns", [])
        format_type = params.get("format_type", "email")
        action = params.get("action", "drop_invalid") # 'drop_invalid' or 'set_null'
        
        # Super-permissive but industry-standard regex definitions
        patterns = {
            "email": r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
            "phone": r"(^\+?[\d\s\-\(\)]{7,20}$)",
            "url": r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\\/\w \.-]*)*\/?$",
            "ip_address": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
            "credit_card": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})$",
            "aadhaar": r"^\s*[2-9]{1}[0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\s*$",
            "numeric": r"^\s*-?\d+(\.\d+)?\s*$",
            "date": r"^\s*(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})\s*(?:T| )?(?:\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[\+-]\d{2}:\d{2})?)?\s*$",
            "custom": params.get("pattern", r".*")
        }
        
        pattern = patterns.get(format_type, patterns["custom"])
        
        for col in columns:
            if col in df.columns:
                # Evaluate matches. Treating True as valid.
                is_valid = df[col].astype(str).str.match(pattern, na=False)
                
                if action == "drop_invalid":
                    # Drops rows that are explicitly invalid (it also drops NaNs by default since na=False)
                    df = df[is_valid]
                elif action == "set_null":
                    # Keep the row but blast the invalid cell
                    df.loc[~is_valid, col] = np.nan

    elif operation == "extract_numeric":
        """
        Smart-parse a numeric value out of messy strings like:
          '$4308.85'       -> 4308.85  (keep)
          '3868.9 usd'     -> 3868.9   (keep)
          'Price: 45.0'    -> 45.0     (keep)
          'Rs. 1,234.56'   -> 1234.56  (keep)
          '34675 usd!!!'   -> invalid  (null/drop)
          'FREE'           -> invalid  (null/drop)
        Logic: strip known noise (currency symbols, labels, whitespace, commas),
        then extract the first number pattern. If what remains after extracting
        the number contains ONLY known harmless chars (letters, spaces, known symbols),
        it's valid. If it contains junk like !!!, ???, etc., it's invalid.
        on_invalid: 'null' (set cell to NaN, keep row) | 'drop' (remove row entirely)
        """
        import re
        columns = params.get("columns", [])
        on_invalid = params.get("on_invalid", "null")  # 'null' or 'drop'

        # Regex to extract a number (optional sign, digits, optional decimal)
        NUMBER_RE = re.compile(r'[-+]?\d[\d,]*(?:\.\d+)?')
        # Allowed surrounding characters: letters (currency names, labels), spaces, common symbols
        ALLOWED_NOISE_RE = re.compile(r'^[\w\s$€£₹¥₩₪%,.\-\+\/\(\)@#&:]*$')

        def try_extract(val):
            if pd.isnull(val):
                return np.nan
            s = str(val).strip()
            if not s:
                return np.nan
            # Find a numeric pattern
            match = NUMBER_RE.search(s)
            if not match:
                return np.nan  # No number found at all (e.g. 'FREE', 'N/A')
            # Check the surrounding noise for garbage characters
            noise = s[:match.start()] + s[match.end():]
            if not ALLOWED_NOISE_RE.match(noise):
                return np.nan  # Garbage chars in the noise (e.g. '!!!')
            # Convert commas in number (e.g. '1,234.56' -> 1234.56)
            num_str = match.group(0).replace(',', '')
            try:
                return float(num_str)
            except ValueError:
                return np.nan

        for col in columns:
            if col in df.columns:
                df[col] = df[col].apply(try_extract)
                if on_invalid == "drop":
                    df = df.dropna(subset=[col])

    elif operation == "remove_outliers_iqr":
        columns = params.get("columns", [])
        multiplier = float(params.get("multiplier", 1.5))
        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - (multiplier * IQR)
                upper_bound = Q3 + (multiplier * IQR)
                # Keep only rows within bounds or rows that are NaN (don't drop NaNs here)
                df = df[(df[col].isna()) | ((df[col] >= lower_bound) & (df[col] <= upper_bound))]

    elif operation == "standard_scale":
        columns = params.get("columns", [])
        from sklearn.preprocessing import StandardScaler
        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                df[[col]] = StandardScaler().fit_transform(df[[col]])

    elif operation == "normalize":
        # Min-Max Scaling
        columns = params.get("columns", [])
        feature_min = float(params.get("feature_min", 0.0))
        feature_max = float(params.get("feature_max", 1.0))
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val != min_val:
                    # Scale to 0-1
                    std_val = (df[col] - min_val) / (max_val - min_val)
                    # Scale to target
                    df[col] = std_val * (feature_max - feature_min) + feature_min
                else:
                    df[col] = feature_min
    
    elif operation == "rename_columns":
        mapping = params.get("mapping", {})
        df = df.rename(columns=mapping)
    
    elif operation == "drop_columns":
        columns = params.get("columns", [])
        df = df.drop(columns=columns, errors='ignore')

    elif operation == "filter_rows":
        condition = params.get("condition") # e.g. "age > 30"
        if condition:
            try:
                df = df.query(condition)
            except Exception:
                pass # Ignore invalid queries for now to prevent crash
    
    elif operation == "merge":
        # Supports 'inner', 'left', 'right', 'outer'
        # Expects: secondary_dataset_id, how, left_on, right_on
        secondary_id = params.get("secondary_dataset_id")
        how = params.get("how", "inner")
        left_on = params.get("left_on")
        right_on = params.get("right_on")
        
        if secondary_id and secondary_id in context:
            other_df = context[secondary_id]
            
            # If keys are same, we can use 'on'. If different, left_on/right_on
            if left_on and right_on:
                # Ensure keys exist
                if left_on in df.columns and right_on in other_df.columns:
                    # Strict Type Validation for Merges
                    left_type = df[left_on].dtype
                    right_type = other_df[right_on].dtype
                    
                    is_left_num = pd.api.types.is_numeric_dtype(left_type)
                    is_right_num = pd.api.types.is_numeric_dtype(right_type)
                    
                    is_left_str = pd.api.types.is_string_dtype(left_type) or pd.api.types.is_object_dtype(left_type)
                    is_right_str = pd.api.types.is_string_dtype(right_type) or pd.api.types.is_object_dtype(right_type)
                    
                    if (is_left_num != is_right_num) and (is_left_str != is_right_str):
                        raise InvalidColumnTypeError(f"Incompatible merge keys: '{left_on}' ({left_type}) and '{right_on}' ({right_type})")
                        
                    # Rename overlapping columns to avoid collision if not joining on them
                    # Pandas adds suffixes automatically (_x, _y), but let's be explicit if needed?
                    # Default suffixes are fine for now.
                    df = pd.merge(df, other_df, left_on=left_on, right_on=right_on, how=how)
            elif left_on and left_on in df.columns and left_on in other_df.columns:
                 # Assume same key name
                 df = pd.merge(df, other_df, on=left_on, how=how)
                 
    elif operation == "concat":
        # Vertical concatenation (Union)
        secondary_id = params.get("secondary_dataset_id")
        axis = params.get("axis", 0) # 0 for rows, 1 for cols
        
        if secondary_id and secondary_id in context:
            other_df = context[secondary_id]
            df = pd.concat([df, other_df], axis=axis, ignore_index=True)

    elif operation == 'add_missingness_indicator':
        df, _ = add_missingness_indicator(
            df=df,
            columns=params['columns'],
            drop_original=params.get('drop_original', False),
        )

    elif operation == 'encode_categorical':
        df, _ = encode_column(
            df=df, column=params['column'], method=params['method'],
            ordered_categories=params.get('ordered_categories'),
            target_column=params.get('target_column'),
            drop_first=params.get('drop_first', True),
            max_categories=params.get('max_categories', 50),
        )

    elif operation == 'handle_outliers':
        df, _ = handle_outliers(
            df=df, columns=params['columns'],
            method=params.get('method','iqr'), fold=params.get('fold',1.5),
            strategy=params.get('strategy','cap'),
        )

    elif operation == 'handle_imbalance':
        target_col = params['target_column']
        # Re-derive feature columns from the *live* df at execution time.
        # The params snapshot may be stale (columns dropped / added by prior steps).
        # Rules:
        #   1. Must currently exist in df
        #   2. Must be numeric (SMOTE only works on numeric features)
        #   3. Must not be the target column
        #   4. Honour an optional explicit exclude list
        explicit_cols = params.get('feature_columns') or []
        exclude = set(params.get('exclude_columns', []))
        exclude.add(target_col)

        if explicit_cols:
            # Filter the explicit list down to columns that still exist and are numeric
            feature_cols = [
                c for c in explicit_cols
                if c in df.columns
                and pd.api.types.is_numeric_dtype(df[c])
                and c not in exclude
            ]
        else:
            # Auto-detect: all numeric columns except the target
            feature_cols = [
                c for c in df.columns
                if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude
            ]

        if not feature_cols:
            raise ValueError(
                "handle_imbalance: no valid numeric feature columns found. "
                "Encode categorical columns and impute missing values first."
            )

        # Auto-clamp k_neighbors so SMOTE doesn't crash on small minority classes.
        # e.g. if minority class has 3 rows, k_neighbors must be at most 2.
        requested_k = params.get('k_neighbors', 5)
        strategy = params.get('strategy', 'smote')
        if strategy in ('smote', 'smote_then_undersample'):
            from collections import Counter
            class_counts = Counter(df[target_col].dropna())
            if class_counts:
                min_class_size = min(class_counts.values())
                safe_k = max(1, min(requested_k, min_class_size - 1))
                if safe_k != requested_k:
                    print(f"[handle_imbalance] Auto-adjusted k_neighbors from {requested_k} → {safe_k} "
                          f"(minority class size = {min_class_size})")
            else:
                safe_k = requested_k
        else:
            safe_k = requested_k

        df, _ = handle_imbalance(
            df=df, target_col=target_col, feature_cols=feature_cols,
            strategy=strategy,
            k_neighbors=safe_k,
            sampling_strategy=params.get('sampling_strategy', 'auto'),
        )

    elif operation == 'bin_column':
        df, _ = bin_column(
            df=df, column=params['column'], strategy=params.get('strategy','equal_width'),
            n_bins=params.get('n_bins',5), labels=params.get('labels'),
            custom_boundaries=params.get('custom_boundaries'), output_column=params.get('output_column'),
            drop_original=params.get('drop_original',False),
        )

    elif operation == 'extract_datetime_components':
        df, _ = extract_datetime_components(
            df=df, column=params['column'],
            components=params['components'])

    elif operation == 'create_lag_features':
        df, _ = create_lag_features(
            df=df, column=params['column'], lags=params['lags'], sort_by=params.get('sort_by'))

    elif operation == 'create_rolling_features':
        df, _ = create_rolling_features(
            df=df, column=params['column'], windows=params['windows'],
            stats=params.get('stats',['mean','std']),
            min_periods=params.get('min_periods',1), sort_by=params.get('sort_by'))

    # Post-Execution Type Check
    types_after = df.dtypes.apply(lambda x: str(x)).to_dict()
    
    # We allow intentional type conversions
    # Operations that intentionally change column dtypes are excluded from the strict
    # float→object type mutation guard. bin_column produces string labels from floats,
    # encode_categorical produces int/float from strings, extract_datetime_components
    # extracts numeric components from dates.
    INTENTIONAL_TYPE_CHANGE_OPS = (
        "convert_type", "extract_numeric", "bin_column",
        "encode_categorical", "extract_datetime_components",
    )
    if operation not in INTENTIONAL_TYPE_CHANGE_OPS:
        for col, dtype_pre in types_before.items():
            if col in types_after:
                dtype_post = types_after[col]
                # Allow float->float, int->int, object->object
                # But flag float->object (unless intentional) or int->float (maybe ok for NaNs but risky)
                
                # Critical: Silent mutation float->object (e.g. fillna with string)
                if "float" in dtype_pre and "object" in dtype_post:
                    if STRICT_MODE:
                         raise TypeMutationError(f"Implicit cast forbidden: {col} changed from {dtype_pre} to {dtype_post}")
    
    return df

def execute_pipeline(df: pd.DataFrame, steps: List[Dict[str, Any]], context: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
    # Validate Pipeline Schema
    step_ids = [s.get("step_id") for s in steps if s.get("step_id")]
    if len(step_ids) != len(set(step_ids)):
        raise DuplicateStepIDError("Pipeline contains duplicate step IDs")

    for step in steps:
        # Validate Required Fields
        if "operation" not in step:
            raise PipelineSchemaError("Step missing required field 'operation'")
            
        try:
            df = execute_step(df, step, context)
        except Exception as e:
            # If a step fails, print the error and stop the pipeline execution,
            # but crucially, RETURN the dataframe up to this point. 
            # This prevents the entire workspace from bricking with a 422 if a saved
            # step becomes invalid, allowing the user to delete the bad step in the UI.
            print(f"Pipeline Execution Error at step '{step.get('operation')}': {e}")
            break
            
    return df
