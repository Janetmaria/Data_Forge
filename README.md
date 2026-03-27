# DataForge — Automated Multi-Format Data Preprocessing System

> A local-first, AI-assisted data cleaning and preprocessing desktop application. Upload raw datasets, apply transformations visually or via natural language, and export clean, ML-ready data — all without sending your data anywhere.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the App](#running-the-app)
- [The Workspace](#the-workspace)
- [Transformations & Operations](#transformations--operations)
- [NLP Console Commands](#nlp-console-commands)
- [AI Inference Engine](#ai-inference-engine)
- [Data Quality Alerts](#data-quality-alerts)
- [Pipeline Management](#pipeline-management)
- [Export](#export)
- [Data Safety](#data-safety)
- [Troubleshooting](#troubleshooting)

---

## Overview

DataForge is a full-stack desktop application for data preprocessing. It is designed to replace ad-hoc pandas scripts with a structured, visual, and reproducible workflow. You can:

- Upload CSV, Excel, or JSON files
- Interactively clean and transform data using a sidebar, buttons, or typed natural language commands
- See live previews of every change
- Compare data before and after any step
- Save transformation pipelines and replay them on new datasets
- Export the result as CSV or Excel

Everything runs **100% locally** — no cloud API calls, no data upload, no account required.

---

## Features

| Category | Feature |
|---|---|
| **Ingestion** | CSV, Excel (.xlsx), JSON (including nested/flattened), auto-encoding detection |
| **Type Inference** | Auto-detects Numeric, Text, Date, Boolean, ID, and Mixed-type columns |
| **Date Handling** | Auto-standardises all date-like columns to `YYYY-MM-DD` on load |
| **Missing Values** | Fill with mean, median, mode, custom value, forward-fill, or drop rows |
| **Outlier Handling** | IQR-based outlier detection and removal |
| **Normalisation** | Min-Max scaling, Z-score standardisation, robust scaling |
| **Type Conversion** | Convert columns between Numeric, String, Boolean, and Date |
| **Encoding** | One-Hot Encoding, Label Encoding, Ordinal Encoding, Target Encoding |
| **Deduplication** | Drop exact or subset-key duplicate rows |
| **Regex Validation** | Validate email, phone, URL, custom regex; flag or drop invalid entries |
| **Smart Numeric Parse** | Extract numbers from messy currency/price strings |
| **Dataset Merge** | Join a second dataset on a key column |
| **NLP Console** | Type plain-English commands to apply any operation |
| **AI Inference Panel** | Domain detection, ML readiness score, and severity-ranked findings |
| **Quality Alerts** | Auto-flagged issues (high null %, mixed types) with one-click fixes |
| **Before/After Compare** | Side-by-side column diff after every operation |
| **Pipeline Templates** | Save pipelines and apply them to new datasets |
| **Export** | CSV and Excel export of the cleaned dataset |
| **Desktop App** | Electron wrapper with loading screen and clean process management |

---

## Tech Stack

### Backend
| Library | Role |
|---|---|
| **FastAPI** | REST API framework |
| **SQLAlchemy + Alembic** | ORM and database migrations |
| **pandas** | Core data manipulation |
| **scikit-learn** | Scaling, encoding, ML utilities |
| **imbalanced-learn** | SMOTE and resampling |
| **category-encoders** | Target encoding and advanced encoders |
| **feature-engine** | Feature engineering utilities |
| **scipy** | Statistical operations |
| **openpyxl / pyarrow** | Excel and Parquet I/O |
| **numpy** | Numerical computation |
| **python-jose / passlib** | Auth (JWT + hashing) |

### Frontend
| Library | Role |
|---|---|
| **React 18 + TypeScript** | UI framework |
| **Vite** | Build tool and dev server |
| **TailwindCSS** | Utility-first styling |
| **Radix UI** | Accessible component primitives |
| **TanStack Query** | Server state management |
| **TanStack Table** | Table rendering |
| **Zustand** | Client-side state |
| **React Router** | Page routing |
| **Axios** | HTTP client |
| **Recharts** | Charting (installed, available for use) |
| **lucide-react** | Icon library |

### Desktop
| Technology | Role |
|---|---|
| **Electron** | Native desktop wrapper |
| Node.js child processes | Spawns backend (uvicorn) and frontend (vite) |

---

## Project Structure

```
data_processing/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── datasets.py        # Dataset upload, preview, export, inference
│   │   │   └── pipelines.py       # Interactive pipeline CRUD and step execution
│   │   ├── services/
│   │   │   ├── dataset_service.py # File parsing, type inference, profiling, quality alerts
│   │   │   ├── pipeline_service.py# Core transform engine (execute_step, execute_pipeline)
│   │   │   └── nlp_service.py     # Natural language command parser
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── db/                    # DB session and init
│   │   └── main.py                # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/workspace/
│       │   ├── Sidebar.tsx            # Column selector + operation buttons
│       │   ├── PreviewPanel.tsx       # Live data table
│       │   ├── LogPanel.tsx           # Step history + NLP console
│       │   ├── InferencePanel.tsx     # AI inference modal
│       │   ├── DataQualityPanel.tsx   # Quality alerts slide-in panel
│       │   ├── ColumnStatsPanel.tsx   # Per-column statistics card
│       │   ├── BeforeAfterModal.tsx   # Before/after column diff
│       │   ├── MergeDialog.tsx        # Dataset merge configuration
│       │   ├── ScaleDialog.tsx        # Scaling options dialog
│       │   ├── MLEncodeDialog.tsx     # Encoding options dialog
│       │   ├── FormatValidationDialog.tsx # Regex validation dialog
│       │   ├── CustomFillDialog.tsx   # Custom fill value dialog
│       │   ├── SavePipelineDialog.tsx # Pipeline save dialog
│       │   └── ApplyTemplateDialog.tsx# Apply saved pipeline dialog
│       └── pages/
│           ├── DatasetDetailsPage.tsx # Main workspace page
│           └── Dashboard.tsx          # Dataset list / upload page
├── electron-app/
│   ├── main.js        # Electron main process, spawns backend + frontend
│   ├── preload.js     # Electron preload bridge
│   └── loading.html   # Loading screen shown while services boot
├── docs/
│   ├── setup_guide.md
│   └── nlp_commands.md
├── tests/
├── sample_datasets/
├── docker-compose.yml
└── start_app.sh       # One-command browser mode launcher
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 16+** with npm
- **PostgreSQL** (or SQLite for local dev — configured via `.env`)

---

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd data_processing

# 2. Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env to set DATABASE_URL and SECRET_KEY

# 5. Install frontend dependencies
cd frontend && npm install && cd ..

# 6. Install Electron dependencies (for desktop mode)
cd electron-app && npm install && cd ..
```

---

## Running the App

### Option A — Browser Mode (recommended for development)

```bash
./start_app.sh
```

Starts the backend on **port 8000** and frontend on **port 5173**.  
Navigate to `http://localhost:5173`.

### Option B — Desktop App (Electron)

```bash
cd electron-app
npm start
```

A native desktop window opens with a loading screen while the backend and frontend boot (~5–10 seconds). Closing the window cleanly terminates all child processes.

### Option C — Docker

```bash
docker-compose up
```

---

## The Workspace

The workspace has three zones:

| Zone | Location | Description |
|---|---|---|
| **Control Panel** | Left sidebar | Column list, statistics, all operation buttons |
| **Data Preview** | Centre | Scrollable live table (first 100 rows). Click a column to select it |
| **Console & Log** | Bottom | History of applied steps, undo buttons, NLP command input |

**Header bar** contains:
- File name, row/col counts, detected domain badge
- `✨ INFERENCE` button — opens the AI Inference Panel
- `⚠ ALERTS` button — opens the Data Quality Panel (only shown when alerts exist)
- `VIEW DIFF` button — appears after any transformation, opens before/after comparison
- **Apply Template**, **Save Pipeline**, **Export CSV**, **Export Excel**

---

## Transformations & Operations

All operations are applied to the **selected column** (click any column header in the preview table).

### Missing Values
| Operation | Description |
|---|---|
| Fill with Mean | Replaces nulls with the column's mean (numeric only) |
| Fill with Median | Replaces nulls with the column's median (numeric only) |
| Fill with Mode | Replaces nulls with the most frequent value |
| Fill with Custom Value | Replace nulls with a user-specified value |
| Forward Fill | Propagates the last valid value downward |
| Drop Null Rows | Removes any row where this column is null |

### Cleaning
| Operation | Description |
|---|---|
| Drop Duplicates | Removes exact duplicate rows |
| Remove Outliers | IQR-based outlier removal |
| Trim Whitespace | Strips leading/trailing whitespace from text columns |
| Standardise Dates | Converts date strings to `YYYY-MM-DD` |
| Extract Numeric (Smart Parse) | Extracts numbers from messy strings like `$1,200.50` |

### Type Conversion
Convert a column to Numeric, String, Boolean, or Date.

### Normalisation & Scaling
| Method | Description |
|---|---|
| Min-Max | Scales values to [0, 1] |
| Z-score | Standardises to mean=0, std=1 |
| Robust | Uses median/IQR — resistant to outliers |

### Encoding (ML Preparation)
| Method | Description |
|---|---|
| One-Hot Encoding | Creates binary columns for each category |
| Label Encoding | Maps categories to integers |
| Ordinal Encoding | Maps with a user-specified order |
| Target Encoding | Encodes based on target variable mean |

### Validation
Regex-based format validation for Email, Phone, URL, or any custom pattern.  
Invalid entries can be flagged (null) or dropped.

### Dataset Merge
Join another uploaded dataset to the current one on a shared key column.

---

## NLP Console Commands

Type natural language commands in the console at the bottom of the workspace. Examples:

```
fill age with mean
fill salary with median
fill city with mode
drop nulls in email
scale price between 0 and 1
standardise age
remove outliers from salary
convert age to string
validate email format in contact
drop duplicates
```

Full reference: [`docs/nlp_commands.md`](docs/nlp_commands.md)

---

## AI Inference Engine

Click **✨ INFERENCE** in the header to open the AI Inference Panel. It runs a multi-heuristic analysis on the current state of your dataset and provides:

### Detected Domain
Classifies the dataset as one of: `hr`, `finance`, `healthcare`, `ecommerce`, `iot_sensor`, or `generic`, with a confidence percentage and evidence list.

### ML Readiness Score
A 0–100 score and label (`Not Ready` / `Needs Work` / `Almost Ready` / `Ready`) summarising how prepared the dataset is for machine learning.

### Recommended Next Steps
A numbered list of the highest-priority actions to improve the dataset.

### Alerts & Findings
Severity-ranked list of all detected issues, each with:
- Severity badge (Critical / Warning / Info / Suggestion)
- Affected columns
- Suggested action
- **Fix Now** button for auto-fixable issues (applies the fix and closes the panel)

---

## Data Quality Alerts

On every load and after every transformation, DataForge scans for:
- Columns with high null percentages
- Columns with mixed data types
- Suspicious patterns (e.g. numeric columns with text entries)

Alerts appear as a count badge in the header. Click it to open the **Data Quality Panel** (slides in from the right), where each alert shows the column, issue type, and a quick-fix button.

---

## Pipeline Management

Transformations are applied as an ordered list of steps. The log panel shows each step with an `✕` button to remove it.

| Action | How |
|---|---|
| Undo a step | Click `✕` next to the step in the log |
| Reset all | Click **Reset** in the log panel |
| Save pipeline | Click **Save Pipeline** in the header |
| Apply saved pipeline | Click **Apply Template** → select a saved pipeline |
| Export | **Export CSV** or **Export Excel** in the header |

Pipelines are replayed from the **original source file**, guaranteeing deterministic results regardless of order of undo operations.

---

## Export

| Format | Notes |
|---|---|
| **CSV** | UTF-8 encoded, comma-separated |
| **Excel (.xlsx)** | Full formatting preserved via openpyxl |

Exported files reflect all currently applied pipeline steps.

---

## Data Safety

- **100% Offline** — No data ever leaves your machine. No external API calls.
- **Replay Consistency** — Pipelines are replayed from the original raw file for reproducibility.
- **Type Safety** — Operations that would corrupt column types (e.g. filling a numeric column with a non-numeric string) are blocked at the API level with a descriptive error.
- **Non-destructive** — The original uploaded file is never modified.

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|---|---|---|
| Loading screen stuck (Electron) | venv or Node not found | Run `./start_app.sh` manually to see error output |
| `"Operation Blocked: Implicit Cast"` | Filling a numeric column with text | Use **Convert Type** first, or provide a numeric fill value |
| `"No Data Loaded"` in preview | Backend error or empty file | Click **Reset**; re-import the file if corrupted |
| NLP command not recognised | Phrasing too complex | Use simple keywords: `fill`, `drop`, `scale`, `validate`, `convert` |
| Port 8000 or 5173 already in use | Another process using the port | `lsof -ti:8000 \| xargs kill` and `lsof -ti:5173 \| xargs kill` |
| Excel export opens corrupted | Incompatible openpyxl version | Ensure `openpyxl>=3.1.2` is installed in venv |
