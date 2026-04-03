#!/usr/bin/env bash
set -euo pipefail

cd /app/backend
echo "==> Running database migrations..."
uv run alembic upgrade head
echo "==> Starting uvicorn..."
uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
