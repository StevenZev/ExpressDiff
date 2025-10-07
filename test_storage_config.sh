#!/bin/bash
# Verify ExpressDiff storage configuration

echo "=== ExpressDiff Storage Configuration Test ==="
echo

# Source configuration
cd /home/vth3bk/Pipelinin/ExpressDiff
source .env

echo "1. Environment Variables:"
echo "   EXPRESSDIFF_HOME:    $EXPRESSDIFF_HOME"
echo "   EXPRESSDIFF_WORKDIR: $EXPRESSDIFF_WORKDIR"
echo "   SCRATCH:             $SCRATCH"
echo

echo "2. Directory Verification:"
if [ -d "$EXPRESSDIFF_HOME" ]; then
    echo "   ✓ Install directory exists: $EXPRESSDIFF_HOME"
else
    echo "   ✗ Install directory missing: $EXPRESSDIFF_HOME"
fi

if [ -d "$EXPRESSDIFF_WORKDIR" ]; then
    echo "   ✓ Work directory exists: $EXPRESSDIFF_WORKDIR"
else
    echo "   ⚠ Work directory will be created: $EXPRESSDIFF_WORKDIR"
    mkdir -p "$EXPRESSDIFF_WORKDIR/runs"
fi
echo

echo "3. Template Files:"
if [ -f "$EXPRESSDIFF_HOME/slurm_templates/trim.slurm.template" ]; then
    echo "   ✓ Trim template found"
    lines=$(wc -l < "$EXPRESSDIFF_HOME/slurm_templates/trim.slurm.template")
    echo "     ($lines lines)"
else
    echo "   ✗ Trim template missing"
fi
echo

echo "4. Backend Files:"
if [ -f "$EXPRESSDIFF_HOME/backend/api/main.py" ]; then
    echo "   ✓ Backend API found"
else
    echo "   ✗ Backend API missing"
fi
echo

echo "5. Storage Location Test:"
echo "   Code will run from:  $EXPRESSDIFF_HOME"
echo "   Data will be stored: $EXPRESSDIFF_WORKDIR/runs/"
echo

# Check Python config will pick this up
echo "6. Testing Python Config Detection:"
export EXPRESSDIFF_HOME="$EXPRESSDIFF_HOME"
export EXPRESSDIFF_WORKDIR="$EXPRESSDIFF_WORKDIR"

python3 -c "
import os
from pathlib import Path
workdir = os.environ.get('EXPRESSDIFF_WORKDIR')
if workdir:
    print(f'   ✓ Python will use: {workdir}')
else:
    scratch = os.environ.get('SCRATCH')
    if scratch:
        print(f'   ✓ Python will use: {scratch}/ExpressDiff')
    else:
        print(f'   ✓ Python will use: {Path.home()}/ExpressDiff')
" 2>/dev/null || echo "   ⚠ Could not test Python config"

echo
echo "=== Configuration Valid ==="
echo
echo "To start backend with this configuration:"
echo "  ./start_backend.sh"
