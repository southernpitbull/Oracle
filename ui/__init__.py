"""
Simple UI module initialization
"""

try:
    __all__ = ['ChatApp']
except ImportError as e:
    print(f"Error importing ChatApp: {e}")
    __all__ = []
