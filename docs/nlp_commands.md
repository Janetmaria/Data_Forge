# NLP Command Reference

DataForge includes a natural language command console. Type commands in plain English and the system will automatically parse and apply the correct pipeline operation.

---

## Supported Commands

### Dropping & Cleaning
| Command | Operation |
|---|---|
| `drop duplicates` | Remove duplicate rows |
| `drop missing` | Drop all rows with any null |
| `drop missing from age` | Drop rows where specific column `age` is null |
| `drop column ssn` | Delete a specific column |
| `delete column ssn` | Delete a specific column |

### Filling Missing Values
| Command | Operation |
|---|---|
| `fill missing in age with mean` | Fill missing values using column mean |
| `fill missing in salary with median` | Fill using median |
| `fill missing in department with mode` | Fill using most common value |
| `fill phone with Unknown` | Fill with a custom constant value |

### Type Conversion & Formatting
| Command | Operation |
|---|---|
| `convert age to numeric` | Convert column to numeric (supports float/int/number) |
| `convert name to string` | Convert column to text/string |
| `convert join_date to date` | Convert column to datetime |
| `round score to 2 decimal places` | Round numeric column to X decimals |
| `uppercase department` | Convert text to uppercase |
| `lowercase name` | Convert text to lowercase |
| `titlecase name` | Convert text to title case |

### Scaling & Normalisation
| Command | Operation |
|---|---|
| `scale salary` | Min-Max scale to 0–1 |
| `scale salary between 4 and 5` | Min-Max scale to custom range |
| `standard scale salary` | Z-Score (standard) scaling |
| `zscore salary` | Z-Score (standard) scaling |

### Outlier Removal
| Command | Operation |
|---|---|
| `remove outliers from age` | IQR-based outlier removal |
| `drop outliers in salary` | IQR-based outlier removal |

### Date Extraction
| Command | Operation |
|---|---|
| `extract date join_date` | Extract Year/Month/Day from date column |
| `parse date created_at` | Same as above |

### Time-Series Fill
*(Currently available via UI/API, NLP support planned)*
| Command | Operation |
|---|---|
| `ffill price` | Forward-fill missing values |
| `bfill price` | Backward-fill missing values |

### Format Validation
| Command | Operation |
|---|---|
| `validate email format in contact` | Validate email format, set invalid to null |
| `validate phone in mobile` | Validate phone numbers |
| `validate url in website` | Validate URLs |
| `validate ip in server_address` | Validate IP addresses |
| `validate aadhaar in id_col` | Validate Aadhaar card numbers |
| `validate credit card in card_num` | Validate credit card numbers |

---

## Notes

- Commands are **case insensitive**
- Column names should match exactly as they appear in the dataset
- If a command is not recognised, the system will show an alert
