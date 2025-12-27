@echo off
echo ========================================
echo Installing Optimized Hedge Fund Files
echo ========================================
echo.
echo This script will:
echo 1. Backup your current files
echo 2. Download the optimized versions
echo 3. Copy them to the correct locations
echo.
pause

REM Create backup directory
if not exist "backups" mkdir backups
set BACKUP_DIR=backups\backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%"

REM Backup existing files
echo.
echo Creating backups...
copy "trader\autonomous_trader.py" "%BACKUP_DIR%\autonomous_trader_backup.py"
copy "trader\run_autonomous.py" "%BACKUP_DIR%\run_autonomous_backup.py"
copy "scanner\stock_universe.py" "%BACKUP_DIR%\stock_universe_backup.py"

echo.
echo ========================================
echo MANUAL STEP REQUIRED
echo ========================================
echo.
echo Please download these 3 files from Claude's output panel:
echo   1. autonomous_trader_optimized.py
echo   2. run_autonomous_optimized.py  
echo   3. stock_universe_optimized.py
echo.
echo Then:
echo   1. Copy autonomous_trader_optimized.py to trader\autonomous_trader.py
echo   2. Copy run_autonomous_optimized.py to trader\run_autonomous.py
echo   3. Copy stock_universe_optimized.py to scanner\stock_universe.py
echo.
echo (stock_universe.py has already been updated automatically)
echo.
echo Your backups are in: %BACKUP_DIR%
echo.
pause
