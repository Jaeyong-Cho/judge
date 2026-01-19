from flask import Flask, render_template, jsonify, send_file, request
from pathlib import Path
import json
from function_analyzer import analyze_project, analyze_python_file
from function_display import (
    generate_call_graph,
    generate_function_focus_graph,
    generate_project_call_graph,
    generate_project_function_focus_graph
)

app = Flask(__name__)

PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR = PROJECT_DIR.parent / 'output' / 'graphs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/project/structure')
def get_project_structure():
    functions = analyze_project(PROJECT_DIR)
    
    file_structure = {}
    for full_name, func_info in functions.items():
        file_path = Path(func_info.file_path).name
        if file_path not in file_structure:
            file_structure[file_path] = []
        
        file_structure[file_path].append({
            'name': func_info.name,
            'full_name': full_name,
            'line_start': func_info.line_start,
            'line_end': func_info.line_end,
            'callers_count': len(func_info.called_by),
            'callees_count': len([c for c in func_info.calls if c in functions])
        })
    
    return jsonify(file_structure)


@app.route('/api/graph/project')
def generate_project_graph():
    try:
        output_path = generate_project_call_graph(PROJECT_DIR, OUTPUT_DIR)
        filename = Path(output_path).name
        return jsonify({
            'success': True,
            'path': f'graphs/{filename}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/graph/function/<path:func_full_name>')
def generate_function_graph(func_full_name):
    try:
        functions = analyze_project(PROJECT_DIR)
        
        if func_full_name not in functions:
            return jsonify({
                'success': False,
                'error': 'Function not found'
            }), 404
        
        output_path = generate_project_function_focus_graph(
            func_full_name, 
            functions, 
            OUTPUT_DIR
        )
        
        filename = Path(output_path).name
        
        func_info = functions[func_full_name]
        
        return jsonify({
            'success': True,
            'path': f'graphs/{filename}',
            'function': {
                'name': func_info.name,
                'file': Path(func_info.file_path).name,
                'lines': f"{func_info.line_start}-{func_info.line_end}",
                'callers': len(func_info.called_by),
                'callees': len([c for c in func_info.calls if c in functions])
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/graphs/<path:filename>')
def serve_graph(filename):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return send_file(file_path, mimetype='image/svg+xml')
    return "File not found", 404


@app.route('/api/project/tree')
def get_project_tree():
    import os
    
    def build_tree(directory, prefix="", is_last=True):
        entries = []
        try:
            items = sorted(os.listdir(directory))
            items = [item for item in items if not item.startswith('.') and item not in ['__pycache__', '.venv', 'output', 'graphs']]
            
            for i, item in enumerate(items):
                path = os.path.join(directory, item)
                is_last_item = i == len(items) - 1
                
                connector = "└── " if is_last_item else "├── "
                entries.append({
                    'name': prefix + connector + item,
                    'path': path,
                    'is_dir': os.path.isdir(path)
                })
                
                if os.path.isdir(path):
                    extension = "    " if is_last_item else "│   "
                    entries.extend(build_tree(path, prefix + extension, is_last_item))
        except PermissionError:
            pass
        
        return entries
    
    tree = build_tree(PROJECT_DIR)
    return jsonify({'tree': tree, 'root': str(PROJECT_DIR)})


def start_web_ui(port=4800):
    print(f"\nStarting web UI at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    app.run(debug=False, port=port, host='0.0.0.0')


if __name__ == '__main__':
    start_web_ui()
