#!/usr/bin/env bash

# Quick installation script for ExpressDiff with Python 3.11.4
set -e

echo "========================================"
echo "ExpressDiff Installation"
echo "========================================"
echo

# Load modules
echo "Step 1: Loading Python 3.11.4..."
module load gcc/11.4.0 openmpi/4.1.4 python/3.11.4
echo "✓ Modules loaded"
echo

# Create virtual environment
echo "Step 2: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Remove it? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf venv
        python -m venv venv
        echo "✓ Virtual environment recreated"
    else
        echo "Using existing virtual environment"
    fi
else
    python -m venv venv
    echo "✓ Virtual environment created"
fi
echo

# Activate and install
echo "Step 3: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo

# Verify installation
echo "Step 4: Verifying installation..."
python -c "
import fastapi
import uvicorn
import pydantic
import pandas
import numpy

print('✓ All core packages installed successfully')
print(f'  - FastAPI: {fastapi.__version__}')
print(f'  - Uvicorn: {uvicorn.__version__}')
print(f'  - Pydantic: {pydantic.__version__}')
print(f'  - Pandas: {pandas.__version__}')
print(f'  - NumPy: {numpy.__version__}')
"
echo

echo "========================================"
echo "Installation complete!"
echo "========================================"
echo
echo "To start ExpressDiff:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Start backend: uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000"
echo "  3. Or use: ./launch_expressdiff.sh"
echo
