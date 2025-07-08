#!/usr/bin/env python3
"""
The Oracle - A sophisticated AI chat application with multi-provider support.

This is the main entry point for the modular version of The Oracle application.
The application has been split into several modules for better maintainability:

- core/: Core functionality (config, evaluator, knowledge graph)
- api/: API clients and multi-provider management
- ui/: User interface components
- utils/: Utility functions and helpers
"""

import os
import sys
import logging
import json
import webbrowser
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QTextEdit, QScrollArea, QWidget, QFrame, QApplication,
                           QMessageBox, QInputDialog, QMenu, QListWidgetItem,
                           QFileDialog, QCheckBox, QSpinBox, QComboBox, QTabWidget,
                           QGridLayout, QGroupBox, QSlider, QLineEdit, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QSettings, QSize
from PyQt6.QtGui import QDesktopServices, QFont, QPixmap, QIcon, QClipboard, QAction, QKeySequence
import subprocess
import platform
# Optional imports with fallbacks
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

import sqlite3
import threading
import asyncio
from functools import partial
import re
import html
import uuid
import hashlib
import shutil
import tempfile
import concurrent.futures
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import utility functions first
from utils.dependencies import add_python_to_path, check_and_install_dependencies

# Add Python to PATH before importing other modules
add_python_to_path()

# Check for GUI framework availability - PyQt6 is already imported at the top
QT_AVAILABLE = True

# Rich imports with fallback
try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    RichHandler = None
    console = None

# Setup logging
if RICH_AVAILABLE and console and RichHandler:
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

logger = logging.getLogger("TheOracle")

# Import our modular components
try:
    from ui.chat_app import ChatApp
    from core.config import *
    from core.evaluator import AIEvaluator
    from core.knowledge_graph import KnowledgeGraph
    from api.multi_provider import MultiProviderClient
    from api.settings import APISettingsDialog
    from utils.file_utils import *
    from utils.formatting import *

    logger.info("Successfully imported all modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print(f"❌ Failed to import required modules: {e}")

    # Show error and exit
    print("Please ensure all modules are properly installed.")
    sys.exit(1)


def setup_application():
    """Set up the application with proper configuration"""
    # Create QApplication instance
    app = QApplication(sys.argv)
    app.setApplicationName("The Oracle")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("TheOracle")
    app.setOrganizationDomain("theoracle.ai")

    # Set application icon if available
    try:
        from PyQt6.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "oracle_app.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except ImportError:
        pass

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    return app


def main():
    """Main entry point for The Oracle application"""
    try:
        logger.info("Starting The Oracle application...")

        # Set up the Qt application
        app = setup_application()

        # Show splash screen
        from ui.splash_screen import show_splash_screen
        splash, loading_thread = show_splash_screen()

        # Process events to show splash screen
        app.processEvents()

        # Wait for loading to complete
        loading_thread.wait()

        # Create main window with enhanced UI
        main_window = ChatApp()

        # Hide splash screen and show main window
        splash.finish(main_window)
        main_window.show()

        logger.info("The Oracle application started successfully")

        # Run the application
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Fatal error in main application: {e}")
        print(f"❌ Fatal error: {e}")
        print("Please check your installation and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
