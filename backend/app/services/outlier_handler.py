import pandas as pd

def _compute_bounds(series, method, fold):
    if method == 'iqr':
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        return q1 - fold * iqr, q3 + fold * iqr
    elif method == 'zscore':
        return series.mean() - fold * series.std(), series.mean() + fold * series.std()
    elif method == 'percentile':
        return series.quantile(fold), series.quantile(1 - fold)
    raise ValueError(f'Unknown method {method!r}')

def handle_outliers(df, columns, method='iqr', fold=1.5, strategy='cap'):
    for col in columns:
        if col not in df.columns:
            raise ValueError(f'Column {col!r} not found')
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f'Column {col!r} is not numeric')

    df_out = df.copy()
    per_column = {}
    outlier_mask = pd.Series(False, index=df_out.index)

    for col in columns:
        series = df_out[col].dropna()
        lower, upper = _compute_bounds(series, method, fold)
        col_mask = (df_out[col] < lower) | (df_out[col] > upper)
        n_out = int(col_mask.sum())
        per_column[col] = {'lower': round(float(lower),4), 'upper': round(float(upper),4),
                           'n_outliers': n_out, 'pct': round(n_out/len(df_out)*100, 2)}
        if strategy == 'cap':
            df_out[col] = df_out[col].clip(lower=lower, upper=upper)
        elif strategy == 'drop':
            outlier_mask |= col_mask
        elif strategy == 'flag':
            df_out[f'{col}_is_outlier'] = col_mask.astype(int)
        else:
            raise ValueError(f'Unknown strategy {strategy!r}')

    rows_before = len(df_out)
    if strategy == 'drop':
        df_out = df_out[~outlier_mask].reset_index(drop=True)

    rows_affected = (rows_before - len(df_out) if strategy == 'drop'
                     else sum(v['n_outliers'] for v in per_column.values()))

    return df_out, {'method': method, 'fold': fold, 'strategy': strategy,
                    'per_column': per_column, 'rows_affected': rows_affected}
