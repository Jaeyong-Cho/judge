from pathlib import Path
from typing import Dict
from function_analyzer import FunctionInfo, analyze_python_file


def display_function_list(functions: Dict[str, FunctionInfo], file_name: str):
    print(f"\n{file_name}")
    print("=" * 70)
    print(f"Total Functions: {len(functions)}\n")
    
    for func_name, func_info in sorted(functions.items()):
        print(f"  {func_name} (Lines {func_info.line_start}-{func_info.line_end})")


def display_caller_callee_details(functions: Dict[str, FunctionInfo]):
    print("\nFunction Call Relationships")
    print("=" * 70)
    
    for func_name, func_info in sorted(functions.items()):
        print(f"\n{func_name} (Lines {func_info.line_start}-{func_info.line_end})")
        print("-" * 70)
        
        if func_info.calls:
            print("  Calls:")
            for callee in sorted(func_info.calls):
                if callee in functions:
                    callee_info = functions[callee]
                    print(f"    - {callee} (Lines {callee_info.line_start}-{callee_info.line_end})")
                else:
                    print(f"    - {callee} (external or built-in)")
        else:
            print("  Calls: None")
        
        if func_info.called_by:
            print("  Called by:")
            for caller in sorted(func_info.called_by):
                caller_info = functions[caller]
                print(f"    - {caller} (Lines {caller_info.line_start}-{caller_info.line_end})")
        else:
            print("  Called by: None (entry point or unused)")


def display_function_analysis(file_path: Path):
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    functions = analyze_python_file(file_path)
    
    if not functions:
        print(f"No functions found in {file_path.name}")
        return
    
    display_function_list(functions, file_path.name)
    print()
    input("Press Enter to see detailed call relationships...")
    display_caller_callee_details(functions)


def display_project_function_summary(directory: Path):
    from function_analyzer import get_all_python_files
    
    print("\nProject Function Analysis")
    print("=" * 70)
    
    python_files = get_all_python_files(directory)
    total_functions = 0
    
    for py_file in sorted(python_files):
        functions = analyze_python_file(py_file)
        if functions:
            relative_path = py_file.relative_to(directory)
            print(f"\n{relative_path}")
            print(f"  Functions: {len(functions)}")
            total_functions += len(functions)
            for func_name in sorted(functions.keys()):
                print(f"    - {func_name}")
    
    print("\n" + "=" * 70)
    print(f"Total Python Files: {len(python_files)}")
    print(f"Total Functions: {total_functions}")
