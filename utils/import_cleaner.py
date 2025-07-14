"""
Import and Variable Cleaner for The Oracle Project

This module provides comprehensive cleaning of unused imports and variables
across all Python files in the project.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportCleaner:
    """Comprehensive import and variable cleaner for Python files."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changes_made = 0
        self.files_processed = 0
        self.errors = []
        
    def find_all_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return sorted(python_files)
    
    def parse_file(self, file_path: Path) -> Optional[ast.AST]:
        """Parse a Python file and return the AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content, filename=str(file_path))
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
            return None
    
    def get_used_names(self, node: ast.AST) -> Set[str]:
        """Extract all used names from an AST."""
        used_names = set()
        
        class NameVisitor(ast.NodeVisitor):
            def __init__(self):
                self.names = set()
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    self.names.add(node.id)
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Handle attribute access like 'module.function'
                if isinstance(node.ctx, ast.Load):
                    # Add the base name (e.g., 'module' from 'module.function')
                    if isinstance(node.value, ast.Name):
                        self.names.add(node.value.id)
                self.generic_visit(node)
        
        visitor = NameVisitor()
        visitor.visit(node)
        return visitor.names
    
    def get_imported_names(self, node: ast.AST) -> Dict[str, List[str]]:
        """Extract all imported names from an AST."""
        
        class ImportVisitor(ast.NodeVisitor):
            def __init__(self):
                self.imports = defaultdict(list)
            
            def visit_Import(self, node):
                for alias in node.names:
                    if alias.asname:
                        self.imports['imports'].append(alias.asname)
                    else:
                        self.imports['imports'].append(alias.name)
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                module = node.module or ''
                for alias in node.names:
                    if alias.name == '*':
                        # Handle star imports - we'll be conservative and keep them
                        self.imports['star_imports'].append(f"{module}.*")
                    else:
                        if alias.asname:
                            self.imports['from_imports'].append((module, alias.name, alias.asname))
                        else:
                            self.imports['from_imports'].append((module, alias.name, alias.name))
                self.generic_visit(node)
        
        visitor = ImportVisitor()
        visitor.visit(node)
        return dict(visitor.imports)
    
    def get_defined_names(self, node: ast.AST) -> Set[str]:
        """Extract all defined names (variables, functions, classes) from an AST."""
        defined_names = set()
        
        class DefinitionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.definitions = set()
            
            def visit_FunctionDef(self, node):
                self.definitions.add(node.name)
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                self.definitions.add(node.name)
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                self.definitions.add(node.name)
                self.generic_visit(node)
            
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.definitions.add(target.id)
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                self.definitions.add(elt.id)
                self.generic_visit(node)
            
            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    self.definitions.add(node.target.id)
                self.generic_visit(node)
            
            def visit_For(self, node):
                if isinstance(node.target, ast.Name):
                    self.definitions.add(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for elt in node.target.elts:
                        if isinstance(elt, ast.Name):
                            self.definitions.add(elt.id)
                self.generic_visit(node)
            
            def visit_With(self, node):
                for item in node.items:
                    if item.optional_vars:
                        if isinstance(item.optional_vars, ast.Name):
                            self.definitions.add(item.optional_vars.id)
                        elif isinstance(item.optional_vars, ast.Tuple):
                            for elt in item.optional_vars.elts:
                                if isinstance(elt, ast.Name):
                                    self.definitions.add(elt.id)
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                if node.name:
                    self.definitions.add(node.name)
                self.generic_visit(node)
        
        visitor = DefinitionVisitor()
        visitor.visit(node)
        return visitor.definitions
    
    def clean_file(self, file_path: Path) -> bool:
        """Clean unused imports and variables from a single file."""
        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Parse the file
            tree = self.parse_file(file_path)
            if tree is None:
                return False
            
            # Get all used names
            used_names = self.get_used_names(tree)
            
            # Get all imported names
            imported_data = self.get_imported_names(tree)
            
            # Get all defined names
            defined_names = self.get_defined_names(tree)
            
            # Find unused imports
            unused_imports = []
            for import_name in imported_data.get('imports', []):
                if import_name not in used_names:
                    unused_imports.append(import_name)
            
            unused_from_imports = []
            for module, name, asname in imported_data.get('from_imports', []):
                if asname not in used_names:
                    unused_from_imports.append((module, name, asname))
            
            # Find unused variables (defined but not used)
            unused_variables = []
            for var_name in defined_names:
                if var_name not in used_names and not var_name.startswith('_'):
                    # Skip special names and dunder methods
                    if not (var_name.startswith('__') and var_name.endswith('__')):
                        unused_variables.append(var_name)
            
            # If no cleanup needed, return early
            if not unused_imports and not unused_from_imports and not unused_variables:
                return False
            
            # Apply fixes
            new_content = original_content
            
            # Remove unused imports
            if unused_imports:
                new_content = self.remove_unused_imports(new_content, unused_imports)
            
            if unused_from_imports:
                new_content = self.remove_unused_from_imports(new_content, unused_from_imports)
            
            # Remove unused variables (be more conservative)
            if unused_variables:
                new_content = self.remove_unused_variables(new_content, unused_variables)
            
            # Write the cleaned content back
            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"Cleaned {file_path}: removed {len(unused_imports)} imports, {len(unused_from_imports)} from-imports, {len(unused_variables)} variables")
                self.changes_made += 1
                return True
            
            return False
            
        except Exception as e:
            self.errors.append(f"Error cleaning {file_path}: {e}")
            return False
    
    def remove_unused_imports(self, content: str, unused_imports: List[str]) -> str:
        """Remove unused import statements."""
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for import statements
            if line.startswith('import '):
                # Parse the import line
                import_match = re.match(r'import\s+(.+)', line)
                if import_match:
                    imports = [imp.strip() for imp in import_match.group(1).split(',')]
                    remaining_imports = []
                    
                    for imp in imports:
                        # Handle 'as' aliases
                        if ' as ' in imp:
                            alias = imp.split(' as ')[1].strip()
                            if alias not in unused_imports:
                                remaining_imports.append(imp)
                        else:
                            if imp not in unused_imports:
                                remaining_imports.append(imp)
                    
                    if remaining_imports:
                        # Reconstruct the import line
                        indent = len(lines[i]) - len(lines[i].lstrip())
                        new_line = ' ' * indent + 'import ' + ', '.join(remaining_imports)
                        new_lines.append(new_line)
                    # If no remaining imports, skip this line
                else:
                    new_lines.append(lines[i])
            else:
                new_lines.append(lines[i])
            
            i += 1
        
        return '\n'.join(new_lines)
    
    def remove_unused_from_imports(self, content: str, unused_from_imports: List[Tuple[str, str, str]]) -> str:
        """Remove unused from-import statements."""
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for from-import statements
            if line.startswith('from ') and ' import ' in line:
                from_match = re.match(r'from\s+(.+?)\s+import\s+(.+)', line)
                if from_match:
                    module = from_match.group(1).strip()
                    imports = [imp.strip() for imp in from_match.group(2).split(',')]
                    remaining_imports = []
                    
                    for imp in imports:
                        # Handle 'as' aliases
                        if ' as ' in imp:
                            name, alias = imp.split(' as ')
                            if (module, name.strip(), alias.strip()) not in unused_from_imports:
                                remaining_imports.append(imp)
                        else:
                            if (module, imp, imp) not in unused_from_imports:
                                remaining_imports.append(imp)
                    
                    if remaining_imports:
                        # Reconstruct the from-import line
                        indent = len(lines[i]) - len(lines[i].lstrip())
                        new_line = ' ' * indent + f'from {module} import ' + ', '.join(remaining_imports)
                        new_lines.append(new_line)
                    # If no remaining imports, skip this line
                else:
                    new_lines.append(lines[i])
            else:
                new_lines.append(lines[i])
            
            i += 1
        
        return '\n'.join(new_lines)
    
    def remove_unused_variables(self, content: str, unused_variables: List[str]) -> str:
        """Remove unused variable assignments (conservative approach)."""
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for simple variable assignments
            if '=' in line and not line.startswith('#'):
                # Look for simple assignments like 'var = value'
                assign_match = re.match(r'^(\w+)\s*=\s*(.+)$', line)
                if assign_match:
                    var_name = assign_match.group(1)
                    if var_name in unused_variables:
                        # Check if this is a simple assignment (not function call, etc.)
                        value = assign_match.group(2).strip()
                        if not (value.startswith('(') or 'def ' in value or 'class ' in value):
                            # Skip this line (remove the assignment)
                            i += 1
                            continue
            
            new_lines.append(lines[i])
            i += 1
        
        return '\n'.join(new_lines)
    
    def clean_all_files(self) -> Dict[str, any]:
        """Clean all Python files in the project."""
        logger.info("Starting comprehensive import and variable cleanup...")
        
        python_files = self.find_all_python_files()
        logger.info(f"Found {len(python_files)} Python files to process")
        
        for file_path in python_files:
            if self.clean_file(file_path):
                self.files_processed += 1
        
        # Generate report
        report = {
            'files_processed': self.files_processed,
            'changes_made': self.changes_made,
            'errors': self.errors,
            'total_files': len(python_files)
        }
        
        logger.info(f"Cleanup complete: {self.changes_made} files modified, {len(self.errors)} errors")
        return report


def main():
    """Main function to run the import cleaner."""
    project_root = Path(__file__).parent.parent
    cleaner = ImportCleaner(project_root)
    report = cleaner.clean_all_files()
    
    print(f"\n📊 Import and Variable Cleanup Report:")
    print(f"   Files processed: {report['files_processed']}")
    print(f"   Changes made: {report['changes_made']}")
    print(f"   Total files: {report['total_files']}")
    print(f"   Errors: {len(report['errors'])}")
    
    if report['errors']:
        print(f"\n❌ Errors encountered:")
        for error in report['errors']:
            print(f"   - {error}")
    
    return report


if __name__ == "__main__":
    main() 
