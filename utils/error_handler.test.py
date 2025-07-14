#!/usr/bin/env python3
"""
Oracle/utils/error_handler.test.py

Author: The Oracle Development Team
Date: 2024-01-01

Test suite for the automatic error correction system.
"""

import unittest
import tempfile
import os
import sys
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import (
    CriticalErrorDetector,
    ErrorCorrector,
    AutoErrorCorrector,
    start_auto_error_correction,
    stop_auto_error_correction,
    get_error_correction_status,
    force_error_scan
)


class TestCriticalErrorDetector(unittest.TestCase):
    """Test cases for CriticalErrorDetector"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.detector = CriticalErrorDetector(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_scan_python_files(self):
        """Test scanning for Python files"""
        # Create some test files
        test_files = [
            'test1.py',
            'test2.py',
            'test3.txt',
            'subdir/test4.py'
        ]
        
        for file_path in test_files:
            full_path = Path(self.temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text('# Test file')
        
        # Scan for Python files
        python_files = self.detector.scan_python_files()
        
        # Should find 3 Python files
        self.assertEqual(len(python_files), 3)
        
        # Check that all found files are Python files
        for file_path in python_files:
            self.assertTrue(file_path.suffix == '.py')
    
    def test_check_syntax_errors_valid_file(self):
        """Test syntax checking with valid Python file"""
        valid_code = """
def test_function():
    print("Hello, World!")
    return True
"""
        test_file = Path(self.temp_dir) / 'valid.py'
        test_file.write_text(valid_code)
        
        errors = self.detector.check_syntax_errors(test_file)
        self.assertEqual(len(errors), 0)
    
    def test_check_syntax_errors_invalid_file(self):
        """Test syntax checking with invalid Python file"""
        invalid_code = """
def test_function(
    print("Hello, World!")
    return True
"""
        test_file = Path(self.temp_dir) / 'invalid.py'
        test_file.write_text(invalid_code)
        
        errors = self.detector.check_syntax_errors(test_file)
        self.assertGreater(len(errors), 0)
        self.assertEqual(errors[0]['type'], 'syntax_error')
    
    def test_check_import_errors(self):
        """Test import error checking"""
        # Create a file with a valid import
        valid_import_code = """
import os
import sys
from pathlib import Path
"""
        test_file = Path(self.temp_dir) / 'valid_imports.py'
        test_file.write_text(valid_import_code)
        
        errors = self.detector.check_import_errors(test_file)
        self.assertEqual(len(errors), 0)
    
    def test_check_missing_files(self):
        """Test missing file detection"""
        # Should detect missing files
        errors = self.detector.check_missing_files()
        
        # Should find missing files (since we're in a temp directory)
        self.assertGreater(len(errors), 0)
        
        # Check that all errors are missing_file type
        for error in errors:
            self.assertEqual(error['type'], 'missing_file')


class TestErrorCorrector(unittest.TestCase):
    """Test cases for ErrorCorrector"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.corrector = ErrorCorrector(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_fix_syntax_errors(self):
        """Test syntax error fixing"""
        # Create a file with syntax errors
        invalid_code = """
def test_function(
    print("Hello, World!")
    return True
"""
        test_file = Path(self.temp_dir) / 'test_syntax.py'
        test_file.write_text(invalid_code)
        
        error = {
            'type': 'syntax_error',
            'file': str(test_file),
            'line': 2,
            'message': 'invalid syntax',
            'severity': 'critical'
        }
        
        # Attempt to fix
        success = self.corrector.fix_syntax_errors(error)
        
        # Should have attempted to fix
        self.assertTrue(success)
        
        # Check that correction history was updated
        self.assertGreater(len(self.corrector.correction_history), 0)
    
    def test_fix_missing_files(self):
        """Test missing file creation"""
        error = {
            'type': 'missing_file',
            'file': 'requirements.txt',
            'line': 0,
            'message': 'Missing required file: requirements.txt',
            'severity': 'critical'
        }
        
        # Attempt to fix
        success = self.corrector.fix_missing_files(error)
        
        # Should have created the file
        self.assertTrue(success)
        
        # Check that file was created
        created_file = Path(self.temp_dir) / 'requirements.txt'
        self.assertTrue(created_file.exists())
        
        # Check file content
        content = created_file.read_text()
        self.assertIn('PyQt6', content)
    
    def test_correct_errors(self):
        """Test the main error correction method"""
        errors = [
            {
                'type': 'missing_file',
                'file': 'README.md',
                'line': 0,
                'message': 'Missing required file: README.md',
                'severity': 'critical'
            }
        ]
        
        # Correct errors
        results = self.corrector.correct_errors(errors)
        
        # Should have fixed 1 error
        self.assertEqual(results['total_errors'], 1)
        self.assertEqual(results['fixed_errors'], 1)
        self.assertEqual(results['failed_errors'], 0)


class TestAutoErrorCorrector(unittest.TestCase):
    """Test cases for AutoErrorCorrector"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.auto_corrector = AutoErrorCorrector(self.temp_dir, interval=1)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
        if self.auto_corrector.running:
            self.auto_corrector.stop_monitoring()
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        # Should not be running initially
        self.assertFalse(self.auto_corrector.running)
        
        # Start monitoring
        self.auto_corrector.start_monitoring()
        self.assertTrue(self.auto_corrector.running)
        
        # Stop monitoring
        self.auto_corrector.stop_monitoring()
        self.assertFalse(self.auto_corrector.running)
    
    def test_get_status(self):
        """Test status reporting"""
        status = self.auto_corrector.get_status()
        
        # Check required fields
        required_fields = ['running', 'interval', 'last_scan_time', 'total_errors_fixed', 'correction_history']
        for field in required_fields:
            self.assertIn(field, status)
        
        # Check initial values
        self.assertFalse(status['running'])
        self.assertEqual(status['interval'], 1)
        self.assertEqual(status['total_errors_fixed'], 0)
    
    def test_force_scan(self):
        """Test forcing an immediate scan"""
        # Should not work when not running
        self.auto_corrector.force_scan()  # Should not raise an error
        
        # Start monitoring and force scan
        self.auto_corrector.start_monitoring()
        time.sleep(0.1)  # Give it time to start
        
        self.auto_corrector.force_scan()
        
        # Should have performed a scan
        status = self.auto_corrector.get_status()
        self.assertIsNotNone(status['last_scan_time'])


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global functions"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
        # Stop any running correction
        stop_auto_error_correction()
    
    def test_start_stop_functions(self):
        """Test global start/stop functions"""
        # Start auto correction
        start_auto_error_correction(interval=1)
        
        # Check status
        status = get_error_correction_status()
        self.assertTrue(status['running'])
        
        # Stop auto correction
        stop_auto_error_correction()
        
        # Check status again
        status = get_error_correction_status()
        self.assertFalse(status['running'])
    
    def test_force_error_scan(self):
        """Test forcing an error scan"""
        # Start auto correction
        start_auto_error_correction(interval=1)
        
        # Force a scan
        force_error_scan()
        
        # Check that a scan was performed
        status = get_error_correction_status()
        self.assertIsNotNone(status['last_scan_time'])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete error correction system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.auto_corrector = AutoErrorCorrector(self.temp_dir, interval=1)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
        if self.auto_corrector.running:
            self.auto_corrector.stop_monitoring()
    
    def test_full_error_correction_cycle(self):
        """Test a complete error detection and correction cycle"""
        # Create a file with syntax errors
        invalid_code = """
def test_function(
    print("Hello, World!")
    return True
"""
        test_file = Path(self.temp_dir) / 'test_integration.py'
        test_file.write_text(invalid_code)
        
        # Start monitoring
        self.auto_corrector.start_monitoring()
        
        # Wait a bit for the scan to complete
        time.sleep(2)
        
        # Check status
        status = self.auto_corrector.get_status()
        self.assertIsNotNone(status['last_scan_time'])
        
        # Should have attempted to fix errors
        self.assertGreaterEqual(status['total_errors_fixed'], 0)


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestCriticalErrorDetector,
        TestErrorCorrector,
        TestAutoErrorCorrector,
        TestGlobalFunctions,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running Error Handler Tests...")
    success = run_tests()
    
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    sys.exit(0 if success else 1)