from pathlib import Path
from typing import Dict, List, Set, Tuple
import tree_sitter_python as tspython
from tree_sitter import Language, Parser


class FunctionInfo:
    def __init__(self, name: str, line_start: int, line_end: int, file_path: str = ""):
        self.name = name
        self.line_start = line_start
        self.line_end = line_end
        self.file_path = file_path
        self.calls: Set[str] = set()
        self.called_by: Set[str] = set()
        self.assertions: List[str] = []


class ProjectAnalyzer:
    def __init__(self):
        self.parser = Parser(Language(tspython.language()))
        self.functions: Dict[str, FunctionInfo] = {}
        self.imports: Dict[str, Dict[str, str]] = {}
        self.file_modules: Dict[str, str] = {}
    
    def analyze_project(self, directory: Path) -> Dict[str, FunctionInfo]:
        self.functions.clear()
        self.imports.clear()
        self.file_modules.clear()
        
        python_files = get_all_python_files(directory)
        
        for py_file in python_files:
            module_name = self._get_module_name(py_file, directory)
            self.file_modules[module_name] = str(py_file)
        
        for py_file in python_files:
            self._analyze_file(py_file, directory)
        
        self._resolve_cross_file_calls()
        
        return self.functions
    
    def _get_module_name(self, file_path: Path, project_root: Path) -> str:
        relative_path = file_path.relative_to(project_root)
        return str(relative_path.with_suffix('')).replace('/', '.')
    
    def _analyze_file(self, file_path: Path, project_root: Path):
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        tree = self.parser.parse(bytes(source_code, 'utf8'))
        module_name = self._get_module_name(file_path, project_root)
        
        self._extract_imports(tree.root_node, module_name)
        self._extract_functions(tree.root_node, module_name)
        self._build_call_graph(tree.root_node, module_name)
    
    def _extract_imports(self, node, current_module: str):
        if node.type == 'import_statement' or node.type == 'import_from_statement':
            self._parse_import(node, current_module)
        
        for child in node.children:
            self._extract_imports(child, current_module)
    
    def _parse_import(self, node, current_module: str):
        if current_module not in self.imports:
            self.imports[current_module] = {}
        
        if node.type == 'import_from_statement':
            module_node = node.child_by_field_name('module_name')
            if module_node:
                module_name = module_node.text.decode('utf8')
                
                for child in node.children:
                    if child.type == 'dotted_name' or child.type == 'identifier':
                        if child != module_node:
                            imported_name = child.text.decode('utf8')
                            full_name = f"{module_name}.{imported_name}"
                            self.imports[current_module][imported_name] = full_name
    
    def _extract_functions(self, node, current_module: str):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                full_name = f"{current_module}.{func_name}"
                file_path = self.file_modules.get(current_module, "")
                self.functions[full_name] = FunctionInfo(func_name, start_line, end_line, file_path)
                self._extract_assertions(node, full_name)
        
        for child in node.children:
            self._extract_functions(child, current_module)
    
    def _build_call_graph(self, node, current_module: str, current_func: str = ""):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                current_func = f"{current_module}.{func_name}"
        
        if node.type == 'call':
            function_node = node.child_by_field_name('function')
            if function_node:
                called_name = self._extract_function_name(function_node)
                if called_name and current_func:
                    if current_func in self.functions:
                        self.functions[current_func].calls.add(called_name)
        
        for child in node.children:
            self._build_call_graph(child, current_module, current_func)
    
    def _extract_function_name(self, node) -> str:
        if node.type == 'identifier':
            return node.text.decode('utf8')
        elif node.type == 'attribute':
            attr_node = node.child_by_field_name('attribute')
            if attr_node:
                return attr_node.text.decode('utf8')
        return ""
    
    def _extract_assertions(self, func_node, func_full_name: str):
        assert func_full_name in self.functions, f"Function not found: {func_full_name}"
        
        for node in self._traverse_nodes(func_node):
            if node.type == 'assert_statement':
                assertion_text = node.text.decode('utf8').strip()
                self.functions[func_full_name].assertions.append(assertion_text)
    
    def _traverse_nodes(self, node):
        yield node
        for child in node.children:
            yield from self._traverse_nodes(child)
    
    def _resolve_cross_file_calls(self):
        for func_full_name, func_info in self.functions.items():
            module_name = '.'.join(func_full_name.split('.')[:-1])
            resolved_calls = set()
            
            for called_name in func_info.calls:
                resolved_name = self._resolve_function_name(called_name, module_name)
                if resolved_name:
                    resolved_calls.add(resolved_name)
                    if resolved_name in self.functions:
                        self.functions[resolved_name].called_by.add(func_full_name)
                else:
                    resolved_calls.add(called_name)
            
            func_info.calls = resolved_calls


    def _resolve_function_name(self, func_name: str, current_module: str) -> str:
        for full_name in self.functions.keys():
            if full_name.endswith(f".{func_name}"):
                module_part = '.'.join(full_name.split('.')[:-1])
                
                if module_part == current_module:
                    return full_name
                
                if current_module in self.imports:
                    if func_name in self.imports[current_module]:
                        imported_full = self.imports[current_module][func_name]
                        if imported_full == full_name or full_name.endswith(imported_full):
                            return full_name
        
        return ""


class FunctionAnalyzer:
    def __init__(self):
        self.parser = Parser(Language(tspython.language()))
        self.functions: Dict[str, FunctionInfo] = {}
        self.current_function: str = ""
    
    def analyze_file(self, file_path: Path) -> Dict[str, FunctionInfo]:
        self.functions.clear()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        tree = self.parser.parse(bytes(source_code, 'utf8'))
        self._extract_functions(tree.root_node, str(file_path))
        self._build_call_graph(tree.root_node)
        
        return self.functions
    
    def _extract_functions(self, node, file_path: str):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                self.functions[func_name] = FunctionInfo(func_name, start_line, end_line, file_path)
                self._extract_assertions(node, func_name)
        
        for child in node.children:
            self._extract_functions(child, file_path)
    
    def _build_call_graph(self, node, current_func: str = ""):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                current_func = name_node.text.decode('utf8')
        
        if node.type == 'call':
            function_node = node.child_by_field_name('function')
            if function_node:
                called_name = self._extract_function_name(function_node)
                if called_name and current_func:
                    if current_func in self.functions:
                        self.functions[current_func].calls.add(called_name)
                    if called_name in self.functions:
                        self.functions[called_name].called_by.add(current_func)
        
        for child in node.children:
            self._build_call_graph(child, current_func)
    
    def _extract_function_name(self, node) -> str:
        if node.type == 'identifier':
            return node.text.decode('utf8')
        elif node.type == 'attribute':
            attr_node = node.child_by_field_name('attribute')
            if attr_node:
                return attr_node.text.decode('utf8')
        return ""
    
    def _extract_assertions(self, func_node, func_name: str):
        assert func_name in self.functions, f"Function not found: {func_name}"
        
        for node in self._traverse_nodes(func_node):
            if node.type == 'assert_statement':
                assertion_text = node.text.decode('utf8').strip()
                self.functions[func_name].assertions.append(assertion_text)
    
    def _traverse_nodes(self, node):
        yield node
        for child in node.children:
            yield from self._traverse_nodes(child)


def analyze_python_file(file_path: Path) -> Dict[str, FunctionInfo]:
    analyzer = FunctionAnalyzer()
    return analyzer.analyze_file(file_path)


def analyze_project(directory: Path) -> Dict[str, FunctionInfo]:
    analyzer = ProjectAnalyzer()
    return analyzer.analyze_project(directory)


def get_all_python_files(directory: Path) -> List[Path]:
    exclude_dirs = {'.venv', 'venv', '__pycache__', 'node_modules', '.git', 'build', 'dist', '.eggs', '*.egg-info'}
    
    python_files = []
    for py_file in directory.rglob("*.py"):
        if not any(excluded in py_file.parts for excluded in exclude_dirs):
            python_files.append(py_file)
    
    return python_files
