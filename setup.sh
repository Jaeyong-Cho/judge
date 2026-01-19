#!/bin/bash

set -e

echo "======================================"
echo "Judge - Function Analysis Tool Setup"
echo "======================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

if ! command -v dot &> /dev/null; then
    echo ""
    echo "Warning: Graphviz is not installed"
    echo "Installing Graphviz..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install graphviz
        else
            echo "Error: Homebrew is not installed"
            echo "Please install Graphviz manually:"
            echo "  brew install graphviz"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y graphviz
        elif command -v yum &> /dev/null; then
            sudo yum install -y graphviz
        else
            echo "Error: Package manager not found"
            echo "Please install Graphviz manually"
            exit 1
        fi
    else
        echo "Unsupported OS: $OSTYPE"
        echo "Please install Graphviz manually"
        exit 1
    fi
fi

echo ""
echo "Creating Python virtual environment..."
if [ -d ".venv" ]; then
    echo "Virtual environment already exists, skipping creation"
else
    python3 -m venv .venv
    echo "Virtual environment created"
fi

echo ""
echo "Activating virtual environment..."
source "$SCRIPT_DIR/.venv/bin/activate"

echo ""
echo "Installing Python dependencies..."
"$SCRIPT_DIR/.venv/bin/pip" install --upgrade pip
"$SCRIPT_DIR/.venv/bin/pip" install -r requirements.txt

echo ""
echo "Creating output directories..."
mkdir -p output/graphs

echo ""
echo "======================================"
echo "Setup completed successfully!"
echo "======================================"
echo ""
echo "To start using the tool:"
echo ""
echo "  Option 1 (Recommended):"
echo "    ./run.sh            # Start CLI"
echo "    ./run.sh web        # Start Web UI"
echo ""
echo "  Option 2:"
echo "    source .venv/bin/activate"
echo "    python src/main.py"
echo ""
