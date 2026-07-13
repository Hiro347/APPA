#!/bin/bash
echo "🚀 Starting APPA Backend (FastAPI)..."
cd "$(dirname "$0")/backend"

# Gunakan python3 dan uvicorn langsung (tanpa repot activate venv)
python3 -m uvicorn main:app --reload --port 8000
