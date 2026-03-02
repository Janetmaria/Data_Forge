# 🛠️ DataForge Setup & Launch Guide

This guide explains how to set up, run, and package DataForge as a desktop application.

---

## 🚀 Quick Launch (Developer Mode)

If you have Python and Node.js installed, you can use the auto-start script.

### 1. Prerequisites
*   **Python 3.10+**
*   **Node.js 16+**

### 2. One-Time Setup
If this is your first time running the project:

```bash
# 1. Backend Setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Frontend Setup
cd frontend
npm install
cd ..
```

### 3. Launching the App
Simply run the start script from the root directory:

```bash
./start_app.sh
```
This will:
1.  Start the FastAPI backend on port 8000.
2.  Start the React frontend on port 5173.
3.  Automatically clean up both processes when you press `Ctrl+C`.

---

## 📦 Packaging as a Desktop App (Electron)

To distribute DataForge as a standalone `.dmg` (Mac) or `.exe` (Windows) file, follow these steps.

### Step 1: Build the Frontend
Compile the React app into static files.
```bash
cd frontend
npm run build
```
This creates a `dist/` folder containing the UI.

### Step 2: Freeze the Backend
Use PyInstaller to turn the Python backend into a single executable file.
```bash
pip install pyinstaller
cd backend
pyinstaller --onefile --name dataforge-backend app/main.py
```
This creates `dist/dataforge-backend` (Mac/Linux) or `dist/dataforge-backend.exe` (Windows).

### Step 3: Create Electron Wrapper
1.  Initialize a new Electron project in the root:
    ```bash
    mkdir electron-app
    cd electron-app
    npm init -y
    npm install electron --save-dev
    ```
2.  Copy the frontend build (`frontend/dist`) and backend executable (`backend/dist/dataforge-backend`) into this folder.
3.  Create an `main.js` file that:
    *   Spawns the backend process on launch.
    *   Loads `index.html` from the frontend build.
    *   Kills the backend process on quit.

### Step 4: Build the Installer
Use `electron-builder` to create the final installer.
```bash
npm install electron-builder --save-dev
npm run dist
```
You will now have a professional installer file in `electron-app/dist/`.
