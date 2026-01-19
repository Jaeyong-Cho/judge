from pathlib import Path
from typing import Dict, List, Set
from function_analyzer import FunctionInfo, analyze_python_file, get_all_python_files, analyze_project
import graphviz


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


def generate_call_graph(functions: Dict[str, FunctionInfo], file_name: str, output_dir: Path):
    assert len(functions) > 0, "No functions to visualize"
    
    dot = graphviz.Digraph(comment=f'Call Graph: {file_name}')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
    
    entry_points: Set[str] = set()
    for func_name, func_info in functions.items():
        if not func_info.called_by:
            entry_points.add(func_name)
    
    for func_name in entry_points:
        dot.node(func_name, func_name, fillcolor='lightgreen')
    
    for func_name, func_info in functions.items():
        if func_name not in entry_points:
            if not func_info.calls:
                dot.node(func_name, func_name, fillcolor='lightyellow')
            else:
                dot.node(func_name, func_name)
    
    for func_name, func_info in functions.items():
        for callee in func_info.calls:
            if callee in functions:
                edge_color = 'red' if callee == func_name else 'black'
                dot.edge(func_name, callee, color=edge_color, penwidth='2' if edge_color == 'red' else '1')
    
    output_path = output_dir / f'{file_name}_call_graph'
    dot.render(output_path, format='svg', cleanup=True)
    
    print(f"\nGraph generated: {output_path}.svg")
    return f"{output_path}.svg"


def generate_function_focus_graph(func_name: str, functions: Dict[str, FunctionInfo], file_name: str, output_dir: Path):
    assert func_name in functions, f"Function not found: {func_name}"
    
    func_info = functions[func_name]
    dot = graphviz.Digraph(comment=f'Function Focus: {func_name}')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled')
    
    dot.node(func_name, func_name, fillcolor='orange', penwidth='3')
    
    for caller in func_info.called_by:
        if caller in functions:
            dot.node(caller, caller, fillcolor='lightgreen')
            dot.edge(caller, func_name, color='blue', penwidth='2')
    
    for callee in func_info.calls:
        if callee in functions:
            is_recursive = callee == func_name
            color = 'red' if is_recursive else 'lightblue'
            dot.node(callee, callee, fillcolor=color)
            dot.edge(func_name, callee, color='red' if is_recursive else 'darkgreen', penwidth='2')
        else:
            dot.node(callee, callee, fillcolor='lightgray', style='filled,dashed')
            dot.edge(func_name, callee, style='dashed')
    
    output_path = output_dir / f'{file_name}_{func_name}_focus'
    dot.render(output_path, format='svg', cleanup=True)
    
    print(f"\nGraph generated: {output_path}.svg")
    print("\nLegend:")
    print("  Orange (bold): Target function")
    print("  Green: Callers")
    print("  Blue: Callees (internal)")
    print("  Gray (dashed): External functions")
    print("  Red edges: Recursive calls")
    
    return f"{output_path}.svg"


def generate_project_call_graph(directory: Path, output_dir: Path):
    functions = analyze_project(directory)
    
    assert len(functions) > 0, "No functions found in project"
    
    dot = graphviz.Digraph(comment='Project Call Graph')
    dot.attr(rankdir='LR')
    dot.attr('graph', splines='ortho', nodesep='0.8', ranksep='1.5')
    
    file_clusters: Dict[str, List[str]] = {}
    for full_name, func_info in functions.items():
        file_path = func_info.file_path
        if file_path not in file_clusters:
            file_clusters[file_path] = []
        file_clusters[file_path].append(full_name)
    
    for idx, (file_path, func_list) in enumerate(sorted(file_clusters.items())):
        file_name = Path(file_path).name
        with dot.subgraph(name=f'cluster_{idx}') as cluster:
            cluster.attr(label=file_name, style='filled', color='lightgrey')
            cluster.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
            
            for full_name in func_list:
                func_info = functions[full_name]
                display_name = func_info.name
                
                if not func_info.called_by:
                    cluster.node(full_name, display_name, fillcolor='lightgreen')
                elif not func_info.calls:
                    cluster.node(full_name, display_name, fillcolor='lightyellow')
                else:
                    cluster.node(full_name, display_name)
    
    for full_name, func_info in functions.items():
        for callee in func_info.calls:
            if callee in functions:
                caller_file = func_info.file_path
                callee_file = functions[callee].file_path
                
                if caller_file != callee_file:
                    dot.edge(full_name, callee, color='red', penwidth='2')
                else:
                    if callee == full_name:
                        dot.edge(full_name, callee, color='purple', penwidth='2')
                    else:
                        dot.edge(full_name, callee, color='blue')
    
    output_path = output_dir / 'project_call_graph'
    dot.render(output_path, format='svg', cleanup=True)
    
    print(f"\nProject call graph generated: {output_path}.svg")
    print("\nLegend:")
    print("  Clusters: Individual files")
    print("  Green: Entry points")
    print("  Yellow: Leaf functions")
    print("  Red edges: Cross-file calls")
    print("  Blue edges: Same-file calls")
    print("  Purple edges: Recursive calls")
    
    total_files = len(file_clusters)
    total_functions = len(functions)
    cross_file_calls = sum(1 for f in functions.values() 
                          for c in f.calls 
                          if c in functions and functions[c].file_path != f.file_path)
    
    print(f"\nStatistics:")
    print(f"  Total files: {total_files}")
    print(f"  Total functions: {total_functions}")
    print(f"  Cross-file calls: {cross_file_calls}")
    
    return f"{output_path}.svg"


def select_project_function_interactive(directory: Path) -> str:
    functions = analyze_project(directory)
    
    assert len(functions) > 0, "No functions found in project"
    
    print("\nProject Functions")
    print("=" * 70)
    
    func_list = sorted(functions.keys())
    for idx, full_name in enumerate(func_list, 1):
        func_info = functions[full_name]
        file_name = Path(func_info.file_path).name
        print(f"  {idx}. {func_info.name} ({file_name})")
    
    while True:
        choice = input("\nSelect function number (0 to cancel): ").strip()
        
        if choice == "0":
            return None, None
        
        try:
            idx = int(choice) - 1
            assert 0 <= idx < len(func_list), "Invalid selection"
            return func_list[idx], functions
        except (ValueError, AssertionError):
            print("Invalid selection. Try again.")


def generate_project_function_focus_graph(func_full_name: str, functions: Dict[str, FunctionInfo], output_dir: Path):
    assert func_full_name in functions, f"Function not found: {func_full_name}"
    
    target_func = functions[func_full_name]
    
    def collect_related_functions(start_func: str, depth: int = 2) -> Set[str]:
        related = {start_func}
        
        def traverse_callers(func_name: str, current_depth: int):
            if current_depth >= depth or func_name not in functions:
                return
            for caller in functions[func_name].called_by:
                if caller not in related:
                    related.add(caller)
                    traverse_callers(caller, current_depth + 1)
        
        def traverse_callees(func_name: str, current_depth: int):
            if current_depth >= depth or func_name not in functions:
                return
            for callee in functions[func_name].calls:
                if callee not in related and callee in functions:
                    related.add(callee)
                    traverse_callees(callee, current_depth + 1)
        
        traverse_callers(start_func, 0)
        traverse_callees(start_func, 0)
        
        return related
    
    related_funcs = collect_related_functions(func_full_name)
    
    dot = graphviz.Digraph(comment=f'Project Function Focus: {target_func.name}')
    dot.attr(rankdir='TB')
    dot.attr('graph', splines='ortho', nodesep='0.6', ranksep='0.8')
    
    file_clusters: Dict[str, List[str]] = {}
    for full_name in related_funcs:
        if full_name in functions:
            func_info = functions[full_name]
            file_path = func_info.file_path
            if file_path not in file_clusters:
                file_clusters[file_path] = []
            file_clusters[file_path].append(full_name)
    
    for idx, (file_path, func_list) in enumerate(sorted(file_clusters.items())):
        file_name = Path(file_path).name
        with dot.subgraph(name=f'cluster_{idx}') as cluster:
            cluster.attr(label=file_name, style='filled', color='lightgrey')
            cluster.attr('node', shape='box', style='rounded,filled')
            
            for full_name in func_list:
                func_info = functions[full_name]
                display_name = func_info.name
                
                if full_name == func_full_name:
                    cluster.node(full_name, display_name, fillcolor='orange', penwidth='3')
                elif full_name in target_func.called_by:
                    cluster.node(full_name, display_name, fillcolor='lightgreen')
                elif full_name in target_func.calls:
                    cluster.node(full_name, display_name, fillcolor='lightblue')
                else:
                    cluster.node(full_name, display_name, fillcolor='lightyellow')
    
    for full_name in related_funcs:
        if full_name in functions:
            func_info = functions[full_name]
            for callee in func_info.calls:
                if callee in related_funcs and callee in functions:
                    caller_file = func_info.file_path
                    callee_file = functions[callee].file_path
                    
                    if full_name == func_full_name or callee == func_full_name:
                        if caller_file != callee_file:
                            dot.edge(full_name, callee, color='red', penwidth='3')
                        else:
                            dot.edge(full_name, callee, color='darkgreen', penwidth='3')
                    else:
                        if caller_file != callee_file:
                            dot.edge(full_name, callee, color='red', penwidth='1.5')
                        else:
                            dot.edge(full_name, callee, color='blue')
    
    output_path = output_dir / f'project_{target_func.name}_focus'
    dot.render(output_path, format='svg', cleanup=True)
    
    print(f"\nProject function focus graph generated: {output_path}.svg")
    print("\nLegend:")
    print("  Orange (bold): Target function")
    print("  Green: Direct callers")
    print("  Blue: Direct callees")
    print("  Yellow: Indirect relations")
    print("  Red edges: Cross-file calls")
    print("  Blue/Green edges: Same-file calls")
    print("  Thick edges: Connected to target function")
    
    direct_callers = len([c for c in target_func.called_by if c in functions])
    direct_callees = len([c for c in target_func.calls if c in functions])
    cross_file_calls = sum(1 for c in target_func.calls 
                          if c in functions and functions[c].file_path != target_func.file_path)
    
    print(f"\nStatistics:")
    print(f"  Direct callers: {direct_callers}")
    print(f"  Direct callees: {direct_callees}")
    print(f"  Cross-file calls from this function: {cross_file_calls}")
    print(f"  Related functions (depth 2): {len(related_funcs)}")
    
    return f"{output_path}.png"


def generate_all_function_focus_graphs(directory: Path, output_dir: Path):
    print("\nAnalyzing project...")
    functions = analyze_project(directory)
    
    assert len(functions) > 0, "No functions found in project"
    
    batch_output_dir = output_dir / 'batch_function_focus'
    batch_output_dir.mkdir(exist_ok=True)
    
    total_functions = len(functions)
    print(f"\nGenerating focus graphs for {total_functions} functions...")
    print("=" * 70)
    
    generated_count = 0
    for idx, func_full_name in enumerate(sorted(functions.keys()), 1):
        func_info = functions[func_full_name]
        file_name = Path(func_info.file_path).stem
        
        print(f"[{idx}/{total_functions}] {func_info.name} ({file_name}.py)")
        
        try:
            target_func = func_info
            
            def collect_related(start_func: str, depth: int = 2) -> Set[str]:
                related = {start_func}
                
                def traverse_callers(func_name: str, current_depth: int):
                    if current_depth >= depth or func_name not in functions:
                        return
                    for caller in functions[func_name].called_by:
                        if caller not in related:
                            related.add(caller)
                            traverse_callers(caller, current_depth + 1)
                
                def traverse_callees(func_name: str, current_depth: int):
                    if current_depth >= depth or func_name not in functions:
                        return
                    for callee in functions[func_name].calls:
                        if callee not in related and callee in functions:
                            related.add(callee)
                            traverse_callees(callee, current_depth + 1)
                
                traverse_callers(start_func, 0)
                traverse_callees(start_func, 0)
                
                return related
            
            related_funcs = collect_related(func_full_name)
            
            if len(related_funcs) == 1:
                print(f"  Skipped: No relationships")
                continue
            
            dot = graphviz.Digraph(comment=f'Focus: {target_func.name}')
            dot.attr(rankdir='TB')
            dot.attr('graph', splines='ortho', nodesep='0.6', ranksep='0.8')
            
            file_clusters: Dict[str, List[str]] = {}
            for full_name in related_funcs:
                if full_name in functions:
                    f_info = functions[full_name]
                    f_path = f_info.file_path
                    if f_path not in file_clusters:
                        file_clusters[f_path] = []
                    file_clusters[f_path].append(full_name)
            
            for cluster_idx, (f_path, func_list) in enumerate(sorted(file_clusters.items())):
                f_name = Path(f_path).name
                with dot.subgraph(name=f'cluster_{cluster_idx}') as cluster:
                    cluster.attr(label=f_name, style='filled', color='lightgrey')
                    cluster.attr('node', shape='box', style='rounded,filled')
                    
                    for full_name in func_list:
                        f_info = functions[full_name]
                        display_name = f_info.name
                        
                        if full_name == func_full_name:
                            cluster.node(full_name, display_name, fillcolor='orange', penwidth='3')
                        elif full_name in target_func.called_by:
                            cluster.node(full_name, display_name, fillcolor='lightgreen')
                        elif full_name in target_func.calls:
                            cluster.node(full_name, display_name, fillcolor='lightblue')
                        else:
                            cluster.node(full_name, display_name, fillcolor='lightyellow')
            
            for full_name in related_funcs:
                if full_name in functions:
                    f_info = functions[full_name]
                    for callee in f_info.calls:
                        if callee in related_funcs and callee in functions:
                            caller_file = f_info.file_path
                            callee_file = functions[callee].file_path
                            
                            if full_name == func_full_name or callee == func_full_name:
                                if caller_file != callee_file:
                                    dot.edge(full_name, callee, color='red', penwidth='3')
                                else:
                                    dot.edge(full_name, callee, color='darkgreen', penwidth='3')
                            else:
                                if caller_file != callee_file:
                                    dot.edge(full_name, callee, color='red', penwidth='1.5')
                                else:
                                    dot.edge(full_name, callee, color='blue')
            
            output_filename = f'{file_name}_{target_func.name}_focus'
            output_path = batch_output_dir / output_filename
            dot.render(output_path, format='svg', cleanup=True)
            
            generated_count += 1
            print(f"  Generated: {output_filename}.svg")
            
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"Batch generation complete!")
    print(f"  Total functions: {total_functions}")
    print(f"  Graphs generated: {generated_count}")
    print(f"  Skipped: {total_functions - generated_count}")
    print(f"  Output directory: {batch_output_dir}")
    
    return batch_output_dir
