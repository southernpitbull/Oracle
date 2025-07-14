#!/usr/bin/env python3
"""
Oracle/utils/error_handler.py

Author: The Oracle Development Team
Date: 2024-01-01

This module provides comprehensive error detection and automatic correction capabilities
for The Oracle application. It continuously monitors the codebase for critical errors
and attempts to fix them automatically.
"""

import os
import sys
import logging
import subprocess
import ast
import re
import importlib
import traceback
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class CriticalErrorDetector:
    """Detects critical errors in the codebase"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.error_patterns = {
            'syntax_error': r'SyntaxError|IndentationError|TabError',
            'import_error': r'ImportError|ModuleNotFoundError',
            'name_error': r'NameError|UnboundLocalError',
            'type_error': r'TypeError|AttributeError',
            'value_error': r'ValueError|KeyError|IndexError',
            'file_not_found': r'FileNotFoundError|OSError.*No such file',
            'permission_error': r'PermissionError|OSError.*Permission denied',
            'connection_error': r'ConnectionError|TimeoutError',
            'memory_error': r'MemoryError|OverflowError',
            'recursion_error': r'RecursionError|RuntimeError.*maximum recursion'
        }
        
    def scan_python_files(self) -> List[Path]:
        """Scan for all Python files in the workspace"""
        python_files = []
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip common directories that shouldn't be scanned
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def check_syntax_errors(self, file_path: Path) -> List[Dict]:
        """Check for syntax errors in a Python file"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to compile the code
            ast.parse(content)
            
        except SyntaxError as e:
            errors.append({
                'type': 'syntax_error',
                'file': str(file_path),
                'line': e.lineno,
                'message': str(e),
                'severity': 'critical'
            })
        except Exception as e:
            errors.append({
                'type': 'parsing_error',
                'file': str(file_path),
                'line': 0,
                'message': f"Failed to parse file: {str(e)}",
                'severity': 'critical'
            })
        
        return errors
    
    def check_import_errors(self, file_path: Path) -> List[Dict]:
        """Check for import errors in a Python file"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST to find imports
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name
                            try:
                                importlib.import_module(module_name)
                            except ImportError:
                                errors.append({
                                    'type': 'import_error',
                                    'file': str(file_path),
                                    'line': node.lineno,
                                    'message': f"Failed to import module: {module_name}",
                                    'severity': 'critical'
                                })
                    elif isinstance(node, ast.ImportFrom):
                        module_name = node.module
                        if module_name:
                            try:
                                module = importlib.import_module(module_name)
                                for alias in node.names:
                                    if not hasattr(module, alias.name):
                                        errors.append({
                                            'type': 'import_error',
                                            'file': str(file_path),
                                            'line': node.lineno,
                                            'message': f"Failed to import {alias.name} from {module_name}",
                                            'severity': 'critical'
                                        })
                            except ImportError:
                                errors.append({
                                    'type': 'import_error',
                                    'file': str(file_path),
                                    'line': node.lineno,
                                    'message': f"Failed to import from module: {module_name}",
                                    'severity': 'critical'
                                })
                                
        except Exception as e:
            errors.append({
                'type': 'import_check_error',
                'file': str(file_path),
                'line': 0,
                'message': f"Failed to check imports: {str(e)}",
                'severity': 'warning'
            })
        
        return errors
    
    def check_missing_files(self) -> List[Dict]:
        """Check for missing files that are referenced in the codebase"""
        errors = []
        
        # Common file patterns to check
        file_patterns = [
            'requirements.txt',
            'README.md',
            'main.py',
            '__init__.py'
        ]
        
        for pattern in file_patterns:
            if not (self.workspace_path / pattern).exists():
                errors.append({
                    'type': 'missing_file',
                    'file': pattern,
                    'line': 0,
                    'message': f"Missing required file: {pattern}",
                    'severity': 'critical'
                })
        
        return errors
    
    def detect_all_errors(self) -> List[Dict]:
        """Detect all critical errors in the codebase"""
        all_errors = []
        
        # Get all Python files
        python_files = self.scan_python_files()
        
        # Check each file for errors
        for file_path in python_files:
            # Check syntax errors
            syntax_errors = self.check_syntax_errors(file_path)
            all_errors.extend(syntax_errors)
            
            # Check import errors
            import_errors = self.check_import_errors(file_path)
            all_errors.extend(import_errors)
        
        # Check for missing files
        missing_file_errors = self.check_missing_files()
        all_errors.extend(missing_file_errors)
        
        return all_errors


class ErrorCorrector:
    """Automatically corrects detected errors"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.correction_history = []
        
    def fix_syntax_errors(self, error: Dict) -> bool:
        """Attempt to fix syntax errors"""
        try:
            file_path = Path(error['file'])
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Common syntax error fixes
            fixed_content = content
            
            # Fix common indentation issues
            fixed_content = re.sub(r'\t', '    ', fixed_content)  # Replace tabs with spaces
            
            # Fix common quote issues
            fixed_content = re.sub(r'([^\\])"([^"]*)"([^"]*)"', r'\1"\2\3"', fixed_content)
            
            # Fix missing colons
            fixed_content = re.sub(r'(\s+)(if|for|while|def|class|try|except|finally|with|async def)\s*\([^)]*\)\s*$', r'\1\2\1:', fixed_content, flags=re.MULTILINE)
            
            # Fix missing parentheses
            fixed_content = re.sub(r'print\s+([^;]+);', r'print(\1)', fixed_content)
            
            # Write the fixed content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            self.correction_history.append({
                'timestamp': datetime.now(),
                'error_type': error['type'],
                'file': error['file'],
                'action': 'fixed_syntax_errors'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix syntax error in {error['file']}: {e}")
            return False
    
    def fix_import_errors(self, error: Dict) -> bool:
        """Attempt to fix import errors"""
        try:
            file_path = Path(error['file'])
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to install missing packages
            if 'Failed to import module:' in error['message']:
                module_name = error['message'].split(': ')[-1]
                try:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', module_name], 
                                 capture_output=True, check=True)
                    self.correction_history.append({
                        'timestamp': datetime.now(),
                        'error_type': error['type'],
                        'file': error['file'],
                        'action': f'installed_package_{module_name}'
                    })
                    return True
                except subprocess.CalledProcessError:
                    pass
            
            # Try to fix relative imports
            if 'Failed to import from module:' in error['message']:
                module_name = error['message'].split(': ')[-1]
                # Add sys.path modification for local modules
                if not content.startswith('import sys\nimport os\n'):
                    content = f"import sys\nimport os\nsys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n\n{content}"
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.correction_history.append({
                        'timestamp': datetime.now(),
                        'error_type': error['type'],
                        'file': error['file'],
                        'action': 'fixed_relative_imports'
                    })
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to fix import error in {error['file']}: {e}")
            return False
    
    def fix_missing_files(self, error: Dict) -> bool:
        """Attempt to fix missing files"""
        try:
            file_name = error['file']
            file_path = self.workspace_path / file_name
            
            if file_name == 'requirements.txt':
                # Create a basic requirements.txt
                requirements_content = """# Oracle Application Requirements
PyQt6>=6.0.0
requests>=2.25.0
markdown>=3.0.0
rich>=10.0.0
keyring>=20.0.0
"""
                with open(file_path, 'w') as f:
                    f.write(requirements_content)
                    
            elif file_name == 'README.md':
                # Create a basic README.md
                readme_content = """# Oracle Application

A sophisticated AI chat application with multi-provider support.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Features

- Multi-provider AI support
- Modern GUI interface
- Real-time error correction
- Comprehensive logging
"""
                with open(file_path, 'w') as f:
                    f.write(readme_content)
                    
            elif file_name == '__init__.py':
                # Create an empty __init__.py file
                with open(file_path, 'w') as f:
                    f.write("# Package initialization\n")
            
            self.correction_history.append({
                'timestamp': datetime.now(),
                'error_type': error['type'],
                'file': error['file'],
                'action': f'created_missing_file_{file_name}'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create missing file {error['file']}: {e}")
            return False
    
    def correct_errors(self, errors: List[Dict]) -> Dict[str, int]:
        """Correct all detected errors"""
        correction_results = {
            'total_errors': len(errors),
            'fixed_errors': 0,
            'failed_errors': 0
        }
        
        for error in errors:
            try:
                success = False
                
                if error['type'] == 'syntax_error':
                    success = self.fix_syntax_errors(error)
                elif error['type'] == 'import_error':
                    success = self.fix_import_errors(error)
                elif error['type'] == 'missing_file':
                    success = self.fix_missing_files(error)
                
                if success:
                    correction_results['fixed_errors'] += 1
                    logger.info(f"✅ Fixed {error['type']} in {error['file']}")
                else:
                    correction_results['failed_errors'] += 1
                    logger.warning(f"❌ Failed to fix {error['type']} in {error['file']}")
                    
            except Exception as e:
                correction_results['failed_errors'] += 1
                logger.error(f"❌ Error during correction of {error['type']} in {error['file']}: {e}")
        
        return correction_results


class AutoErrorCorrector:
    """Main class for automatic error correction system"""
    
    def __init__(self, workspace_path: str = "/workspace", interval: int = 60):
        self.workspace_path = workspace_path
        self.interval = interval
        self.detector = CriticalErrorDetector(workspace_path)
        self.corrector = ErrorCorrector(workspace_path)
        self.running = False
        self.thread = None
        self.last_scan_time = None
        self.total_errors_fixed = 0
        
    def start_monitoring(self):
        """Start the automatic error correction monitoring"""
        if self.running:
            logger.warning("Auto error correction is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
        logger.info(f"🚀 Started automatic error correction (scanning every {self.interval} seconds)")
    
    def stop_monitoring(self):
        """Stop the automatic error correction monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🛑 Stopped automatic error correction")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._perform_error_scan()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.interval)
    
    def _perform_error_scan(self):
        """Perform a complete error scan and correction cycle"""
        try:
            logger.info("🔍 Starting error scan...")
            
            # Detect errors
            errors = self.detector.detect_all_errors()
            
            if errors:
                logger.warning(f"⚠️  Found {len(errors)} critical errors")
                
                # Log all errors
                for error in errors:
                    logger.error(f"❌ {error['type']} in {error['file']}: {error['message']}")
                
                # Attempt to correct errors
                correction_results = self.corrector.correct_errors(errors)
                
                # Update statistics
                self.total_errors_fixed += correction_results['fixed_errors']
                self.last_scan_time = datetime.now()
                
                # Log results
                logger.info(f"✅ Fixed {correction_results['fixed_errors']} errors")
                logger.info(f"❌ Failed to fix {correction_results['failed_errors']} errors")
                
                if correction_results['failed_errors'] > 0:
                    logger.warning("⚠️  Some errors could not be automatically fixed")
                    
            else:
                logger.info("✅ No critical errors detected")
                self.last_scan_time = datetime.now()
                
        except Exception as e:
            logger.error(f"❌ Error during error scan: {e}")
    
    def get_status(self) -> Dict:
        """Get the current status of the error correction system"""
        return {
            'running': self.running,
            'interval': self.interval,
            'last_scan_time': self.last_scan_time,
            'total_errors_fixed': self.total_errors_fixed,
            'correction_history': self.corrector.correction_history[-10:]  # Last 10 corrections
        }
    
    def force_scan(self):
        """Force an immediate error scan"""
        if self.running:
            self._perform_error_scan()
        else:
            logger.warning("Auto error correction is not running")


# Global instance for easy access
auto_corrector = AutoErrorCorrector()


def start_auto_error_correction(interval: int = 60):
    """Start the automatic error correction system"""
    auto_corrector.interval = interval
    auto_corrector.start_monitoring()


def stop_auto_error_correction():
    """Stop the automatic error correction system"""
    auto_corrector.stop_monitoring()


def get_error_correction_status() -> Dict:
    """Get the current status of the error correction system"""
    return auto_corrector.get_status()


def force_error_scan():
    """Force an immediate error scan"""
    auto_corrector.force_scan()


if __name__ == "__main__":
    # Test the error correction system
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Auto Error Correction System...")
    
    # Start monitoring
    start_auto_error_correction(interval=30)  # Test with 30 second interval
    
    try:
        # Run for a few minutes
        time.sleep(180)
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        stop_auto_error_correction()
        print("✅ Test completed")