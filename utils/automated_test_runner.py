# utils/automated_test_runner.py
"""
Automated Test Runner
Author: AI Assistant
Date: 2024-12-19

This module provides automated test execution and reporting for the Oracle AI Assistant project.
It runs all tests automatically and generates comprehensive test reports.
"""

import os
import sys
import subprocess
import unittest
import time
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class AutomatedTestRunner:
    """Automated test runner for comprehensive testing."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.test_reports_dir = self.project_root / 'test_reports'
        self.test_reports_dir.mkdir(exist_ok=True)
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in the project."""
        print("🧪 Starting Automated Test Runner...")
        
        try:
            # Phase 1: Unit Tests
            print("\n📋 Phase 1: Unit Tests")
            unit_results = self._run_unit_tests()
            
            # Phase 2: Integration Tests
            print("\n🔗 Phase 2: Integration Tests")
            integration_results = self._run_integration_tests()
            
            # Phase 3: Feature Tests
            print("\n✨ Phase 3: Feature Tests")
            feature_results = self._run_feature_tests()
            
            # Phase 4: GUI Tests
            print("\n🖥️ Phase 4: GUI Tests")
            gui_results = self._run_gui_tests()
            
            # Phase 5: Performance Tests
            print("\n⚡ Phase 5: Performance Tests")
            performance_results = self._run_performance_tests()
            
            # Phase 6: Generate Comprehensive Report
            print("\n📊 Phase 6: Generate Comprehensive Report")
            report = self._generate_test_report({
                'unit_tests': unit_results,
                'integration_tests': integration_results,
                'feature_tests': feature_results,
                'gui_tests': gui_results,
                'performance_tests': performance_results
            })
            
            print("\n✅ Automated Test Runner Complete!")
            return report
            
        except Exception as e:
            error_msg = f"Critical error in test runner: {str(e)}"
            print(f"❌ {error_msg}")
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return {'error': error_msg, 'traceback': traceback.format_exc()}
    
    def _run_unit_tests(self) -> Dict[str, Any]:
        """Run all unit tests."""
        results = {'passed': True, 'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0, 'details': {}}
        
        try:
            # Find all test files
            test_files = list(self.project_root.rglob('*test*.py'))
            results['total_files'] = len(test_files)
            
            for test_file in test_files:
                try:
                    print(f"  Running: {test_file.relative_to(self.project_root)}")
                    
                    # Run test file
                    result = subprocess.run(
                        [sys.executable, str(test_file)],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=str(self.project_root)
                    )
                    
                    results['tests_run'] += 1
                    
                    if result.returncode == 0:
                        results['tests_passed'] += 1
                        results['details'][str(test_file)] = {
                            'status': 'PASSED',
                            'output': result.stdout
                        }
                    else:
                        results['tests_failed'] += 1
                        results['details'][str(test_file)] = {
                            'status': 'FAILED',
                            'output': result.stdout,
                            'error': result.stderr
                        }
                        results['passed'] = False
                        
                except subprocess.TimeoutExpired:
                    results['tests_failed'] += 1
                    results['details'][str(test_file)] = {
                        'status': 'TIMEOUT',
                        'error': 'Test execution timed out'
                    }
                    results['passed'] = False
                except Exception as e:
                    results['tests_failed'] += 1
                    results['details'][str(test_file)] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    results['passed'] = False
            
            print(f"  ✅ Unit tests completed: {results['tests_passed']}/{results['tests_run']} passed")
            
        except Exception as e:
            results['passed'] = False
            results['error'] = str(e)
            print(f"  ❌ Unit tests failed: {str(e)}")
        
        return results
    
    def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        results = {'passed': True, 'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0, 'details': {}}
        
        try:
            # Test main application startup
            print("  Testing main application startup...")
            
            main_script = self.project_root / 'main.py'
            if main_script.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, str(main_script), '--test-mode'],
                        capture_output=True,
                        text=True,
                        timeout=15,
                        cwd=str(self.project_root)
                    )
                    
                    results['tests_run'] += 1
                    
                    if result.returncode == 0:
                        results['tests_passed'] += 1
                        results['details']['main_app_startup'] = {
                            'status': 'PASSED',
                            'output': result.stdout
                        }
                    else:
                        results['tests_failed'] += 1
                        results['details']['main_app_startup'] = {
                            'status': 'FAILED',
                            'output': result.stdout,
                            'error': result.stderr
                        }
                        results['passed'] = False
                        
                except subprocess.TimeoutExpired:
                    results['tests_failed'] += 1
                    results['details']['main_app_startup'] = {
                        'status': 'TIMEOUT',
                        'error': 'Application startup timed out'
                    }
                    results['passed'] = False
                except Exception as e:
                    results['tests_failed'] += 1
                    results['details']['main_app_startup'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    results['passed'] = False
            
            # Test module imports
            print("  Testing module imports...")
            
            test_modules = [
                'main',
                'ui.main_window',
                'ui.bottom_panel',
                'core.quick_switch',
                'utils.error_handler',
                'api.settings',
                'api.clients'
            ]
            
            for module_name in test_modules:
                try:
                    # Add project root to path
                    sys.path.insert(0, str(self.project_root))
                    
                    start_time = time.time()
                    module = __import__(module_name, fromlist=['*'])
                    import_time = time.time() - start_time
                    
                    results['tests_run'] += 1
                    results['tests_passed'] += 1
                    results['details'][f'import_{module_name}'] = {
                        'status': 'PASSED',
                        'import_time': f"{import_time:.3f}s"
                    }
                    
                except Exception as e:
                    results['tests_run'] += 1
                    results['tests_failed'] += 1
                    results['details'][f'import_{module_name}'] = {
                        'status': 'FAILED',
                        'error': str(e)
                    }
                    results['passed'] = False
            
            print(f"  ✅ Integration tests completed: {results['tests_passed']}/{results['tests_run']} passed")
            
        except Exception as e:
            results['passed'] = False
            results['error'] = str(e)
            print(f"  ❌ Integration tests failed: {str(e)}")
        
        return results
    
    def _run_feature_tests(self) -> Dict[str, Any]:
        """Run feature-specific tests."""
        results = {'passed': True, 'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0, 'details': {}}
        
        try:
            # Test conversation tagging
            print("  Testing conversation tagging...")
            results.update(self._test_conversation_tagging())
            
            # Test command palette
            print("  Testing command palette...")
            results.update(self._test_command_palette())
            
            # Test quick switch
            print("  Testing quick switch...")
            results.update(self._test_quick_switch())
            
            # Test error handling
            print("  Testing error handling...")
            results.update(self._test_error_handling())
            
            print(f"  ✅ Feature tests completed: {results['tests_passed']}/{results['tests_run']} passed")
            
        except Exception as e:
            results['passed'] = False
            results['error'] = str(e)
            print(f"  ❌ Feature tests failed: {str(e)}")
        
        return results
    
    def _test_conversation_tagging(self) -> Dict[str, Any]:
        """Test conversation tagging functionality."""
        results = {'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0}
        
        try:
            # Test tag manager
            sys.path.insert(0, str(self.project_root))
            
            # Test basic tag operations
            test_script = """
import sys
sys.path.insert(0, '.')

try:
    from ui.conversation_tagging import TagManager
    from ui.conversation_tagging import ConversationTagWidget
    
    # Test tag manager
    tag_manager = TagManager()
    tag_manager.add_tag("test_tag", "#FF0000")
    tags = tag_manager.get_all_tags()
    
    if "test_tag" in tags:
        print("Tag manager test: PASSED")
    else:
        print("Tag manager test: FAILED")
        
    # Test conversation tag widget
    widget = ConversationTagWidget()
    widget.set_tags(["test_tag"])
    current_tags = widget.get_tags()
    
    if "test_tag" in current_tags:
        print("Conversation tag widget test: PASSED")
    else:
        print("Conversation tag widget test: FAILED")
        
except Exception as e:
    print(f"Conversation tagging test failed: {e}")
"""
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            results['tests_run'] += 1
            
            if result.returncode == 0 and 'PASSED' in result.stdout:
                results['tests_passed'] += 1
            else:
                results['tests_failed'] += 1
                
        except Exception as e:
            results['tests_failed'] += 1
        
        return results
    
    def _test_command_palette(self) -> Dict[str, Any]:
        """Test command palette functionality."""
        results = {'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0}
        
        try:
            test_script = """
import sys
sys.path.insert(0, '.')

try:
    from ui.command_palette import CommandPalette
    
    # Test command palette
    palette = CommandPalette()
    palette.register_command("test_command", "Test Command", lambda: None)
    commands = palette.get_commands()
    
    if "test_command" in commands:
        print("Command palette test: PASSED")
    else:
        print("Command palette test: FAILED")
        
except Exception as e:
    print(f"Command palette test failed: {e}")
"""
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            results['tests_run'] += 1
            
            if result.returncode == 0 and 'PASSED' in result.stdout:
                results['tests_passed'] += 1
            else:
                results['tests_failed'] += 1
                
        except Exception as e:
            results['tests_failed'] += 1
        
        return results
    
    def _test_quick_switch(self) -> Dict[str, Any]:
        """Test quick switch functionality."""
        results = {'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0}
        
        try:
            test_script = """
import sys
sys.path.insert(0, '.')

try:
    from core.quick_switch import QuickSwitchModelMenu
    
    # Test quick switch
    quick_switch = QuickSwitchModelMenu()
    quick_switch.add_model("test_model", "Test Model", "test_provider")
    models = quick_switch.get_available_models()
    
    if "test_model" in models:
        print("Quick switch test: PASSED")
    else:
        print("Quick switch test: FAILED")
        
except Exception as e:
    print(f"Quick switch test failed: {e}")
"""
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            results['tests_run'] += 1
            
            if result.returncode == 0 and 'PASSED' in result.stdout:
                results['tests_passed'] += 1
            else:
                results['tests_failed'] += 1
                
        except Exception as e:
            results['tests_failed'] += 1
        
        return results
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling functionality."""
        results = {'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0}
        
        try:
            test_script = """
import sys
sys.path.insert(0, '.')

try:
    from utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory
    
    # Test error handler
    error_handler = ErrorHandler()
    error_handler.log_error("Test error", ErrorSeverity.ERROR, ErrorCategory.GENERAL)
    
    print("Error handling test: PASSED")
        
except Exception as e:
    print(f"Error handling test failed: {e}")
"""
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            results['tests_run'] += 1
            
            if result.returncode == 0 and 'PASSED' in result.stdout:
                results['tests_passed'] += 1
            else:
                results['tests_failed'] += 1
                
        except Exception as e:
            results['tests_failed'] += 1
        
        return results
    
    def _run_gui_tests(self) -> Dict[str, Any]:
        """Run GUI tests."""
        results = {'passed': True, 'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0, 'details': {}}
        
        try:
            # Test GUI components without displaying
            print("  Testing GUI components...")
            
            test_script = """
import sys
sys.path.insert(0, '.')

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    
    # Create application
    app = QApplication([])
    
    # Test main window creation
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    # Test bottom panel
    from ui.bottom_panel import BottomSlidingPanel
    panel = BottomSlidingPanel()
    
    # Test quick switch widget
    from ui.quick_switch_widget import QuickSwitchWidget
    widget = QuickSwitchWidget()
    
    # Test command palette
    from ui.command_palette import CommandPalette
    palette = CommandPalette()
    
    print("GUI components test: PASSED")
    
    # Close after a short delay
    QTimer.singleShot(100, app.quit)
    app.exec()
    
except Exception as e:
    print(f"GUI test failed: {e}")
"""
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            results['tests_run'] += 1
            
            if result.returncode == 0 and 'PASSED' in result.stdout:
                results['tests_passed'] += 1
                results['details']['gui_components'] = {
                    'status': 'PASSED',
                    'output': result.stdout
                }
            else:
                results['tests_failed'] += 1
                results['details']['gui_components'] = {
                    'status': 'FAILED',
                    'output': result.stdout,
                    'error': result.stderr
                }
                results['passed'] = False
            
            print(f"  ✅ GUI tests completed: {results['tests_passed']}/{results['tests_run']} passed")
            
        except Exception as e:
            results['passed'] = False
            results['error'] = str(e)
            print(f"  ❌ GUI tests failed: {str(e)}")
        
        return results
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        results = {'passed': True, 'tests_run': 0, 'tests_passed': 0, 'tests_failed': 0, 'details': {}}
        
        try:
            print("  Testing import performance...")
            
            # Test import performance
            test_modules = [
                'ui.main_window',
                'ui.bottom_panel',
                'core.quick_switch',
                'utils.error_handler',
                'api.settings'
            ]
            
            for module_name in test_modules:
                try:
                    sys.path.insert(0, str(self.project_root))
                    
                    start_time = time.time()
                    module = __import__(module_name, fromlist=['*'])
                    import_time = time.time() - start_time
                    
                    results['tests_run'] += 1
                    results['tests_passed'] += 1
                    
                    # Performance threshold: 2 seconds
                    if import_time < 2.0:
                        results['details'][f'{module_name}_import'] = {
                            'status': 'PASSED',
                            'time': f"{import_time:.3f}s"
                        }
                    else:
                        results['tests_failed'] += 1
                        results['details'][f'{module_name}_import'] = {
                            'status': 'SLOW',
                            'time': f"{import_time:.3f}s"
                        }
                        results['passed'] = False
                        
                except Exception as e:
                    results['tests_run'] += 1
                    results['tests_failed'] += 1
                    results['details'][f'{module_name}_import'] = {
                        'status': 'FAILED',
                        'error': str(e)
                    }
                    results['passed'] = False
            
            print(f"  ✅ Performance tests completed: {results['tests_passed']}/{results['tests_run']} passed")
            
        except Exception as e:
            results['passed'] = False
            results['error'] = str(e)
            print(f"  ❌ Performance tests failed: {str(e)}")
        
        return results
    
    def _generate_test_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_test_categories': len(results),
                'passed_categories': sum(1 for r in results.values() if r.get('passed', False)),
                'failed_categories': sum(1 for r in results.values() if not r.get('passed', True)),
                'total_tests_run': sum(r.get('tests_run', 0) for r in results.values()),
                'total_tests_passed': sum(r.get('tests_passed', 0) for r in results.values()),
                'total_tests_failed': sum(r.get('tests_failed', 0) for r in results.values())
            },
            'detailed_results': results,
            'recommendations': []
        }
        
        # Calculate pass rate
        total_tests = report['summary']['total_tests_run']
        if total_tests > 0:
            pass_rate = (report['summary']['total_tests_passed'] / total_tests) * 100
            report['summary']['pass_rate'] = f"{pass_rate:.1f}%"
        else:
            report['summary']['pass_rate'] = "0.0%"
        
        # Generate recommendations
        if report['summary']['failed_categories'] > 0:
            report['recommendations'].append("Some test categories failed - review detailed results")
        
        if report['summary']['total_tests_failed'] > 0:
            report['recommendations'].append(f"Found {report['summary']['total_tests_failed']} failed tests - review and fix")
        
        if pass_rate < 80:
            report['recommendations'].append(f"Low pass rate ({pass_rate:.1f}%) - investigate failing tests")
        
        # Save report
        report_file = self.test_reports_dir / 'comprehensive_test_report.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print(f"\n📊 Test Report Summary:")
        print(f"   Categories: {report['summary']['passed_categories']}/{report['summary']['total_test_categories']} passed")
        print(f"   Tests: {report['summary']['total_tests_passed']}/{report['summary']['total_tests_run']} passed")
        print(f"   Pass Rate: {report['summary']['pass_rate']}")
        print(f"   Report saved to: {report_file}")
        
        return report

def run_automated_tests():
    """Main function to run automated tests."""
    runner = AutomatedTestRunner()
    return runner.run_all_tests()

if __name__ == '__main__':
    run_automated_tests() 
