import pandas as pd
import category_encoders as ce

SUPPORTED = {'one_hot','ordinal','frequency','target','binary'}

def encode_column(df, column, method, ordered_categories=None,
                  target_column=None, drop_first=True, max_categories=50):
    if method not in SUPPORTED:
        raise ValueError(f'Unknown method {method!r}')
    if column not in df.columns:
        raise ValueError(f'Column {column!r} not found')
    if df[column].isna().any():
        raise ValueError(f'Column {column!r} has nulls. Impute first.')

    unique_vals = df[column].dropna().unique().tolist()
    n_unique = len(unique_vals)
    df_out = df.copy()
    new_columns = []

    if method == 'one_hot':
        if n_unique > max_categories:
            raise ValueError(f'{column!r} has {n_unique} unique values. '
                             f'One-Hot would create {n_unique} cols. '
                             f'Limit is {max_categories}. Use binary or frequency.')
        dummies = pd.get_dummies(df_out[column], prefix=column,
                                 drop_first=drop_first, dtype=int)
        new_columns = dummies.columns.tolist()
        df_out = pd.concat([df_out.drop(columns=[column]), dummies], axis=1)

    elif method == 'ordinal':
        if ordered_categories is None:
            ordered_categories = sorted(unique_vals)  # alphabetical fallback
        mapping = {cat: i for i, cat in enumerate(ordered_categories)}
        df_out[column] = df_out[column].map(mapping)
        new_columns = [column]

    elif method == 'frequency':
        freq_map = df_out[column].value_counts(normalize=True).to_dict()
        encoded_col = f'{column}_freq'
        df_out[encoded_col] = df_out[column].map(freq_map)
        df_out = df_out.drop(columns=[column])
        new_columns = [encoded_col]

    elif method == 'target':
        if target_column is None:
            raise ValueError('target encoding requires target_column param')
        if target_column not in df_out.columns:
            raise ValueError(f'Target column {target_column!r} not found')
        enc = ce.TargetEncoder(cols=[column], smoothing=1.0)
        df_out[column] = enc.fit_transform(df_out[[column]], df_out[target_column])[column]
        new_columns = [column]

    elif method == 'binary':
        enc = ce.BinaryEncoder(cols=[column])
        encoded = enc.fit_transform(df_out[[column]])
        new_columns = encoded.columns.tolist()
        df_out = pd.concat([df_out.drop(columns=[column]), encoded], axis=1)

    return df_out, {'method': method, 'new_columns': new_columns,
                    'n_unique': n_unique, 'n_new_columns': len(new_columns)}
