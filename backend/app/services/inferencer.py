import pandas as pd
import numpy as np
from difflib import get_close_matches
import logging
import scipy.stats
from typing import List, Dict, Any
from app.schemas.inference import DomainResult, Inference, InferenceReport

logger = logging.getLogger(__name__)

def col_matches(col_name: str, keywords: list, cutoff=0.8) -> bool:
    """Fuzzy match column names against a list of keywords."""
    normalized = str(col_name).lower().replace('_', ' ').replace('-', ' ')
    words = normalized.split()
    return any(get_close_matches(word, keywords, n=1, cutoff=cutoff) for word in words)

def detect_domain(df: pd.DataFrame) -> DomainResult:
    """Detect the dataset domain using weighted rules."""
    if df.empty:
        return DomainResult(domain='generic', confidence=1.0, evidence=["Dataset is empty"])

    scores = {'hr': 0.0, 'finance': 0.0, 'healthcare': 0.0, 'ecommerce': 0.0, 'iot_sensor': 0.0}
    evidence = {'hr': [], 'finance': [], 'healthcare': [], 'ecommerce': [], 'iot_sensor': []}

    sample_df = df.head(1000)
    row_count = len(df)
    
    # Pre-compute column names and types
    cols = df.columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    bool_cols = df.select_dtypes(include=[bool, object]).columns # approximation
    date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns
    
    # HR Signals
    hr_keywords = [
        'employee', 'emp_id', 'staff', 'personnel', 'worker', 'headcount',
        'salary', 'compensation', 'pay', 'wage', 'ctc', 'annual_income',
        'department', 'dept', 'division', 'team', 'business_unit',
        'hire_date', 'joining_date', 'join_date', 'start_date', 'tenure',
        'churn', 'attrition', 'resigned', 'termination', 'left_company',
        'performance', 'rating', 'score', 'appraisal',
        'age', 'gender', 'designation', 'title', 'role', 'level', 'grade'
    ]
    for c in cols:
        if col_matches(c, hr_keywords):
            scores['hr'] += 0.15
            evidence['hr'].append(f"Column '{c}' matches HR terminology")
            break

    for c in numeric_cols:
        col_data = sample_df[c].dropna()
        if not col_data.empty:
            if col_data.between(10000, 10000000).mean() > 0.5:
                scores['hr'] += 0.20
                evidence['hr'].append(f"Column '{c}' has values typical of salaries")
                break
            
    for c in numeric_cols:
        col_data = sample_df[c].dropna()
        if not col_data.empty:
            if 20 <= col_data.mean() <= 65 and col_data.max() < 100:
                scores['hr'] += 0.15
                evidence['hr'].append(f"Column '{c}' has values typical of age")
                break

    for c in sample_df.columns:
        valid_vals = sample_df[c].dropna().astype(str).str.lower()
        if valid_vals.isin(['0','1','true','false','yes','no','active','inactive']).mean() > 0.8:
            scores['hr'] += 0.10
            evidence['hr'].append(f"Found binary column '{c}' typical of HR status features")
            break

    if row_count < 100000:
        scores['hr'] += 0.05
        evidence['hr'].append("Dataset size is consistent with HR records")

    # Finance Signals
    fin_keywords = [
        'transaction', 'txn', 'payment', 'transfer', 'amount', 'debit', 'credit',
        'balance', 'account', 'account_no', 'account_id', 'iban', 'swift',
        'merchant', 'vendor', 'payee', 'sender', 'receiver',
        'fraud', 'is_fraud', 'fraudulent', 'anomaly', 'suspicious',
        'currency', 'fx_rate', 'exchange',
        'invoice', 'order_id', 'reference', 'ref_no'
    ]
    for c in cols:
        if col_matches(c, fin_keywords):
            scores['finance'] += 0.15
            evidence['finance'].append(f"Column '{c}' matches Finance terminology")
            break

    for c in numeric_cols:
        col_data = sample_df[c].dropna()
        if not col_data.empty and (col_data > 0).mean() > 0.8:
            # Check for 2 decimal places approximation (modulo 1)
            # A strict check is hard without string conversions, so we look for float types
            if pd.api.types.is_float_dtype(col_data):
                scores['finance'] += 0.20
                evidence['finance'].append(f"Column '{c}' contains positive floats typical of monetary amounts")
                break

    # Check for currency codes
    currency_codes = {'usd', 'eur', 'gbp', 'inr', 'jpy', 'aud', 'cad', 'chf'}
    for c in sample_df.select_dtypes(include=[object]).columns:
        if sample_df[c].astype(str).str.lower().isin(currency_codes).any():
            scores['finance'] += 0.15
            evidence['finance'].append(f"Column '{c}' contains currency codes")
            break

    if len(date_cols) > 0:
        for c in numeric_cols:
            if col_matches(c, ['amount', 'txn', 'transaction', 'transfer']):
                scores['finance'] += 0.15
                evidence['finance'].append("Contains both date and monetary amount patterns")
                break

    # Healthcare Signals
    hc_keywords = [
        'patient', 'patient_id', 'mrn', 'medical_record',
        'diagnosis', 'icd', 'icd_code', 'icd9', 'icd10', 'cpt', 'drg',
        'admission', 'discharge', 'los', 'length_of_stay',
        'medication', 'drug', 'prescription', 'dosage',
        'lab', 'test', 'result', 'specimen', 'pathology',
        'doctor', 'physician', 'provider', 'npi',
        'blood_pressure', 'bp', 'heart_rate', 'hr_bpm', 'glucose',
        'bmi', 'weight_kg', 'height_cm', 'vital'
    ]
    for c in cols:
        if col_matches(c, hc_keywords):
            scores['healthcare'] += 0.15
            evidence['healthcare'].append(f"Column '{c}' matches Healthcare terminology")
            break

    for c in numeric_cols:
        col_data = sample_df[c].dropna()
        if not col_data.empty and col_data.between(60, 200).mean() > 0.8:
            scores['healthcare'] += 0.15
            evidence['healthcare'].append(f"Column '{c}' has values typical of heart rate or BP")
            break
        if not col_data.empty and col_data.between(50, 500).mean() > 0.8:
            scores['healthcare'] += 0.10
            evidence['healthcare'].append(f"Column '{c}' has values suggesting medical lab ranges")
            break

    # Ecommerce Signals
    ec_keywords = [
        'product', 'product_id', 'sku', 'asin', 'item', 'listing',
        'customer', 'customer_id', 'buyer', 'user_id', 'shopper',
        'order', 'order_id', 'cart', 'basket', 'purchase',
        'price', 'unit_price', 'list_price', 'discount', 'promo',
        'quantity', 'qty', 'units_sold', 'stock', 'inventory',
        'category', 'subcategory', 'brand', 'seller',
        'rating', 'review', 'stars', 'feedback',
        'return', 'refund', 'cancellation'
    ]
    for c in cols:
        if col_matches(c, ec_keywords):
            scores['ecommerce'] += 0.15
            evidence['ecommerce'].append(f"Column '{c}' matches Ecommerce terminology")
            break

    for c in numeric_cols:
        col_data = sample_df[c].dropna()
        if not col_data.empty and col_data.between(0, 100).mean() > 0.8:
            scores['ecommerce'] += 0.10
            evidence['ecommerce'].append(f"Column '{c}' has values typical of percentage/rating")
            break

    # Check for qty (small ints) and price (floats) pattern
    has_small_ints = False
    has_floats = False
    for c in numeric_cols:
        col_data = sample_df[c].dropna()
        if not col_data.empty:
            if pd.api.types.is_integer_dtype(col_data) and col_data.between(1, 100).mean() > 0.8:
                has_small_ints = True
            if pd.api.types.is_float_dtype(col_data):
                has_floats = True
    if has_small_ints and has_floats:
        scores['ecommerce'] += 0.15
        evidence['ecommerce'].append("Dataset contains separate quantity and price indicators")

    # IoT / Sensor Signals
    iot_keywords = [
        'device_id', 'sensor_id', 'device', 'node', 'gateway', 'equipment',
        'reading', 'measurement', 'value', 'metric',
        'temperature', 'temp', 'humidity', 'pressure', 'voltage',
        'current', 'power', 'rpm', 'vibration', 'flow_rate',
        'unit', 'unit_of_measure', 'uom',
        'timestamp', 'event_time', 'recorded_at', 'sampled_at',
        'status', 'state', 'alert', 'alarm', 'threshold'
    ]
    for c in cols:
        if col_matches(c, iot_keywords):
            scores['iot_sensor'] += 0.15
            evidence['iot_sensor'].append(f"Column '{c}' matches IoT/Sensor terminology")
            break

    if row_count > 500000:
        scores['iot_sensor'] += 0.20
        evidence['iot_sensor'].append(f"Very high row count ({row_count}) typical of sensor telemetry")

    if len(date_cols) > 0:
        scores['iot_sensor'] += 0.15
        evidence['iot_sensor'].append("Contains timestamp column for telemetry")
        
    for c in cols:
        if col_matches(c, ['device_id', 'sensor_id', 'node', 'equipment']):
            uniques = sample_df[c].nunique()
            if uniques > 0 and (uniques / len(sample_df)) < 0.1:
                scores['iot_sensor'] += 0.15
                evidence['iot_sensor'].append(f"Column '{c}' indicates few devices writing many records")
            break

    # Winner evaluation
    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]

    if best_score <= 0.25:
        return DomainResult(domain='generic', confidence=1.0, evidence=["No strong domain signals detected"])

    return DomainResult(
        domain=best_domain,
        confidence=min(best_score / 1.0, 1.0), 
        evidence=evidence[best_domain]
    )

def run_general_inferences(df: pd.DataFrame) -> List[Inference]:
    """Run completely agnostic data quality and ML readiness checks."""
    inferences = []
    if df.empty:
        return inferences

    row_count = len(df)
    
    for col in df.columns:
        col_data = df[col]
        null_count = col_data.isna().sum()
        null_pct = null_count / row_count
        non_null_data = col_data.dropna()
        
        # Rule G-01: High Null Density
        if null_pct > 0.40:
            inferences.append(Inference(
                id=f"high_null_col_{col}",
                severity='critical',
                category='data_quality',
                title='High Missing Data Rate',
                detail=f"Column '{col}' has {null_count} missing values ({null_pct*100:.1f}%).",
                affected_columns=[col],
                suggested_action="Drop this column or use KNN imputation if the missing values carry signal",
                auto_fixable=True,
                fix_operation="drop_missing_specific"
            ))

        if len(non_null_data) == 0:
            continue
            
        unique_count = non_null_data.nunique()
        
        # Rule G-02: Zero variance
        if unique_count == 1:
            val = non_null_data.iloc[0]
            inferences.append(Inference(
                id=f"zero_variance_{col}",
                severity='critical',
                category='ml_readiness',
                title='Zero Variance Feature',
                detail=f"Column '{col}' has only one unique value: '{val}'. It carries no information for an ML model and will cause zero-variance errors in many algorithms including PCA.",
                affected_columns=[col],
                suggested_action="Drop this column before ML training.",
                auto_fixable=True,
                fix_operation="drop_columns"
            ))
            continue
            
        # Rule G-04: High cardinality
        is_numeric = pd.api.types.is_numeric_dtype(col_data)
        if not is_numeric and unique_count > 50 and (unique_count / row_count) > 0.8:
            inferences.append(Inference(
                id=f"high_cardinality_{col}",
                severity='warning',
                category='ml_readiness',
                title='High Cardinality Categorical',
                detail=f"Column '{col}' has {unique_count} unique values ({(unique_count/row_count)*100:.0f}% of rows). This is likely an ID or free-text column that should be dropped or hashed before ML training.",
                affected_columns=[col],
                suggested_action="Drop this column if it is an identifier, or apply Binary encoding to reduce dimensionality",
                auto_fixable=False
            ))

        # Rule G-05: Potential ID
        if unique_count == row_count:
            inferences.append(Inference(
                id=f"id_leakage_{col}",
                severity='info',
                category='ml_readiness',
                title='Potential ID Column Detected',
                detail=f"Column '{col}' has perfectly unique values. Perfect uniqueness means this is likely a row identifier.",
                affected_columns=[col],
                suggested_action="Confirm this is an ID column and drop it before ML training — ID columns leak row identity into models.",
                auto_fixable=True,
                fix_operation="drop_columns"
            ))

        if is_numeric:
            # Rule G-03: Near-Zero variance
            try:
                mean_val = non_null_data.mean()
                if mean_val != 0:
                    cov = non_null_data.std() / mean_val
                    if abs(cov) < 0.01:
                        inferences.append(Inference(
                            id=f"near_zero_variance_{col}",
                            severity='warning',
                            category='statistics',
                            title='Near-Zero Variance Feature',
                            detail=f"Column '{col}' has a coefficient of variation of {cov:.5f}.",
                            affected_columns=[col],
                            suggested_action="Consider dropping or investigating why this column has almost no variation.",
                            auto_fixable=False
                        ))
            except Exception as e:
                logger.warning(f"Error computing G-03 for {col}: {e}")

            # Rule G-06: Highly Skewed
            try:
                skew_val = float(scipy.stats.skew(non_null_data.astype(float)))
                if abs(skew_val) > 2.0:
                    dir_str = "right-skewed" if skew_val > 0 else "left-skewed"
                    inferences.append(Inference(
                        id=f"skewed_dist_{col}",
                        severity='warning',
                        category='statistics',
                        title=f'Highly Skewed Distribution',
                        detail=f"Column '{col}' is highly {dir_str} (skewness = {skew_val:.2f}). Min: {non_null_data.min()}, Median: {non_null_data.median()}, Max: {non_null_data.max()}",
                        affected_columns=[col],
                        suggested_action=f"Apply log1p transformation for right-skewed columns, or square-root for moderately skewed. Linear models are sensitive to skewed inputs.",
                        auto_fixable=False
                    ))
            except Exception as e:
                logger.warning(f"Error computing G-06 for {col}: {e}")

            # Rule G-13: Suspicious Negatives
            try:
                if non_null_data.min() < 0:
                    sus_keys = ['age', 'count', 'quantity', 'qty', 'price', 'amount', 'salary', 'score', 'rating', 'duration', 'distance', 'weight', 'height']
                    if col_matches(col, sus_keys):
                        neg_count = (non_null_data < 0).sum()
                        inferences.append(Inference(
                            id=f"suspicious_negatives_{col}",
                            severity='warning',
                            category='data_quality',
                            title='Suspicious Negative Values',
                            detail=f"Column '{col}' has {neg_count} negative values (min: {non_null_data.min()}).",
                            affected_columns=[col],
                            suggested_action=f"Negative values in '{col}' may be data entry errors. Investigate and consider capping at 0 or dropping.",
                            auto_fixable=False
                        ))
            except Exception:
                pass

        # Rule G-08: Mixed dtype numeric
        if str(col_data.dtype) == 'object':
            sample_size = min(100, len(non_null_data))
            if sample_size > 0:
                sample_s = non_null_data.sample(sample_size)
                numeric_cast = pd.to_numeric(sample_s, errors='coerce')
                num_ratio = numeric_cast.notna().mean()
                if num_ratio > 0.6:
                    inferences.append(Inference(
                        id=f"mixed_numeric_{col}",
                        severity='warning',
                        category='data_quality',
                        title='Numeric Values Stored as Text',
                        detail=f"Column '{col}' appears to be numeric but is stored as text. This prevents numeric operations and ML algorithms from using it correctly.",
                        affected_columns=[col],
                        suggested_action="Use 'Convert to Numeric' normalization step",
                        auto_fixable=True,
                        fix_operation="convert_type_numeric"
                    ))

        # Rule G-09: Dates stored as text
        if str(col_data.dtype) == 'object':
            date_keys = ['date', 'time', 'dt', 'at', 'on', 'when', 'day', 'month', 'year', 'timestamp']
            if col_matches(col, date_keys):
                sample_size = min(100, len(non_null_data))
                if sample_size > 0:
                    sample_s = non_null_data.sample(sample_size)
                    try:
                        date_cast = pd.to_datetime(sample_s, errors='coerce', format='mixed')
                        if date_cast.notna().mean() > 0.7:
                            inferences.append(Inference(
                                id=f"hidden_datetime_{col}",
                                severity='warning',
                                category='structure',
                                title='Date Stored as Text',
                                detail=f"Column '{col}' contains datetime strings stored as text.",
                                affected_columns=[col],
                                suggested_action="Override this column's type to Date to unlock date-specific operations and time series features",
                                auto_fixable=False
                            ))
                    except Exception:
                        pass

        # Rule G-10: Binary target imbalance
        if unique_count == 2:
            counts = non_null_data.value_counts()
            minority_count = counts.min()
            min_pct = minority_count / len(non_null_data)
            if min_pct < 0.20:
                min_class = counts.idxmin()
                inferences.append(Inference(
                    id=f"imbalanced_binary_{col}",
                    severity='warning',
                    category='ml_readiness',
                    title='Imbalanced Binary Label',
                    detail=f"Column '{col}' is heavily imbalanced. Minority class '{min_class}' has {min_pct*100:.1f}% of rows.",
                    affected_columns=[col],
                    suggested_action="Apply SMOTE oversampling or random undersampling before training a classifier. Imbalanced labels cause models to predict the majority class for almost all inputs.",
                    auto_fixable=True,
                    fix_operation="handle_imbalance"
                ))

        # Rule G-12: Suspicious constants / placeholders
        try:
            val_counts = non_null_data.value_counts()
            if len(val_counts) > 0:
                top_val = val_counts.iloc[0]
                top_val_pct = top_val / len(non_null_data)
                if top_val_pct > 0.8:
                    top_name = str(val_counts.index[0]).strip().lower()
                    placeholders = ['0', '-1', '-999', '9999', 'n/a', 'null', 'unknown', 'none', 'na', 'missing', 'undefined', '-']
                    if top_name in placeholders:
                        inferences.append(Inference(
                            id=f"placeholder_{col}",
                            severity='critical',
                            category='data_quality',
                            title='Widespread Placeholder Value',
                            detail=f"Column '{col}' has {top_val_pct*100:.0f}% of rows set to '{val_counts.index[0]}', which appears to be a placeholder for missing data, not a real value.",
                            affected_columns=[col],
                            suggested_action=f"Replace '{val_counts.index[0]}' with NaN using the Replace Value operation, then handle as missing data.",
                            auto_fixable=False
                        ))
        except Exception as e:
            logger.warning(f"Error computing G-12 for {col}: {e}")

    # Rule G-07: Duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        dup_pct = dup_count / row_count
        inferences.append(Inference(
            id="duplicate_rows",
            severity='critical' if dup_pct >= 0.05 else 'warning',
            category='data_quality',
            title='Duplicate Rows Detected',
            detail=f"Dataset contains {dup_count} exactly duplicated rows ({dup_pct*100:.2f}%).",
            affected_columns=['(entire dataset)'],
            suggested_action="Drop duplicate rows to prevent data leakage and train-test contamination.",
            auto_fixable=True,
            fix_operation="drop_duplicates"
        ))

    # Rule G-14: Memory
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    if mem_mb > 500:
        inferences.append(Inference(
            id="high_memory",
            severity='warning',
            category='structure',
            title='High Memory Footprint',
            detail=f"Dataset requires {mem_mb:.1f} MB in memory.",
            affected_columns=['(entire dataset)'],
            suggested_action="Consider downsampling, dropping unused columns, or converting float64 columns to float32 to reduce memory.",
            auto_fixable=False
        ))

    # Rule G-11: Numeric Correlation
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] > 1:
        # Sample columns to prevent memory crash on very wide datasets
        if numeric_df.shape[1] > 50:
            numeric_df = numeric_df.sample(n=30, axis=1)
            
        try:
            corr_matrix = numeric_df.corr(numeric_only=True)
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    
                    # Ensure both have at least 20 non-nulls
                    if numeric_df[col1].count() > 20 and numeric_df[col2].count() > 20:
                        corr_val = corr_matrix.iloc[i, j]
                        if pd.notna(corr_val) and abs(corr_val) > 0.95:
                            inferences.append(Inference(
                                id=f"high_corr_{col1}_{col2}",
                                severity='info',
                                category='statistics',
                                title='Extreme Collinearity',
                                detail=f"Columns '{col1}' and '{col2}' are highly correlated (r = {corr_val:.2f}).",
                                affected_columns=[col1, col2],
                                suggested_action="Consider dropping one of these columns before training linear models to avoid multicollinearity. Tree-based models are unaffected.",
                                auto_fixable=False
                            ))
        except Exception as e:
            logger.warning(f"Error computing correlation matrix: {e}")

    return inferences

def run_domain_inferences(df: pd.DataFrame, domain: str) -> List[Inference]:
    """Run strict domain-specific rules based on detected domain label."""
    inferences = []
    
    if domain == 'hr':
        age_col = None
        tenure_col = None
        for c in df.columns:
            if col_matches(c, ['age']): age_col = c
            if col_matches(c, ['tenure', 'years_of_service', 'experience']): tenure_col = c
            
        if age_col and tenure_col:
            try:
                invalid = df[(df[age_col].astype(float) - df[tenure_col].astype(float)) < 16]
                if len(invalid) > 0:
                    inferences.append(Inference(
                        id="hr_age_tenure_conflict",
                        severity='warning',
                        category='consistency',
                        title='Age vs Tenure Logic Error',
                        detail=f"Found {len(invalid)} records where (age - tenure) is less than 16, which is logically inconsistent (starting work before age 16).",
                        affected_columns=[age_col, tenure_col],
                        suggested_action="Investigate these records for data entry errors on age or tenure.",
                        auto_fixable=False
                    ))
            except Exception:
                pass
                
        sal_col = None
        dept_col = None
        for c in df.columns:
            if col_matches(c, ['salary', 'pay', 'compensation']): sal_col = c
            if col_matches(c, ['department', 'dept', 'division']): dept_col = c
            
        if sal_col and dept_col and pd.api.types.is_numeric_dtype(df[sal_col]):
            try:
                # Group by department, find outliers > 3 IQR
                def get_outliers(group):
                    Q1 = group.quantile(0.25)
                    Q3 = group.quantile(0.75)
                    IQR = Q3 - Q1
                    return group > (Q3 + 3 * IQR)
                
                outliers_mask = df.groupby(dept_col)[sal_col].transform(get_outliers)
                outlier_count = outliers_mask.sum()
                if outlier_count > 0:
                    inferences.append(Inference(
                        id="hr_salary_dept_outlier",
                        severity='warning',
                        category='statistics',
                        title='Department-Level Salary Outliers',
                        detail=f"Found {outlier_count} employees with salaries that are statistical outliers WITHIN their own department — suggesting data entry errors rather than legitimate high earners.",
                        affected_columns=[sal_col, dept_col],
                        suggested_action="Review these entries with HR or cap them iteratively per department.",
                        auto_fixable=False
                    ))
            except Exception:
                pass

    if domain == 'finance':
        amount_col = None
        for c in df.columns:
            if col_matches(c, ['amount', 'txn', 'transaction', 'transfer']) and pd.api.types.is_numeric_dtype(df[c]):
                amount_col = c
                break
                
        if amount_col:
            data = df[amount_col].dropna()
            if (data < 0).any():
                neg_count = (data < 0).sum()
                inferences.append(Inference(
                    id="fi_negative_amounts",
                    severity='info',
                    category='data_quality',
                    title='Negative Monetary Limits',
                    detail=f"Found {neg_count} negative amounts. Negative amounts may represent refunds, chargebacks, or corrections — or they may be data errors.",
                    affected_columns=[amount_col],
                    suggested_action="Investigate whether negative values should be treated as a separate transaction type or absolute-valued.",
                    auto_fixable=False
                ))

    if domain == 'healthcare':
        for c in df.columns:
            if not pd.api.types.is_numeric_dtype(df[c]): continue
            data = df[c].dropna()
            if col_matches(c, ['age']) and (data < 0).any() or (data > 130).any():
                violators = ((data < 0) | (data > 130)).sum()
                inferences.append(Inference(
                    id=f"hc_impossible_age_{c}",
                    severity='critical',
                    category='data_quality',
                    title='Physiologically Impossible Age',
                    detail=f"Column '{c}' has {violators} rows outside valid human bounds [0-130].",
                    affected_columns=[c],
                    suggested_action="Cap out of bounds values to NaN.",
                    auto_fixable=False
                ))
            if col_matches(c, ['heart_rate', 'hr_bpm']) and ((data < 20) | (data > 300)).any():
                violators = ((data < 20) | (data > 300)).sum()
                inferences.append(Inference(
                    id=f"hc_impossible_hr_{c}",
                    severity='critical',
                    category='data_quality',
                    title='Physiologically Impossible Heart Rate',
                    detail=f"Column '{c}' has {violators} rows outside valid bounds.",
                    affected_columns=[c],
                    suggested_action="Replace outlier vital signs with NaN.",
                    auto_fixable=False
                ))

    return inferences

def run_full_inference(df: pd.DataFrame) -> InferenceReport:
    """Core entry point mapping dataset to all inferences and generating ML Readiness score."""
    try:
        domain_res = detect_domain(df)
    except Exception as e:
        logger.error(f"Domain detection failed: {e}")
        domain_res = DomainResult(domain='generic', confidence=0.0, evidence=["Domain detection failed internally."])

    all_inferences = []
    
    try:
        all_inferences.extend(run_general_inferences(df))
    except Exception as e:
        logger.error(f"General inferences failed: {e}")

    try:
        all_inferences.extend(run_domain_inferences(df, domain_res.domain))
    except Exception as e:
        logger.error(f"Domain inferences failed: {e}")

    # Enforce constraints
    for inf in all_inferences:
        if not inf.affected_columns:
            inf.affected_columns = ['(entire dataset)']

    # Sorting
    severity_order = {'critical': 0, 'warning': 1, 'info': 2, 'suggestion': 3}
    all_inferences.sort(key=lambda x: severity_order.get(x.severity, 99))
    
    crit_count = sum(1 for x in all_inferences if x.severity == 'critical')
    warn_count = sum(1 for x in all_inferences if x.severity == 'warning')
    info_count = sum(1 for x in all_inferences if x.severity == 'info')
    sugg_count = sum(1 for x in all_inferences if x.severity == 'suggestion')

    # ML Readiness Scoring
    score = 1.0
    score -= (0.15 * crit_count)
    score -= (0.07 * warn_count)
    score -= (0.02 * info_count)
    score = max(0.0, min(1.0, score))

    if score >= 0.85:
        label = 'Ready'
    elif score >= 0.65:
        label = 'Almost Ready'
    elif score >= 0.40:
        label = 'Needs Work'
    else:
        label = 'Not Ready'

    # Top actions deduplication
    top_actions = []
    for inf in all_inferences:
        action = f"{inf.affected_columns[0]}: {inf.suggested_action}"
        if action not in top_actions:
            top_actions.append(action)
        if len(top_actions) == 5:
            break

    return InferenceReport(
        domain_detection=domain_res,
        general_inferences=[x for x in all_inferences if x.id.startswith('G-') or not x.id.startswith(('hr_','fi_','ec_','hc_','io_'))],
        domain_inferences=[x for x in all_inferences if x.id.startswith(('hr_','fi_','ec_','hc_','io_'))],
        all_inferences=all_inferences,
        critical_count=crit_count,
        warning_count=warn_count,
        info_count=info_count,
        suggestion_count=sugg_count,
        ml_readiness_score=float(score),
        ml_readiness_label=label,
        top_actions=top_actions
    )
