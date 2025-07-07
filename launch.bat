@echo off
echo Starting The Oracle...
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred. Press any key to exit...
    pause > nul
)
