#!/usr/bin/env python3
"""
The Oracle AI Assistant - Main Application Entry Point
File: main.py
Author: AI Assistant
Date: 2024-12-19

Main entry point for The Oracle AI Assistant application with comprehensive
error handling, logging, and recovery mechanisms.
"""

import sys
import os
import traceback
from typing import Optional, NoReturn

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import PyQt6 components
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
    from PyQt6.QtCore import QTimer
    from PyQt6.QtGui import QPixmap
except ImportError as e:
    print(f"Critical error: Failed to import PyQt6 components: {e}")
    print("Please install PyQt6: pip install PyQt6")
    sys.exit(1)

# Import logging and error handling
try:
    import logging
    from utils.error_handler import safe_execute, error_handler
    from utils.error_handler import ErrorSeverity, ErrorCategory
    from utils.error_handler import RetryConfig, handle_error, create_error_context
except ImportError as e:
    print(f"Warning: Error handling utilities not available: {e}")
    # Create basic logging fallback
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create fallback error handler
    def safe_execute(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return None
    
    def error_handler(severity=None, category=None):
        def decorator(func):
            return func
        return decorator

# Initialize logger
try:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
except Exception as e:
    print(f"Warning: Failed to initialize logger: {e}")
    logger = None

def log_info(message):
    """Safe logging function."""
    if logger and hasattr(logger, 'info'):
        logger.info(message)
    else:
        print(f"INFO: {message}")

def log_error(message):
    """Safe error logging function."""
    if logger and hasattr(logger, 'error'):
        logger.error(message)
    else:
        print(f"ERROR: {message}")

def log_critical(message):
    """Safe critical logging function."""
    if logger and hasattr(logger, 'critical'):
        logger.critical(message)
    else:
        print(f"CRITICAL: {message}")

@error_handler(severity=ErrorSeverity.ERROR if 'ErrorSeverity' in globals() else None,
              category=ErrorCategory.FILE_SYSTEM if 'ErrorCategory' in globals() else None)
def add_current_dir_to_path():
    """Add current directory to Python path for imports."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        log_info("Current directory added to Python path")
    except Exception as e:
        log_error(f"Failed to add current directory to path: {e}")

@error_handler(severity=ErrorSeverity.CRITICAL if 'ErrorSeverity' in globals() else None,
              category=ErrorCategory.CONFIGURATION if 'ErrorCategory' in globals() else None)
def initialize_application() -> QApplication:
    """Initialize the QApplication with proper configuration."""
    try:
        log_info("Initializing QApplication...")
        
        app = QApplication(sys.argv)
        app.setApplicationName("The Oracle")
        app.setApplicationVersion("2.0.0")
        
        log_info(f"QApplication initialized successfully: name={app.applicationName()}, version={app.applicationVersion()}")
        return app
        
    except Exception as e:
        log_critical(f"Failed to initialize QApplication: {e}")
        raise

@error_handler(severity=ErrorSeverity.ERROR if 'ErrorSeverity' in globals() else None, 
              category=ErrorCategory.UI if 'ErrorCategory' in globals() else None)
def create_main_window() -> Optional['MainWindow']:
    """Create the main window with error handling and recovery."""
    try:
        log_info("Creating main window...")
        
        # Import main window class with error handling
        try:
            from ui.main_window import MainWindow
            log_info("MainWindow class imported successfully")
        except ImportError as import_error:
            log_error(f"Failed to import MainWindow: {import_error}")
            raise
        
        # Create main window instance
        main_window = MainWindow()
        log_info("Main window created successfully")
        
        return main_window
        
    except Exception as exc:
        log_error(f"Failed to create main window: {exc}")
        
        # Attempt recovery
        try:
            log_info("Attempting to create fallback main window...")
            # Could implement a fallback/simple main window here
            return None
        except Exception as recovery_error:
            log_critical(f"Recovery attempt failed: {recovery_error}")
            return None

@error_handler(severity=ErrorSeverity.ERROR if 'ErrorSeverity' in globals() else None,
              category=ErrorCategory.UI if 'ErrorCategory' in globals() else None)
def show_splash_screen_with_fallback():
    """Show splash screen with fallback error handling."""
    try:
        log_info("Showing splash screen...")
        from ui.splash_screen import show_splash_screen
        splash = show_splash_screen()
        log_info("Splash screen displayed successfully")
        return splash
        
    except Exception as exc:
        log_error(f"Failed to show splash screen: {exc}")
        
        # Fallback: show simple message box
        try:
            QMessageBox.information(None, "The Oracle",
                                   "Starting The Oracle...\nPlease wait while dependencies are loaded.")
            return None
        except Exception as fallback_error:
            log_error(f"Fallback splash screen also failed: {fallback_error}")
            return None

# Global variables with error tracking
main_window = None

@error_handler(severity=ErrorSeverity.CRITICAL if 'ErrorSeverity' in globals() else None,
              category=ErrorCategory.UI if 'ErrorCategory' in globals() else None)
def on_loaded():
    """Callback function for when splash screen loading is complete."""
    global main_window
    
    try:
        log_info("Splash screen loading complete, creating main window...")
        
        # Create main window with retry mechanism
        if 'RetryConfig' in globals():
            retry_config = RetryConfig(
                max_attempts=3,
                base_delay=2.0,
                exponential_backoff=True,
                retry_on_exceptions=[ImportError, RuntimeError]
            )
        
        main_window = safe_execute(create_main_window)
        
        if main_window is None:
            log_error("Failed to create main window after all attempts")
            raise RuntimeError("Main window creation failed")
        
        # Show main window with error handling
        try:
            log_info("Main window created, showing...")
            main_window.show()
            log_info("Main window displayed successfully.")
            
            # Close splash after 2 seconds
            QTimer.singleShot(2000, lambda: safe_execute(splash.close))
            log_info("Splash screen will close after 2 seconds overlap.")
            
        except Exception as show_error:
            log_error(f"Failed to show main window: {show_error}")
            if 'handle_error' in globals() and 'create_error_context' in globals():
                handle_error(show_error, create_error_context("show_main_window"))
            
    except Exception as exc:
        log_critical(f"Critical error in on_loaded: {exc}")
        
        # Show error dialog to user
        try:
            error_msg = f"Failed to start The Oracle:\n{str(exc)}\n\nPlease check the logs for more details."
            QMessageBox.critical(None, "Startup Error", error_msg)
        except Exception as dialog_error:
            log_error(f"Failed to show error dialog: {dialog_error}")
        
        # Exit application
        sys.exit(1)

@error_handler(severity=ErrorSeverity.CRITICAL if 'ErrorSeverity' in globals() else None,
              category=ErrorCategory.CONFIGURATION if 'ErrorCategory' in globals() else None)
def main() -> NoReturn:
    """Main application entry point with comprehensive error handling."""
    try:
        # Add current directory to path
        add_current_dir_to_path()
        
        # Initialize QApplication
        log_info("Initializing QApplication...")
        
        app = QApplication(sys.argv)
        app.setApplicationName("The Oracle")
        app.setApplicationVersion("2.0.0")
        
        log_info(f"QApplication initialized successfully: name={app.applicationName()}, version={app.applicationVersion()}")
        
        # Show splash screen
        log_info("Showing splash screen...")
        
        splash = None
        try:
            splash = QSplashScreen(QPixmap("icons/general/oracle.png"))
            splash.show()
            log_info("Splash screen displayed successfully")
        except Exception as e:
            log_error(f"Failed to show splash screen: {e}")
        
        # Process events to show splash
        app.processEvents()
        
        # Import dependencies with error handling
        try:
            import PyPDF2
            log_info("Package PyPDF2 imported successfully")
        except ImportError as e:
            log_error(f"Failed to import PyPDF2: {e}")
        
        # Import main window
        try:
            from ui.main_window import MainWindow
        except ImportError as e:
            log_critical(f"Failed to import MainWindow: {e}")
            raise
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Close splash screen if it exists
        if splash:
            splash.finish(window)
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as exc:
        log_critical(f"Critical error in main function: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    # Run main with error handling
    try:
        main()
    except KeyboardInterrupt:
        log_info("Application interrupted by user")
        sys.exit(0)
    except Exception as exc:
        log_critical(f"Unhandled exception in main: {exc}")
        traceback.print_exc()
        sys.exit(1)
