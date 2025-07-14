#!/usr/bin/env python3
"""
Comprehensive Automated Debugging Workflow
Author: AI Assistant
Date: 2024-12-19

This module provides automated debugging, error fixing, and testing capabilities
for the Oracle AI Assistant project. It runs comprehensive diagnostics and
automatically fixes issues without user intervention.
"""

import os
import sys
import subprocess
import importlib
import traceback
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_workflow.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class AutomatedDebugWorkflow:
    """Comprehensive automated debugging and testing workflow."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.fixes_applied = []
        self.errors_found = []
        self.warnings = []
        
    def run_comprehensive_debug(self) -> Dict[str, Any]:
        """Run the complete automated debugging workflow."""
        print("🚀 Starting Comprehensive Automated Debug Workflow...")
        
        try:
            # Phase 1: Environment Diagnostics
            print("\n📋 Phase 1: Environment Diagnostics")
            env_status = self._diagnose_environment()
            
            # Phase 2: Python Interpreter Check
            print("\n🐍 Phase 2: Python Interpreter Check")
            python_status = self._check_python_interpreter()
            
            # Phase 3: Dependency Verification
            print("\n📦 Phase 3: Dependency Verification")
            deps_status = self._verify_dependencies()
            
            # Phase 4: Syntax Error Detection
            print("\n🔍 Phase 4: Syntax Error Detection")
            syntax_status = self._detect_syntax_errors()
            
            # Phase 5: Import Error Detection
            print("\n📥 Phase 5: Import Error Detection")
            import_status = self._detect_import_errors()
            
            # Phase 6: Automatic Fixes
            print("\n🔧 Phase 6: Automatic Fixes")
            fixes_status = self._apply_automatic_fixes()
            
            # Phase 7: Comprehensive Testing
            print("\n🧪 Phase 7: Comprehensive Testing")
            test_status = self._run_comprehensive_tests()
            
            # Phase 8: Integration Testing
            print("\n🔗 Phase 8: Integration Testing")
            integration_status = self._run_integration_tests()
            
            # Phase 9: Performance Testing
            print("\n⚡ Phase 9: Performance Testing")
            performance_status = self._run_performance_tests()
            
            # Phase 10: Generate Report
            print("\n📊 Phase 10: Generate Report")
            report = self._generate_comprehensive_report({
                'environment': env_status,
                'python': python_status,
                'dependencies': deps_status,
                'syntax': syntax_status,
                'imports': import_status,
                'fixes': fixes_status,
                'tests': test_status,
                'integration': integration_status,
                'performance': performance_status
            })
            
            print("\n✅ Comprehensive Debug Workflow Complete!")
            return report
            
        except Exception as e:
            error_msg = f"Critical error in debug workflow: {str(e)}"
            print(f"❌ {error_msg}")
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return {'error': error_msg, 'traceback': traceback.format_exc()}
    
    def _diagnose_environment(self) -> Dict[str, Any]:
        """Diagnose the current environment."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
        try:
            # Check Python version
            status['details']['python_version'] = sys.version
            
            # Check working directory
            status['details']['working_directory'] = os.getcwd()
            
            # Check project structure
            status['details']['project_root'] = str(self.project_root)
            status['details']['project_exists'] = self.project_root.exists()
            
            # Check file permissions
            status['details']['can_write'] = os.access(self.project_root, os.W_OK)
            status['details']['can_read'] = os.access(self.project_root, os.R_OK)
            
            # Check available memory
            try:
                import psutil
                status['details']['memory_available'] = psutil.virtual_memory().available
            except ImportError:
                status['details']['memory_available'] = 'psutil not available'
            
            print("✅ Environment diagnostics completed")
            
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Environment diagnosis failed: {str(e)}")
            print(f"❌ Environment diagnostics failed: {str(e)}")
        
        return status
    
    def _check_python_interpreter(self) -> Dict[str, Any]:
        """Check Python interpreter functionality."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
        try:
            # Test basic Python functionality
            test_script = """
import sys
print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("Python path:", sys.path[:3])
"""
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                status['details']['interpreter_working'] = True
                status['details']['output'] = result.stdout
                print("✅ Python interpreter is working")
            else:
                status['passed'] = False
                status['issues'].append(f"Python interpreter test failed: {result.stderr}")
                print(f"❌ Python interpreter test failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            status['passed'] = False
            status['issues'].append("Python interpreter test timed out")
            print("❌ Python interpreter test timed out")
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Python interpreter check failed: {str(e)}")
            print(f"❌ Python interpreter check failed: {str(e)}")
        
        return status
    
    def _verify_dependencies(self) -> Dict[str, Any]:
        """Verify all project dependencies."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
        try:
            # Read requirements.txt
            requirements_file = self.project_root / 'requirements.txt'
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                status['details']['requirements'] = requirements
                
                # Test each dependency
                for req in requirements:
                    package_name = req.split('==')[0].split('>=')[0].split('<=')[0]
                    try:
                        importlib.import_module(package_name.replace('-', '_'))
                        status['details'][package_name] = 'OK'
                    except ImportError:
                        status['issues'].append(f"Missing dependency: {package_name}")
                        status['details'][package_name] = 'MISSING'
                        status['passed'] = False
                
                print(f"✅ Dependencies verified ({len(requirements)} packages)")
            else:
                status['issues'].append("requirements.txt not found")
                status['passed'] = False
                print("❌ requirements.txt not found")
                
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Dependency verification failed: {str(e)}")
            print(f"❌ Dependency verification failed: {str(e)}")
        
        return status
    
    def _detect_syntax_errors(self) -> Dict[str, Any]:
        """Detect syntax errors in all Python files."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
        try:
            python_files = list(self.project_root.rglob('*.py'))
            status['details']['files_checked'] = len(python_files)
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check syntax
                    compile(content, str(py_file), 'exec')
                    status['details'][str(py_file)] = 'OK'
                    
                except SyntaxError as e:
                    status['issues'].append(f"Syntax error in {py_file}: {str(e)}")
                    status['details'][str(py_file)] = f"SYNTAX ERROR: {str(e)}"
                    status['passed'] = False
                except Exception as e:
                    status['issues'].append(f"Error reading {py_file}: {str(e)}")
                    status['details'][str(py_file)] = f"READ ERROR: {str(e)}"
                    status['passed'] = False
            
            print(f"✅ Syntax check completed ({len(python_files)} files)")
            
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Syntax detection failed: {str(e)}")
            print(f"❌ Syntax detection failed: {str(e)}")
        
        return status
    
    def _detect_import_errors(self) -> Dict[str, Any]:
        """Detect import errors in all Python modules."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
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
                    status['details'][module_name] = 'OK'
                except ImportError as e:
                    status['issues'].append(f"Import error in {module_name}: {str(e)}")
                    status['details'][module_name] = f"IMPORT ERROR: {str(e)}"
                    status['passed'] = False
                except Exception as e:
                    status['issues'].append(f"Error importing {module_name}: {str(e)}")
                    status['details'][module_name] = f"ERROR: {str(e)}"
                    status['passed'] = False
            
            print(f"✅ Import check completed ({len(main_modules)} modules)")
            
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Import detection failed: {str(e)}")
            print(f"❌ Import detection failed: {str(e)}")
        
        return status
    
    def _apply_automatic_fixes(self) -> Dict[str, Any]:
        """Apply automatic fixes for common issues."""
        status = {'passed': True, 'issues': [], 'fixes_applied': [], 'details': {}}
        
        try:
            # Fix 1: Ensure __init__.py files exist
            self._fix_init_files(status)
            
            # Fix 2: Fix common import issues
            self._fix_import_issues(status)
            
            # Fix 3: Fix syntax issues
            self._fix_syntax_issues(status)
            
            # Fix 4: Fix path issues
            self._fix_path_issues(status)
            
            print(f"✅ Automatic fixes applied ({len(status['fixes_applied'])} fixes)")
            
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Automatic fixes failed: {str(e)}")
            print(f"❌ Automatic fixes failed: {str(e)}")
        
        return status
    
    def _fix_init_files(self, status: Dict[str, Any]):
        """Ensure __init__.py files exist in all packages."""
        try:
            for py_dir in self.project_root.rglob('*/'):
                if py_dir.is_dir() and any(py_dir.glob('*.py')):
                    init_file = py_dir / '__init__.py'
                    if not init_file.exists():
                        init_file.write_text('# Package initialization\n')
                        status['fixes_applied'].append(f"Created {init_file}")
                        status['details'][str(init_file)] = 'CREATED'
        except Exception as e:
            status['issues'].append(f"Init file fix failed: {str(e)}")
    
    def _fix_import_issues(self, status: Dict[str, Any]):
        """Fix common import issues."""
        try:
            # Fix QUrl import issue
            files_to_fix = [
                'ui/bottom_panel.py',
                'ui/api_settings_dialog.py'
            ]
            
            for file_path in files_to_fix:
                full_path = self.project_root / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    
                    # Fix QUrl import
                    if 'from PyQt6.QtGui import QUrl' in content:
                        content = content.replace(
                            'from PyQt6.QtGui import QUrl',
                            'from PyQt6.QtCore import QUrl'
                        )
                        full_path.write_text(content, encoding='utf-8')
                        status['fixes_applied'].append(f"Fixed QUrl import in {file_path}")
                        status['details'][file_path] = 'FIXED'
                        
        except Exception as e:
            status['issues'].append(f"Import fix failed: {str(e)}")
    
    def _fix_syntax_issues(self, status: Dict[str, Any]):
        """Fix common syntax issues."""
        try:
            # Fix logger issues in error_handler.py
            error_handler_path = self.project_root / 'utils' / 'error_handler.py'
            if error_handler_path.exists():
                content = error_handler_path.read_text(encoding='utf-8')
                
                # Fix global logger declaration
                if 'global logger' in content and 'logger = logging.getLogger' in content:
                    # Move global logger to top of functions
                    lines = content.split('\n')
                    fixed_lines = []
                    in_function = False
                    
                    for line in lines:
                        if line.strip().startswith('def '):
                            in_function = True
                            fixed_lines.append(line)
                            # Add global logger at start of function
                            if 'logger' in line and 'global logger' not in line:
                                fixed_lines.append('    global logger')
                        elif in_function and line.strip() == 'global logger':
                            # Skip this line as we already added it
                            continue
                        else:
                            fixed_lines.append(line)
                            if line.strip() == '':
                                in_function = False
                    
                    fixed_content = '\n'.join(fixed_lines)
                    error_handler_path.write_text(fixed_content, encoding='utf-8')
                    status['fixes_applied'].append("Fixed global logger declaration in error_handler.py")
                    status['details']['error_handler.py'] = 'FIXED'
                    
        except Exception as e:
            status['issues'].append(f"Syntax fix failed: {str(e)}")
    
    def _fix_path_issues(self, status: Dict[str, Any]):
        """Fix common path issues."""
        try:
            # Ensure test directories exist
            test_dirs = [
                'tests/test_data',
                'tests/backups',
                'tests/temp',
                'exports',
                'conversations',
                'attachments/assistant',
                'attachments/user'
            ]
            
            for test_dir in test_dirs:
                dir_path = self.project_root / test_dir
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    status['fixes_applied'].append(f"Created directory: {test_dir}")
                    status['details'][test_dir] = 'CREATED'
                    
        except Exception as e:
            status['issues'].append(f"Path fix failed: {str(e)}")
    
    def _run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
        try:
            # Run all test files
            test_files = list((self.project_root / 'tests').rglob('*test*.py'))
            status['details']['test_files'] = len(test_files)
            
            for test_file in test_files:
                try:
                    result = subprocess.run(
                        [sys.executable, str(test_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        status['details'][str(test_file)] = 'PASSED'
                    else:
                        status['details'][str(test_file)] = f"FAILED: {result.stderr}"
                        status['issues'].append(f"Test failed: {test_file}")
                        status['passed'] = False
                        
                except subprocess.TimeoutExpired:
                    status['details'][str(test_file)] = 'TIMEOUT'
                    status['issues'].append(f"Test timeout: {test_file}")
                    status['passed'] = False
                except Exception as e:
                    status['details'][str(test_file)] = f"ERROR: {str(e)}"
                    status['issues'].append(f"Test error: {test_file} - {str(e)}")
                    status['passed'] = False
            
            print(f"✅ Comprehensive tests completed ({len(test_files)} test files)")
            
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Comprehensive testing failed: {str(e)}")
            print(f"❌ Comprehensive testing failed: {str(e)}")
        
        return status
    
    def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
        try:
            # Test main application startup
            main_script = self.project_root / 'main.py'
            if main_script.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, str(main_script), '--test-mode'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        status['details']['main_app'] = 'STARTED SUCCESSFULLY'
                    else:
                        status['details']['main_app'] = f"FAILED: {result.stderr}"
                        status['issues'].append("Main application failed to start")
                        status['passed'] = False
                        
                except subprocess.TimeoutExpired:
                    status['details']['main_app'] = 'TIMEOUT'
                    status['issues'].append("Main application startup timeout")
                    status['passed'] = False
                except Exception as e:
                    status['details']['main_app'] = f"ERROR: {str(e)}"
                    status['issues'].append(f"Main application error: {str(e)}")
                    status['passed'] = False
            
            print("✅ Integration tests completed")
            
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Integration testing failed: {str(e)}")
            print(f"❌ Integration testing failed: {str(e)}")
        
        return status
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        status = {'passed': True, 'issues': [], 'details': {}}
        
        try:
            # Test import performance
            start_time = time.time()
            
            test_modules = [
                'ui.main_window',
                'ui.bottom_panel',
                'core.quick_switch',
                'utils.error_handler'
            ]
            
            for module_name in test_modules:
                try:
                    start = time.time()
                    importlib.import_module(module_name)
                    import_time = time.time() - start
                    status['details'][f'{module_name}_import_time'] = f"{import_time:.3f}s"
                    
                    if import_time > 1.0:
                        status['issues'].append(f"Slow import: {module_name} ({import_time:.3f}s)")
                        status['passed'] = False
                        
                except Exception as e:
                    status['details'][f'{module_name}_import_time'] = f"ERROR: {str(e)}"
                    status['issues'].append(f"Import error: {module_name} - {str(e)}")
                    status['passed'] = False
            
            total_time = time.time() - start_time
            status['details']['total_performance_test_time'] = f"{total_time:.3f}s"
            
            print(f"✅ Performance tests completed ({total_time:.3f}s)")
            
        except Exception as e:
            status['passed'] = False
            status['issues'].append(f"Performance testing failed: {str(e)}")
            print(f"❌ Performance testing failed: {str(e)}")
        
        return status
    
    def _generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive debug report."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_phases': len(results),
                'passed_phases': sum(1 for r in results.values() if r.get('passed', False)),
                'failed_phases': sum(1 for r in results.values() if not r.get('passed', True)),
                'total_issues': sum(len(r.get('issues', [])) for r in results.values()),
                'total_fixes': sum(len(r.get('fixes_applied', [])) for r in results.values())
            },
            'detailed_results': results,
            'recommendations': []
        }
        
        # Generate recommendations
        if report['summary']['failed_phases'] > 0:
            report['recommendations'].append("Some phases failed - review detailed results")
        
        if report['summary']['total_issues'] > 0:
            report['recommendations'].append(f"Found {report['summary']['total_issues']} issues - review and address")
        
        if report['summary']['total_fixes'] > 0:
            report['recommendations'].append(f"Applied {report['summary']['total_fixes']} automatic fixes")
        
        # Save report
        report_file = self.project_root / 'test_reports' / 'comprehensive_debug_report.json'
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print(f"\n📊 Debug Report Summary:")
        print(f"   Phases: {report['summary']['passed_phases']}/{report['summary']['total_phases']} passed")
        print(f"   Issues: {report['summary']['total_issues']}")
        print(f"   Fixes: {report['summary']['total_fixes']}")
        print(f"   Report saved to: {report_file}")
        
        return report

def run_automated_debug():
    """Main function to run the automated debug workflow."""
    workflow = AutomatedDebugWorkflow()
    return workflow.run_comprehensive_debug()

if __name__ == '__main__':
    run_automated_debug() 
