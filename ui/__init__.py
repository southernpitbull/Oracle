"""
Simple UI module initialization
"""

try:
    from .chat_app import ChatApp
    __all__ = ['ChatApp']
except ImportError as e:
    print(f"Error importing ChatApp: {e}")
    ChatApp = None
    __all__ = []
