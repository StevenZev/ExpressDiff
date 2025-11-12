#!/usr/bin/env bash

# ExpressDiff Launch Script - Non-interactive module deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "ExpressDiff RNA-seq Pipeline — launcher"
echo "(non-interactive — dependencies managed by module)"
echo "========================================"

# Determine install directory (prefer EasyBuild root)
INSTALL_DIR="${EBROOTEXPRESSDIFF:-$SCRIPT_DIR}"

# Determine work directory for user data (matching backend config logic)
if [[ -n "${EXPRESSDIFF_WORKDIR:-}" ]]; then
    WORK_DIR="$EXPRESSDIFF_WORKDIR"
elif [[ -n "${SCRATCH:-}" ]]; then
    WORK_DIR="$SCRATCH/ExpressDiff"
else
    WORK_DIR="$HOME/ExpressDiff"
fi
mkdir -p "$WORK_DIR"

# Configure Node.js/npm to use cache in user's work directory (not system/software dirs)
export npm_config_cache="$WORK_DIR/.npm"
export npm_config_userconfig="$WORK_DIR/.npmrc"
export NPM_CONFIG_CACHE="$WORK_DIR/.npm"
export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=4096"

# Host info for user-facing URLs
HOSTNAME=$(hostname -f 2>/dev/null || hostname)

#echo "Using install dir: $INSTALL_DIR"
echo "Backend will listen on: http://$HOSTNAME:8000"
echo "Frontend will listen on: http://$HOSTNAME:3000"
echo

# Logs directory in user's work directory (not install dir, which is read-only)
LOG_DIR="$WORK_DIR/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Helper to start backend in background
start_backend_bg() {
    echo "Starting backend (uvicorn)..."
    cd "$INSTALL_DIR"

    if command -v uvicorn >/dev/null 2>&1; then
        BACKEND_CMD=(uvicorn backend.api.main:app --host 0.0.0.0 --port 8000)
    else
        BACKEND_CMD=(python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000)
    fi

    nohup "${BACKEND_CMD[@]}" > "$BACKEND_LOG" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
    echo "Backend started (PID=$(cat $LOG_DIR/backend.pid)), logs: $BACKEND_LOG"
}

# Helper to start frontend in background
start_frontend_bg() {
    echo "Starting frontend..."
    # Prefer serving a built static site if present
    if [[ -f "$INSTALL_DIR/frontend/build/index.html" ]]; then
        # Prefer npx serve if available, fall back to python http.server
        if command -v npx >/dev/null 2>&1; then
            FRONTEND_CMD=(npx serve -s "$INSTALL_DIR/frontend/build" -l 3000)
        elif command -v serve >/dev/null 2>&1; then
            FRONTEND_CMD=(serve -s "$INSTALL_DIR/frontend/build" -l 3000)
        else
            FRONTEND_CMD=(python3 -m http.server 3000 --directory "$INSTALL_DIR/frontend/build")
        fi
    else
        # No build found — fall back to dev server (npm start)
        if [[ -d "$INSTALL_DIR/frontend" && -f "$INSTALL_DIR/frontend/package.json" ]]; then
            FRONTEND_CMD=(bash -lc "cd '$INSTALL_DIR/frontend' && export npm_config_cache='$WORK_DIR/.npm' && export npm_config_userconfig='$WORK_DIR/.npmrc' && export NPM_CONFIG_CACHE='$WORK_DIR/.npm' && export REACT_APP_API_URL='http://localhost:8000' && export BROWSER=none && npm start")
        else
            echo "No frontend available to start (no build or package.json)." >&2
            return 0
        fi
    fi

    nohup "${FRONTEND_CMD[@]}" > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
    echo "Frontend started (PID=$(cat $LOG_DIR/frontend.pid)), logs: $FRONTEND_LOG"
}

# Start services (non-interactive)
start_backend_bg
start_frontend_bg

echo
echo "Launch complete. To stop services, kill the PIDs in $LOG_DIR/*.pid"
echo "Backend log: $BACKEND_LOG"
echo "Frontend log: $FRONTEND_LOG"