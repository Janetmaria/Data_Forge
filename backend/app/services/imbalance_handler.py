import pandas as pd
from collections import Counter
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

SUPPORTED = {'smote','undersample','smote_then_undersample'}

def handle_imbalance(df, target_col, feature_cols, strategy='smote',
                     k_neighbors=5, sampling_strategy='auto', random_state=42):
    if strategy not in SUPPORTED:
        raise ValueError(f'Unknown strategy {strategy!r}')
    if target_col not in df.columns:
        raise ValueError(f'Target column {target_col!r} not found')
    # If the target is float but all values are whole numbers (e.g. 0.0, 1.0),
    # auto-cast to int — this is common after fill_missing_mean or CSV round-trips.
    # Only reject genuinely continuous float targets (e.g. 0.5, 3.7).
    if pd.api.types.is_float_dtype(df[target_col]):
        import numpy as np
        non_null = df[target_col].dropna()
        if non_null.apply(lambda x: x == int(x)).all():
            df = df.copy()
            df[target_col] = df[target_col].astype('Int64').astype(int)
        elif non_null.nunique() <= 20:
            # User likely mean-imputed a binary target, resulting in decimals like 0.73.
            # Force-round to nearest integer to restore discrete classes.
            df = df.copy()
            df[target_col] = np.round(df[target_col]).astype('Int64').astype(int)
        else:
            raise ValueError(
                f"Target '{target_col}' has continuous decimals (>20 unique). "
                "Did you fill missing values with Mean? Use Mode instead, "
                "or use Bin Column to make it categorical before SMOTE."
            )
    for col in feature_cols:
        if col not in df.columns:
            raise ValueError(f'Feature column {col!r} not found')
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f'{col!r} is not numeric. Encode categorical columns first.')
    null_cols = [c for c in feature_cols if df[c].isna().any()]
    if null_cols:
        raise ValueError(f'Null values in feature columns: {null_cols}. Impute first.')

    class_counts = Counter(df[target_col].dropna())
    min_size = min(class_counts.values()) if class_counts else 0
    if min_size > 0 and k_neighbors >= min_size:
        raise ValueError(f'k_neighbors ({k_neighbors}) must be < minority class size ({min_size})')

    # Drop target nulls
    df_clean = df.dropna(subset=[target_col])
    
    # ── Save columns that are NOT part of the SMOTE operation ──────────────────
    # SMOTE only works on numeric feature+target arrays. Any other columns
    # (text, IDs, dates, etc.) must be preserved manually.
    # Strategy:
    #   • Keep their values for *original* rows (SMOTE always outputs originals first)
    #   • Fill NaN for *synthetic* rows (SMOTE cannot generate text/categorical values)
    non_smote_cols = [c for c in df_clean.columns
                      if c not in feature_cols and c != target_col]
    df_other = df_clean[non_smote_cols].reset_index(drop=True)

    X = df_clean[feature_cols].values
    y = df_clean[target_col].values

    if strategy == 'smote':
        X_res, y_res = SMOTE(sampling_strategy=sampling_strategy,
            random_state=random_state, k_neighbors=k_neighbors).fit_resample(X, y)
    elif strategy == 'undersample':
        X_res, y_res = RandomUnderSampler(sampling_strategy=sampling_strategy,
            random_state=random_state).fit_resample(X, y)
    elif strategy == 'smote_then_undersample':
        X_res, y_res = SMOTE(sampling_strategy=sampling_strategy,
            random_state=random_state, k_neighbors=k_neighbors).fit_resample(X, y)
        X_res, y_res = RandomUnderSampler(random_state=random_state).fit_resample(X_res, y_res)

    df_out = pd.DataFrame(X_res, columns=feature_cols)
    df_out[target_col] = y_res

    # ── Re-attach non-feature columns ──────────────────────────────────────────
    n_original = len(df_clean)
    n_total = len(df_out)
    for col in non_smote_cols:
        original_vals = df_other[col].tolist()
        # Pad with NaN for any synthetic rows added beyond the original count
        synthetic_pad = [None] * max(0, n_total - n_original)
        df_out[col] = (original_vals + synthetic_pad)[:n_total]

    after = dict(Counter(y_res))

    return df_out, {
        'strategy': strategy, 'rows_before': len(df), 'rows_after': len(df_out),
        'rows_added': len(df_out)-len(df),
        'class_dist_before': {str(k):v for k,v in class_counts.items()},
        'class_dist_after': {str(k):v for k,v in after.items()},
        'columns_dropped': [c for c in df.columns if c not in feature_cols+[target_col]],
    }
