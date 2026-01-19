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

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / 'output' / 'graphs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

current_project_dir = PROJECT_DIR / 'src'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/project/structure')
def get_project_structure():
    try:
        assert current_project_dir.exists(), f"Project directory does not exist: {current_project_dir}"
        assert current_project_dir.is_dir(), f"Path is not a directory: {current_project_dir}"
        
        print(f"Analyzing project directory: {current_project_dir}")
        functions = analyze_project(current_project_dir)
        print(f"Found {len(functions)} functions")
        
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
                'callees_count': len([c for c in func_info.calls if c in functions]),
                'assertions_count': len(func_info.assertions)
            })
        
        print(f"Organized into {len(file_structure)} files")
        return jsonify(file_structure)
    except Exception as e:
        print(f"Error in get_project_structure: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'directory': str(current_project_dir)
        }), 500


@app.route('/api/graph/project')
def generate_project_graph():
    try:
        output_path = generate_project_call_graph(current_project_dir, OUTPUT_DIR)
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
        functions = analyze_project(current_project_dir)
        
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
        
        with open(func_info.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            source_code = ''.join(lines[func_info.line_start - 1:func_info.line_end])
        
        callers_data = []
        for caller_full_name in sorted(func_info.called_by):
            if caller_full_name in functions:
                caller = functions[caller_full_name]
                with open(caller.file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    caller_code = ''.join(lines[caller.line_start - 1:caller.line_end])
                callers_data.append({
                    'name': caller.name,
                    'full_name': caller_full_name,
                    'file': Path(caller.file_path).name,
                    'lines': f"{caller.line_start}-{caller.line_end}",
                    'source_code': caller_code
                })
        
        callees_data = []
        for callee_full_name in sorted(func_info.calls):
            if callee_full_name in functions:
                callee = functions[callee_full_name]
                with open(callee.file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    callee_code = ''.join(lines[callee.line_start - 1:callee.line_end])
                callees_data.append({
                    'name': callee.name,
                    'full_name': callee_full_name,
                    'file': Path(callee.file_path).name,
                    'lines': f"{callee.line_start}-{callee.line_end}",
                    'source_code': callee_code
                })
        
        return jsonify({
            'success': True,
            'path': f'graphs/{filename}',
            'function': {
                'name': func_info.name,
                'file': Path(func_info.file_path).name,
                'lines': f"{func_info.line_start}-{func_info.line_end}",
                'callers': len(func_info.called_by),
                'callees': len([c for c in func_info.calls if c in functions]),
                'assertions': func_info.assertions,
                'source_code': source_code,
                'file_path': func_info.file_path,
                'callers_code': callers_data,
                'callees_code': callees_data
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/directory', methods=['GET'])
def get_project_directory():
    return jsonify({
        'success': True,
        'directory': str(current_project_dir)
    })


@app.route('/api/project/directory', methods=['POST'])
def set_project_directory():
    global current_project_dir
    try:
        data = request.json
        new_dir = Path(data.get('directory', ''))
        
        print(f"Attempting to set project directory to: {new_dir}")
        
        assert new_dir.exists(), f"Directory does not exist: {new_dir}"
        assert new_dir.is_dir(), f"Path is not a directory: {new_dir}"
        
        current_project_dir = new_dir
        print(f"Project directory set to: {current_project_dir}")
        
        return jsonify({
            'success': True,
            'directory': str(current_project_dir)
        })
    except Exception as e:
        print(f"Error setting project directory: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/graphs/<path:filename>')
def serve_graph(filename):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return send_file(file_path, mimetype='image/svg+xml')
    return "File not found", 404


@app.route('/api/project/assertions')
def get_all_assertions():
    try:
        functions = analyze_project(current_project_dir)
        
        assertions_data = []
        total_assertions = 0
        functions_with_assertions = 0
        
        for full_name, func_info in sorted(functions.items()):
            if func_info.assertions:
                functions_with_assertions += 1
                total_assertions += len(func_info.assertions)
                
                assertions_data.append({
                    'full_name': full_name,
                    'name': func_info.name,
                    'file': Path(func_info.file_path).name,
                    'lines': f"{func_info.line_start}-{func_info.line_end}",
                    'assertions': func_info.assertions,
                    'assertion_count': len(func_info.assertions)
                })
        
        return jsonify({
            'success': True,
            'functions': assertions_data,
            'summary': {
                'total_functions': len(functions),
                'functions_with_assertions': functions_with_assertions,
                'total_assertions': total_assertions,
                'average': total_assertions / len(functions) if len(functions) > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
