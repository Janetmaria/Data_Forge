# DataForge — Automated Multi-Format Data Preprocessing System

## What Is DataForge?

DataForge is a **fully offline, browser-based data preprocessing workbench** designed for analysts, data engineers, and data scientists who need to clean, transform, and prepare raw datasets before feeding them into machine learning pipelines, BI dashboards, or reporting workflows — without writing a single line of code.

All data stays on your local machine. Nothing is sent to the cloud.

---

## Use Cases

| Scenario | How DataForge Helps |
|---|---|
| Pre-ML Data Cleaning | Remove duplicates, impute missing values (KNN / Mean / Mode), drop outliers, scale features |
| Data Standardisation | Normalise phone numbers, validate email formats, convert mixed text/number columns |
| Multi-Source Data Joining | Merge datasets from different CSVs via Inner / Left / Right / Outer joins or vertically concatenate them |
| Time-Series Prep | Forward-fill / Backward-fill gaps, extract Year / Month / Day features from date columns |
| Exploratory Review | Instant live preview of any transform; undo any step; view column statistics inline |
| Pipeline Reuse | Save a cleaning pipeline as a reusable template and apply it to a new dataset in one click |
| Export | Export the final cleaned dataset as CSV or Excel |

---

## Supported File Types & Sizes

| Format | Extension | Recommended Max Size |
|---|---|---|
| CSV | `.csv` | ~500 MB |
| Excel | `.xlsx`, `.xls` | ~100 MB |
| JSON | `.json` | ~200 MB |

> Files are stored locally in `data/uploads/`. Pandas reads them into memory for processing, so available RAM is the practical upper limit.

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (Python) |
| **Data Processing** | Pandas 3.0, NumPy |
| **Machine Learning** | scikit-learn (KNN Imputer, Standard Scaler, Min-Max Scaler) |
| **Database** | SQLite via SQLAlchemy ORM |
| **NLP Parser** | Custom regex-based natural language command engine |
| **Server** | Uvicorn with `--reload` hot-reload |

### Frontend
| Layer | Technology |
|---|---|
| **Framework** | React + TypeScript (Next.js / Vite) |
| **Styling** | Tailwind CSS |
| **UI Components** | shadcn/ui (Dialog, Select, Button, Label) |
| **Icons** | Lucide React |
| **HTTP Client** | Axios |

---

## Full Feature List

### 📁 Data Integration
- **Merge / Join Datasets** — Inner, Left, Right, Outer joins with strict column-type compatibility checking
- **Concatenate (Append Rows)** — Vertical stacking of two datasets
- Column dropdown menus auto-populated from real schema metadata

### 🧹 Data Cleaning
- Remove Duplicates
- Drop Missing Rows (entire dataset or specific column)
- Fill Missing Values — Mean, Median, Mode, or any Custom Value
- **Format Validation** — Validates and flags/drops/nullifies cells that don't match:
  - Email Address
  - Phone Number (international country codes, landlines)
  - Website URL
  - IP Address
  - Credit Card Number
  - Aadhaar Card Number (Indian national ID)
  - Custom Regex Pattern (user-defined)

### 🔤 Standardisation
- To Uppercase / Lowercase / Title Case
- Convert Column to Numeric / String
- Mixed-to-Number (e.g. "thirty" → 30)
- Mixed-to-Words (e.g. 30 → "thirty")
- Extract Date Info (Year, Month, Day from a date column)

### ⚙️ Advanced
- **KNN Imputation** — Context-aware missing value filling using nearest neighbours
- **Min-Max Scaling** — Scale to any custom [min, max] range (default 0–1)
- **Standard Scaling (Z-Score)** — Zero-mean, unit-variance normalisation
- **Remove Outliers (IQR)** — Removes rows outside the 1.5×IQR fence
- **Time-Series Forward Fill / Backward Fill**

### 📊 Column Statistics Panel *(New — being implemented now)*
- When a column is selected, a compact statistics table appears in the sidebar showing:
  - Detected Type, Null Count, Null %, Unique Values, Min, Max, Mean
- Statistics **refresh automatically** after any pipeline step is applied

### 🤖 NLP Command Console
- Type natural language commands (e.g. `"scale salary between 0 and 1"`, `"validate aadhaar in id_col"`, `"remove outliers from age"`)
- Commands are parsed and turned into pipeline steps instantly

### 💾 Pipeline Management
- **Save Pipeline** — Clone the current draft pipeline steps as a named reusable template
- **Apply Template** — Apply a saved pipeline to any dataset
- **Undo Step** — Remove any individual step from the pipeline
- **Reset** — Clear all pipeline steps and start fresh

### 📤 Export
- Export cleaned dataset as **CSV** or **Excel**
- Export reflects all active pipeline steps

---

## Architecture Overview

```
Browser (React)
      │
      │ HTTP (Axios)
      ▼
FastAPI Backend
      │
      ├── /datasets/*         — Upload, list, preview, delete
      ├── /pipelines/*        — Create, list, clone saved pipelines
      └── /pipelines/interactive/{id}/*
                │
                ├── GET  → Load draft pipeline + live preview
                ├── POST /steps → Add a step, returns updated preview
                ├── DELETE /steps/{n} → Remove step n, recalculate preview
                ├── POST /reset → Clear all steps
                └── POST /command → NLP text → auto-add step
                      │
                      └── pipeline_service.py
                              └── execute_pipeline(df, steps, context)
                                      └── Per-step execute_step(df, op, params)
```

---

*DataForge is built for fully offline, privacy-first data preprocessing.*
