# Quick Start Guide

Get up and running with DataForge in under 5 minutes.

---

## 1. Start the Application

```bash
cd /path/to/data_processing
./start_app.sh
```

The app will be available at **http://localhost:3000** (frontend) and the API at **http://localhost:8000**.

---

## 2. Upload a Dataset

1. Open the Dashboard at `http://localhost:3000`
2. Click **New Dataset**
3. Select a `.csv`, `.xlsx`, `.xls`, or `.json` file
4. The system will automatically profile your data and detect column types

---

## 3. Open the Workspace

Click **Open Workspace** on any dataset card to enter the data processing workspace.

The workspace has three main areas:
- **Left Sidebar** — Control panel with column selector and operation buttons
- **Data Preview** — Live scrollable table showing your current data state
- **Console** — Log of applied operations + NLP command input

---

## 4. Clean Your Data

1. **Click a column header** in the data table to select it
2. A **statistics panel** appears at the top of the sidebar showing Type, Null Count, Min/Max, Mean
3. Choose an operation from the sidebar (e.g. *Fill Missing (Mean)*)
4. The preview table and statistics update instantly

You can also type natural language commands in the console, e.g.:
```
drop duplicates
fill age with mean
remove outliers from salary
validate email format in contact_email
```

---

## 5. Merge With Another Dataset

1. Under **Data Integration**, click **Merge / Join Datasets**
2. Select the secondary dataset from the dropdown
3. Choose the join method (Inner / Left / Right / Outer / Concatenate)
4. Select matching key columns from each dataset
5. Click **Merge**

---

## 6. Save Your Pipeline

Click **Save Pipeline** in the top bar to save the current set of steps as a reusable template.

To reuse a pipeline on a different dataset:
1. Open that dataset's workspace
2. Click **Apply Template**
3. Select your saved pipeline

---

## 7. Export Results

Click **Export CSV** or **Export Excel** in the top bar to download the cleaned dataset with all transformations applied.

---

## Supported Operations Summary

| Category | Operations |
|---|---|
| Cleaning | Drop Duplicates, Drop Missing, Fill Missing, Format Validation |
| Standardisation | Text Case, Type Conversion, Mixed → Numeric/Words, Date Extraction |
| Advanced | KNN Imputation, Min-Max Scaling, Z-Score, IQR Outlier Removal |
| Time-Series | Forward Fill, Backward Fill |
| Integration | Inner/Left/Right/Outer Join, Concatenate |
