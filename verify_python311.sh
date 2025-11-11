#!/usr/bin/env bash

# Verification script for Python 3.11.4 setup
echo "========================================"
echo "ExpressDiff Python 3.11.4 Verification"
echo "========================================"
echo

# Load modules
echo "Loading required modules..."
module load gcc/11.4.0 openmpi/4.1.4 python/3.11.4

if [ $? -eq 0 ]; then
    echo "✓ Modules loaded successfully"
else
    echo "✗ Failed to load modules"
    exit 1
fi

echo

# Check Python version
echo "Python version:"
python --version

echo

# Check key packages
echo "Checking if key packages can be imported..."
python -c "
import sys
print(f'Python executable: {sys.executable}')
print(f'Python version: {sys.version}')
print()

packages = {
    'fastapi': 'FastAPI',
    'uvicorn': 'Uvicorn',
    'pydantic': 'Pydantic',
    'pandas': 'Pandas',
    'numpy': 'NumPy'
}

print('Package availability:')
for module, name in packages.items():
    try:
        __import__(module)
        print(f'  ✓ {name}')
    except ImportError:
        print(f'  ✗ {name} (not installed)')
"

echo
echo "========================================"
echo "To install dependencies, run:"
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "========================================"
