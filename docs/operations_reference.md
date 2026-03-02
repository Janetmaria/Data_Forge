# Operations Reference

A complete reference for every pipeline operation available in DataForge.

---

## Data Integration

### `merge`
Joins two datasets horizontally on a shared key column.

| Parameter | Type | Description |
|---|---|---|
| `secondary_dataset_id` | string | ID of the dataset to merge with |
| `how` | string | `inner`, `left`, `right`, `outer` |
| `left_on` | string | Column from the current dataset |
| `right_on` | string | Column from the secondary dataset |

Join types explained:
- **Inner** — Only rows where the key exists in **both** datasets
- **Left** — All rows from current dataset, fill blanks from secondary where matched
- **Right** — All rows from secondary dataset, fill blanks from current where matched
- **Outer** — All rows from **both** datasets; unmatched cells become NaN

### `concat`
Appends rows from a second dataset vertically (stacks datasets).

| Parameter | Type | Description |
|---|---|---|
| `secondary_dataset_id` | string | ID of the dataset to append |
| `axis` | int | `0` = row-wise (default) |

---

## Data Cleaning

### `drop_duplicates`
Removes fully duplicate rows across all columns. No parameters required.

### `drop_missing`
Drops rows where **any** column has a missing value. No parameters required.

### `drop_missing_specific`
Drops rows where a **specific column** is missing.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Columns to check for nulls |

### `fill_missing`
Fills missing values in a column using a strategy.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `method` | string | `mean`, `median`, `mode`, `constant` |
| `value` | any | Required when `method` is `constant` |

### `validate_format`
Validates cell values against an industry-standard regex pattern.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `format_type` | string | `email`, `phone`, `url`, `ip_address`, `credit_card`, `aadhaar`, `custom` |
| `action` | string | `drop_invalid` or `set_null` |
| `pattern` | string | Required when `format_type` is `custom` |

---

## Standardisation

### `text_case`
Converts string column casing.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `case` | string | `upper`, `lower`, `title` |

### `convert_type`
Converts a column's data type.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `type` | string | `numeric`, `string`, `text_to_numeric`, `numeric_to_text` |

### `extract_datetime`
Extracts Year, Month, Day from a date column into new separate columns.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target date columns |

---

## Advanced

### `knn_impute`
Fills missing values using K-Nearest Neighbours based on other numeric columns.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `n_neighbors` | int | Number of neighbours (default: 5) |

### `normalize`
Min-Max scaling to a custom range.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `feature_min` | float | Lower bound (default: 0.0) |
| `feature_max` | float | Upper bound (default: 1.0) |

### `standard_scale`
Z-Score standardisation (zero mean, unit variance).

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |

### `remove_outliers_iqr`
Removes rows where a value falls outside the IQR fence.

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `multiplier` | float | IQR fence multiplier (default: 1.5) |

### `time_series_fill`
Forward-fill or backward-fill missing values (for ordered time-series data).

| Parameter | Type | Description |
|---|---|---|
| `columns` | list[str] | Target columns |
| `method` | string | `ffill` or `bfill` |
