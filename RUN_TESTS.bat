@echo off
echo ========================================
echo RUNNING SYSTEM TESTS
echo ========================================
echo.

cd /d "%~dp0"
python test_system.py

echo.
echo ========================================
echo Test complete! Press any key to exit...
pause > nul
