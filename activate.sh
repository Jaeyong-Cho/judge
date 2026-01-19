#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

echo "Activating virtual environment..."
source "$SCRIPT_DIR/.venv/bin/activate"

echo "Virtual environment activated!"
echo ""
echo "Available commands:"
echo "  python src/main.py      - Start CLI interface"
echo "  python src/web_ui.py    - Start web UI (http://localhost:4800)"
echo ""
echo "To deactivate: deactivate"
echo ""

exec "$SHELL"
