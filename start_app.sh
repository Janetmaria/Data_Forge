#!/bin/bash

# DataForge Auto-Start Script
# Launches Backend (FastAPI) and Frontend (Vite) in a unified process

echo "🚀 Starting DataForge..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down DataForge..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Trap Ctrl+C (SIGINT) to run cleanup
trap cleanup SIGINT

# 1. Start Backend
echo "🔹 Launching Backend..."
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to initialize..."
sleep 3

# 2. Start Frontend
echo "🔹 Launching Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ DataForge is running!"
echo "👉 Open http://localhost:5173 in your browser"
echo "Press Ctrl+C to stop everything."

# Keep script running to maintain processes
wait
