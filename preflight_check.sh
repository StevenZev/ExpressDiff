#!/bin/bash
# Pre-flight check before starting ExpressDiff

echo "=== ExpressDiff Pre-Flight Check ==="
echo

# Check we're in the right directory
CURRENT_DIR=$(pwd)
EXPECTED_DIR="/home/vth3bk/Pipelinin/ExpressDiff"

if [ "$CURRENT_DIR" != "$EXPECTED_DIR" ]; then
    echo "❌ Wrong directory!"
    echo "   Current:  $CURRENT_DIR"
    echo "   Expected: $EXPECTED_DIR"
    echo
    echo "Run: cd $EXPECTED_DIR"
    exit 1
fi
echo "✓ In correct directory: $CURRENT_DIR"

# Check .env file
if [ -f ".env" ]; then
    echo "✓ .env file exists"
    source .env
else
    echo "❌ .env file missing!"
    exit 1
fi

# Check environment variables
echo
echo "Environment variables:"
echo "  EXPRESSDIFF_HOME:    ${EXPRESSDIFF_HOME}"
echo "  EXPRESSDIFF_WORKDIR: ${EXPRESSDIFF_WORKDIR}"
echo "  SCRATCH:             ${SCRATCH}"

if [ -z "$EXPRESSDIFF_WORKDIR" ]; then
    echo "❌ EXPRESSDIFF_WORKDIR not set!"
    exit 1
fi
echo "✓ Environment configured"

# Check Python backend can be imported
echo
echo "Testing Python backend..."
python3 -c "import backend.api.main; from backend.core.config import Config; print('  BASE_DIR:', Config.BASE_DIR); print('  INSTALL_DIR:', Config.INSTALL_DIR)" 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Backend module OK"
else
    echo "❌ Backend import failed!"
    exit 1
fi

# Check templates
echo
echo "Checking templates..."
if [ -f "slurm_templates/trim.slurm.template" ]; then
    LINES=$(wc -l < slurm_templates/trim.slurm.template)
    echo "✓ trim.slurm.template exists ($LINES lines)"
else
    echo "❌ trim.slurm.template missing!"
    exit 1
fi

# Check work directory exists
echo
echo "Checking work directory..."
if [ -d "$EXPRESSDIFF_WORKDIR" ]; then
    echo "✓ Work directory exists: $EXPRESSDIFF_WORKDIR"
else
    echo "⚠ Work directory doesn't exist yet: $EXPRESSDIFF_WORKDIR"
    echo "  Will be created automatically"
fi

# Check for other running instances
echo
echo "Checking for running instances..."
RUNNING=$(ps aux | grep -E "[u]vicorn.*backend.api.main" | wc -l)
if [ $RUNNING -gt 0 ]; then
    echo "⚠ Found $RUNNING running backend instance(s)"
    echo "  You may want to stop them first:"
    echo "  pkill -f 'uvicorn.*backend.api.main'"
    ps aux | grep "[u]vicorn.*backend.api.main"
else
    echo "✓ No conflicting instances running"
fi

# Summary
echo
echo "=== Summary ==="
echo "✓ All checks passed!"
echo
echo "You can now start ExpressDiff:"
echo "  bash launch_expressdiff.sh > backend.log 2>&1 &"
echo
echo "Data will be stored in:"
echo "  $EXPRESSDIFF_WORKDIR/runs/"
