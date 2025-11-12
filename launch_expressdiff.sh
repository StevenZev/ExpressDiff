#!/usr/bin/env bash

# ExpressDiff Launch Script
# This script helps users start the ExpressDiff RNA-seq pipeline on HPC

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment configuration (sets up scratch storage)
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Set working directory if not already set
if [[ -z "$EXPRESSDIFF_WORKDIR" ]]; then
    if [[ -n "$SCRATCH" ]]; then
        export EXPRESSDIFF_WORKDIR="$SCRATCH/expressdiff"
        echo "Setting work directory to: $EXPRESSDIFF_WORKDIR"
    else
        # Fallback to a sensible default in the project directory
        export EXPRESSDIFF_WORKDIR="$SCRIPT_DIR/ExpressDiff"
        echo "WARNING: SCRATCH not set. Using project directory: $EXPRESSDIFF_WORKDIR"
    fi
    mkdir -p "$EXPRESSDIFF_WORKDIR"
fi

echo "ExpressDiff RNA-seq Pipeline Launcher"
echo "========================================"
echo

# Check if we're in a SLURM allocation
if [[ -z "$SLURM_JOB_ID" ]]; then
    echo "WARNING: You are not in a SLURM allocation. For best results, start an interactive session:"
    echo "   salloc -A <your_account> -p standard -c 4 --mem=16G -t 02:00:00"
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Load required modules
echo "Loading modules..."
if command -v module &> /dev/null; then
    # Load Python (try different versions)
    if module load python/3.10 2>/dev/null; then
    echo "   Loaded Python 3.10"
    elif module load python/3.9 2>/dev/null; then
    echo "   Loaded Python 3.9"
    elif module load python/3.8 2>/dev/null; then
    echo "   Loaded Python 3.8"
    else
    echo "   WARNING: No Python 3.8+ module found, using system Python"
    fi
    
    # Load Node.js
    if module load nodejs 2>/dev/null || module load nodejs/24.5.0 2>/dev/null; then
    echo "   Loaded Node.js"
    else
    echo "   WARNING: Node.js module not found - frontend won't work"
    fi
else
    echo "   WARNING: Module system not available"
fi

# Skip any installation; rely on pre-installed environment
echo
echo "Environment setup"
echo "Using existing environment (no installations will be performed)."
if ! command -v npm &> /dev/null; then
    echo "WARNING: Node.js not available; frontend won't be started."
    echo "You can access the API directly at: http://localhost:8000/docs"
fi

# Get the current hostname (compute node)
HOSTNAME=$(hostname)
echo
echo "Starting ExpressDiff..."
echo "   Backend will be available at: http://$HOSTNAME:8000"
if command -v npm &> /dev/null; then
    echo "   Frontend will be available at: http://$HOSTNAME:3000"
fi
echo

# Function to start backend
start_backend() {
    echo "Starting backend server..."
    # Activate venv if present
    if [[ -f "venv/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source venv/bin/activate
        echo "   Activated venv at ./venv"
    else
        echo "   No venv found at ./venv — running with system Python"
    fi

    # Ensure EXPRESSDIFF_WORKDIR is exported
    if [[ -z "$EXPRESSDIFF_WORKDIR" ]]; then
        echo "ERROR: EXPRESSDIFF_WORKDIR not set"
        exit 1
    fi
    echo "   Work directory: $EXPRESSDIFF_WORKDIR"

    # Use the current Python interpreter to run uvicorn so the venv's python is used when active
    python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
}

# Function to start frontend
start_frontend() {
    if command -v npm &> /dev/null; then
        echo "Starting frontend server..."
        cd frontend
        export REACT_APP_API_URL="http://localhost:8000"
        npm start
    else
        echo "Frontend not available (Node.js not found)"
        echo "Access the API documentation at: http://localhost:8000/docs"
        sleep infinity  # Keep the script running
    fi
}

# Check if user wants to run both or just backend
if command -v npm &> /dev/null; then
    echo "Choose launch mode:"
    echo "1) Backend only (API server)"
    echo "2) Frontend only (React app) - requires backend running separately"
    echo "3) Backend + Frontend (recommended for FastX desktop)"
    echo "4) Help with SSH tunneling"
    echo
    read -p "Select option (1-4): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            start_backend
            ;;
        2)
            start_frontend
            ;;
        3)
            echo "Starting both services..."
            echo "Backend logs will be in the background."
            echo "Press Ctrl+C to stop both services."
            echo
            
            # Start backend in background
            start_backend &
            BACKEND_PID=$!
            
            # Wait a moment for backend to start
            sleep 3
            
            # Start frontend in foreground
            trap "kill $BACKEND_PID 2>/dev/null; exit" EXIT INT TERM
            start_frontend
            ;;
        4)
            echo
            echo "SSH Tunneling Help:"
            echo "==================="
            echo
            echo "If you're not using FastX desktop, you can tunnel to your local machine:"
            echo
            echo "1. Note the hostname: $HOSTNAME"
            echo "2. On your LOCAL machine, run:"
            echo "   ssh -L 8000:$HOSTNAME:8000 -L 3000:$HOSTNAME:3000 <username>@<hpc-login-node>"
            echo
            echo "3. Then access in your local browser:"
            echo "   - Frontend: http://localhost:3000"
            echo "   - API docs: http://localhost:8000/docs"
            echo
            echo "Run this script again to start the servers."
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
else
    # No npm, just run backend
    start_backend
fi