#!/usr/bin/env bash
set -euo pipefail

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Load environment variables
export SOLARAPP_DB_URL=${SOLARAPP_DB_URL:-sqlite:///./solarapp.db}

# Run FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
