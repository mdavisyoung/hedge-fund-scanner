# Autonomous Trader - Automatic Setup Guide

## Overview

The autonomous trader can run **completely independently** of Streamlit. You have two options:

1. **Manual Background Process** - Start it manually, runs until you stop it
2. **Windows Scheduled Task** - Runs automatically on startup, only during market hours

## Option 1: Manual Background Process (Simple)

### Start the trader:
```bash
START_AUTONOMOUS_TRADER.bat
```

Or manually:
```bash
python trader/run_autonomous.py --mode continuous --interval 300 --paper
```

**What this does:**
- Runs the trader every 5 minutes (300 seconds)
- Only trades during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
- Uses paper trading mode (safe for testing)
- Runs until you press Ctrl+C or close the window

### To run in the background:
1. Open a new Command Prompt
2. Navigate to the project directory
3. Run: `START_AUTONOMOUS_TRADER.bat`
4. Minimize the window (it will keep running)

## Option 2: Windows Scheduled Task (Automatic)

This will make the trader start automatically every weekday at market open.

### Setup:
1. **Run as Administrator** (Right-click Command Prompt → "Run as administrator")
2. Navigate to project directory
3. Run:
   ```bash
   python START_AUTONOMOUS_TRADER_SERVICE.py
   ```
4. Follow the prompts

**What this creates:**
- Windows Scheduled Task named "AutonomousTrader"
- Runs: Monday-Friday, 9:25 AM - 4:15 PM ET
- Starts automatically when your computer boots (if booted before market open)
- Stops automatically after market close

### Managing the Task:
- **View**: Open Task Scheduler → Look for "AutonomousTrader"
- **Delete**: Run `schtasks /Delete /TN "AutonomousTrader" /F`
- **Start manually**: Task Scheduler → Right-click task → Run

## Important Notes

### Streamlit is NOT Required
- ✅ The autonomous trader runs independently
- ✅ The scanner runs via GitHub Actions (cloud-based)
- ✅ Streamlit is ONLY for viewing the dashboard/manual interaction
- ✅ You can close Streamlit and trading will continue

### What Runs When:

**Automated (No manual action needed):**
1. **Daily Scanner** - Runs at 9:30 AM ET via GitHub Actions (even if computer is off)
2. **Autonomous Trader** - If you set up the scheduled task, runs automatically during market hours

**Manual (Optional):**
1. **Streamlit Dashboard** - Only needed when you want to view/manually interact
2. **Manual Trader Start** - Only if you didn't set up scheduled task

## Trading Modes

### Paper Trading (Recommended for Testing)
```bash
python trader/run_autonomous.py --mode continuous --interval 300 --paper
```
- Uses fake money
- Safe for testing
- Real market data
- No real trades executed

### Live Trading (⚠️ Real Money)
```bash
python trader/run_autonomous.py --mode continuous --interval 300
# You'll be prompted to confirm
```
- Uses real money
- Real trades executed
- Make sure you understand the risks!

## Verification

### Check if trader is running:
1. Look for the command prompt window running `run_autonomous.py`
2. Or check Task Scheduler for the "AutonomousTrader" task status
3. Check `data/trade_history.json` for recent trades

### Check recent activity:
```bash
# View trade history
type data\trade_history.json

# View recent logs (if logging to file)
```

## Troubleshooting

### Trader not starting automatically:
- Check Task Scheduler → Verify task exists and is enabled
- Check task history for errors
- Make sure Python path is correct in the task

### Trader stops unexpectedly:
- Check Windows Event Viewer for errors
- Verify API keys are set in `.env`
- Check internet connection
- Verify Alpaca account is active

### Want to stop the trader:
- **Manual mode**: Press Ctrl+C in the command window
- **Scheduled task**: Task Scheduler → Right-click → End
- Or run: `schtasks /End /TN "AutonomousTrader"`

## Recommended Setup

For maximum automation:
1. ✅ Set up GitHub Actions for daily scanning (already done)
2. ✅ Create Windows Scheduled Task for autonomous trader
3. ✅ Start Streamlit only when you want to view the dashboard

This way:
- Scanner runs in the cloud (even if computer is off)
- Trader runs automatically during market hours
- Dashboard is optional for viewing/manual interaction

