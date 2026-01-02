#!/usr/bin/env bash

# Convenience setup script to create/activate a venv and install Python and Node deps.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PATH="venv"
PYTHON_EXEC="python"
INSTALL_NODE="yes"
AUTO_YES="no"

usage() {
    cat <<EOF
Usage: $0 [--venv PATH] [--python EXEC] [--no-node] [--yes]

Options:
  --venv PATH     Path to virtualenv (default: ./venv)
  --python EXEC   Python executable to use for venv creation (default: python)
  --no-node       Skip Node.js frontend installation
  --yes           Non-interactive, accept all prompts
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --venv)
            VENV_PATH="$2"; shift 2;;
        --python)
            PYTHON_EXEC="$2"; shift 2;;
        --no-node)
            INSTALL_NODE="no"; shift;;
        --yes)
            AUTO_YES="yes"; shift;;
        -h|--help)
            usage; exit 0;;
        *)
            echo "Unknown arg: $1"; usage; exit 1;;
    esac
done

echo "Setup: venv="$VENV_PATH" using python="$PYTHON_EXEC" (install_node=$INSTALL_NODE)"

if [[ -d "$VENV_PATH" ]]; then
    echo "Found existing virtualenv at $VENV_PATH"
else
    if [[ "$AUTO_YES" == "no" ]]; then
        read -p "Create virtualenv at $VENV_PATH using $PYTHON_EXEC? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo "Skipping virtualenv creation.";
            VENV_CREATED="no"
        else
            VENV_CREATED="yes"
        fi
    else
        VENV_CREATED="yes"
    fi

    if [[ "$VENV_CREATED" == "yes" ]]; then
        echo "Creating virtualenv..."
        if ! $PYTHON_EXEC -m venv "$VENV_PATH"; then
            echo "Failed to create venv with $PYTHON_EXEC, trying system python..."
            python3 -m venv "$VENV_PATH"
        fi
    fi
fi

if [[ -d "$VENV_PATH" ]]; then
    echo "Activating virtualenv..."
    # shellcheck disable=SC1091
    source "$VENV_PATH/bin/activate"

    if [[ -f requirements.txt ]]; then
        echo "Installing Python requirements..."
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
    else
        echo "No requirements.txt found; skipping pip install"
    fi
else
    echo "No virtualenv active; skipping Python package installation."
fi

if [[ "$INSTALL_NODE" == "yes" && -d frontend ]]; then
    if command -v npm &> /dev/null; then
        echo "Installing frontend Node.js packages..."
        pushd frontend >/dev/null
        if [[ -f package.json ]]; then
            npm install --silent
        else
            echo "No package.json in frontend/; skipping npm install"
        fi
        popd >/dev/null
    else
        echo "npm not found; skipping frontend install"
    fi
fi

echo "Setup complete."
