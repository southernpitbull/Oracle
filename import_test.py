#!/usr/bin/env python3
"""
Import Test
File: import_test.py
Author: AI Assistant
Date: 2024-12-19

This script tests all critical imports to verify they work correctly.
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_import(module_name, class_name=None):
    """Test importing a module and optionally a class."""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        if class_name:
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name}")
                return True
            else:
                print(f"❌ {module_name}.{class_name} - Class not found")
                return False
        else:
            print(f"✅ {module_name}")
            return True
    except ImportError as e:
        print(f"❌ {module_name} - Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ {module_name} - Unexpected error: {e}")
        return False

def main():
    """Test all critical imports."""
    print("🔍 TESTING ALL CRITICAL IMPORTS")
    print("=" * 50)
    
    # Test PyQt6 imports
    print("\n🎨 PyQt6 Imports:")
    pyqt6_tests = [
        ("PyQt6.QtWidgets", "QApplication"),
        ("PyQt6.QtWidgets", "QMainWindow"),
        ("PyQt6.QtWidgets", "QWidget"),
        ("PyQt6.QtGui", "QAction"),
        ("PyQt6.QtGui", "QShortcut"),
        ("PyQt6.QtGui", "QKeySequence"),
        ("PyQt6.QtGui", "QFont"),
        ("PyQt6.QtCore", "Qt"),
        ("PyQt6.QtCore", "pyqtSignal"),
        ("PyQt6.QtCore", "QTimer"),
    ]
    
    pyqt6_success = 0
    for module, class_name in pyqt6_tests:
        if test_import(module, class_name):
            pyqt6_success += 1
    
    # Test application module imports
    print("\n🏗️ Application Module Imports:")
    app_tests = [
        ("ui.main_window", "MainWindow"),
        ("utils.error_handler", "ErrorHandler"),
        ("utils.error_handler", "ErrorSeverity"),
        ("utils.error_handler", "ErrorCategory"),
        ("utils.dependencies", "log"),
        ("core.quick_switch", "QuickSwitchModelMenu"),
        ("ui.conversation_tagging", "TagManager"),
        ("ui.conversation_tagging", "ConversationTagWidget"),
        ("ui.conversation_tagging", "TagManagerWidget"),
        ("ui.command_palette", "CommandPaletteManager"),
        ("ui.command_palette", "CommandPaletteDialog"),
        ("core.last_read_marker", "LastReadMarker"),
        ("ui.last_read_marker_widget", "LastReadMarkerDialog"),
    ]
    
    app_success = 0
    for module, class_name in app_tests:
        if test_import(module, class_name):
            app_success += 1
    
    # Test basic Python imports
    print("\n🐍 Basic Python Imports:")
    basic_tests = [
        ("os", None),
        ("sys", None),
        ("json", None),
        ("datetime", None),
        ("pathlib", "Path"),
        ("typing", "List"),
        ("re", None),
        ("uuid", None),
    ]
    
    basic_success = 0
    for module, class_name in basic_tests:
        if test_import(module, class_name):
            basic_success += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 IMPORT TEST RESULTS")
    print(f"PyQt6 Imports: {pyqt6_success}/{len(pyqt6_tests)}")
    print(f"Application Imports: {app_success}/{len(app_tests)}")
    print(f"Basic Python Imports: {basic_success}/{len(basic_tests)}")
    
    total_tests = len(pyqt6_tests) + len(app_tests) + len(basic_tests)
    total_success = pyqt6_success + app_success + basic_success
    
    print(f"\nOverall: {total_success}/{total_tests} imports successful")
    
    if total_success == total_tests:
        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        print("The application should work correctly.")
        return True
    else:
        print(f"\n⚠️ {total_tests - total_success} imports failed.")
        print("Please check the failed imports above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
