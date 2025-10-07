#!/bin/bash
# Start ExpressDiff backend with scratch storage configuration

# Change to ExpressDiff directory
cd /home/vth3bk/Pipelinin/ExpressDiff

# Source environment configuration (scratch storage)
source .env

# Stop any existing backend
echo "Stopping any existing backend..."
pkill -f "uvicorn.*expressdiff" 2>/dev/null || true
sleep 2

# Start the backend
echo ""
echo "Starting ExpressDiff backend..."
echo "  Code location: $(pwd)"
echo "  Data storage:  $EXPRESSDIFF_WORKDIR"
echo ""

nohup bash launch_expressdiff.sh > backend.log 2>&1 &

sleep 3

# Check if it's running
if pgrep -f "uvicorn.*expressdiff" > /dev/null; then
    echo "✓ Backend started successfully!"
    echo ""
    echo "Backend is running at: http://localhost:8000"
    echo "Logs: tail -f backend.log"
    echo ""
    echo "All uploads and outputs will be stored in:"
    echo "  $EXPRESSDIFF_WORKDIR/runs/"
else
    echo "✗ Backend failed to start. Check backend.log for errors."
    tail -20 backend.log
fi
