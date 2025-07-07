#!/usr/bin/env python3
"""
Test script to verify The Oracle setup is working properly.
"""

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    try:
        # Test PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        print("✅ PyQt6 - OK")
    except ImportError as e:
        print(f"❌ PyQt6 - FAILED: {e}")
        return False
    
    try:
        # Test core modules
        import core.config
        print("✅ Core config - OK")
    except ImportError as e:
        print(f"❌ Core config - FAILED: {e}")
        return False
    
    try:
        # Test API modules
        from api.multi_provider import MultiProviderClient
        print("✅ API modules - OK")
    except ImportError as e:
        print(f"❌ API modules - FAILED: {e}")
        return False
    
    try:
        # Test UI modules
        from ui.chat_app import ChatApp
        print("✅ UI modules - OK")
    except ImportError as e:
        print(f"❌ UI modules - FAILED: {e}")
        return False
    
    try:
        # Test utilities
        import utils.file_utils
        import utils.formatting
        print("✅ Utility modules - OK")
    except ImportError as e:
        print(f"❌ Utility modules - FAILED: {e}")
        return False
    
    return True

def test_optional_dependencies():
    """Test optional dependencies"""
    print("\n🔍 Testing optional dependencies...")
    
    # Test Rich
    try:
        from rich.console import Console
        print("✅ Rich - OK")
    except ImportError:
        print("⚠️ Rich - Not available (optional)")
    
    # Test Markdown
    try:
        import markdown
        print("✅ Markdown - OK")
    except ImportError:
        print("⚠️ Markdown - Not available (optional)")
    
    # Test Keyring
    try:
        import keyring
        print("✅ Keyring - OK")
    except ImportError:
        print("⚠️ Keyring - Not available (optional)")

if __name__ == "__main__":
    print("🚀 Testing The Oracle setup...\n")
    
    if test_imports():
        print("\n✅ All critical imports successful!")
        test_optional_dependencies()
        print("\n🎉 The Oracle is ready to run!")
        print("\n💡 To start the application, run:")
        print("   python main.py")
    else:
        print("\n❌ Some critical imports failed. Please check the errors above.")
