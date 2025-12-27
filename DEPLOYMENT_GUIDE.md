# 🚀 Deployment Guide

Complete guide to deploying your automated stock scanner.

## Quick Start (5 Minutes)

### Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com) and create a new repository
2. Name it `hedge-fund-scanner` (or anything you like)
3. Make it **Private** (recommended)
4. Don't initialize with README (we already have one)

### Step 2: Push Your Code

```bash
cd hedge_fund_app
git init
git add .
git commit -m "Initial commit: Hedge Fund Scanner"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Step 3: Add GitHub Secret

1. Go to your repo on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `XAI_API_KEY`
5. Value: Your xAI API key (from console.x.ai)
6. Click **Add secret**

### Step 4: Enable GitHub Actions

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select **Read and write permissions**
3. Check **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### Step 5: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repository
5. Branch: `main`
6. Main file: `app.py`
7. Click **Advanced settings**
8. Add secret: `XAI_API_KEY` (same value as GitHub)
9. Click **Deploy**

### Step 6: Test the Scanner

1. Go to your repo → **Actions** tab
2. Click **Daily Market Scanner**
3. Click **Run workflow** → **Run workflow**
4. Wait 2-3 minutes
5. Check the workflow run for success ✅

## Verify Everything Works

### Check GitHub Actions

1. Go to repo → **Actions** tab
2. You should see "Daily Market Scanner" workflow
3. It will run automatically at 9:30am ET daily
4. Or trigger manually anytime

### Check Streamlit App

1. Open your Streamlit app URL
2. Navigate to **Trade Desk** page
3. You should see scan results (after first scan runs)

### Check Data Files

1. Go to repo → **data/** folder
2. You should see JSON files:
   - `hot_stocks.json`
   - `warming_stocks.json`
   - `watching_stocks.json`
   - `scan_progress.json`

## Troubleshooting

### Workflow Fails

**Error: "XAI_API_KEY not found"**
- Go to Settings → Secrets → Actions
- Verify `XAI_API_KEY` is set correctly

**Error: "Permission denied"**
- Go to Settings → Actions → General
- Enable "Read and write permissions"

**Error: "Module not found"**
- Check `requirements.txt` has all dependencies
- Verify workflow installs dependencies correctly

### No Stocks Appearing

**First time setup:**
- Wait for first scan (9:30am ET next business day)
- Or trigger manually: Actions → Run workflow

**After first scan:**
- Check `data/scan_progress.json` for last scan time
- Verify stocks were found (check workflow logs)
- Check score thresholds (stocks need 60+ score)

### Streamlit App Issues

**App won't load:**
- Check Streamlit Cloud logs
- Verify secrets are set
- Check `requirements.txt` is correct

**No data showing:**
- Ensure GitHub Actions is running
- Check data files exist in repo
- Verify app can read from `data/` directory

## Customization

### Change Scan Time

Edit `.github/workflows/daily_scan.yml`:
```yaml
schedule:
  - cron: '30 13 * * 1-6'  # Change to your preferred time
```

Cron format: `minute hour day month weekday`
- 9:30am ET = 13:30 UTC
- Adjust for your timezone

### Add More Stocks

Edit `scanner/stock_universe.py`:
- Add tickers to appropriate lists
- They'll be included in next scan

### Adjust Scoring

Edit `scanner/scoring.py`:
- Modify weights in `TradeScorer.__init__()`
- Adjust thresholds in scoring methods

### Change Thresholds

Edit `config.yaml`:
```yaml
thresholds:
  hot: 80      # Change to 75 for more hot stocks
  warming: 70
  watching: 60
```

## Mobile Access

### iPhone

1. Open Streamlit app in Safari
2. Tap Share button (square with arrow)
3. Select "Add to Home Screen"
4. Name it "Trade Desk"
5. Tap "Add"

### Android

1. Open Streamlit app in Chrome
2. Tap menu (3 dots)
3. Select "Add to Home screen"
4. Confirm

## Cost Breakdown

- **GitHub Actions**: FREE (2000 minutes/month)
  - Daily scans use ~2-5 minutes
  - ~60-150 minutes/month
  - Well under free tier

- **Streamlit Cloud**: FREE
  - Unlimited apps
  - Unlimited usage
  - Perfect for personal use

- **xAI Grok API**: ~$1-5/month
  - Pay per use
  - Only charged when AI strategies are generated
  - Scanner doesn't use AI (only manual analysis does)

**Total: ~$1-5/month** (just API costs)

## Next Steps

1. ✅ Scanner running automatically
2. ✅ App deployed and accessible
3. 📱 Add to phone home screen
4. 🔔 Set up email notifications (optional)
5. 📊 Start logging trades
6. 📈 Monitor performance

## Support

- Check README.md for general info
- Check SCANNER_SYSTEM.md for technical details
- Check GitHub Issues for known problems
- Review workflow logs for errors

Happy scanning! 🔍📈

