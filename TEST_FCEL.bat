@echo off
echo ========================================
echo TESTING FCEL DATA
echo ========================================
echo.
echo This test will show you that P/E = 0.00
echo is CORRECT for unprofitable companies!
echo.

cd /d "%~dp0"
python test_fcel.py

echo.
echo ========================================
echo Want to compare with a profitable stock?
echo Run: python compare_stocks.py
echo ========================================
pause
