# Quick Start: Desktop Application

## 🚀 Fastest Way to Run

### Windows Users:
Double-click `launch_desktop.bat`

### All Platforms:
```bash
cd hedge_fund_app
python desktop_app.py
```

The app will:
1. Start the Streamlit server
2. Open automatically in your browser
3. Run as a desktop application

## 📦 Building a Standalone Executable

### Step 1: Install Build Tools
```bash
pip install -r requirements_desktop.txt
```

### Step 2: Build
```bash
python build_desktop.py
```

Or use PyInstaller directly:
```bash
pyinstaller HedgeFundManager.spec
```

### Step 3: Find Your App
The executable will be in: `dist/HedgeFundManager.exe`

## 🎯 Features

- ✅ Native desktop window (with PyQt5)
- ✅ Browser-based interface (fallback)
- ✅ Standalone executable option
- ✅ All features from web app included

## 📝 Requirements

**Minimum:**
- Python 3.8+
- Streamlit
- All packages from `requirements.txt`

**For Native Window:**
- PyQt5
- PyQtWebEngine

**For Building Executable:**
- PyInstaller

## 🔧 Troubleshooting

**App won't start?**
- Make sure you're in the `hedge_fund_app` directory
- Check that `.env` file exists with your API key
- Install requirements: `pip install -r requirements.txt`

**Want native window instead of browser?**
```bash
pip install PyQt5 PyQtWebEngine
```

**Build fails?**
- Make sure PyInstaller is installed: `pip install pyinstaller`
- Check that all dependencies are installed
- Try building with console enabled (edit .spec file)

## 📱 Distribution

To share the app:
1. Build the executable
2. Include `dist/HedgeFundManager.exe`
3. Include `.env.example` (users create their own `.env`)
4. Optionally create an installer

The executable is self-contained and doesn't require Python!

