from pathlib import Path
from typing import Dict, List, Set
import tree_sitter_python as tspython
from tree_sitter import Language, Parser


class FunctionInfo:
    def __init__(self, name: str, line_start: int, line_end: int):
        self.name = name
        self.line_start = line_start
        self.line_end = line_end
        self.calls: Set[str] = set()
        self.called_by: Set[str] = set()


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
        self._extract_functions(tree.root_node)
        self._build_call_graph(tree.root_node)
        
        return self.functions
    
    def _extract_functions(self, node):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                self.functions[func_name] = FunctionInfo(func_name, start_line, end_line)
        
        for child in node.children:
            self._extract_functions(child)
    
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


def analyze_python_file(file_path: Path) -> Dict[str, FunctionInfo]:
    analyzer = FunctionAnalyzer()
    return analyzer.analyze_file(file_path)


def get_all_python_files(directory: Path) -> List[Path]:
    return list(directory.rglob("*.py"))
