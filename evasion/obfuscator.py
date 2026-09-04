import os
import sys
import ast
import astor
import base64
import random
import string
import zlib
import marshal
import builtins
import importlib
import tokenize
import io
import re
from typing import Any, Dict, List, Optional, Tuple, Union

class Obfuscator:
    def __init__(self, config=None):
        self.config = config or {}
        self.mapping = {}
        self.used_names = set()
        self.string_counter = 0
        
    def generate_random_name(self, prefix="var"):
        while True:
            name = f"{prefix}_{random.randint(1000, 9999)}"
            if name not in self.used_names:
                self.used_names.add(name)
                return name
    
    def generate_random_string(self, length=16):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def obfuscate_string(self, s):
        key = random.randint(1, 255)
        encrypted = bytes([ord(c) ^ key for c in s])
        return f"''.join(chr(ord(c) ^ {key}) for c in {repr(encrypted.decode('latin1'))})"
    
    def encode_string_base64(self, s):
        encoded = base64.b64encode(s.encode()).decode()
        return f"base64.b64decode('{encoded}').decode()"
    
    def encode_string_zlib(self, s):
        compressed = zlib.compress(s.encode())
        encoded = base64.b64encode(compressed).decode()
        return f"zlib.decompress(base64.b64decode('{encoded}')).decode()"
    
    def encode_string_hex(self, s):
        encoded = s.encode().hex()
        return f"bytes.fromhex('{encoded}').decode()"
    
    def obfuscate_string_advanced(self, s):
        methods = [
            self.obfuscate_string,
            self.encode_string_base64,
            self.encode_string_zlib,
            self.encode_string_hex
        ]
        method = random.choice(methods)
        return method(s)
    
    def obfuscate_variable_names(self, tree):
        class VariableRenamer(ast.NodeTransformer):
            def __init__(self, obfuscator):
                self.obfuscator = obfuscator
                self.var_mapping = {}
                
            def visit_Name(self, node):
                if isinstance(node, ast.Name):
                    if node.id not in self.var_mapping:
                        if node.id not in ['True', 'False', 'None', 'self', 'cls']:
                            self.var_mapping[node.id] = self.obfuscator.generate_random_name()
                    node.id = self.var_mapping.get(node.id, node.id)
                return node
            
            def visit_FunctionDef(self, node):
                if node.name not in ['__init__', '__main__']:
                    node.name = self.obfuscator.generate_random_name("func")
                self.generic_visit(node)
                return node
            
            def visit_ClassDef(self, node):
                node.name = self.obfuscator.generate_random_name("class")
                self.generic_visit(node)
                return node
            
            def visit_Attribute(self, node):
                self.generic_visit(node)
                return node
        
        renamer = VariableRenamer(self)
        return renamer.visit(tree)
    
    def add_dead_code(self, code):
        dead_code_templates = [
            """
def _dead_func_{0}():
    x = {0}
    y = x * 2 + 1
    z = y - x
    if z > 1000:
        return "never"
    return None

_dead_func_{0}()
""",
            """
class _DeadClass{0}:
    def __init__(self):
        self.value = {0}
    def get_value(self):
        return self.value * 0

_dead_instance = _DeadClass{0}()
_dead_result = _dead_instance.get_value()
""",
            """
try:
    _dead_var_{0} = [i * {0} for i in range(100)]
    _dead_sum = sum(_dead_var_{0})
except:
    pass
""",
            """
def _unused_loop_{0}():
    total = 0
    for i in range({0}):
        total += i
    return total if total < 0 else -1

_unused_loop_{0}()
"""
        ]
        
        num_dead_blocks = random.randint(2, 5)
        for _ in range(num_dead_blocks):
            template = random.choice(dead_code_templates)
            dead_code = template.format(random.randint(1000, 9999))
            insert_pos = random.randint(0, len(code.split('\n')))
            lines = code.split('\n')
            lines.insert(insert_pos, dead_code)
            code = '\n'.join(lines)
        
        return code
    
    def flatten_control_flow(self, code):
        # Simple control flow flattening
        lines = code.split('\n')
        flattened = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:'):
                condition = stripped.replace('if ', '').replace('elif ', '').replace('else:', 'True')
                flattened.append(f"if eval({repr(condition)}):")
                indented = line[len(line) - len(line.lstrip()):]
                flattened.append(f"{indented}    pass")
            else:
                flattened.append(line)
        
        return '\n'.join(flattened)
    
    def insert_junk_imports(self, code):
        junk_imports = [
            "import os",
            "import sys",
            "import time",
            "import random",
            "import string",
            "import base64",
            "import json",
            "import hashlib",
            "import zlib",
            "import marshal",
            "import types",
            "import functools",
            "import itertools",
            "import collections",
            "import threading",
            "import subprocess",
            "import tempfile",
            "import shutil",
            "import socket",
            "import struct",
            "import array",
            "import math",
            "import cmath",
            "import decimal",
            "import fractions",
            "import statistics",
            "import datetime",
            "import calendar",
            "import re",
            "import textwrap",
            "import difflib",
            "import stringprep",
            "import unicodedata",
            "import binascii",
            "import quopri",
            "import uu"
        ]
        
        num_imports = random.randint(5, 10)
        selected_imports = random.sample(junk_imports, num_imports)
        
        lines = code.split('\n')
        for imp in selected_imports:
            insert_pos = random.randint(0, len(lines))
            lines.insert(insert_pos, imp)
        
        return '\n'.join(lines)
    
    def encrypt_code_strings(self, tree):
        class StringEncryptor(ast.NodeTransformer):
            def __init__(self, obfuscator):
                self.obfuscator = obfuscator
                
            def visit_Str(self, node):
                if isinstance(node, ast.Str):
                    if len(node.s) > 3:
                        obfuscated = self.obfuscator.obfuscate_string_advanced(node.s)
                        try:
                            return ast.parse(obfuscated).body[0].value
                        except:
                            return node
                return node
            
            def visit_Constant(self, node):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if len(node.value) > 3:
                        obfuscated = self.obfuscator.obfuscate_string_advanced(node.value)
                        try:
                            return ast.parse(obfuscated).body[0].value
                        except:
                            return node
                return node
        
        encryptor = StringEncryptor(self)
        return encryptor.visit(tree)
    
    def add_try_except_wrappers(self, code):
        lines = code.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            if i % 10 == 0 and i > 0:
                result.append("try:")
                result.append("    " + line)
                result.append("except:")
                result.append("    pass")
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def obfuscate_imports(self, code):
        # Convert imports to dynamic imports
        lines = code.split('\n')
        obfuscated_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import '):
                module_name = stripped.replace('import ', '').strip()
                if module_name and not module_name.startswith('_'):
                    var_name = self.generate_random_name("module")
                    obfuscated_lines.append(f"{var_name} = __import__({repr(module_name)})")
                    # Replace usage
                    for j, other_line in enumerate(lines):
                        if module_name in other_line:
                            lines[j] = other_line.replace(module_name, var_name)
                else:
                    obfuscated_lines.append(line)
            elif stripped.startswith('from '):
                # Handle from imports
                parts = stripped.replace('from ', '').replace(' import ', ' ').split()
                if len(parts) >= 2:
                    module_name = parts[0]
                    imported_items = ' '.join(parts[1:])
                    var_name = self.generate_random_name("module")
                    obfuscated_lines.append(f"{var_name} = __import__({repr(module_name)})")
                    # Add item assignments
                    for item in imported_items.split(','):
                        item = item.strip()
                        if item:
                            obfuscated_lines.append(f"{item} = getattr({var_name}, {repr(item)})")
                else:
                    obfuscated_lines.append(line)
            else:
                obfuscated_lines.append(line)
        
        return '\n'.join(obfuscated_lines)
    
    def split_strings(self, code):
        # Split strings into multiple parts
        def split_string_match(match):
            s = match.group(1)
            if len(s) > 10:
                parts = []
                i = 0
                while i < len(s):
                    chunk_size = random.randint(3, 8)
                    parts.append(s[i:i+chunk_size])
                    i += chunk_size
                return '(' + ' + '.join([repr(part) for part in parts]) + ')'
            return match.group(0)
        
        # Simple string splitting
        pattern = r'(["\'])([^"\']+)\1'
        return re.sub(pattern, lambda m: m.group(1) + m.group(2) + m.group(1) if len(m.group(2)) <= 10 else '(' + ' + '.join([repr(m.group(2)[i:i+random.randint(3,8)]) for i in range(0, len(m.group(2)), random.randint(3,8))]) + ')', code)
    
    def add_opaque_predicates(self, code):
        opaque_predicates = [
            "if (1 == 1):",
            "if (2 > 1):",
            "if (0 == 0):",
            "if (True):",
            "if (len('abc') == 3):",
            "if (10 % 3 == 1):"
        ]
        
        lines = code.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            if i % 15 == 0 and i > 0:
                predicate = random.choice(opaque_predicates)
                result.append(predicate)
                result.append("    pass")
                result.append("else:")
                result.append("    pass")
            result.append(line)
        
        return '\n'.join(result)
    
    def compile_to_bytecode(self, code):
        try:
            compiled = compile(code, '<string>', 'exec')
            marshaled = marshal.dumps(compiled)
            encoded = base64.b64encode(marshaled).decode()
            return f"import marshal, base64\ncode = base64.b64decode('{encoded}')\nexec(marshal.loads(code))"
        except:
            return code
    
    def obfuscate(self, code, level=3):
        if not code:
            return ""
        
        try:
            # Level 1: Basic obfuscation
            if level >= 1:
                code = self.insert_junk_imports(code)
                code = self.split_strings(code)
                code = self.add_dead_code(code)
            
            # Level 2: Medium obfuscation
            if level >= 2:
                code = self.add_opaque_predicates(code)
                code = self.add_try_except_wrappers(code)
                code = self.obfuscate_imports(code)
            
            # Level 3: Advanced obfuscation
            if level >= 3:
                try:
                    tree = ast.parse(code)
                    tree = self.encrypt_code_strings(tree)
                    tree = self.obfuscate_variable_names(tree)
                    code = ast.unparse(tree)
                except:
                    pass
                
                # Add final bytecode compilation
                if self.config.get("compile_to_bytecode", False):
                    code = self.compile_to_bytecode(code)
            
            return code
            
        except Exception as e:
            return code
    
    def obfuscate_file(self, input_file, output_file=None, level=3):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            obfuscated = self.obfuscate(code, level)
            
            if output_file is None:
                output_file = input_file + '.obfuscated'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(obfuscated)
            
            return {
                "success": True,
                "input_file": input_file,
                "output_file": output_file
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def obfuscate_directory(self, input_dir, output_dir=None, level=3):
        if output_dir is None:
            output_dir = input_dir + '_obfuscated'
        
        results = []
        
        try:
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    if file.endswith('.py'):
                        input_file = os.path.join(root, file)
                        relative_path = os.path.relpath(input_file, input_dir)
                        output_file = os.path.join(output_dir, relative_path)
                        
                        os.makedirs(os.path.dirname(output_file), exist_ok=True)
                        
                        result = self.obfuscate_file(input_file, output_file, level)
                        results.append(result)
            
            return {
                "success": True,
                "results": results,
                "output_dir": output_dir
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    obfuscator = Obfuscator()
    
    # Example usage
    test_code = """
import os
import sys

def main():
    print("Hello World")
    x = 10
    y = 20
    result = x + y
    return result

if __name__ == "__main__":
    main()
"""
    
    obfuscated = obfuscator.obfuscate(test_code, level=3)
    print(obfuscated)