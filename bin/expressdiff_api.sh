#!/usr/bin/env bash
# Lightweight launcher to start ExpressDiff FastAPI backend inside (or creating) a venv
# Usage: expressdiff_api.sh [PORT]
set -euo pipefail

PORT="${1:-81234}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

if [ ! -d .venv ]; then
  echo "[ExpressDiff] Creating virtual environment (.venv)" >&2
  python3 -m venv .venv
fi
source .venv/bin/activate

# Install / upgrade minimal deps if needed (idempotent)
python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -q -r requirements.txt

echo "[ExpressDiff] Starting FastAPI server on 0.0.0.0:${PORT}" >&2
exec uvicorn backend.api.main:app --host 0.0.0.0 --port "${PORT}" --log-level info
