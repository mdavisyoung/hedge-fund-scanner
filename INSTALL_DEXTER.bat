@echo off
echo ================================================
echo Installing Native Python Dexter Dependencies
echo ================================================
echo.

echo Installing openai package...
pip install openai>=1.0.0

echo.
echo Installing requests (if not already installed)...
pip install requests>=2.31.0

echo.
echo Installing python-dotenv (if not already installed)...
pip install python-dotenv>=1.0.0

echo.
echo ================================================
echo Installation Complete!
echo ================================================
echo.
echo Now you can test with:
echo python test_dexter_native.py
echo.
pause
