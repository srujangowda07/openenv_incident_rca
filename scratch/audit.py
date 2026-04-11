import ast
import os

def walk_tree(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith('.py'):
                yield os.path.join(root, file)

class Auditor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.in_function = False
        self.in_try_except_import = False

    def visit_FunctionDef(self, node):
        old = self.in_function
        self.in_function = True
        self.generic_visit(node)
        self.in_function = old

    def visit_AsyncFunctionDef(self, node):
        old = self.in_function
        self.in_function = True
        self.generic_visit(node)
        self.in_function = old

    def visit_Try(self, node):
        # check if it has except ImportError
        has_import_error = any(
            isinstance(handler.type, ast.Name) and handler.type.id == 'ImportError'
            for handler in node.handlers
        )
        if has_import_error:
            old = self.in_try_except_import
            self.in_try_except_import = True
            self.generic_visit(node)
            self.in_try_except_import = old
        else:
            self.generic_visit(node)

    def visit_Import(self, node):
        bad_mods = ['environment', 'server', 'tasks', 'models']
        for name in node.names:
            mod_root = name.name.split('.')[0]
            if mod_root in bad_mods:
                print(f"[BAD_IMPORT] {self.filepath}:{node.lineno} -> {name.name}")
        if self.in_function:
            print(f"[LAZY_IMPORT] {self.filepath}:{node.lineno} -> import {', '.join(n.name for n in node.names)}")
        if self.in_try_except_import:
            print(f"[TRY_IMPORT] {self.filepath}:{node.lineno} -> import {', '.join(n.name for n in node.names)}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        bad_mods = ['environment', 'server', 'tasks', 'models']
        if node.module:
            mod_root = node.module.split('.')[0]
            if mod_root in bad_mods:
                print(f"[BAD_IMPORT] {self.filepath}:{node.lineno} -> from {node.module} import ...")
        if self.in_function:
            print(f"[LAZY_IMPORT] {self.filepath}:{node.lineno} -> from {node.module} import ...")
        if self.in_try_except_import:
            print(f"[TRY_IMPORT] {self.filepath}:{node.lineno} -> from {node.module} import ...")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id == 'open':
                print(f"[OPEN_CALL] {self.filepath}:{node.lineno} -> open(...)")
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == 'os' and node.func.attr == 'getcwd':
                print(f"[OS_GETCWD] {self.filepath}:{node.lineno} -> os.getcwd()")
        self.generic_visit(node)

for fpath in walk_tree('incident_rca_env'):
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        tree = ast.parse(src)
        auditor = Auditor(fpath)
        auditor.visit(tree)
    except Exception as e:
        pass
