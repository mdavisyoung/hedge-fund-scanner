@echo off
echo ================================================
echo   TEST DEXTER MONTHLY ALLOCATION
echo ================================================
echo.
echo This tests Dexter's ability to decide where
echo to invest your $100 monthly budget.
echo.
echo Make sure NewsAdmin is running first!
echo.

cd /d "%~dp0"

echo [1/2] Testing Dexter connection...
python -c "from utils.dexter_client import DexterClient; client = DexterClient(); print('Connected!' if client.health_check() else 'Not connected - start NewsAdmin')"

echo.
echo [2/2] Running allocation test with $100...
echo.

python utils\dexter_allocator.py

echo.
echo ================================================
echo   TEST COMPLETE
echo ================================================
echo.
echo If successful, you should see:
echo   - Dexter's research process
echo   - Allocation recommendations
echo   - Specific tickers and amounts
echo.
echo Next: Open Streamlit and go to Monthly Allocation page
echo ================================================
pause
