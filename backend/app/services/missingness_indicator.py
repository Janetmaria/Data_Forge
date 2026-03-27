import pandas as pd

def add_missingness_indicator(
    df: pd.DataFrame,
    columns: list[str],
    drop_original: bool = False,
) -> tuple[pd.DataFrame, dict]:
    df_out = df.copy()
    indicators_created = []
    rows_affected = {}
    for col in columns:
        if col not in df_out.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame.")
        indicator_name = f"{col}_was_missing"
        null_count = int(df_out[col].isna().sum())
        df_out[indicator_name] = df_out[col].isna().astype(int)
        indicators_created.append(indicator_name)
        rows_affected[col] = null_count
        if drop_original:
            df_out = df_out.drop(columns=[col])
    return df_out, {'indicators_created': indicators_created, 'rows_affected': rows_affected}
