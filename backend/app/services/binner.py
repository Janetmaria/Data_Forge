import pandas as pd

def bin_column(df, column, strategy, n_bins=5, labels=None,
               custom_boundaries=None, output_column=None, drop_original=False):
    if column not in df.columns:
        raise ValueError(f'Column {column!r} not found')
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(f'Column {column!r} is not numeric')

    out_col = output_column or f'{column}_binned'
    df_out  = df.copy()

    if strategy == 'equal_width':
        df_out[out_col] = pd.cut(df_out[column], bins=n_bins, labels=labels, include_lowest=True)
    elif strategy == 'equal_frequency':
        df_out[out_col] = pd.qcut(df_out[column], q=n_bins, labels=labels, duplicates='drop')
    elif strategy == 'custom':
        if not custom_boundaries or len(custom_boundaries) < 2:
            raise ValueError('custom strategy requires at least 2 boundary values')
        n_custom = len(custom_boundaries) - 1
        if labels and len(labels) != n_custom:
            raise ValueError(f'labels ({len(labels)}) must equal bin count ({n_custom})')
        df_out[out_col] = pd.cut(df_out[column], bins=custom_boundaries,
                                  labels=labels, include_lowest=True)
    else:
        raise ValueError(f'Unknown strategy {strategy!r}')

    # If no explicit labels were given, auto-generate ML-friendly names from bin edges.
    # E.g. col="age", interval (17.999, 25.0] -> "age_18_25"
    # This avoids unreadable "(17.999, 25.0]" strings in feature importance charts
    # and also ensures the values are JSON-serializable (no pandas.Interval objects).
    if not labels:
        prefix = column
        def _interval_to_label(val):
            if hasattr(val, 'left') and hasattr(val, 'right'):
                lo = int(round(val.left))
                hi = int(round(val.right))
                return f"{prefix}_{lo}_{hi}"
            return str(val)  # NaN or already a string
        df_out[out_col] = df_out[out_col].apply(_interval_to_label)

    bin_counts = {str(k):int(v) for k,v in df_out[out_col].value_counts().sort_index().items()}
    if drop_original:
        df_out = df_out.drop(columns=[column])

    return df_out, {'strategy':strategy,'output_column':out_col,
                    'bin_distribution':bin_counts,'rows_affected':len(df_out)}
