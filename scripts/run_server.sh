#!/bin/bash
# Helper script to start the DailyNews FastAPI server
set -euo pipefail
PORT="${API_PORT:-8000}"
exec uvicorn server.main:app --reload --port "$PORT"
