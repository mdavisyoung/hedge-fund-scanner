"""
Build script to create a standalone desktop executable
Run this script to package the app as a Windows executable.
"""
import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build_executable():
    """Build the desktop executable using PyInstaller"""
    
    app_dir = Path(__file__).parent
    app_name = "HedgeFundManager"
    
    print("="*60)
    print("Building Desktop Application")
    print("="*60)
    print()
    
    # PyInstaller arguments
    args = [
        "desktop_app.py",
        "--name", app_name,
        "--onefile",
        "--windowed",
        "--icon=NONE",  # Add icon path here if you have one
        "--add-data", f"app.py;.",
        "--add-data", f"utils.py;.",
        "--add-data", f"custom.css;.",
        "--add-data", f"pages;pages",
        "--hidden-import", "streamlit",
        "--hidden-import", "streamlit.web.cli",
        "--hidden-import", "yfinance",
        "--hidden-import", "plotly",
        "--hidden-import", "pandas",
        "--hidden-import", "numpy",
        "--hidden-import", "requests",
        "--hidden-import", "dotenv",
        "--hidden-import", "PyQt5",
        "--hidden-import", "PyQt5.QtWebEngineWidgets",
        "--collect-all", "streamlit",
        "--collect-all", "plotly",
    ]
    
    print("Running PyInstaller...")
    print("This may take several minutes...")
    print()
    
    try:
        PyInstaller.__main__.run(args)
        print()
        print("="*60)
        print("Build Complete!")
        print("="*60)
        print(f"Executable location: {app_dir / 'dist' / f'{app_name}.exe'}")
        print()
        print("You can now distribute this .exe file.")
        print("Note: The first run may be slow as it extracts files.")
    except Exception as e:
        print(f"Error building executable: {e}")
        print("\nMake sure you have installed all requirements:")
        print("pip install -r requirements_desktop.txt")


if __name__ == "__main__":
    build_executable()

