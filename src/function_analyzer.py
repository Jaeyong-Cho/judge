from pathlib import Path
from typing import Dict, List, Set, Tuple
import tree_sitter_python as tspython
from tree_sitter import Language, Parser


class FunctionInfo:
    def __init__(self, name: str, line_start: int, line_end: int, file_path: str = "", class_name: str = ""):
        self.name = name
        self.line_start = line_start
        self.line_end = line_end
        self.file_path = file_path
        self.class_name = class_name
        self.calls: Set[str] = set()
        self.called_by: Set[str] = set()
        self.assertions: List[str] = []


class ProjectAnalyzer:
    def __init__(self):
        self.parser = Parser(Language(tspython.language()))
        self.functions: Dict[str, FunctionInfo] = {}
        self.imports: Dict[str, Dict[str, Tuple[str, str]]] = {}
        self.file_modules: Dict[str, str] = {}
        self.variable_types: Dict[str, Dict[str, str]] = {}
        self.class_attributes: Dict[str, Dict[str, str]] = {}
    
    def analyze_project(self, directory: Path) -> Dict[str, FunctionInfo]:
        self.functions.clear()
        self.imports.clear()
        self.file_modules.clear()
        self.variable_types.clear()
        self.class_attributes.clear()
        
        python_files = get_all_python_files(directory)
        
        for py_file in python_files:
            module_name = self._get_module_name(py_file, directory)
            self.file_modules[module_name] = str(py_file)
        
        for py_file in python_files:
            self._analyze_file(py_file, directory)
        
        self._resolve_cross_file_calls()
        
        return self.functions
    
    def _get_module_name(self, file_path: Path, project_root: Path) -> str:
        try:
            relative_path = file_path.relative_to(project_root)
            module_name = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
            return module_name
        except ValueError as e:
            print(f"Warning: Cannot compute relative path for {file_path} from {project_root}: {e}")
            return file_path.stem
    
    def _analyze_file(self, file_path: Path, project_root: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = self.parser.parse(bytes(source_code, 'utf8'))
            module_name = self._get_module_name(file_path, project_root)
            
            self._extract_imports(tree.root_node, module_name)
            self._extract_functions(tree.root_node, module_name)
            self._build_call_graph(tree.root_node, module_name)
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_imports(self, node, current_module: str):
        if node.type == 'import_statement' or node.type == 'import_from_statement':
            self._parse_import(node, current_module)
        
        for child in node.children:
            self._extract_imports(child, current_module)
    
    def _parse_import(self, node, current_module: str):
        if current_module not in self.imports:
            self.imports[current_module] = {}
        
        imports_before = len(self.imports[current_module])
        
        if node.type == 'import_from_statement':
            base_module = self._extract_from_module(node, current_module)
            
            for child in node.children:
                if child.type == 'aliased_import':
                    name_node = child.child_by_field_name('name')
                    alias_node = child.child_by_field_name('alias')
                    
                    if name_node:
                        imported_name = name_node.text.decode('utf8')
                        alias = alias_node.text.decode('utf8') if alias_node else imported_name
                        
                        if base_module:
                            full_path = f"{base_module}.{imported_name}"
                        else:
                            full_path = imported_name
                        
                        self.imports[current_module][alias] = (full_path, imported_name)
                
                elif child.type == 'dotted_name' or (child.type == 'identifier' and child.text.decode('utf8') not in ['from', 'import']):
                    if not any(c.type in ['module_name', 'relative_import'] for c in node.children if c == child.parent):
                        imported_name = child.text.decode('utf8')
                        
                        if imported_name not in ['from', 'import', 'as']:
                            if base_module:
                                full_path = f"{base_module}.{imported_name}"
                            else:
                                full_path = imported_name
                            
                            self.imports[current_module][imported_name] = (full_path, imported_name)
                
                elif child.type == 'wildcard_import':
                    if base_module:
                        self.imports[current_module]['*'] = (base_module, '*')
        
        elif node.type == 'import_statement':
            for child in node.children:
                if child.type == 'aliased_import':
                    name_node = child.child_by_field_name('name')
                    alias_node = child.child_by_field_name('alias')
                    
                    if name_node:
                        module_name = name_node.text.decode('utf8')
                        alias = alias_node.text.decode('utf8') if alias_node else module_name
                        self.imports[current_module][alias] = (module_name, module_name)
                
                elif child.type == 'dotted_name' or child.type == 'identifier':
                    module_name = child.text.decode('utf8')
                    if module_name != 'import':
                        self.imports[current_module][module_name] = (module_name, module_name)
        
        imports_after = len(self.imports[current_module])
        if imports_after > imports_before:
            new_imports = {k: v for k, v in list(self.imports[current_module].items())[imports_before:]}
            print(f"[{current_module}] New imports: {new_imports}")
    
    def _extract_from_module(self, node, current_module: str) -> str:
        module_node = node.child_by_field_name('module_name')
        
        relative_level = 0
        for child in node.children:
            if child.type == 'relative_import':
                dots_text = child.text.decode('utf8')
                relative_level = dots_text.count('.')
                break
        
        if module_node:
            module_name = module_node.text.decode('utf8')
            
            if relative_level > 0:
                current_parts = current_module.split('.')
                if relative_level <= len(current_parts):
                    base_parts = current_parts[:-relative_level] if relative_level < len(current_parts) else []
                    return '.'.join(base_parts + [module_name]) if base_parts else module_name
            
            return module_name
        elif relative_level > 0:
            current_parts = current_module.split('.')
            if relative_level <= len(current_parts):
                base_parts = current_parts[:-relative_level] if relative_level < len(current_parts) else []
                return '.'.join(base_parts) if base_parts else ''
        
        return ''
    
    def _extract_functions(self, node, current_module: str, current_class: str = ""):
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            if class_name_node:
                class_name = class_name_node.text.decode('utf8')
                for child in node.children:
                    self._extract_functions(child, current_module, class_name)
                return
        
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                
                if current_class:
                    full_name = f"{current_module}.{current_class}.{func_name}"
                else:
                    full_name = f"{current_module}.{func_name}"
                
                file_path = self.file_modules.get(current_module, "")
                self.functions[full_name] = FunctionInfo(func_name, start_line, end_line, file_path, current_class)
                self._extract_assertions(node, full_name)
        
        for child in node.children:
            self._extract_functions(child, current_module, current_class)
    
    def _build_call_graph(self, node, current_module: str, current_func: str = "", current_class: str = ""):
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            if class_name_node:
                class_name = class_name_node.text.decode('utf8')
                for child in node.children:
                    self._build_call_graph(child, current_module, current_func, class_name)
                return
        
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                if current_class:
                    current_func = f"{current_module}.{current_class}.{func_name}"
                else:
                    current_func = f"{current_module}.{func_name}"
                
                if current_func not in self.variable_types:
                    self.variable_types[current_func] = {}
        
        if node.type == 'assignment':
            self._track_variable_assignment(node, current_func, current_module, current_class)
        
        if node.type == 'call':
            function_node = node.child_by_field_name('function')
            if function_node:
                called_info = self._extract_function_name(function_node, current_module, current_class, current_func)
                if called_info and current_func:
                    if current_func in self.functions:
                        self.functions[current_func].calls.add(called_info)
                        
                        if called_info in self.functions:
                            self.functions[called_info].called_by.add(current_func)
                        
                        init_method = self._resolve_class_instantiation(called_info, current_module)
                        if init_method and init_method in self.functions:
                            self.functions[current_func].calls.add(init_method)
                            self.functions[init_method].called_by.add(current_func)
        
        for child in node.children:
            self._build_call_graph(child, current_module, current_func, current_class)
    
    def _track_variable_assignment(self, node, current_func: str, current_module: str, current_class: str = ""):
        """Track variable assignments to class instances."""
        if not current_func or current_func not in self.variable_types:
            return
        
        left_node = node.child_by_field_name('left')
        right_node = node.child_by_field_name('right')
        
        if not left_node or not right_node:
            return
        
        var_name = None
        is_self_attribute = False
        
        if left_node.type == 'identifier':
            var_name = left_node.text.decode('utf8')
        elif left_node.type == 'attribute':
            obj_node = left_node.child_by_field_name('object')
            attr_node = left_node.child_by_field_name('attribute')
            if obj_node and obj_node.type == 'identifier' and obj_node.text.decode('utf8') == 'self' and attr_node:
                var_name = attr_node.text.decode('utf8')
                is_self_attribute = True
        
        if var_name and right_node.type == 'call':
            func_node = right_node.child_by_field_name('function')
            if func_node:
                class_name = self._extract_function_name(func_node, current_module, "")
                if class_name and len(class_name) > 0 and class_name[0].isupper():
                    parts = class_name.split('.')
                    class_path = None
                    
                    if len(parts) == 1:
                        current_module_match = None
                        other_match = None
                        
                        for full_name in self.functions.keys():
                            name_parts = full_name.split('.')
                            if len(name_parts) >= 2 and name_parts[-2] == class_name:
                                candidate_module = '.'.join(name_parts[:-2])
                                candidate_class = '.'.join(name_parts[:-1])
                                
                                if candidate_module == current_module:
                                    current_module_match = candidate_class
                                    break
                                elif not other_match:
                                    other_match = candidate_class
                        
                        class_path = current_module_match or other_match
                    else:
                        class_path = '.'.join(parts[:-1]) if parts[-1] == parts[-1].title() else class_name
                    
                    if class_path:
                        if is_self_attribute and current_class:
                            class_full_name = f"{current_module}.{current_class}"
                            if class_full_name not in self.class_attributes:
                                self.class_attributes[class_full_name] = {}
                            self.class_attributes[class_full_name][var_name] = class_path
                        else:
                            self.variable_types[current_func][var_name] = class_path
    
    def _extract_function_name(self, node, current_module: str = "", current_class: str = "", current_func: str = "") -> str:
        if node.type == 'identifier':
            return node.text.decode('utf8')
        elif node.type == 'attribute':
            full_path = []
            current = node
            base_obj = None
            
            while current and current.type == 'attribute':
                attr_node = current.child_by_field_name('attribute')
                if attr_node:
                    full_path.insert(0, attr_node.text.decode('utf8'))
                
                obj_node = current.child_by_field_name('object')
                if obj_node:
                    if obj_node.type == 'identifier':
                        base_obj = obj_node.text.decode('utf8')
                        full_path.insert(0, base_obj)
                        break
                    elif obj_node.type == 'call':
                        call_func = obj_node.child_by_field_name('function')
                        if call_func:
                            if call_func.type == 'identifier':
                                base_obj = call_func.text.decode('utf8')
                                full_path.insert(0, base_obj)
                            elif call_func.type == 'attribute':
                                call_path = self._extract_function_name(call_func, current_module, current_class, current_func)
                                if call_path:
                                    full_path.insert(0, call_path)
                        break
                    current = obj_node
                else:
                    break
            
            if full_path:
                if base_obj == 'self' and current_class:
                    if len(full_path) == 2:
                        method_name = full_path[-1]
                        return f"{current_module}.{current_class}.{method_name}"
                    elif len(full_path) >= 3:
                        attribute_name = full_path[1]
                        class_full_name = f"{current_module}.{current_class}"
                        
                        if class_full_name in self.class_attributes and attribute_name in self.class_attributes[class_full_name]:
                            class_path = self.class_attributes[class_full_name][attribute_name]
                            method_name = full_path[-1]
                            return f"{class_path}.{method_name}"
                        
                        if current_func and current_func in self.variable_types:
                            if attribute_name in self.variable_types[current_func]:
                                class_path = self.variable_types[current_func][attribute_name]
                                method_name = full_path[-1]
                                return f"{class_path}.{method_name}"
                        
                        method_name = full_path[-1]
                        return f"{current_module}.{current_class}.{method_name}"
                elif base_obj and current_func and current_func in self.variable_types:
                    if base_obj in self.variable_types[current_func]:
                        class_path = self.variable_types[current_func][base_obj]
                        method_name = full_path[-1]
                        return f"{class_path}.{method_name}"
                return '.'.join(full_path)
        
        return ""
    
    def _resolve_class_instantiation(self, called_name: str, current_module: str) -> str:
        parts = called_name.split('.')
        
        if len(parts) == 1:
            class_name = parts[0]
            if class_name and class_name[0].isupper():
                for full_name in self.functions.keys():
                    name_parts = full_name.split('.')
                    if len(name_parts) >= 3 and name_parts[-2] == class_name and name_parts[-1] == '__init__':
                        func_module = '.'.join(name_parts[:-2])
                        if func_module == current_module:
                            return full_name
                
                if current_module in self.imports and class_name in self.imports[current_module]:
                    full_path, _ = self.imports[current_module][class_name]
                    init_candidate = f"{full_path}.__init__"
                    if init_candidate in self.functions:
                        return init_candidate
        
        elif len(parts) == 2:
            module_or_alias = parts[0]
            class_name = parts[1]
            
            if current_module in self.imports and module_or_alias in self.imports[current_module]:
                full_path, _ = self.imports[current_module][module_or_alias]
                init_candidate = f"{full_path}.{class_name}.__init__"
                if init_candidate in self.functions:
                    return init_candidate
            
            for full_name in self.functions.keys():
                if full_name.endswith(f".{class_name}.__init__"):
                    return full_name
        
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
        print(f"\n=== Starting cross-file call resolution ===")
        print(f"Total functions: {len(self.functions)}")
        print(f"Total imports: {len(self.imports)}")
        
        for func_full_name, func_info in self.functions.items():
            if func_info.class_name:
                parts = func_full_name.split('.')
                module_name = '.'.join(parts[:-2])
            else:
                parts = func_full_name.split('.')
                module_name = '.'.join(parts[:-1])
            
            resolved_calls = set()
            unresolved_calls = []
            
            for called_name in func_info.calls:
                if called_name.startswith(module_name + '.'):
                    if called_name in self.functions:
                        resolved_calls.add(called_name)
                        self.functions[called_name].called_by.add(func_full_name)
                    else:
                        resolved_name = self._resolve_function_name(called_name, module_name)
                        if resolved_name:
                            resolved_calls.add(resolved_name)
                            if resolved_name in self.functions:
                                self.functions[resolved_name].called_by.add(func_full_name)
                        else:
                            unresolved_calls.append(called_name)
                            resolved_calls.add(called_name)
                else:
                    resolved_name = self._resolve_function_name(called_name, module_name)
                    if resolved_name:
                        resolved_calls.add(resolved_name)
                        if resolved_name in self.functions:
                            self.functions[resolved_name].called_by.add(func_full_name)
                    else:
                        unresolved_calls.append(called_name)
                        resolved_calls.add(called_name)
            
            if unresolved_calls:
                print(f"[{func_full_name}] Unresolved calls: {unresolved_calls}")
            
            func_info.calls = resolved_calls
        
        print(f"=== Cross-file call resolution complete ===\n")


    def _resolve_function_name(self, func_name: str, current_module: str) -> str:
        parts = func_name.split('.')
        
        if len(parts) > 1:
            first_part = parts[0]
            
            if current_module in self.imports and first_part in self.imports[current_module]:
                full_path, original_name = self.imports[current_module][first_part]
                
                if len(parts) == 2:
                    method_name = parts[1]
                    
                    candidate = f"{full_path}.{method_name}"
                    if candidate in self.functions:
                        return candidate
                    
                    for full_name in self.functions.keys():
                        if full_name.endswith(f".{method_name}"):
                            name_parts = full_name.split('.')
                            func_module = '.'.join(name_parts[:-1])
                            
                            if func_module == full_path or func_module.startswith(f"{full_path}."):
                                return full_name
                
                elif len(parts) == 3:
                    class_or_module = parts[1]
                    method_name = parts[2]
                    
                    candidate = f"{full_path}.{class_or_module}.{method_name}"
                    if candidate in self.functions:
                        return candidate
            
            for full_name in self.functions.keys():
                name_parts = full_name.split('.')
                if len(name_parts) >= len(parts):
                    if all(name_parts[-(len(parts)-i)] == parts[i] for i in range(len(parts))):
                        func_module = '.'.join(name_parts[:-(len(parts)-1)])
                        if func_module == current_module:
                            return full_name
        else:
            if current_module in self.imports and func_name in self.imports[current_module]:
                full_path, original_name = self.imports[current_module][func_name]
                
                if full_path in self.functions:
                    return full_path
                
                for full_name in self.functions.keys():
                    if full_name == full_path:
                        return full_name
                    
                    if full_name.endswith(f".{original_name}"):
                        name_parts = full_name.split('.')
                        func_module = '.'.join(name_parts[:-1])
                        
                        if func_module == '.'.join(full_path.split('.')[:-1]):
                            return full_name
            
            for full_name in self.functions.keys():
                if full_name.endswith(f".{func_name}"):
                    name_parts = full_name.split('.')
                    func_module = '.'.join(name_parts[:-1])
                    
                    if func_module == current_module:
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
    
    def _extract_functions(self, node, file_path: str, current_class: str = ""):
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            if class_name_node:
                class_name = class_name_node.text.decode('utf8')
                for child in node.children:
                    self._extract_functions(child, file_path, class_name)
                return
        
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                
                if current_class:
                    full_name = f"{current_class}.{func_name}"
                else:
                    full_name = func_name
                
                self.functions[full_name] = FunctionInfo(func_name, start_line, end_line, file_path, current_class)
                self._extract_assertions(node, full_name)
        
        for child in node.children:
            self._extract_functions(child, file_path, current_class)
    
    def _build_call_graph(self, node, current_func: str = "", current_class: str = ""):
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            if class_name_node:
                class_name = class_name_node.text.decode('utf8')
                for child in node.children:
                    self._build_call_graph(child, current_func, class_name)
                return
        
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = name_node.text.decode('utf8')
                if current_class:
                    current_func = f"{current_class}.{func_name}"
                else:
                    current_func = func_name
        
        if node.type == 'call':
            function_node = node.child_by_field_name('function')
            if function_node:
                called_name = self._extract_function_name(function_node, current_class, current_func)
                if called_name and current_func:
                    if current_func in self.functions:
                        self.functions[current_func].calls.add(called_name)
                        
                        init_method = self._resolve_class_instantiation(called_name)
                        if init_method and init_method in self.functions:
                            self.functions[current_func].calls.add(init_method)
                            self.functions[init_method].called_by.add(current_func)
                    
                    if called_name in self.functions:
                        self.functions[called_name].called_by.add(current_func)
        
        for child in node.children:
            self._build_call_graph(child, current_func, current_class)
    
    def _extract_function_name(self, node, current_class: str = "", current_func: str = "") -> str:
        if node.type == 'identifier':
            return node.text.decode('utf8')
        elif node.type == 'attribute':
            full_path = []
            current = node
            base_obj = None
            
            while current and current.type == 'attribute':
                attr_node = current.child_by_field_name('attribute')
                if attr_node:
                    full_path.insert(0, attr_node.text.decode('utf8'))
                
                obj_node = current.child_by_field_name('object')
                if obj_node:
                    if obj_node.type == 'identifier':
                        base_obj = obj_node.text.decode('utf8')
                        full_path.insert(0, base_obj)
                        break
                    elif obj_node.type == 'call':
                        call_func = obj_node.child_by_field_name('function')
                        if call_func:
                            if call_func.type == 'identifier':
                                base_obj = call_func.text.decode('utf8')
                                full_path.insert(0, base_obj)
                            elif call_func.type == 'attribute':
                                call_path = self._extract_function_name(call_func, current_class, current_func)
                                if call_path:
                                    full_path.insert(0, call_path)
                        break
                    current = obj_node
                else:
                    break
            
            if full_path:
                if base_obj == 'self' and current_class:
                    method_name = full_path[-1]
                    return f"{current_class}.{method_name}"
                return '.'.join(full_path)
        
        return ""
    
    def _resolve_class_instantiation(self, called_name: str) -> str:
        parts = called_name.split('.')
        
        if len(parts) == 1:
            class_name = parts[0]
            if class_name and class_name[0].isupper():
                init_candidate = f"{class_name}.__init__"
                if init_candidate in self.functions:
                    return init_candidate
        
        elif len(parts) == 2:
            class_name = parts[1] if parts[1][0].isupper() else parts[0]
            init_candidate = f"{called_name}.__init__"
            if init_candidate in self.functions:
                return init_candidate
        
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
