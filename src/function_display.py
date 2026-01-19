from pathlib import Path
from typing import Dict, List
from function_analyzer import FunctionInfo, analyze_python_file, get_all_python_files


def display_project_structure(directory: Path):
    python_files = get_all_python_files(directory)
    
    print("\nProject Structure (Python Files)")
    print("=" * 70)
    
    for idx, py_file in enumerate(sorted(python_files), 1):
        relative_path = py_file.relative_to(directory)
        print(f"  {idx}. {relative_path}")
    
    print("=" * 70)
    print(f"Total: {len(python_files)} files")


def display_file_functions(file_path: Path):
    assert file_path.exists(), f"File not found: {file_path}"
    
    functions = analyze_python_file(file_path)
    
    assert len(functions) > 0, f"No functions found in {file_path.name}"
    
    print(f"\nFile: {file_path.name}")
    print("=" * 70)
    print(f"Functions: {len(functions)}\n")
    
    for idx, (func_name, func_info) in enumerate(sorted(functions.items()), 1):
        print(f"  {idx}. {func_name} (Lines {func_info.line_start}-{func_info.line_end})")
    
    return functions


def display_function_calls(func_name: str, functions: Dict[str, FunctionInfo]):
    assert func_name in functions, f"Function not found: {func_name}"
    
    func_info = functions[func_name]
    
    print(f"\nFunction: {func_name}")
    print("=" * 70)
    print(f"Location: Lines {func_info.line_start}-{func_info.line_end}\n")
    
    print("Calls:")
    print("-" * 70)
    if func_info.calls:
        for callee in sorted(func_info.calls):
            if callee in functions:
                callee_info = functions[callee]
                print(f"  - {callee} (Lines {callee_info.line_start}-{callee_info.line_end})")
            else:
                print(f"  - {callee} (external)")
    else:
        print("  None")
    
    print("\nCalled by:")
    print("-" * 70)
    if func_info.called_by:
        for caller in sorted(func_info.called_by):
            caller_info = functions[caller]
            print(f"  - {caller} (Lines {caller_info.line_start}-{caller_info.line_end})")
    else:
        print("  None (entry point or unused)")


def select_file_interactive(directory: Path) -> Path:
    python_files = sorted(get_all_python_files(directory))
    
    assert len(python_files) > 0, "No Python files found"
    
    display_project_structure(directory)
    
    while True:
        choice = input("\nSelect file number (0 to cancel): ").strip()
        
        if choice == "0":
            return None
        
        try:
            idx = int(choice) - 1
            assert 0 <= idx < len(python_files), "Invalid selection"
            return python_files[idx]
        except (ValueError, AssertionError):
            print("Invalid selection. Try again.")


def select_function_interactive(functions: Dict[str, FunctionInfo]) -> str:
    func_list = sorted(functions.keys())
    
    while True:
        choice = input("\nSelect function number (0 to cancel): ").strip()
        
        if choice == "0":
            return None
        
        try:
            idx = int(choice) - 1
            assert 0 <= idx < len(func_list), "Invalid selection"
            return func_list[idx]
        except (ValueError, AssertionError):
            print("Invalid selection. Try again.")
