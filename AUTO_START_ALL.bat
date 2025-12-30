@echo off
echo ================================================
echo   AUTO-START: Dexter + Hedge Fund Scanner
echo ================================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the auto-start Python script
echo Starting services automatically...
echo.
python auto_start_dexter.py

pause





