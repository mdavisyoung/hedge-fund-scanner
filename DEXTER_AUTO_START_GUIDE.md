# Dexter Auto-Start Guide

## Overview

The Dexter service (NewsAdmin) can now be started automatically when you launch the Hedge Fund Scanner app.

## Features

✅ **Automatic Detection**: Finds NewsAdmin directory automatically  
✅ **Health Check**: Verifies service is ready before proceeding  
✅ **Streamlit Integration**: Auto-start button in Chat with Dexter page  
✅ **Standalone Launcher**: One-click startup for both services  

## Usage Options

### Option 1: Auto-Start Button (Recommended)

1. Start Streamlit normally:
   ```bash
   streamlit run app.py
   ```

2. Navigate to **"Chat with Dexter"** page

3. If Dexter is not running, click **"🚀 Auto-Start Dexter"** button

4. Wait ~10-15 seconds for service to start

5. Service will be ready automatically!

### Option 2: Standalone Auto-Start Script

Run the automated launcher that starts both services:

**Windows:**
```bash
AUTO_START_ALL.bat
```

**Or manually:**
```bash
python auto_start_dexter.py
```

This will:
1. Check if Dexter is running
2. Start it if needed
3. Wait for it to be ready
4. Launch Streamlit

### Option 3: Manual Start (Fallback)

If auto-start fails, start manually:

```bash
cd NewsAdmin
npm run dev
```

Then in another terminal:
```bash
streamlit run app.py
```

## Configuration

### Set Custom NewsAdmin Path

If NewsAdmin is not in the default location, set environment variable:

**Windows:**
```cmd
set DEXTER_NEWSADMIN_PATH=C:\path\to\NewsAdmin
```

**Linux/Mac:**
```bash
export DEXTER_NEWSADMIN_PATH=/path/to/NewsAdmin
```

Or add to `.env` file:
```
DEXTER_NEWSADMIN_PATH=C:\path\to\NewsAdmin
```

## Troubleshooting

### "NewsAdmin directory not found"

- Check that NewsAdmin exists in one of these locations:
  - `~/Desktop/NewsAdmin`
  - `~/Documents/NewsAdmin`
  - `~/NewsAdmin`
- Or set `DEXTER_NEWSADMIN_PATH` environment variable

### "npm is not installed"

- Install Node.js from https://nodejs.org/
- Verify: `npm --version`

### "Service started but not ready"

- Check NewsAdmin logs for errors
- Verify port 3000 is not in use by another service
- Try manual start to see error messages

### Auto-start button doesn't work

- Check that `psutil` is installed: `pip install psutil`
- Check console/terminal for error messages
- Try manual start as fallback

## Files

- `utils/dexter_manager.py` - Core automation logic
- `auto_start_dexter.py` - Standalone launcher script
- `AUTO_START_ALL.bat` - Windows batch launcher
- `pages/04_Chat_with_Dexter.py` - Streamlit integration

## Requirements

- `psutil>=5.9.0` (for process management)
- Node.js and npm (for NewsAdmin)
- NewsAdmin directory accessible





