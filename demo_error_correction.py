#!/usr/bin/env python3
"""
Oracle/demo_error_correction.py

Author: The Oracle Development Team
Date: 2024-01-01

Demonstration script for the automatic error correction system.
This script shows how the system detects and fixes critical errors.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.error_handler import (
    CriticalErrorDetector,
    ErrorCorrector,
    AutoErrorCorrector,
    start_auto_error_correction,
    stop_auto_error_correction,
    get_error_correction_status,
    force_error_scan
)


def create_test_files_with_errors(temp_dir):
    """Create test files with various errors to demonstrate the system"""
    print("🔧 Creating test files with errors...")
    
    # Create a file with syntax errors
    syntax_error_file = temp_dir / "syntax_error.py"
    syntax_error_content = """
def test_function(
    print("Hello, World!")
    return True
"""
    syntax_error_file.write_text(syntax_error_content)
    print(f"   Created {syntax_error_file} with syntax error")
    
    # Create a file with import errors
    import_error_file = temp_dir / "import_error.py"
    import_error_content = """
import nonexistent_module
from another_nonexistent_module import some_function
"""
    import_error_file.write_text(import_error_content)
    print(f"   Created {import_error_file} with import errors")
    
    # Create a file with indentation errors
    indentation_error_file = temp_dir / "indentation_error.py"
    indentation_error_content = """
def test_function():
print("Wrong indentation")
    return True
"""
    indentation_error_file.write_text(indentation_error_content)
    print(f"   Created {indentation_error_file} with indentation error")
    
    print("✅ Test files created successfully!")


def demonstrate_error_detection():
    """Demonstrate error detection capabilities"""
    print("\n" + "="*60)
    print("🔍 DEMONSTRATION: Error Detection")
    print("="*60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with errors
        create_test_files_with_errors(temp_path)
        
        # Initialize error detector
        detector = CriticalErrorDetector(str(temp_path))
        
        # Detect all errors
        print("\n🔍 Scanning for errors...")
        errors = detector.detect_all_errors()
        
        if errors:
            print(f"\n⚠️  Found {len(errors)} critical errors:")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error['type']} in {error['file']}: {error['message']}")
        else:
            print("✅ No errors detected!")
        
        return errors


def demonstrate_error_correction():
    """Demonstrate error correction capabilities"""
    print("\n" + "="*60)
    print("🔧 DEMONSTRATION: Error Correction")
    print("="*60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with errors
        create_test_files_with_errors(temp_path)
        
        # Initialize error detector and corrector
        detector = CriticalErrorDetector(str(temp_path))
        corrector = ErrorCorrector(str(temp_path))
        
        # Detect errors
        print("\n🔍 Detecting errors...")
        errors = detector.detect_all_errors()
        
        if errors:
            print(f"\n⚠️  Found {len(errors)} errors, attempting to fix...")
            
            # Attempt to correct errors
            results = corrector.correct_errors(errors)
            
            print(f"\n📊 Correction Results:")
            print(f"   Total errors: {results['total_errors']}")
            print(f"   Fixed: {results['fixed_errors']}")
            print(f"   Failed: {results['failed_errors']}")
            
            # Show correction history
            if corrector.correction_history:
                print(f"\n📝 Recent corrections:")
                for correction in corrector.correction_history[-5:]:  # Last 5
                    timestamp = correction['timestamp'].strftime('%H:%M:%S')
                    print(f"   [{timestamp}] {correction['action']} in {correction['file']}")
            
            # Re-scan to see if errors were fixed
            print(f"\n🔍 Re-scanning after corrections...")
            remaining_errors = detector.detect_all_errors()
            
            if remaining_errors:
                print(f"⚠️  {len(remaining_errors)} errors remain:")
                for error in remaining_errors:
                    print(f"   - {error['type']} in {error['file']}: {error['message']}")
            else:
                print("✅ All errors have been fixed!")
        else:
            print("✅ No errors to fix!")


def demonstrate_auto_correction():
    """Demonstrate automatic error correction system"""
    print("\n" + "="*60)
    print("🤖 DEMONSTRATION: Automatic Error Correction")
    print("="*60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with errors
        create_test_files_with_errors(temp_path)
        
        # Initialize auto corrector
        auto_corrector = AutoErrorCorrector(str(temp_path), interval=5)  # 5 second interval
        
        print("\n🚀 Starting automatic error correction...")
        auto_corrector.start_monitoring()
        
        # Let it run for a few cycles
        print("⏳ Running for 15 seconds (3 scan cycles)...")
        for i in range(15):
            time.sleep(1)
            if i % 5 == 0:
                status = auto_corrector.get_status()
                print(f"   [{i}s] Status: {'Running' if status['running'] else 'Stopped'}, "
                      f"Fixed: {status['total_errors_fixed']}")
        
        # Stop monitoring
        print("\n🛑 Stopping automatic error correction...")
        auto_corrector.stop_monitoring()
        
        # Show final status
        final_status = auto_corrector.get_status()
        print(f"\n📊 Final Status:")
        print(f"   Running: {final_status['running']}")
        print(f"   Total errors fixed: {final_status['total_errors_fixed']}")
        print(f"   Last scan: {final_status['last_scan_time']}")
        
        # Show correction history
        if final_status['correction_history']:
            print(f"\n📝 Correction History:")
            for correction in final_status['correction_history']:
                timestamp = correction['timestamp'].strftime('%H:%M:%S')
                print(f"   [{timestamp}] {correction['action']} in {correction['file']}")


def demonstrate_global_functions():
    """Demonstrate global error correction functions"""
    print("\n" + "="*60)
    print("🌐 DEMONSTRATION: Global Functions")
    print("="*60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with errors
        create_test_files_with_errors(temp_path)
        
        print("\n🚀 Starting global auto correction...")
        start_auto_error_correction(interval=3)  # 3 second interval
        
        # Check status
        status = get_error_correction_status()
        print(f"   Status: {'Running' if status['running'] else 'Stopped'}")
        print(f"   Interval: {status['interval']} seconds")
        
        # Force a scan
        print("\n🔍 Forcing immediate scan...")
        force_error_scan()
        
        # Wait a bit
        time.sleep(2)
        
        # Check status again
        status = get_error_correction_status()
        print(f"   Total errors fixed: {status['total_errors_fixed']}")
        print(f"   Last scan: {status['last_scan_time']}")
        
        # Stop
        print("\n🛑 Stopping global auto correction...")
        stop_auto_error_correction()
        
        # Final status
        status = get_error_correction_status()
        print(f"   Final status: {'Running' if status['running'] else 'Stopped'}")


def main():
    """Main demonstration function"""
    print("🔧 Oracle Automatic Error Correction System")
    print("=" * 60)
    print("This demonstration shows the automatic error correction")
    print("system detecting and fixing critical errors in real-time.")
    print()
    
    try:
        # Demonstrate error detection
        demonstrate_error_detection()
        
        # Demonstrate error correction
        demonstrate_error_correction()
        
        # Demonstrate automatic correction
        demonstrate_auto_correction()
        
        # Demonstrate global functions
        demonstrate_global_functions()
        
        print("\n" + "="*60)
        print("✅ DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nThe automatic error correction system is now ready to:")
        print("• Continuously monitor your codebase for critical errors")
        print("• Automatically fix syntax errors, import issues, and missing files")
        print("• Provide real-time status updates and correction history")
        print("• Run every 60 seconds while the application is open")
        print("\nAccess the GUI via: Tools → Error Correction System (Ctrl+Shift+E)")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()