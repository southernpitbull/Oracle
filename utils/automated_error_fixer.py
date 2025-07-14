# utils/automated_error_fixer.py
"""
Automated Error Fixer
Author: AI Assistant
Date: 2024-12-19

This module provides automated error detection and fixing capabilities
for the Oracle AI Assistant project. It automatically fixes common
errors without user intervention.
"""

import os
import sys
import re
import ast
import subprocess
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import json
import importlib
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_fixer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class AutomatedErrorFixer:
    """Automated error detection and fixing system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.fixes_applied = []
        self.errors_found = []
        self.files_processed = 0
        
    def run_automated_fixes(self) -> Dict[str, Any]:
        """Run automated error detection and fixing."""
        print("🔧 Starting Automated Error Fixer...")
        
        try:
            # Phase 1: Syntax Error Detection and Fixing
            print("\n📋 Phase 1: Syntax Error Detection and Fixing")
            syntax_results = self._fix_syntax_errors()
            
            # Phase 2: Import Error Detection and Fixing
            print("\n📥 Phase 2: Import Error Detection and Fixing")
            import_results = self._fix_import_errors()
            
            # Phase 3: Path Error Detection and Fixing
            print("\n📁 Phase 3: Path Error Detection and Fixing")
            path_results = self._fix_path_errors()
            
            # Phase 4: Code Style and Formatting Fixes
            print("\n🎨 Phase 4: Code Style and Formatting Fixes")
            style_results = self._fix_code_style()
            
            # Phase 5: Dependency and Configuration Fixes
            print("\n⚙️ Phase 5: Dependency and Configuration Fixes")
            config_results = self._fix_configuration_issues()
            
            # Phase 6: Generate Fix Report
            print("\n📊 Phase 6: Generate Fix Report")
            report = self._generate_fix_report({
                'syntax': syntax_results,
                'imports': import_results,
                'paths': path_results,
                'style': style_results,
                'configuration': config_results
            })
            
            print("\n✅ Automated Error Fixer Complete!")
            return report
            
        except Exception as e:
            error_msg = f"Critical error in error fixer: {str(e)}"
            print(f"❌ {error_msg}")
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return {'error': error_msg, 'traceback': traceback.format_exc()}
    
    def _fix_syntax_errors(self) -> Dict[str, Any]:
        """Detect and fix syntax errors."""
        results = {'fixed': 0, 'errors': [], 'details': {}}
        
        try:
            python_files = list(self.project_root.rglob('*.py'))
            results['files_checked'] = len(python_files)
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for common syntax issues
                    fixed_content = content
                    
                    # Fix 1: Global logger declaration issues
                    fixed_content = self._fix_global_logger_issues(fixed_content, py_file)
                    
                    # Fix 2: String formatting issues
                    fixed_content = self._fix_string_formatting_issues(fixed_content, py_file)
                    
                    # Fix 3: Indentation issues
                    fixed_content = self._fix_indentation_issues(fixed_content, py_file)
                    
                    # Fix 4: Missing imports
                    fixed_content = self._fix_missing_imports(fixed_content, py_file)
                    
                    # Fix 5: Function definition issues
                    fixed_content = self._fix_function_definition_issues(fixed_content, py_file)
                    
                    # Write back if changes were made
                    if fixed_content != content:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        results['fixed'] += 1
                        results['details'][str(py_file)] = 'FIXED'
                        self.fixes_applied.append(f"Fixed syntax issues in {py_file}")
                    else:
                        results['details'][str(py_file)] = 'OK'
                    
                    # Verify syntax is now valid
                    try:
                        compile(fixed_content, str(py_file), 'exec')
                    except SyntaxError as e:
                        results['errors'].append(f"Syntax error in {py_file}: {str(e)}")
                        results['details'][str(py_file)] = f"SYNTAX ERROR: {str(e)}"
                    
                except Exception as e:
                    results['errors'].append(f"Error processing {py_file}: {str(e)}")
                    results['details'][str(py_file)] = f"PROCESSING ERROR: {str(e)}"
            
            print(f"✅ Syntax fixes completed: {results['fixed']} files fixed")
            
        except Exception as e:
            results['errors'].append(f"Syntax fixing failed: {str(e)}")
            print(f"❌ Syntax fixing failed: {str(e)}")
        
        return results
    
    def _fix_global_logger_issues(self, content: str, file_path: Path) -> str:
        """Fix global logger declaration issues."""
        lines = content.split('\n')
        fixed_lines = []
        in_function = False
        function_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect function start
            if stripped.startswith('def '):
                in_function = True
                function_indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                
                # Check if this function uses logger
                # Look ahead to see if logger is used in this function
                logger_used = False
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    
                    # Check if we've reached the end of this function
                    if next_stripped and len(next_line) - len(next_line.lstrip()) <= function_indent:
                        break
                    
                    # Check if logger is used
                    if 'logger.' in next_stripped and not next_stripped.startswith('#'):
                        logger_used = True
                        break
                
                # Add global logger declaration if needed
                if logger_used:
                    fixed_lines.append(' ' * (function_indent + 4) + 'global logger')
                    
            elif in_function and stripped == 'global logger':
                # Skip this line as we already added it
                continue
            else:
                fixed_lines.append(line)
                
                # Check if we've exited the function
                if in_function and stripped and len(line) - len(line.lstrip()) <= function_indent:
                    in_function = False
        
        return '\n'.join(fixed_lines)
    
    def _fix_string_formatting_issues(self, content: str, file_path: Path) -> str:
        """Fix string formatting issues."""
        # Fix logger calls that use f-strings incorrectly
        content = re.sub(
            r'logger\.(debug|info|warning|error|critical)\s*\(\s*f(["\'])(.*?)\2\s*\)',
            r'logger.\1(\2\3\2)',
            content
        )
        
        # Fix logger calls that use .format() incorrectly
        content = re.sub(
            r'logger\.(debug|info|warning|error|critical)\s*\(\s*(["\'])(.*?)\2\.format\((.*?)\)\s*\)',
            r'logger.\1(\2\3\2.format(\4))',
            content
        )
        
        return content
    
    def _fix_indentation_issues(self, content: str, file_path: Path) -> str:
        """Fix indentation issues."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix mixed tabs and spaces
            if '\t' in line:
                line = line.replace('\t', '    ')
            
            # Ensure consistent indentation
            stripped = line.lstrip()
            if stripped:
                indent_level = len(line) - len(line.lstrip())
                if indent_level % 4 != 0:
                    # Round to nearest 4-space increment
                    new_indent_level = (indent_level // 4) * 4
                    line = ' ' * new_indent_level + stripped
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_missing_imports(self, content: str, file_path: Path) -> str:
        """Fix missing imports."""
        lines = content.split('\n')
        fixed_lines = []
        
        # Check for missing imports based on usage
        missing_imports = []
        
        # Check for QUrl usage
        if 'QUrl(' in content and 'from PyQt6.QtCore import QUrl' not in content:
            missing_imports.append('from PyQt6.QtCore import QUrl')
        
        # Check for logging usage
        if 'logging.' in content and 'import logging' not in content:
            missing_imports.append('import logging')
        
        # Check for json usage
        if 'json.' in content and 'import json' not in content:
            missing_imports.append('import json')
        
        # Check for pathlib usage
        if 'Path(' in content and 'from pathlib import Path' not in content:
            missing_imports.append('from pathlib import Path')
        
        # Add missing imports at the top
        if missing_imports:
            # Find the first import line
            import_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    import_index = i
                    break
            
            if import_index == -1:
                # No imports found, add at the top after docstring
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        insert_index = i + 1
                        # Find end of docstring
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().endswith('"""') or lines[j].strip().endswith("'''"):
                                insert_index = j + 1
                                break
                        break
                
                # Insert imports
                for import_line in missing_imports:
                    lines.insert(insert_index, import_line)
                    insert_index += 1
            else:
                # Insert before existing imports
                for import_line in reversed(missing_imports):
                    lines.insert(import_index, import_line)
        
        return '\n'.join(lines)
    
    def _fix_function_definition_issues(self, content: str, file_path: Path) -> str:
        """Fix function definition issues."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix function definitions with missing colons
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', line):
                if not line.rstrip().endswith(':'):
                    line = line.rstrip() + ':'
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_import_errors(self) -> Dict[str, Any]:
        """Detect and fix import errors."""
        results = {'fixed': 0, 'errors': [], 'details': {}}
        
        try:
            # Add project root to Python path
            sys.path.insert(0, str(self.project_root))
            
            # Test imports for main modules
            main_modules = [
                'main',
                'ui.main_window',
                'ui.bottom_panel',
                'core.quick_switch',
                'utils.error_handler',
                'api.settings',
                'api.clients'
            ]
            
            for module_name in main_modules:
                try:
                    importlib.import_module(module_name)
                    results['details'][module_name] = 'OK'
                except ImportError as e:
                    # Try to fix the import error
                    fixed = self._fix_specific_import_error(module_name, str(e))
                    if fixed:
                        results['fixed'] += 1
                        results['details'][module_name] = 'FIXED'
                        self.fixes_applied.append(f"Fixed import error in {module_name}")
                    else:
                        results['errors'].append(f"Import error in {module_name}: {str(e)}")
                        results['details'][module_name] = f"IMPORT ERROR: {str(e)}"
                except Exception as e:
                    results['errors'].append(f"Error importing {module_name}: {str(e)}")
                    results['details'][module_name] = f"ERROR: {str(e)}"
            
            print(f"✅ Import fixes completed: {results['fixed']} modules fixed")
            
        except Exception as e:
            results['errors'].append(f"Import fixing failed: {str(e)}")
            print(f"❌ Import fixing failed: {str(e)}")
        
        return results
    
    def _fix_specific_import_error(self, module_name: str, error_msg: str) -> bool:
        """Fix specific import errors."""
        try:
            # Fix common import issues
            if 'QUrl' in error_msg and 'QtCore' in error_msg:
                # Fix QUrl import issue
                files_to_check = [
                    'ui/bottom_panel.py',
                    'ui/api_settings_dialog.py'
                ]
                
                for file_path in files_to_check:
                    full_path = self.project_root / file_path
                    if full_path.exists():
                        content = full_path.read_text(encoding='utf-8')
                        
                        if 'from PyQt6.QtGui import QUrl' in content:
                            content = content.replace(
                                'from PyQt6.QtGui import QUrl',
                                'from PyQt6.QtCore import QUrl'
                            )
                            full_path.write_text(content, encoding='utf-8')
                            return True
            
            # Fix missing __init__.py files
            module_parts = module_name.split('.')
            current_path = self.project_root
            
            for part in module_parts:
                current_path = current_path / part
                if current_path.is_dir() and not (current_path / '__init__.py').exists():
                    (current_path / '__init__.py').write_text('# Package initialization\n')
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error fixing import for {module_name}: {str(e)}")
            return False
    
    def _fix_path_errors(self) -> Dict[str, Any]:
        """Detect and fix path errors."""
        results = {'fixed': 0, 'errors': [], 'details': {}}
        
        try:
            # Ensure required directories exist
            required_dirs = [
                'tests/test_data',
                'tests/backups',
                'tests/temp',
                'exports',
                'conversations',
                'attachments/assistant',
                'attachments/user',
                'test_reports',
                'models'
            ]
            
            for dir_path in required_dirs:
                full_path = self.project_root / dir_path
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    results['fixed'] += 1
                    results['details'][dir_path] = 'CREATED'
                    self.fixes_applied.append(f"Created directory: {dir_path}")
                else:
                    results['details'][dir_path] = 'EXISTS'
            
            # Fix file path references in code
            python_files = list(self.project_root.rglob('*.py'))
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix hardcoded paths
                    fixed_content = content
                    
                    # Fix relative path issues
                    fixed_content = re.sub(
                        r'Path\([\'"](?!\.\./|\./|/)[^\'"]*[\'"]\)',
                        lambda m: f'Path(__file__).parent.parent / {m.group(0)[6:-1]}',
                        fixed_content
                    )
                    
                    # Write back if changes were made
                    if fixed_content != content:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        results['fixed'] += 1
                        results['details'][str(py_file)] = 'PATH FIXED'
                        self.fixes_applied.append(f"Fixed path issues in {py_file}")
                    
                except Exception as e:
                    results['errors'].append(f"Error fixing paths in {py_file}: {str(e)}")
            
            print(f"✅ Path fixes completed: {results['fixed']} fixes applied")
            
        except Exception as e:
            results['errors'].append(f"Path fixing failed: {str(e)}")
            print(f"❌ Path fixing failed: {str(e)}")
        
        return results
    
    def _fix_code_style(self) -> Dict[str, Any]:
        """Fix code style and formatting issues."""
        results = {'fixed': 0, 'errors': [], 'details': {}}
        
        try:
            python_files = list(self.project_root.rglob('*.py'))
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix common style issues
                    fixed_content = content
                    
                    # Fix trailing whitespace
                    lines = fixed_content.split('\n')
                    fixed_lines = [line.rstrip() for line in lines]
                    fixed_content = '\n'.join(fixed_lines)
                    
                    # Fix missing newline at end of file
                    if not fixed_content.endswith('\n'):
                        fixed_content += '\n'
                    
                    # Fix multiple blank lines
                    fixed_content = re.sub(r'\n\s*\n\s*\n', '\n\n', fixed_content)
                    
                    # Fix inconsistent quotes
                    fixed_content = re.sub(r"'(?=[^']*'[^']*$)", '"', fixed_content)
                    
                    # Write back if changes were made
                    if fixed_content != content:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        results['fixed'] += 1
                        results['details'][str(py_file)] = 'STYLE FIXED'
                        self.fixes_applied.append(f"Fixed style issues in {py_file}")
                    
                except Exception as e:
                    results['errors'].append(f"Error fixing style in {py_file}: {str(e)}")
            
            print(f"✅ Style fixes completed: {results['fixed']} files fixed")
            
        except Exception as e:
            results['errors'].append(f"Style fixing failed: {str(e)}")
            print(f"❌ Style fixing failed: {str(e)}")
        
        return results
    
    def _fix_configuration_issues(self) -> Dict[str, Any]:
        """Fix configuration and dependency issues."""
        results = {'fixed': 0, 'errors': [], 'details': {}}
        
        try:
            # Ensure requirements.txt exists and is valid
            requirements_file = self.project_root / 'requirements.txt'
            if not requirements_file.exists():
                # Create basic requirements.txt
                basic_requirements = [
                    'PyQt6>=6.0.0',
                    'requests>=2.25.0',
                    'psutil>=5.8.0'
                ]
                requirements_file.write_text('\n'.join(basic_requirements) + '\n')
                results['fixed'] += 1
                results['details']['requirements.txt'] = 'CREATED'
                self.fixes_applied.append("Created requirements.txt")
            
            # Ensure main.py has proper error handling
            main_file = self.project_root / 'main.py'
            if main_file.exists():
                content = main_file.read_text(encoding='utf-8')
                
                # Add error handling if missing
                if 'try:' not in content or 'except Exception as e:' not in content:
                    # Add basic error handling
                    if 'if __name__ == "__main__":' in content:
                        lines = content.split('\n')
                        fixed_lines = []
                        
                        for line in lines:
                            fixed_lines.append(line)
                            if line.strip() == 'if __name__ == "__main__":':
                                fixed_lines.append('    try:')
                                fixed_lines.append('        app = QApplication(sys.argv)')
                                fixed_lines.append('        window = MainWindow()')
                                fixed_lines.append('        window.show()')
                                fixed_lines.append('        sys.exit(app.exec())')
                                fixed_lines.append('    except Exception as e:')
                                fixed_lines.append('        print(f"Error starting application: {e}")')
                                fixed_lines.append('        sys.exit(1)')
                        
                        fixed_content = '\n'.join(fixed_lines)
                        main_file.write_text(fixed_content, encoding='utf-8')
                        results['fixed'] += 1
                        results['details']['main.py'] = 'ERROR HANDLING ADDED'
                        self.fixes_applied.append("Added error handling to main.py")
            
            print(f"✅ Configuration fixes completed: {results['fixed']} fixes applied")
            
        except Exception as e:
            results['errors'].append(f"Configuration fixing failed: {str(e)}")
            print(f"❌ Configuration fixing failed: {str(e)}")
        
        return results
    
    def _generate_fix_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive fix report."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_fix_categories': len(results),
                'total_fixes_applied': sum(r.get('fixed', 0) for r in results.values()),
                'total_errors_found': sum(len(r.get('errors', [])) for r in results.values()),
                'files_processed': self.files_processed
            },
            'detailed_results': results,
            'fixes_applied': self.fixes_applied,
            'recommendations': []
        }
        
        # Generate recommendations
        if report['summary']['total_errors_found'] > 0:
            report['recommendations'].append(f"Found {report['summary']['total_errors_found']} errors - review detailed results")
        
        if report['summary']['total_fixes_applied'] > 0:
            report['recommendations'].append(f"Applied {report['summary']['total_fixes_applied']} automatic fixes")
        
        # Save report
        report_file = self.project_root / 'test_reports' / 'automated_fix_report.json'
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print(f"\n📊 Fix Report Summary:")
        print(f"   Fixes Applied: {report['summary']['total_fixes_applied']}")
        print(f"   Errors Found: {report['summary']['total_errors_found']}")
        print(f"   Files Processed: {report['summary']['files_processed']}")
        print(f"   Report saved to: {report_file}")
        
        return report

def run_automated_fixes():
    """Main function to run automated fixes."""
    fixer = AutomatedErrorFixer()
    return fixer.run_automated_fixes()

if __name__ == '__main__':
    run_automated_fixes() 
