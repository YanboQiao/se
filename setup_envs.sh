#!/usr/bin/env bash
# Set up Python 3.12 virtual environments for each backend module.
set -euo pipefail

BACKEND_DIR="$(dirname "$0")/se-backend"
PYTHON_BIN="python3.12"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.12 is required but not found. Install python3.12 first." >&2
    exit 1
fi

for mod_dir in "$BACKEND_DIR"/*/; do
    [ -d "$mod_dir" ] || continue
    module=$(basename "$mod_dir")
    echo "Creating virtual environment for $module..."
    "$PYTHON_BIN" -m venv "$mod_dir/.venv"
    source "$mod_dir/.venv/bin/activate"
    python -m pip install --upgrade pip >/dev/null
    if [ -f "$mod_dir/requirements.txt" ]; then
        pip install -r "$mod_dir/requirements.txt"
    fi
    deactivate
    echo "Virtual environment for $module created."
    echo
done

if [ -d "$(dirname "$0")/gpt_academic" ]; then
    echo "Creating virtual environment for gpt_academic..."
    "$PYTHON_BIN" -m venv "$(dirname "$0")/gpt_academic/.venv"
    source "$(dirname "$0")/gpt_academic/.venv/bin/activate"
    python -m pip install --upgrade pip >/dev/null
    if [ -f "$(dirname "$0")/gpt_academic/requirements.txt" ]; then
        pip install -r "$(dirname "$0")/gpt_academic/requirements.txt"
    fi
    deactivate
    echo "Virtual environment for gpt_academic created."
    echo
fi

echo "All backend virtual environments have been created under each module."
