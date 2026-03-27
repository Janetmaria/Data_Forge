# NLP Command Reference

DataForge includes a natural language command console. Type commands in plain English and the system will automatically parse and apply the correct pipeline operation.

Commands are **case-insensitive**. Column names must match exactly as they appear in the dataset header.

---

## Dropping & Cleaning

| Command | Operation |
|---|---|
| `drop duplicates` | Remove all duplicate rows |
| `remove duplicates` | Remove all duplicate rows |
| `drop missing` | Drop every row that has any null value |
| `remove null rows` | Drop every row that has any null value |
| `drop missing from age` | Drop rows where `age` is null |
| `remove null values in salary` | Drop rows where `salary` is null |
| `drop column ssn` | Delete a column entirely |
| `delete column ssn` | Delete a column entirely |
| `remove col id` | Delete a column entirely |

---

## Filling Missing Values

| Command | Operation |
|---|---|
| `fill missing in age with mean` | Fill nulls using the column mean |
| `fill missing in salary with median` | Fill nulls using the column median |
| `fill missing in department with mode` | Fill nulls using the most common value |
| `fill phone with Unknown` | Fill nulls with a custom constant |
| `fill age with 0` | Fill nulls with a numeric constant |
| `knn impute age` | KNN imputation using all numeric columns (k=5) |
| `knn impute salary with k=3` | KNN imputation with custom k |
| `knn fill price` | KNN imputation |

---

## KNN Imputation

| Command | Operation |
|---|---|
| `knn impute age` | KNN imputation, k=5 (default) |
| `knn impute age with k=3` | KNN imputation with custom neighbour count |
| `knn fill salary` | KNN imputation |

---

## Missingness Indicator (Flag)

| Command | Operation |
|---|---|
| `flag missing in age` | Add a binary `age_missing` column (1 = was null) |
| `add missingness indicator for salary` | Add a missingness flag column |
| `missingness flag price` | Add a missingness flag column |

---

## Type Conversion & Formatting

| Command | Operation |
|---|---|
| `convert age to numeric` | Convert to numeric (handles commas, %, $, £, €) |
| `convert name to string` | Convert to text/string |
| `convert join_date to date` | Parse column as datetime |
| `age text to numeric` | Convert word-form numbers to numeric (e.g. "thirty" → 30) |
| `salary numeric to text` | Convert numbers to word form (e.g. 30 → "thirty") |
| `round score to 2 decimal places` | Round a numeric column to N decimals |
| `round price to 0 decimal places` | Round to integer |

---

## Text Case

| Command | Operation |
|---|---|
| `uppercase department` | Convert text to `UPPERCASE` |
| `lowercase name` | Convert text to `lowercase` |
| `titlecase name` | Convert text to `Title Case` |
| `upper case city` | Same as `uppercase` |
| `lower case email` | Same as `lowercase` |

---

## Extract Numeric from Messy Strings

| Command | Operation |
|---|---|
| `extract numeric from price` | Extract numbers from strings; set non-parseable to null |
| `extract number from revenue drop invalid` | Extract numbers; drop rows that can't be parsed |
| `extract numbers from salary null invalid` | Extract numbers; set unparseable cells to null |

---

## Scaling & Normalisation

| Command | Operation |
|---|---|
| `scale salary` | Min-Max scale to 0–1 |
| `scale salary between 4 and 5` | Min-Max scale to a custom range |
| `standard scale salary` | Z-Score (standard) scaling |
| `zscore salary` | Z-Score scaling |
| `standardize age` | Z-Score scaling |

---

## Outlier Handling

| Command | Operation |
|---|---|
| `remove outliers from age` | IQR drop — remove rows outside 1.5×IQR |
| `drop outliers in salary` | IQR drop |
| `cap outliers in age` | IQR cap — clamp extreme values (does not remove rows) |
| `cap outliers in salary iqr 2.0` | IQR cap with custom multiplier |

---

## Encoding Categorical Columns

| Command | Operation |
|---|---|
| `one hot encode department` | One-Hot Encoding |
| `label encode status` | Ordinal / Label Encoding |
| `ordinal encode priority` | Ordinal Encoding |
| `frequency encode city` | Frequency / Count Encoding |
| `binary encode name` | Binary Encoding |
| `target encode department using label` | Target Encoding (requires target column) |

---

## Row Filtering

| Command | Operation |
|---|---|
| `filter rows where age > 30` | Keep only rows matching the condition |
| `filter rows where salary < 50000` | Keep rows where salary < 50,000 |
| `keep rows where status == "active"` | Keep rows matching string condition |
| `filter rows where country == "IN"` | Filter by string equality |

> Conditions follow pandas `.query()` syntax.

---

## Rename Column

| Command | Operation |
|---|---|
| `rename salary to annual_salary` | Rename a column |
| `rename column id to user_id` | Rename a column |

---

## Binning

| Command | Operation |
|---|---|
| `bin age into 5` | Equal-width binning into 5 buckets |
| `bin salary 4 equal frequency` | Equal-frequency (quantile) binning |
| `quantile bin age 5` | Quantile binning into 5 buckets |
| `bin price into 3` | Equal-width (default) |

---

## Date / Datetime Extraction

| Command | Operation |
|---|---|
| `extract date join_date` | Extract year, month, day columns |
| `parse date created_at` | Extract year, month, day columns |
| `extract year from join_date` | Extract a single datetime component |
| `extract month from created_at` | Extract month |
| `extract year month day from join_date` | Extract multiple components at once |
| `extract year quarter from order_date` | Extract year + quarter |
| `extract hour minute from timestamp` | Extract hour + minute |
| `extract dayofweek from event_date` | Extract day-of-week (0=Mon) |
| `extract is_weekend from date` | Binary weekend flag |
| `extract quarter from created_at` | Extract quarter (1–4) |

**Supported components:** `year`, `month`, `day`, `hour`, `minute`, `quarter`, `dayofweek`, `dayofyear`, `weekofyear`, `is_weekend`, `is_month_start`, `is_month_end`

---

## Time-Series Fill

| Command | Operation |
|---|---|
| `ffill price` | Forward-fill missing values (carry last known forward) |
| `forward fill price` | Forward-fill |
| `bfill price` | Backward-fill missing values |
| `backward fill inventory` | Backward-fill |

---

## Lag Features

| Command | Operation |
|---|---|
| `lag features for price with lags 1 2 3` | Create lag columns: `price_lag_1`, `price_lag_2`, `price_lag_3` |
| `create lag for sales lags 1 2` | Create lag features |
| `lag 1 2 3 for revenue` | Create lag features |

---

## Rolling Features

| Command | Operation |
|---|---|
| `rolling mean of price window 7` | 7-day rolling mean |
| `rolling mean std of revenue window 3 7` | Rolling mean + std for windows 3 and 7 |
| `create rolling features for sales windows 3 7` | Rolling mean + std (default stats) |

**Supported stats:** `mean`, `std`, `min`, `max`, `median`

---

## Handle Class Imbalance

| Command | Operation |
|---|---|
| `smote label` | SMOTE oversampling on target column `label` |
| `balance classes using target` | SMOTE oversampling |
| `oversample label` | SMOTE oversampling |
| `undersample label` | Random undersampling |
| `handle imbalance on target` | SMOTE (default) |

---

## Format Validation

| Command | Operation |
|---|---|
| `validate email format in contact` | Validate email; set invalid to null |
| `validate phone in mobile` | Validate phone numbers |
| `validate url in website` | Validate URLs |
| `validate ip in server_address` | Validate IP addresses |
| `validate aadhaar in id_col` | Validate Aadhaar card numbers |
| `validate credit card in card_num` | Validate credit card numbers |

---

## Tips

- Commands are **case-insensitive**
- Column names should match exactly as they appear in the dataset
- Conditions in `filter rows` use **pandas query syntax** (e.g. `age > 30`, `name == "Alice"`, `salary >= 50000 and status == "active"`)
- `bin`, `encode`, `lag`, `rolling`, and `extract_datetime_components` require a selected or named column
- If a command is not recognised, the system will show an error alert
