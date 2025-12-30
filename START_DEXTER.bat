@echo off
echo ================================================
echo   DEXTER + HEDGE FUND SCANNER LAUNCHER
echo ================================================
echo.
echo Starting both services...
echo.

REM Start NewsAdmin (Dexter API) in new window
echo [1/2] Starting Dexter API (NewsAdmin)...
start "Dexter API" cmd /k "cd /d C:\Users\svfam\Desktop\NewsAdmin && npm run dev"

REM Wait a few seconds for NewsAdmin to start
timeout /t 5 /nobreak > nul

REM Start Hedge Fund Scanner (Streamlit) in new window
echo [2/2] Starting Hedge Fund Scanner (Streamlit)...
start "Hedge Fund Scanner" cmd /k "cd /d C:\Users\svfam\Desktop\Money Scanner\hedge-fund-scanner && streamlit run app.py"

echo.
echo ================================================
echo   SERVICES STARTING...
echo ================================================
echo.
echo Dexter API:          http://localhost:3000
echo Hedge Fund Scanner:  http://localhost:8501
echo.
echo Wait ~10 seconds for both services to be ready.
echo Then open: http://localhost:8501
echo.
echo To stop: Close both command windows
echo ================================================
echo.
pause
