#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

source .venv/bin/activate

if [ "$1" == "web" ]; then
    echo "Starting Web UI..."
    python src/web_ui.py
else
    echo "Starting CLI..."
    python src/main.py
fi
