#!/usr/bin/env python3
"""
Launch script for The Oracle application.
This script ensures the virtual environment is used and handles any startup issues.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch The Oracle application using the virtual environment"""
    
    # Get the project directory
    project_dir = Path(__file__).parent
    
    # Path to the virtual environment Python executable
    venv_python = project_dir / ".venv" / "Scripts" / "python.exe"
    
    # Path to the main application script
    main_script = project_dir / "main.py"
    
    print("🚀 Starting The Oracle...")
    print(f"📁 Project directory: {project_dir}")
    print(f"🐍 Using Python: {venv_python}")
    
    # Check if virtual environment exists
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        print("Please run: python -m venv .venv")
        print("Then install dependencies: pip install -r requirements.txt")
        return 1
    
    # Check if main script exists
    if not main_script.exists():
        print("❌ Main script not found!")
        return 1
    
    try:
        # Launch the application
        result = subprocess.run([str(venv_python), str(main_script)], 
                              cwd=str(project_dir),
                              check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Failed to launch The Oracle: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
