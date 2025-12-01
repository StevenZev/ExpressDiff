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
echo "Backend will listen on: http://$HOSTNAME:81234"
echo "Frontend will listen on: http://$HOSTNAME:3000"
echo

# Logs directory in user's work directory (not install dir, which is read-only)
LOG_DIR="$WORK_DIR/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Helper to check if port is available and kill old process if needed
check_and_free_port() {
    local port=$1
    local pid_file="$LOG_DIR/backend.pid"
    
    # Check if port is in use
    if ss -tln | grep -q ":${port} "; then
        echo "Port $port is already in use."
        
        # Check if we have a PID file from a previous run
        if [[ -f "$pid_file" ]]; then
            local old_pid=$(cat "$pid_file")
            if ps -p "$old_pid" > /dev/null 2>&1; then
                echo "Killing previous backend process (PID: $old_pid)..."
                kill "$old_pid" 2>/dev/null || true
                sleep 2
                # Force kill if still running
                if ps -p "$old_pid" > /dev/null 2>&1; then
                    kill -9 "$old_pid" 2>/dev/null || true
                    sleep 1
                fi
            fi
        fi
        
        # Double check port is free now
        if ss -tln | grep -q ":${port} "; then
            echo "WARNING: Port $port is still in use by another process."
            echo "Please free port $port or use a different port."
            return 1
        fi
    fi
    return 0
}

# Helper to start backend in background
start_backend_bg() {
    echo "Starting backend (uvicorn)..."
    
    # Check and free port 81234 if needed
    if ! check_and_free_port 81234; then
        echo "Failed to start backend: port 81234 unavailable" >&2
        return 1
    fi
    
    # Change to install directory so backend module can be imported
    cd "$INSTALL_DIR"
    
    # Set PYTHONPATH to ensure backend module can be found
    export PYTHONPATH="$INSTALL_DIR:${PYTHONPATH:-}"

    if command -v uvicorn >/dev/null 2>&1; then
        BACKEND_CMD=(uvicorn backend.api.main:app --host 0.0.0.0 --port 81234)
    else
        BACKEND_CMD=(python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 81234)
    fi

    nohup "${BACKEND_CMD[@]}" > "$BACKEND_LOG" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
    echo "Backend started (PID=$(cat $LOG_DIR/backend.pid)), logs: $BACKEND_LOG"
}

# Helper to start frontend in background
start_frontend_bg() {
    echo "Starting frontend..."

    # Kill old frontend process if it exists
    local pid_file="$LOG_DIR/frontend.pid"
    if [[ -f "$pid_file" ]]; then
        local old_pid=$(cat "$pid_file")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            echo "Killing previous frontend process (PID: $old_pid)..."
            kill "$old_pid" 2>/dev/null || true
            sleep 2
        fi
    fi

    # Always serve the build from the install directory using python http.server on port 51235
    BUILD_DIR="$INSTALL_DIR/frontend/build"
    if [[ -f "$BUILD_DIR/index.html" ]]; then
        FRONTEND_CMD=(python3 -m http.server 51235 --directory "$BUILD_DIR")
        nohup "${FRONTEND_CMD[@]}" > "$FRONTEND_LOG" 2>&1 &
        echo $! > "$LOG_DIR/frontend.pid"
        echo "Frontend started (PID=$(cat $LOG_DIR/frontend.pid)), logs: $FRONTEND_LOG"
        echo "Frontend is being served at: http://$HOSTNAME:51235"
    else
        echo "No frontend build found at $BUILD_DIR. Please build the frontend and try again." >&2
        return 1
    fi
}

# Start services (non-interactive)
start_backend_bg
start_frontend_bg

echo
echo "Launch complete. To stop services, kill the PIDs in $LOG_DIR/*.pid"
echo "Backend log: $BACKEND_LOG"
echo "Frontend log: $FRONTEND_LOG"