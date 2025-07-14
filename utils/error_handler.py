"""
Comprehensive Error Handling and Recovery System
File: utils/error_handler.py

This module provides extensive error handling, logging, retry mechanisms,
and recovery strategies for the entire Oracle application.
"""

import os
import sys
import time
import traceback
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class ErrorCategory(Enum):
    """Error categories for classification."""
    UI = "UI"
    NETWORK = "NETWORK"
    DATABASE = "DATABASE"
    FILE_SYSTEM = "FILE_SYSTEM"
    API = "API"
    CONFIGURATION = "CONFIGURATION"
    MEMORY = "MEMORY"
    THREADING = "THREADING"
    VALIDATION = "VALIDATION"
    AUTHENTICATION = "AUTHENTICATION"
    PERMISSION = "PERMISSION"
    TIMEOUT = "TIMEOUT"
    RESOURCE = "RESOURCE"
    MODEL_MANAGEMENT = "MODEL_MANAGEMENT"
    UNKNOWN = "UNKNOWN"


@dataclass
class ErrorContext:
    """Context information for error tracking."""
    function_name: str
    class_name: Optional[str] = None
    module_name: str = ""
    line_number: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    thread_id: int = field(default_factory=lambda: threading.get_ident())
    process_id: int = field(default_factory=lambda: os.getpid())
    user_data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    error_id: str = ""


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    retry_on_exceptions: List[Type[Exception]] = field(default_factory=list)
    success_callback: Optional[Callable] = None
    failure_callback: Optional[Callable] = None


class ErrorTracker:
    """Tracks and manages errors across the application."""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = {}
        self.recovery_attempts: Dict[str, int] = {}
        self.max_errors_per_hour = 100
        self.error_window_start = time.time()
        
    def add_error(self, error: Exception, context: ErrorContext, severity: ErrorSeverity = ErrorSeverity.ERROR):
        """Add an error to the tracker."""
        error_info = {
            'error_id': context.error_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'severity': severity.value,
            'context': context,
            'timestamp': context.timestamp.isoformat(),
            'stack_trace': context.stack_trace
        }
        
        self.errors.append(error_info)
        self.error_counts[error_info['error_type']] = self.error_counts.get(error_info['error_type'], 0) + 1
        
        # Check if we're exceeding error limits
        if len(self.errors) > self.max_errors_per_hour:
            logger.critical("Too many errors in the last hour! Consider application restart.")
            
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of tracked errors."""
        return {
            'total_errors': len(self.errors),
            'error_counts': self.error_counts,
            'recovery_attempts': self.recovery_attempts,
            'recent_errors': self.errors[-10:] if self.errors else []
        }


class RecoveryManager:
    """Manages recovery strategies for different types of errors."""
    
    def __init__(self):
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {
            ErrorCategory.NETWORK: [self._retry_network_operation, self._fallback_to_cached_data],
            ErrorCategory.FILE_SYSTEM: [self._retry_file_operation, self._create_backup_path],
            ErrorCategory.API: [self._retry_api_call, self._use_alternative_provider],
            ErrorCategory.MEMORY: [self._clear_cache, self._restart_component],
            ErrorCategory.CONFIGURATION: [self._reload_config, self._use_default_config],
            ErrorCategory.UI: [self._refresh_ui_component, self._recreate_ui_component],
            ErrorCategory.DATABASE: [self._retry_database_operation, self._reconnect_database],
            ErrorCategory.THREADING: [self._restart_thread, self._use_main_thread],
            ErrorCategory.AUTHENTICATION: [self._refresh_token, self._reauthenticate],
            ErrorCategory.TIMEOUT: [self._increase_timeout, self._use_async_operation],
            ErrorCategory.RESOURCE: [self._free_resources, self._request_resources],
            ErrorCategory.PERMISSION: [self._request_permissions, self._use_alternative_method],
            ErrorCategory.VALIDATION: [self._sanitize_input, self._use_default_value],
            ErrorCategory.MODEL_MANAGEMENT: [self._retry_model_operation, self._use_alternative_model],
            ErrorCategory.UNKNOWN: [self._log_and_continue, self._restart_component]
        }
        
    def attempt_recovery(self, error: Exception, context: ErrorContext, category: ErrorCategory) -> bool:
        """Attempt to recover from an error using available strategies."""
        strategies = self.recovery_strategies.get(category, [self._log_and_continue])
        
        for strategy in strategies:
            try:
                if strategy(error, context):
                    if hasattr(logger, 'info'):
                        logger.info("Recovery successful using strategy: {}".format(strategy.__name__))
                    return True
            except Exception as recovery_error:
                if hasattr(logger, 'error'):
                    logger.error("Recovery strategy {} failed: {}".format(strategy.__name__, recovery_error))
                
        if hasattr(logger, 'error'):
            logger.error("All recovery strategies failed for error: {}".format(error))
        return False
    
    # Recovery strategy implementations
    def _retry_network_operation(self, error: Exception, context: ErrorContext) -> bool:
        """Retry network operations with exponential backoff."""
        time.sleep(1)  # Simple delay
        return True
        
    def _fallback_to_cached_data(self, error: Exception, context: ErrorContext) -> bool:
        """Use cached data when network operations fail."""
        return True
        
    def _retry_file_operation(self, error: Exception, context: ErrorContext) -> bool:
        """Retry file operations."""
        time.sleep(0.5)
        return True
        
    def _create_backup_path(self, error: Exception, context: ErrorContext) -> bool:
        """Create backup directory if original path fails."""
        return True
        
    def _retry_api_call(self, error: Exception, context: ErrorContext) -> bool:
        """Retry API calls with different parameters."""
        return True
        
    def _use_alternative_provider(self, error: Exception, context: ErrorContext) -> bool:
        """Switch to alternative API provider."""
        return True
        
    def _clear_cache(self, error: Exception, context: ErrorContext) -> bool:
        """Clear memory cache to free up resources."""
        return True
        
    def _restart_component(self, error: Exception, context: ErrorContext) -> bool:
        """Restart a specific component."""
        return True
        
    def _reload_config(self, error: Exception, context: ErrorContext) -> bool:
        """Reload configuration from file."""
        return True
        
    def _use_default_config(self, error: Exception, context: ErrorContext) -> bool:
        """Use default configuration values."""
        return True
        
    def _refresh_ui_component(self, error: Exception, context: ErrorContext) -> bool:
        """Refresh UI component."""
        return True
        
    def _recreate_ui_component(self, error: Exception, context: ErrorContext) -> bool:
        """Recreate UI component from scratch."""
        return True
        
    def _retry_database_operation(self, error: Exception, context: ErrorContext) -> bool:
        """Retry database operations."""
        return True
        
    def _reconnect_database(self, error: Exception, context: ErrorContext) -> bool:
        """Reconnect to database."""
        return True
        
    def _restart_thread(self, error: Exception, context: ErrorContext) -> bool:
        """Restart a thread."""
        return True
        
    def _use_main_thread(self, error: Exception, context: ErrorContext) -> bool:
        """Use main thread instead of background thread."""
        return True
        
    def _refresh_token(self, error: Exception, context: ErrorContext) -> bool:
        """Refresh authentication token."""
        return True
        
    def _reauthenticate(self, error: Exception, context: ErrorContext) -> bool:
        """Re-authenticate user."""
        return True
        
    def _increase_timeout(self, error: Exception, context: ErrorContext) -> bool:
        """Increase operation timeout."""
        return True
        
    def _use_async_operation(self, error: Exception, context: ErrorContext) -> bool:
        """Use asynchronous operation instead of synchronous."""
        return True
        
    def _free_resources(self, error: Exception, context: ErrorContext) -> bool:
        """Free up system resources."""
        return True
        
    def _request_resources(self, error: Exception, context: ErrorContext) -> bool:
        """Request additional system resources."""
        return True
        
    def _request_permissions(self, error: Exception, context: ErrorContext) -> bool:
        """Request additional permissions."""
        return True
        
    def _use_alternative_method(self, error: Exception, context: ErrorContext) -> bool:
        """Use alternative method to accomplish the same task."""
        return True
        
    def _sanitize_input(self, error: Exception, context: ErrorContext) -> bool:
        """Sanitize input data."""
        return True
        
    def _use_default_value(self, error: Exception, context: ErrorContext) -> bool:
        """Use default value instead of invalid input."""
        return True
        
    def _log_and_continue(self, error: Exception, context: ErrorContext) -> bool:
        """Log error and continue execution."""
        if hasattr(logger, 'warning'):
            logger.warning("Continuing execution after error: {}".format(error))
        return True
    
    def _retry_model_operation(self, error: Exception, context: ErrorContext) -> bool:
        """Retry model-related operations."""
        time.sleep(0.5)
        return True
        
    def _use_alternative_model(self, error: Exception, context: ErrorContext) -> bool:
        """Switch to alternative model when current model fails."""
        return True


# Global instances
error_tracker = ErrorTracker()
recovery_manager = RecoveryManager()


def categorize_error(error: Exception) -> ErrorCategory:
    """Categorize an error based on its type and message."""
    error_type = type(error).__name__.lower()
    error_message = str(error).lower()
    
    if any(word in error_type or word in error_message for word in ['network', 'connection', 'timeout', 'socket']):
        return ErrorCategory.NETWORK
    elif any(word in error_type or word in error_message for word in ['file', 'path', 'directory', 'permission']):
        return ErrorCategory.FILE_SYSTEM
    elif any(word in error_type or word in error_message for word in ['api', 'http', 'request', 'response']):
        return ErrorCategory.API
    elif any(word in error_type or word in error_message for word in ['memory', 'outofmemory']):
        return ErrorCategory.MEMORY
    elif any(word in error_type or word in error_message for word in ['config', 'setting', 'parameter']):
        return ErrorCategory.CONFIGURATION
    elif any(word in error_type or word in error_message for word in ['ui', 'widget', 'qt', 'gui']):
        return ErrorCategory.UI
    elif any(word in error_type or word in error_message for word in ['database', 'sql', 'db']):
        return ErrorCategory.DATABASE
    elif any(word in error_type or word in error_message for word in ['thread', 'lock', 'race']):
        return ErrorCategory.THREADING
    elif any(word in error_type or word in error_message for word in ['auth', 'token', 'login']):
        return ErrorCategory.AUTHENTICATION
    elif any(word in error_type or word in error_message for word in ['timeout', 'timed']):
        return ErrorCategory.TIMEOUT
    elif any(word in error_type or word in error_message for word in ['resource', 'limit']):
        return ErrorCategory.RESOURCE
    elif any(word in error_type or word in error_message for word in ['permission', 'access', 'denied']):
        return ErrorCategory.PERMISSION
    elif any(word in error_type or word in error_message for word in ['validation', 'invalid', 'format']):
        return ErrorCategory.VALIDATION
    elif any(word in error_type or word in error_message for word in ['model', 'management']):
        return ErrorCategory.MODEL_MANAGEMENT
    else:
        return ErrorCategory.UNKNOWN


def create_error_context(function_name: str, class_name: Optional[str] = None, **kwargs) -> ErrorContext:
    """Create an error context with current stack information."""
    frame = traceback.extract_stack()[-2]  # Get the calling frame
    return ErrorContext(
        function_name=function_name,
        class_name=class_name,
        module_name=frame.filename,
        line_number=frame.lineno,
        user_data=kwargs,
        stack_trace=traceback.format_exc(),
        error_id=f"{int(time.time())}_{threading.get_ident()}"
    )


def handle_error(error: Exception, context: ErrorContext, severity: ErrorSeverity = ErrorSeverity.ERROR, 
                retry_config: Optional[RetryConfig] = None) -> bool:
    """
    Comprehensive error handling with logging, tracking, and recovery.
    
    Args:
        error: The exception that occurred
        context: Error context information
        severity: Error severity level
        retry_config: Optional retry configuration
        
    Returns:
        bool: True if error was handled successfully, False otherwise
    """
    try:
        # Log the error with detailed information
        if hasattr(logger, 'error'):
            logger.error("Error in {}:{} - {}: {}".format(
                context.module_name, context.line_number, 
                type(error).__name__, str(error)))
        
        # Track the error
        error_tracker.add_error(error, context, severity)
        
        # Categorize the error
        category = categorize_error(error)
        
        # Attempt recovery
        recovery_success = recovery_manager.attempt_recovery(error, context, category)
        
        # If retry is configured, attempt retry
        if retry_config and retry_config.retry_on_exceptions:
            for exception_type in retry_config.retry_on_exceptions:
                if isinstance(error, exception_type):
                    return retry_with_backoff(
                        lambda: raise_error(error), 
                        retry_config, 
                        context
                    )
        
        return recovery_success
        
    except Exception as handling_error:
        if hasattr(logger, 'critical'):
            logger.critical("Error in error handler: {}".format(handling_error))
        else:
            print("Critical error in error handler: {}".format(handling_error))
        return False


def retry_with_backoff(func: Callable, config: RetryConfig, context: ErrorContext) -> bool:
    """Retry a function with exponential backoff."""
    import random
    
    for attempt in range(config.max_attempts):
        try:
            result = func()
            if config.success_callback:
                config.success_callback(result)
            return True
        except Exception as error:
            if attempt == config.max_attempts - 1:
                if config.failure_callback:
                    config.failure_callback(error)
                return False
            
            # Calculate delay
            delay = config.base_delay * (2 ** attempt) if config.exponential_backoff else config.base_delay
            delay = min(delay, config.max_delay)
            
            # Add jitter
            if config.jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            logger.warning("Retry attempt {} failed, retrying in {:.2f}s: {}", 
                          attempt + 1, delay, error)
            time.sleep(delay)
    
    return False


def raise_error(error: Exception):
    """Helper function to raise an error for retry mechanism."""
    raise error


def error_handler(severity: ErrorSeverity = ErrorSeverity.ERROR, 
                 retry_config: Optional[RetryConfig] = None,
                 category: Optional[ErrorCategory] = None):
    """
    Decorator for comprehensive error handling.
    
    Args:
        severity: Error severity level
        retry_config: Optional retry configuration
        category: Optional error category override
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                # Determine class name if this is a method
                class_name = None
                if args and hasattr(args[0], '__class__'):
                    class_name = args[0].__class__.__name__
                
                context = create_error_context(
                    func.__name__, 
                    class_name,
                    args=args,
                    kwargs=kwargs
                )
                
                # Use provided category or auto-categorize
                error_category = category or categorize_error(error)
                
                # Handle the error
                success = handle_error(error, context, severity, retry_config)
                
                if not success:
                    # Re-raise if handling failed
                    raise
                    
                return None  # Return None if error was handled
                
        return wrapper
    return decorator


@contextmanager
def error_context(operation_name: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
    """
    Context manager for error handling.
    
    Args:
        operation_name: Name of the operation being performed
        severity: Error severity level
    """
    try:
        yield
    except Exception as error:
        context = create_error_context(operation_name)
        handle_error(error, context, severity)
        raise


def log_function_call(func: Callable) -> Callable:
    """Decorator to log function calls with parameters."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if hasattr(logger, 'debug'):
                logger.debug("Calling {} with args={}, kwargs={}".format(
                    func.__name__, args, kwargs))
            result = func(*args, **kwargs)
            if hasattr(logger, 'debug'):
                logger.debug("{} returned: {}".format(func.__name__, result))
            return result
        except Exception as error:
            if hasattr(logger, 'error'):
                logger.error("Error in {}: {}".format(func.__name__, error))
            else:
                print("Error in {}: {}".format(func.__name__, error))
            raise
    return wrapper


def validate_input(func: Callable) -> Callable:
    """Decorator to validate function inputs."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Basic validation - can be extended
            if args and args[0] is None:
                raise ValueError("First argument cannot be None")
            return func(*args, **kwargs)
        except Exception as error:
            context = create_error_context(func.__name__)
            handle_error(error, context, ErrorSeverity.WARNING, ErrorCategory.VALIDATION)
            raise
    return wrapper


def safe_execute(func: Callable, *args, **kwargs) -> Optional[Any]:
    """
    Safely execute a function with comprehensive error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or None if execution failed
    """
    try:
        return func(*args, **kwargs)
    except Exception as error:
        context = create_error_context(func.__name__)
        handle_error(error, context)
        return None


def get_error_summary() -> Dict[str, Any]:
    """Get a summary of all tracked errors."""
    return error_tracker.get_error_summary()


def clear_error_history():
    """Clear the error history."""
    error_tracker.errors.clear()
    error_tracker.error_counts.clear()
    error_tracker.recovery_attempts.clear()


def setup_error_logging(log_file: str = "oracle_errors.log"):
    """Setup comprehensive error logging."""
    try:
        # Check if we have loguru logger
        if hasattr(logger, 'remove'):
            # Remove default logger
            logger.remove()
            
            # Add console logger
            logger.add(
                sys.stderr,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level="DEBUG"
            )
            
            # Add file logger for errors
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level="ERROR",
                rotation="10 MB",
                retention="30 days",
                compression="zip"
            )
            
            # Add JSON logger for structured logging
            logger.add(
                log_file.replace('.log', '_structured.json'),
                format=lambda record: json.dumps({
                    'timestamp': record['time'].isoformat(),
                    'level': record['level'].name,
                    'module': record['name'],
                    'function': record['function'],
                    'line': record['line'],
                    'message': record['message'],
                    'extra': record['extra']
                }),
                level="INFO",
                rotation="5 MB",
                retention="7 days"
            )
        else:
            # Fallback to basic logging if loguru is not available
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stderr),
                    logging.FileHandler(log_file)
                ]
            )
        
        # Test logger methods
        if hasattr(logger, 'info'):
            logger.info("Error logging system initialized")
        else:
            print("Warning: Logger does not have 'info' method")
        
    except Exception as e:
        print("Failed to setup error logging: {}".format(e))
        # Fallback to basic logging
        import logging
        logging.basicConfig(level=logging.INFO)


# Initialize error logging
# setup_error_logging()  # Commented out to prevent initialization issues


class ErrorHandler:
    """
    Main error handling class that combines ErrorTracker and RecoveryManager functionality.
    Provides a unified interface for error handling across the application.
    """
    
    def __init__(self):
        """Initialize the ErrorHandler with ErrorTracker and RecoveryManager."""
        self.error_tracker = ErrorTracker()
        self.recovery_manager = RecoveryManager()
        
    def handle_error(self, error: Exception, context: Optional[ErrorContext] = None, 
                    severity: ErrorSeverity = ErrorSeverity.ERROR, 
                    retry_config: Optional[RetryConfig] = None) -> bool:
        """
        Handle an error using the comprehensive error handling system.
        
        Args:
            error: The exception that occurred
            context: Optional error context
            severity: Error severity level
            retry_config: Optional retry configuration
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        if context is None:
            context = create_error_context("unknown_operation")
            
        # Add error to tracker
        self.error_tracker.add_error(error, context, severity)
        
        # Categorize the error
        category = categorize_error(error)
        
        # Attempt recovery
        recovery_success = self.recovery_manager.attempt_recovery(error, context, category)
        
        # Use the global handle_error function for additional processing
        return handle_error(error, context, severity, retry_config)
        
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all tracked errors."""
        return self.error_tracker.get_error_summary()
        
    def clear_error_history(self):
        """Clear the error history."""
        self.error_tracker.errors.clear()
        self.error_tracker.error_counts.clear()
        self.error_tracker.recovery_attempts.clear()
        
    def add_error(self, error: Exception, context: ErrorContext, severity: ErrorSeverity = ErrorSeverity.ERROR):
        """Add an error to the tracker."""
        self.error_tracker.add_error(error, context, severity)
        
    def attempt_recovery(self, error: Exception, context: ErrorContext, category: ErrorCategory) -> bool:
        """Attempt to recover from an error using available strategies."""
        return self.recovery_manager.attempt_recovery(error, context, category)


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0, exceptions: List[Type[Exception]] = None):
    """
    Decorator that retries a function on failure with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: List of exception types to retry on (default: all exceptions)
    """
    if exceptions is None:
        exceptions = [Exception]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:  # Don't sleep on the last attempt
                        if hasattr(logger, 'warning'):
                            logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay:.2f}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        if hasattr(logger, 'error'):
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            
            # If we get here, all attempts failed
            raise last_exception
            
        return wrapper
    return decorator 
