#!/usr/bin/env bash
set -euo pipefail

cd /app/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
