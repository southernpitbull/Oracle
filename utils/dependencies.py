"""
Dependencies management and installation utilities.
"""

import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)


def add_python_to_path():
    """Add Python directories to system PATH if they're not already present"""
    python_paths = [
        r"C:\Users\PC\AppData\Local\Programs\Python\Python310\python.exe",
        r"C:\Users\PC\AppData\Local\Programs\Python\Python310\Scripts"
    ]
    
    # Get current PATH
    current_path = os.environ.get('PATH', '')
    path_dirs = current_path.split(os.pathsep)
    
    # Check and add each Python path
    paths_added = []
    for python_path in python_paths:
        # For the python.exe path, we need the directory
        if python_path.endswith('python.exe'):
            python_dir = os.path.dirname(python_path)
        else:
            python_dir = python_path
            
        if python_dir not in path_dirs:
            path_dirs.append(python_dir)
            paths_added.append(python_dir)
    
    # Update PATH if we added anything
    if paths_added:
        new_path = os.pathsep.join(path_dirs)
        os.environ['PATH'] = new_path
        
        # Also try to update the system PATH permanently on Windows
        if os.name == 'nt':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_SET_VALUE) as key:
                    current_user_path = winreg.QueryValueEx(key, 'PATH')[0]
                    user_path_dirs = current_user_path.split(os.pathsep)
                    
                    # Add paths to user PATH if not present
                    user_paths_added = []
                    for path in paths_added:
                        if path not in user_path_dirs:
                            user_path_dirs.append(path)
                            user_paths_added.append(path)
                    
                    if user_paths_added:
                        new_user_path = os.pathsep.join(user_path_dirs)
                        winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_user_path)
                        print(f"Added to user PATH: {', '.join(user_paths_added)}")
                        
            except Exception as e:
                print(f"Could not update system PATH permanently: {e}")
        
        print(f"Added to session PATH: {', '.join(paths_added)}")
    else:
        print("Python paths already in PATH")


def check_and_install_dependencies():
    """Check and install required dependencies"""
    required = {
        'customtkinter',
        'sentence-transformers',
        'torch',
        'networkx',
        'ollama',
        'pandas',
        'seaborn',
        'matplotlib',
        'wordcloud',
        'python-docx',
        'markdown',
        'rich',
        'Pillow',
        'transformers',
        'PyQt6',
        'pygments',
        'numpy'
    }
    
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing = required - installed
    except ImportError:
        # If pkg_resources is not available, just try to install all packages
        print("pkg_resources not available, attempting to install all dependencies...")
        missing = required

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Installing missing packages...")
        python = sys.executable
        try:
            subprocess.check_call([python, '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)
            print("All missing packages installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            print("Please install the dependencies manually with:")
            print(f"pip install {' '.join(missing)}")
            # Don't exit, let the user continue with available packages
    
    # Re-import the modules after installation (if needed)
    try:
        import re
        import html
        try:
            import pkg_resources
        except ImportError:
            pass
        try:
            import networkx as nx
        except ImportError:
            pass
        try:
            import numpy as np
        except ImportError:
            pass
    except ImportError as e:
        print(f"Some dependencies are still missing: {e}")
        print("The application will run with limited functionality.")
