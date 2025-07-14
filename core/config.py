"""
Configuration and imports module for The Oracle
Handles all dependency imports with fallbacks and path management
"""

import os
import sys
import json
import subprocess
import logging

# Rich imports with fallback
try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    RichHandler = None

# PIL imports with fallback
try:
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Other optional imports
try:
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False

try:
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

try:
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Ollama and ML imports with fallback
try:
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

# Optional imports with fallbacks
try:
    PKG_RESOURCES_AVAILABLE = True
    # For backward compatibility, also try pkg_resources but suppress warnings
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        import pkg_resources
except ImportError:
    PKG_RESOURCES_AVAILABLE = False
    pkg_resources = None

try:
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# API client imports
try:
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        # Fallback to old library
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False

try:
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Qt GUI imports with fallback and error message
QT_AVAILABLE = False
qt_import_error = None
try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                                 QComboBox, QListWidget, QSplitter, QMenuBar, 
                                 QMenu, QStatusBar, QLabel, QCheckBox, QFileDialog,
                                 QMessageBox, QInputDialog, QFrame, QScrollArea,
                                 QTextBrowser, QPlainTextEdit, QTabWidget, QGroupBox,
                                 QGridLayout, QSpinBox, QDoubleSpinBox, QSlider, QDialog,
                                 QDialogButtonBox)
    QT_AVAILABLE = True
except ImportError as e1:
    try:
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                                     QComboBox, QListWidget, QSplitter, QMenuBar, 
                                     QMenu, QStatusBar, QLabel, QCheckBox, QFileDialog,
                                     QMessageBox, QInputDialog, QFrame, QScrollArea,
                                     QTextBrowser, QPlainTextEdit, QTabWidget, QGroupBox,
                                     QGridLayout, QSpinBox, QDoubleSpinBox, QSlider, QDialog,
                                     QDialogButtonBox)
        QT_AVAILABLE = True
    except ImportError as e2:
        try:
            from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                                           QComboBox, QListWidget, QSplitter, QMenuBar, 
                                           QMenu, QStatusBar, QLabel, QCheckBox, QFileDialog,
                                           QMessageBox, QInputDialog, QFrame, QScrollArea,
                                           QTextBrowser, QPlainTextEdit, QTabWidget, QGroupBox,
                                           QGridLayout, QSpinBox, QDoubleSpinBox, QSlider, QDialog,
                                           QDialogButtonBox)
            QT_AVAILABLE = True
        except ImportError as e3:
            try:
                from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                                               QComboBox, QListWidget, QSplitter, QMenuBar, 
                                               QMenu, QStatusBar, QLabel, QCheckBox, QFileDialog,
                                               QMessageBox, QInputDialog, QFrame, QScrollArea,
                                               QTextBrowser, QPlainTextEdit, QTabWidget, QGroupBox,
                                               QGridLayout, QSpinBox, QDoubleSpinBox, QSlider, QDialog,
                                               QDialogButtonBox)
                QT_AVAILABLE = True
            except ImportError as e4:
                qt_import_error = (e1, e2, e3, e4)
                QT_AVAILABLE = False

# Export QSettings if available, else dummy
try:
    from PyQt6.QtCore import QSettings
except ImportError:

    class DummyQSettings:

        def __getattr__(self, name):
            return None

    QSettings = DummyQSettings()

# Export QThread if available, else dummy
try:
    from PyQt6.QtCore import QThread
except ImportError:

    class DummyQThread:

        def __getattr__(self, name):
            return None

    QThread = DummyQThread()

# Export QVBoxLayout if available, else dummy
try:
    from PyQt6.QtWidgets import QVBoxLayout
except ImportError:

    class DummyQVBoxLayout:

        def __getattr__(self, name):
            return None

    QVBoxLayout = DummyQVBoxLayout()


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
    # (No re-imports needed; removed empty try-except blocks)


def setup_logging():
    """Setup logging configuration"""
    if RICH_AVAILABLE:
        console = Console()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                RichHandler(rich_tracebacks=True, console=console),
                logging.FileHandler("app.log")
            ]
        )
    else:
        # Fallback to standard logging if Rich is not available
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("app.log")
            ]
        )
    return logging.getLogger("TheOracle")


def setup_directories():
    """Setup required directories"""
    ATTACHMENTS_DIR = "attachments"
    EXPORTS_DIR = "exports"
    MEMORY_DB = "memory.db"
    
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(ATTACHMENTS_DIR, "user"), exist_ok=True)
    os.makedirs(os.path.join(ATTACHMENTS_DIR, "assistant"), exist_ok=True)
    
    return ATTACHMENTS_DIR, EXPORTS_DIR, MEMORY_DB


def check_qt_availability():
    """Check if Qt is available and exit if not"""
    if not QT_AVAILABLE:
        print("\n❌ No supported Qt GUI framework (PyQt6, PyQt5, PySide6, PySide2) is installed!")
        print("Please install one of: PyQt6, PyQt5, PySide6, or PySide2.")
        print("Error details:")
        for err in qt_import_error:
            print(f"  - {err}")
        sys.exit(1)


# Feature flags dictionary for easier management
FEATURES = {
    'rich': RICH_AVAILABLE,
    'pil': PIL_AVAILABLE,
    'markdown': MARKDOWN_AVAILABLE,
    'docx': DOCX_AVAILABLE,
    'wordcloud': WORDCLOUD_AVAILABLE,
    'plotting': PLOTTING_AVAILABLE,
    'transformers': TRANSFORMERS_AVAILABLE,
    'ollama': OLLAMA_AVAILABLE,
    'sentence_transformers': SENTENCE_TRANSFORMERS_AVAILABLE,
    'pygments': PYGMENTS_AVAILABLE,
    'pkg_resources': PKG_RESOURCES_AVAILABLE,
    'networkx': NETWORKX_AVAILABLE,
    'numpy': NUMPY_AVAILABLE,
    'gemini': GEMINI_AVAILABLE,
    'anthropic': ANTHROPIC_AVAILABLE,
    'openai': OPENAI_AVAILABLE,
    'qt': QT_AVAILABLE
}

def get_feature_status():
    """Get the status of all features"""
    return FEATURES.copy()

def is_feature_available(feature_name):
    """Check if a specific feature is available"""
    return FEATURES.get(feature_name, False)

def get_missing_features():
    """Get list of missing features"""
    return [name for name, available in FEATURES.items() if not available]


# Initialize the configuration
add_python_to_path()
check_qt_availability()
ATTACHMENTS_DIR, EXPORTS_DIR, MEMORY_DB = setup_directories()


class Config:
    """Configuration management class for The Oracle application."""
    
    def __init__(self, config_file: str=None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or "settings.json"
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from file or return defaults."""
        default_settings = {
            "api": {
                "openai_key": "",
                "anthropic_key": "",
                "gemini_key": "",
                "model": "gpt-3.5-turbo"
            },
            "ui": {
                "theme": "dark",
                "font_size": 12,
                "window_size": [800, 600]
            },
            "features": {
                "auto_save": True,
                "notifications": True,
                "analytics": False
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults
                    self._merge_settings(default_settings, loaded_settings)
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}")
        
        return default_settings
    
    def _merge_settings(self, defaults: dict, loaded: dict):
        """Recursively merge loaded settings with defaults."""
        for key, value in loaded.items():
            if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
                self._merge_settings(defaults[key], value)
            else:
                defaults[key] = value
    
    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
    
    def get(self, key: str, default=None):
        """Get a setting value by key (supports dot notation)."""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value):
        """Set a setting value by key (supports dot notation)."""
        keys = key.split('.')
        current = self.settings
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value


# Export logger at module level for other modules to import
logger = setup_logging()


# Dummy genai object for compatibility
class DummyGenAI:

    def __getattr__(self, name):
        return None


genai = DummyGenAI()

# Export nx (networkx) if available, else dummy
try:
    import networkx as nx
except ImportError:

    class DummyNX:

        def __getattr__(self, name):
            return None

    nx = DummyNX()

# Export anthropic if available, else dummy
try:
    import anthropic
except ImportError:

    class DummyAnthropic:

        def __getattr__(self, name):
            return None

    anthropic = DummyAnthropic()

# Export openai if available, else dummy
try:
    import openai
except ImportError:

    class DummyOpenAI:

        def __getattr__(self, name):
            return None

    openai = DummyOpenAI()
