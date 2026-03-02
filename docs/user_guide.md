# 📘 DataForge User Guide

Welcome to **DataForge**, an automated, offline-first data preprocessing system designed for high-integrity data transformation. This guide covers everything from basic operations to advanced NLP commands and troubleshooting.

---

## 🚀 Getting Started

### 1. Installation & Setup
DataForge is a self-contained desktop application.
1. Ensure the backend server is running:
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```
2. Ensure the frontend is running:
   ```bash
   cd frontend && npm run dev
   ```
3. Open your browser at `http://localhost:5173` (or the provided local URL).

### 2. The Workspace
The interface is divided into three main zones:
*   **Left Panel (Control Panel)**: Contains buttons for standard transformations (Data Cleaning, Standardization, Integration).
*   **Center Panel (Data Preview)**: Shows a real-time preview of your data (first 100 rows). Columns can be clicked to select them.
*   **Bottom Panel (Console & Log)**: Displays the history of operations and allows you to type natural language commands.

---

## 🛠️ Core Features

### Importing Data
*   Click **"Import Dataset"** on the home screen.
*   Supported formats: `.csv`, `.xlsx`, `.json`, `.parquet`.
*   *Note*: Large files are processed efficiently, but the preview is limited to 100 rows for performance.

### Applying Transformations
You can transform data in two ways:
1.  **Clicking Buttons**: Select a column in the preview, then click a transformation button (e.g., "To Uppercase").
2.  **Typing Commands**: Use the console at the bottom (see "NLP Commands" below).

### Pipeline Management
DataForge treats your actions as a reproducible **Pipeline**.
*   **Undo**: Remove the last step if you made a mistake.
*   **Reset**: Revert the dataset to its original state.
*   **Save Pipeline**: Save your current sequence of steps as a reusable template.
*   **Apply Template**: Apply a previously saved pipeline to a *new* dataset.
*   **Export/Import**: Download your pipeline as a `.json` file to share with colleagues.

### Quality Alerts ⚠️
The system automatically scans for issues:
*   **Missing Values**: Columns with nulls are flagged.
*   **Mixed Types**: Columns containing both numbers and text are flagged.
*   **Action**: Click the alert icon to see recommendations (e.g., "Fill with Mean").

---

## 🗣️ NLP Command Reference

DataForge includes a powerful Natural Language Processing (NLP) engine. You can type commands in plain English in the bottom console.

### Common Commands

| Intent | Example Commands |
| :--- | :--- |
| **Drop Columns** | "Drop the age column" <br> "Remove id and email" |
| **Fill Missing** | "Fill missing values in score with 0" <br> "Impute age with mean" <br> "Replace nulls in category with 'Unknown'" |
| **Filter Rows** | "Keep rows where age is greater than 18" <br> "Drop rows where status is 'inactive'" |
| **Text Case** | "Convert name to uppercase" <br> "Make email lowercase" <br> "Title case the city column" |
| **Type Conversion**| "Convert age to number" <br> "Change join_date to date" <br> "Cast zip_code to string" |
| **Remove Duplicates**| "Drop duplicate rows" <br> "Remove duplicates based on email" |
| **Math Operations** | "Scale salary using min-max" |

### Smart Parsing
The system understands context.
*   *"Clean up the age column"* → Suggests dropping or filling missing values.
*   *"Fix dates"* → Attempts to convert the column to datetime format.

---

## 🛡️ Data Integrity & Safety

DataForge is built with "Audit-Grade" architecture.

### Strict Type Safety
*   The system **prevents** accidental data corruption.
*   *Example*: You cannot fill a numeric column (e.g., `Salary`) with a text string (e.g., "Unknown"). The system will block this action to preserve data integrity.

### Replay Consistency
*   Every action you take is recorded.
*   When you save or apply a pipeline, the system **replays** these actions from the original file to ensure the result is bit-perfect every time.
*   If a required column is missing during replay, the process stops safely and alerts you.

### Offline Privacy
*   **100% Local**: No data ever leaves your machine.
*   **No Cloud Calls**: The system operates without internet access.

---

## ❓ Troubleshooting

### "Operation Blocked: Implicit Cast Forbidden"
*   **Cause**: You tried to perform an operation that would change a column's data type (e.g., filling numbers with text).
*   **Fix**: Use the "Convert Type" operation first if you intend to change the data type, or choose a compatible value (e.g., fill with `-1` instead of `"Missing"`).

### "Replay Conflict Detected"
*   **Cause**: You are applying a pipeline that expects a column (e.g., `age`), but the current dataset does not have that column.
*   **Fix**: Ensure your dataset matches the schema expected by the pipeline, or edit the pipeline steps manually.

### "No Data Loaded" in Preview
*   **Cause**: The dataset might be empty or the backend failed to serialize the preview.
*   **Fix**: Try clicking "Reset" to reload the original data. If the file is corrupted, try importing it again.

### NLP Command Not Recognized
*   **Cause**: The phrasing might be too complex or ambiguous.
*   **Fix**: Try simpler phrasing. Use specific keywords like "drop", "fill", "convert".

---

## 🎹 Keyboard Shortcuts

*   `Enter` (in Console): Execute command
*   `Ctrl/Cmd + Z`: Undo last step (if focus is on workspace)

---

*DataForge v1.0.0 — Production-Grade Offline Data Processing*
