# Judge - Function Analysis Tool

A Python-based tool for analyzing function calls, dependencies, and assertions in Python projects with an interactive web interface.

## Features

- Function call graph visualization
- Assertion tracking and analysis
- Interactive web UI with code viewer
- Caller/callee relationship analysis
- Collapsible code sections
- Assert highlighting
- Project-wide analysis

## Requirements

- Python 3.8 or higher
- Graphviz (for graph visualization)

## Quick Setup

Run the setup script to install all dependencies:

```bash
./setup.sh
```

This will:
- Check for Python 3 and Graphviz
- Create a virtual environment
- Install all Python dependencies
- Create necessary output directories
- Activate the virtual environment in a new shell

## Usage

### Option 1: Using run.sh (Recommended)

The easiest way to run the tool:

```bash
# Start CLI interface
./run.sh

# Start Web UI
./run.sh web
```

### Option 2: Using activate.sh

Activate the virtual environment in your current shell:

```bash
source activate.sh
# or
. activate.sh
```

Then run the tool:

```bash
python src/main.py          # CLI interface
python src/web_ui.py        # Web UI
```

### Option 3: Manual Activation

```bash
source .venv/bin/activate
python src/main.py
```

## Manual Setup

If you prefer to set up manually:

1. Install Graphviz:
   - macOS: `brew install graphviz`
   - Ubuntu/Debian: `sudo apt-get install graphviz`
   - CentOS/RHEL: `sudo yum install graphviz`

2. Create and activate virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## CLI Options

When running the tool via `./run.sh` or `python src/main.py`:

### Command Line Interface

Available options:
- **W**: Start Web UI
- **S**: View project structure
- **F**: View file functions
- **C**: View function call relationships
- **G**: Generate full call graph
- **V**: Generate function focus graph
- **P**: Generate project call graph
- **X**: Project-wide function focus
- **A**: Batch generate all function focus graphs
- **T**: View all assertions in a file
- **E**: View assertions for specific function
- **D**: Clear workspace data

### Web UI

Start the web interface:

```bash
./run.sh web
# or
python src/web_ui.py
```

Then open your browser to `http://localhost:4800`

Features:
- Browse all functions in the project
- View function call graphs interactively
- See caller and callee source code
- Highlight assert statements
- Collapsible code sections
- Zoom and pan on graphs

## Project Structure

```
judge/
├── src/
│   ├── function_analyzer.py    # Core analysis engine
│   ├── function_display.py     # Display and graph generation
│   ├── main.py                 # CLI interface
│   ├── web_ui.py               # Web server
│   └── templates/
│       └── index.html          # Web UI interface
├── output/
│   └── graphs/                 # Generated graph files
├── requirements.txt            # Python dependencies
└── setup.sh                    # Setup script
```

## Dependencies

- **Flask**: Web framework for UI
- **graphviz**: Graph generation library
- **tree-sitter**: Code parsing library
- **tree-sitter-python**: Python language grammar

## License

MIT License
