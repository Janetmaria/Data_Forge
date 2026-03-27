import pandas as pd

COMPONENT_MAP = {
    'year'          : lambda s: s.dt.year,
    'month'         : lambda s: s.dt.month,
    'day'           : lambda s: s.dt.day,
    'hour'          : lambda s: s.dt.hour,
    'minute'        : lambda s: s.dt.minute,
    'dayofweek'     : lambda s: s.dt.dayofweek,      # 0=Monday
    'dayofyear'     : lambda s: s.dt.dayofyear,
    'weekofyear'    : lambda s: s.dt.isocalendar().week.astype(int),
    'quarter'       : lambda s: s.dt.quarter,
    'is_weekend'    : lambda s: (s.dt.dayofweek >= 5).astype(int),
    'is_month_start': lambda s: s.dt.is_month_start.astype(int),
    'is_month_end'  : lambda s: s.dt.is_month_end.astype(int),
}

def extract_datetime_components(df, column, components):
    invalid = set(components) - set(COMPONENT_MAP)
    if invalid:
        raise ValueError(f'Unknown components: {invalid}')
    if column not in df.columns:
        raise ValueError(f'Column {column!r} not found')
    df_out = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_out[column]):
        df_out[column] = pd.to_datetime(df_out[column], format='mixed', errors='coerce')
    new_cols = []
    for comp in components:
        new_col = f'{column}_{comp}'
        df_out[new_col] = COMPONENT_MAP[comp](df_out[column])
        new_cols.append(new_col)
    return df_out, {'new_columns': new_cols, 'rows_affected': len(df_out)}

def create_lag_features(df, column, lags, sort_by=None):
    if column not in df.columns:
        raise ValueError(f'Column {column!r} not found')
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(f'{column!r} is not numeric')
    if any(l < 1 for l in lags):
        raise ValueError('All lag values must be >= 1')
    df_out = df.copy()
    if sort_by:
        df_out = df_out.sort_values(sort_by).reset_index(drop=True)
    new_cols = []
    for lag in sorted(set(lags)):
        new_col = f'{column}_lag_{lag}'
        df_out[new_col] = df_out[column].shift(lag)
        new_cols.append(new_col)
    nulls = sum(df_out[c].isna().sum() for c in new_cols)
    return df_out, {'new_columns':new_cols,'rows_affected':len(df_out),
                    'nulls_introduced':int(nulls),
                    'note':'Lag features introduce NaN in first N rows. Handle before training.'}

VALID_STATS = {'mean','std','min','max','median'}

def create_rolling_features(df, column, windows, stats=None, min_periods=1, sort_by=None):
    if stats is None:
        stats = ['mean','std']
    bad = set(stats)-VALID_STATS
    if bad:
        raise ValueError(f'Unknown stats: {bad}')
    if column not in df.columns:
        raise ValueError(f'Column {column!r} not found')
    df_out = df.copy()
    if sort_by:
        df_out = df_out.sort_values(sort_by).reset_index(drop=True)
    new_cols = []
    for window in sorted(set(windows)):
        roller = df_out[column].rolling(window=window, min_periods=min_periods)
        for stat in stats:
            new_col = f'{column}_rolling_{window}_{stat}'
            df_out[new_col] = getattr(roller, stat)()
            new_cols.append(new_col)
    return df_out, {'new_columns':new_cols,'rows_affected':len(df_out)}
