# GitHub Actions Automated Scanning Setup

## Overview

Your scanner is configured to run **automatically in the cloud** via GitHub Actions, which means it can scan stocks even when your computer is offline. The workflow runs daily at **9:30 AM ET (1:30 PM UTC)** Monday through Saturday.

## Current Status

⚠️ **The workflow file exists but may not be running.** Your last scan was on 12/27 or 12/30, which suggests the automated scans may have stopped.

## How to Verify It's Working

### 1. Check GitHub Actions Runs

1. Go to your GitHub repository: `https://github.com/mdavisyoung/hedge-fund-scanner`
2. Click on the **"Actions"** tab
3. Look for **"Daily Market Scanner"** workflow runs
4. Check if there are recent successful runs (should see runs around 9:30 AM ET on weekdays)

### 2. Verify Required Setup

For GitHub Actions to work, you need:

#### ✅ Workflow File (DONE)
- File exists at: `.github/workflows/daily_scan.yml`
- Scheduled to run: `30 13 * * 1-6` (9:30 AM ET, Mon-Sat)

#### ⚠️ GitHub Secrets (NEEDS VERIFICATION)
The workflow requires `XAI_API_KEY` to be set as a GitHub secret:

1. Go to: `https://github.com/mdavisyoung/hedge-fund-scanner/settings/secrets/actions`
2. Click **"New repository secret"**
3. Name: `XAI_API_KEY`
4. Value: Your XAI API key (from your `.env` file)
5. Click **"Add secret"**

#### ⚠️ GitHub Actions Permissions (NEEDS VERIFICATION)
The workflow needs permission to write back to the repository:

1. Go to: `https://github.com/mdavisyoung/hedge-fund-scanner/settings/actions`
2. Under **"Workflow permissions"**, ensure:
   - ✅ **"Read and write permissions"** is selected
   - ✅ **"Allow GitHub Actions to create and approve pull requests"** is checked

### 3. Test the Workflow Manually

You can manually trigger a scan to test if everything works:

1. Go to: `https://github.com/mdavisyoung/hedge-fund-scanner/actions`
2. Click on **"Daily Market Scanner"** workflow
3. Click **"Run workflow"** button (top right)
4. Select branch: `main`
5. Click **"Run workflow"**
6. Watch the workflow run in real-time
7. If successful, you should see commits with scan results in the `data/` directory

### 4. Check Recent Scans

After a scan runs, you should see:

1. **New commits** in the repository with messages like: `🤖 Daily scan: 2025-01-XX XX:XX`
2. **Updated files** in `data/`:
   - `hot_stocks.json`
   - `warming_stocks.json`
   - `watching_stocks.json`
   - `scan_progress.json` (with updated `last_scan` timestamp)

## Troubleshooting

### Problem: No workflow runs appear

**Solution:**
- GitHub Actions might be disabled for the repository
- Go to repository Settings → Actions → General
- Ensure **"Allow all actions and reusable workflows"** is enabled

### Problem: Workflow runs but fails

**Common causes:**
1. **Missing XAI_API_KEY secret** - Add it in Settings → Secrets → Actions
2. **Dependencies fail to install** - Check the workflow logs
3. **API rate limits** - Check if Polygon/XAI APIs are rate-limiting

### Problem: Workflow runs but doesn't commit results

**Solution:**
- Check if workflow has write permissions (see Step 2 above)
- The workflow uses `continue-on-error: true` for the push step, so failures are silent

## Schedule

The workflow runs:
- **Weekdays (Mon-Fri)**: Full batch scan at 9:30 AM ET
- **Saturday**: Re-scans hot/warming stocks only at 9:30 AM ET
- **Sunday**: No scan (market closed)

## What Happens During a Scan

1. GitHub Actions starts a virtual machine
2. Checks out your code
3. Installs Python dependencies
4. Runs `scanner/run_daily_scan.py`
5. Scans stocks based on the day of the week
6. Saves results to `data/*.json` files
7. Commits and pushes results back to the repository
8. You pull the updates next time you open the app

## Manual Local Scanning

If GitHub Actions isn't working, you can still run scans manually:

```bash
python scanner/run_daily_scan.py
```

Or use the Streamlit UI: Go to "Auto Trading Hub" → "Market Scanner" tab → Click "Run Full Scan"

## Next Steps

1. ✅ Verify GitHub Actions is enabled
2. ✅ Set XAI_API_KEY secret
3. ✅ Ensure write permissions are enabled
4. ✅ Manually trigger a test run
5. ✅ Monitor for daily automated runs starting tomorrow

---

**Note:** The scan will only run automatically if all the above setup is complete. The workflow file existing is just the first step - GitHub needs to be configured to actually run it.
