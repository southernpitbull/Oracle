#!/usr/bin/env python3
"""
Oracle - Dependency Bootstrapper
File: utils/dependencies.py

Checks for required dependencies, installs any missing ones, and re-invokes the main script if installation occurs.
"""
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional

# Initialize loguru first, before any other operations
try:
    import loguru
    from loguru import logger
    # Configure loguru for better output
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    log = logger
except ImportError:

    # Fallback logger if loguru is not available
    class DummyLogger:

        def info(self, msg, *args):
            print("[INFO]", msg.format(*args))

        def warning(self, msg, *args):
            print("[WARN]", msg.format(*args))

        def error(self, msg, *args):
            print("[ERROR]", msg.format(*args))

    log = DummyLogger()

REQUIREMENTS_FILE = Path(__file__).parent.parent / "requirements.txt"

# Fallback list if requirements.txt is missing
FALLBACK_DEPENDENCIES = [
    "PyQt6",
    "loguru",
    "chromadb",  # Add chromadb to handle NumPy compatibility
]

# Optional dependencies that require compilation or are not critical
OPTIONAL_DEPENDENCIES = [
    "llama-cpp-python",  # Requires C++ compiler
    "torch",  # Can be large and optional
    "transformers",  # Can be large and optional
]

# Packages that commonly fail to compile and need special handling
COMPILATION_DEPENDENCIES = {
    "llama-cpp-python": {
        "description": "Local LLM inference library",
        "alternatives": [
            "pip install llama-cpp-python --prefer-binary",
            "pip install llama-cpp-python --no-cache-dir --force-reinstall",
        ],
        "requirements": "Visual Studio Build Tools (Windows) or GCC (Linux/Mac)",
        "timeout": 300  # 5 minutes
    },
    "torch": {
        "description": "PyTorch deep learning framework",
        "alternatives": [
            "pip install torch --index-url https://download.pytorch.org/whl/cpu",
            "pip install torch --index-url https://download.pytorch.org/whl/cu118",  # CUDA 11.8
        ],
        "requirements": "None (pre-built wheels available)",
        "timeout": 600  # 10 minutes
    },
    "transformers": {
        "description": "Hugging Face transformers library",
        "alternatives": [
            "pip install transformers --no-deps",
            "pip install transformers[torch]",
        ],
        "requirements": "None (pure Python)",
        "timeout": 300  # 5 minutes
    }
}

# Package name mapping for import vs pip names
PACKAGE_MAPPING = {
    "google-genai": "google.generativeai",
    "google-generativeai": "google.generativeai",
    "ollama-python": "ollama",
    "faiss-cpu": "faiss",
    "langchain-community": "langchain_community",
    "python-docx": "docx",
    "python-magic": "magic",
    "PyPDF2": "PyPDF2",
}


def run_with_timeout(cmd, timeout_seconds=60):
    """Run a command with timeout."""
    try:
        # Use subprocess timeout (works on all platforms)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        return result
    except subprocess.TimeoutExpired:
        log.error("Command timed out after {} seconds: {}", timeout_seconds, " ".join(cmd))
        return None
    except Exception as e:
        log.error("Error running command: {} - {}", " ".join(cmd), e)
        return None


def check_numpy_compatibility():
    """Check and fix NumPy compatibility issues."""
    try:
        import numpy as np
        numpy_version = np.__version__
        log.info("NumPy version detected: {}", numpy_version)
        
        # Check if we have NumPy 2.0+ which might cause compatibility issues
        if numpy_version.startswith('2.'):
            log.warning("NumPy 2.0+ detected. Checking chromadb compatibility...")
            
            # Try to import chromadb to see if there are compatibility issues
            try:
                import chromadb
                log.info("chromadb import successful - no compatibility issues detected")
            except AttributeError as e:
                if "np.float_" in str(e):
                    log.warning("NumPy 2.0 compatibility issue detected with chromadb")
                    log.info("Attempting to fix by upgrading chromadb...")
                    
                    python_exe = sys.executable
                    try:
                        cmd = [python_exe, "-m", "pip", "install", "--upgrade", "chromadb"]
                        result = run_with_timeout(cmd, 120)
                        if result and result.returncode == 0:
                            log.info("chromadb upgraded successfully")
                        else:
                            log.warning("Failed to upgrade chromadb")
                    except Exception as exc:
                        log.error("Error upgrading chromadb: {}", exc)
                else:
                    log.error("Unexpected AttributeError: {}", e)
            except ImportError:
                log.info("chromadb not installed - skipping compatibility check")
                
    except ImportError:
        log.info("NumPy not installed - skipping compatibility check")


def safe_import_check(pkg_name: str) -> bool:
    """Safely check if a package can be imported without triggering compatibility issues."""
    try:
        # Get the actual import name
        import_name = PACKAGE_MAPPING.get(pkg_name, pkg_name)
        
        # Special handling for packages that might cause issues
        if pkg_name in ["chromadb", "torch", "transformers", "faiss-cpu"]:
            # Use pip show for these packages to avoid import issues
            python_exe = sys.executable
            result = run_with_timeout([python_exe, "-m", "pip", "show", pkg_name], 30)
            if result and result.returncode == 0:
                log.info("Package {} found via pip", pkg_name)
                return True
            else:
                log.info("Package {} not found via pip", pkg_name)
                return False
        else:
            # Try to import the module
            import importlib
            try:
                importlib.import_module(import_name)
                log.info("Package {} imported successfully", pkg_name)
                return True
            except ImportError:
                # If import fails, try pip show as fallback
                python_exe = sys.executable
                result = run_with_timeout([python_exe, "-m", "pip", "show", pkg_name], 30)
                if result and result.returncode == 0:
                    log.info("Package {} found via pip but import failed", pkg_name)
                    return True
                else:
                    log.info("Package {} not found", pkg_name)
                    return False
    except Exception as e:
        log.warning("Error checking package {}: {}", pkg_name, e)
        return False


def get_required_dependencies() -> list[str]:
    if REQUIREMENTS_FILE.exists():
        with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            pkgs = [line.split("==")[0].split(">=")[0].split("<=")[0].strip() for line in lines]
            return list(sorted(set(pkgs)))
    return FALLBACK_DEPENDENCIES


def install_package_safely(pkg_name: str) -> bool:
    """Safely install a package with proper error handling and timeout."""
    python_exe = sys.executable
    
    # Get package info
    pkg_info = COMPILATION_DEPENDENCIES.get(pkg_name, {})
    timeout = pkg_info.get("timeout", 300)  # Default 5 minutes
    
    # Special handling for packages that require compilation
    if pkg_name == "llama-cpp-python":
        log.warning("llama-cpp-python requires C++ compiler (Visual Studio Build Tools)")
        log.info("Attempting to install with pre-built wheels...")
        
        # Try pre-built wheels first
        alternatives = pkg_info.get("alternatives", [])
        for alt_cmd in alternatives:
            try:
                cmd = alt_cmd.split()
                log.info("Trying alternative installation: {}", alt_cmd)
                result = run_with_timeout(cmd, timeout)
                if result and result.returncode == 0:
                    log.info("Package {} installed successfully via alternative method", pkg_name)
                    return True
                else:
                    log.warning("Alternative installation failed: {}", alt_cmd)
            except Exception as e:
                log.warning("Error with alternative installation {}: {}", alt_cmd, e)
        
        log.error("All installation methods failed for {}. Skipping.", pkg_name)
        log.info("Manual installation required:")
        log.info("  Install Visual Studio Build Tools, then: pip install llama-cpp-python")
        return False
    
    # For other packages, try standard installation with timeout
    try:
        cmd = [python_exe, "-m", "pip", "install", pkg_name]
        log.info("Installing package: {} (timeout: {}s)", pkg_name, timeout)
        result = run_with_timeout(cmd, timeout)
        
        if result is None:
            log.error("Installation of {} timed out or failed", pkg_name)
            return False
        elif result.returncode == 0:
            log.info("Package {} installed successfully", pkg_name)
            return True
        else:
            log.error("Failed to install {}: {}", pkg_name, result.stderr)
            
            # Try alternatives if available
            alternatives = pkg_info.get("alternatives", [])
            for alt_cmd in alternatives:
                try:
                    cmd = alt_cmd.split()
                    log.info("Trying alternative installation: {}", alt_cmd)
                    result = run_with_timeout(cmd, timeout)
                    if result and result.returncode == 0:
                        log.info("Package {} installed successfully via alternative method", pkg_name)
                        return True
                except Exception as e:
                    log.warning("Error with alternative installation {}: {}", alt_cmd, e)
            
            return False
    except Exception as exc:
        log.error("Error installing {}: {}", pkg_name, exc)
        return False


def check_and_install():
    import time
    
    # First check for NumPy compatibility issues
    check_numpy_compatibility()
    
    required = get_required_dependencies()
    log.info("Checking {} required dependencies", len(required))
    
    missing_required = []
    missing_optional = []
    
    for pkg in required:
        if not safe_import_check(pkg):
            if pkg in OPTIONAL_DEPENDENCIES:
                missing_optional.append(pkg)
            else:
                missing_required.append(pkg)
    
    # Handle optional dependencies first (non-blocking)
    if missing_optional:
        log.warning("Missing optional dependencies: {}", ", ".join(missing_optional))
        log.info("Attempting to install optional dependencies (non-blocking)...")
        
        for pkg in missing_optional:
            try:
                success = install_package_safely(pkg)
                if not success:
                    log.warning("Optional dependency {} failed to install - continuing without it", pkg)
            except Exception as e:
                log.error("Error installing optional dependency {}: {} - continuing without it", pkg, e)
    
    # Handle required dependencies (blocking)
    if missing_required:
        log.warning("Missing required dependencies: {}", ", ".join(missing_required))
        
        # Try to install missing dependencies
        python_exe = sys.executable
        try:
            cmd = [python_exe, "-m", "pip", "install"] + missing_required
            log.info("Installing missing required dependencies: {}", " ".join(missing_required))
            result = run_with_timeout(cmd, 600)  # 10 minute timeout for required deps
            
            if result is None:
                log.error("Installation timed out")
                log.error("Please install the missing dependencies manually:")
                for pkg in missing_required:
                    log.error("  pip install {}", pkg)
                sys.exit(1)
            elif result.returncode != 0:
                log.error("pip install failed: {}", result.stderr)
                log.error("Please install the missing dependencies manually:")
                for pkg in missing_required:
                    log.error("  pip install {}", pkg)
                sys.exit(1)
            
            log.info("Dependencies installed successfully. Re-initializing...")
            # Re-invoke the main script
            main_script = sys.argv[0]
            args = sys.argv[1:]
            time.sleep(1)
            os.execv(python_exe, [python_exe, main_script] + args)
        except Exception as exc:
            log.error("Failed to install dependencies: {}", exc)
            sys.exit(1)
    else:
        log.info("All required dependencies satisfied.")


# Run check on import
check_and_install()
