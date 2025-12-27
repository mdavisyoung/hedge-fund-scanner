@echo off
echo ========================================
echo Personal Hedge Fund Manager
echo Desktop Application Launcher
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    echo.
)

REM Launch the desktop app
echo Starting Personal Hedge Fund Manager...
echo.
python desktop_app.py

pause

