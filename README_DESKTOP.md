# Desktop Application Setup

This guide explains how to run and build the Personal Hedge Fund Manager as a desktop application.

## Quick Start (Run as Desktop App)

### Option 1: Simple Launcher (No Additional Dependencies)
```bash
cd hedge_fund_app
python desktop_app.py
```
This will start the Streamlit app and open it in your default browser.

### Option 2: Native Window (Requires PyQt5)
```bash
pip install PyQt5 PyQtWebEngine
python desktop_app.py
```
This creates a native desktop window with the app embedded.

## Building a Standalone Executable

To create a `.exe` file that can run without Python installed:

### Step 1: Install Build Dependencies
```bash
pip install -r requirements_desktop.txt
```

### Step 2: Build the Executable
```bash
python build_desktop.py
```

This will create:
- `dist/HedgeFundManager.exe` - The standalone executable
- `build/` - Temporary build files (can be deleted)

### Step 3: Run the Executable
Simply double-click `HedgeFundManager.exe` to run the app.

## Manual Build (Advanced)

If you prefer to use PyInstaller directly:

```bash
pyinstaller --name HedgeFundManager --onefile --windowed desktop_app.py
```

## Troubleshooting

### "Streamlit not found" error
```bash
pip install streamlit
```

### "PyQt5 not found" error
```bash
pip install PyQt5 PyQtWebEngine
```

### Large executable size
The executable will be large (100-200MB) because it includes:
- Python interpreter
- All dependencies (Streamlit, Plotly, Pandas, etc.)
- Streamlit's web assets

This is normal for Python desktop applications.

### First run is slow
The first time you run the executable, it extracts files to a temporary directory. This is normal and subsequent runs will be faster.

## Distribution

To distribute the app:
1. Build the executable using `build_desktop.py`
2. Copy `dist/HedgeFundManager.exe` to your distribution folder
3. Include a `.env.example` file (users should create their own `.env` with API key)
4. Optionally create an installer using tools like Inno Setup or NSIS

## Notes

- The app requires an internet connection for:
  - Stock data (yfinance)
  - AI strategy generation (xAI API)
- The `.env` file with API key should be in the same directory as the executable
- On first run, users may need to allow firewall access

