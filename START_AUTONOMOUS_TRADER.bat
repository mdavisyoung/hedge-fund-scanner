@echo off
REM ============================================================================
REM Autonomous Trader Background Service
REM Runs the autonomous trader continuously in the background
REM ============================================================================

cd /d "%~dp0"

echo ============================================================================
echo   AUTONOMOUS TRADER - Background Service
echo ============================================================================
echo.
echo Starting autonomous trader in continuous mode...
echo - Runs every 5 minutes during market hours
echo - Trades automatically based on scanner results
echo - Paper trading mode (safe for testing)
echo.
echo Press Ctrl+C to stop
echo ============================================================================
echo.

REM Run in continuous mode with 5-minute intervals
python trader/run_autonomous.py --mode continuous --interval 300 --paper

pause

