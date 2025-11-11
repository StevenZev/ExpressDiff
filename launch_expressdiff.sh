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

# Host info for user-facing URLs
HOSTNAME=$(hostname -f 2>/dev/null || hostname)

#echo "Using install dir: $INSTALL_DIR"
echo "Backend will listen on: http://$HOSTNAME:8000"
echo "Frontend will listen on: http://$HOSTNAME:3000"
echo

# Logs
mkdir -p "$INSTALL_DIR/logs"
BACKEND_LOG="$INSTALL_DIR/logs/backend.log"
FRONTEND_LOG="$INSTALL_DIR/logs/frontend.log"

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
    echo $! > "$INSTALL_DIR/logs/backend.pid"
    echo "Backend started (PID=$(cat $INSTALL_DIR/logs/backend.pid)), logs: $BACKEND_LOG"
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
            FRONTEND_CMD=(bash -lc "cd '$INSTALL_DIR/frontend' && export REACT_APP_API_URL='http://localhost:8000' && export BROWSER=none && npm start")
        else
            echo "No frontend available to start (no build or package.json)." >&2
            return 0
        fi
    fi

    nohup "${FRONTEND_CMD[@]}" > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$INSTALL_DIR/logs/frontend.pid"
    echo "Frontend started (PID=$(cat $INSTALL_DIR/logs/frontend.pid)), logs: $FRONTEND_LOG"
}

# Start services (non-interactive)
start_backend_bg
start_frontend_bg

echo
echo "Launch complete. To stop services, kill the PIDs in $INSTALL_DIR/logs/*.pid"
echo "Backend log: $BACKEND_LOG"
echo "Frontend log: $FRONTEND_LOG"