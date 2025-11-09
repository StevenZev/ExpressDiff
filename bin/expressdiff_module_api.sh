#!/usr/bin/env bash
# Module-friendly launcher for ExpressDiff FastAPI backend (no venv/pip installs)
# Usage: expressdiff_module_api.sh [--port PORT] [--host HOST] [--background]
# - Respects EBROOTEXPRESSDIFF as install root
# - Uses existing Python from module environment
# - Respects EXPRESSDIFF_WORKDIR or defaults to $SCRATCH/ExpressDiff
# - Does NOT install dependencies at runtime
set -euo pipefail

PORT="8000"
HOST="0.0.0.0"
BACKGROUND="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"; shift 2;;
    --host)
      HOST="$2"; shift 2;;
    --background)
      BACKGROUND="1"; shift;;
    -h|--help)
      echo "Usage: $0 [--port PORT] [--host HOST] [--background]"; exit 0;;
    *)
      echo "Unknown argument: $1" >&2; exit 1;;
  esac
done

# Determine install dir
if [[ -n "${EBROOTEXPRESSDIFF:-}" ]]; then
  INSTALL_DIR="$EBROOTEXPRESSDIFF"
else
  # Fallback: relative to this script's location
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  INSTALL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
cd "$INSTALL_DIR"

# Determine work dir: respect explicit override, else require SCRATCH
if [[ -z "${EXPRESSDIFF_WORKDIR:-}" ]]; then
  if [[ -z "${SCRATCH:-}" ]]; then
    echo "SCRATCH is not available. Please ensure you're on the cluster and SCRATCH is set (e.g., /scratch/$USER)." >&2
    exit 1
  fi
  export EXPRESSDIFF_WORKDIR="$SCRATCH"
fi
mkdir -p "$EXPRESSDIFF_WORKDIR" "$EXPRESSDIFF_WORKDIR/runs" "$EXPRESSDIFF_WORKDIR/mapping_in" || true

# Print environment diagnostics
echo "[ExpressDiff] Install dir: $INSTALL_DIR" >&2
echo "[ExpressDiff] Work dir   : $EXPRESSDIFF_WORKDIR" >&2

# Python diagnostics (support python or python3)
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "Python is not available on PATH. Load appropriate module before running." >&2
  exit 1
fi
PYTHON_VER="$($PYTHON_BIN --version 2>&1 || true)"
echo "[ExpressDiff] Python     : $PYTHON_BIN ($PYTHON_VER)" >&2

# Dependency check (no installs here)
if ! "$PYTHON_BIN" - <<'PY'
try:
    import fastapi, uvicorn  # noqa: F401
except Exception as e:
    raise SystemExit(str(e))
print("ok")
PY
then
  echo "Required Python packages not found (fastapi, uvicorn). Install them in your module environment." >&2
  echo "Hint: pip install --user -r requirements.txt (or build into the module)." >&2
  exit 1
fi

LOG_FILE="$EXPRESSDIFF_WORKDIR/backend.log"
CMD=("$PYTHON_BIN" -m uvicorn backend.api.main:app --host "$HOST" --port "$PORT" --log-level info)

echo "[ExpressDiff] Starting FastAPI server on $HOST:$PORT" >&2
if [[ "$BACKGROUND" == "1" ]]; then
  nohup "${CMD[@]}" >>"$LOG_FILE" 2>&1 &
  echo "[ExpressDiff] Running in background (PID $!). Logs: $LOG_FILE" >&2
else
  exec "${CMD[@]}"
fi
