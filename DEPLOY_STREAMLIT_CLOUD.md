# Deploy Streamlit App to Cloud (24/7 Access)

## Overview

Your scanner runs on GitHub Actions (cloud), but your Streamlit dashboard runs locally. To access it 24/7 from anywhere, deploy it to **Streamlit Cloud** (free).

## Quick Deploy to Streamlit Cloud (5 minutes)

### Step 1: Push Your Code to GitHub (if not already done)

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: https://share.streamlit.io
2. **Sign in with GitHub** (use the same account as your repo)
3. **Click "New app"**
4. **Fill in the details**:
   - **Repository**: Select `mdavisyoung/hedge-fund-scanner`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. **Click "Advanced settings"**
6. **Add secrets** (click "New secret" for each):
   - **Name**: `XAI_API_KEY`
     **Value**: Your xAI API key (from your `.env` file)
   - **Name**: `ALPACA_API_KEY` (if you have one)
     **Value**: Your Alpaca API key
   - **Name**: `ALPACA_SECRET_KEY` (if you have one)
     **Value**: Your Alpaca secret key
7. **Click "Deploy"**

### Step 3: Wait for Deployment

- Takes 2-3 minutes
- You'll see build logs in real-time
- Once done, you'll get a URL like: `https://hedge-fund-scanner-xxxxx.streamlit.app`

### Step 4: Access Your App

Your app is now live at the Streamlit Cloud URL! 
- ✅ Accessible 24/7 from anywhere
- ✅ Updates automatically when you push to GitHub
- ✅ Free to use

## ✅ App is Already Configured!

The app automatically supports both:
- **Local**: Uses `.env` file
- **Cloud**: Uses Streamlit secrets

No additional changes needed!

## What Gets Deployed

When you deploy to Streamlit Cloud:
- ✅ All your code is deployed
- ✅ Scanner results (from GitHub Actions) are automatically synced
- ✅ App updates whenever you push to GitHub
- ✅ Secrets are secure (stored in Streamlit Cloud, not in code)

## Notes About Dexter

**Important**: Dexter (NewsAdmin) runs locally and won't work on Streamlit Cloud since it requires:
- Node.js runtime
- Local file system access
- Port 3000 access

**Solutions:**
1. **Use Dexter locally only** - The "Chat with Dexter" page will show a warning if not available
2. **Deploy Dexter separately** - Host NewsAdmin on a service like Heroku/Railway
3. **Use other features** - Scanner, Trading Hub, Stock Analyzer all work perfectly on cloud

## Troubleshooting

### App Won't Deploy

**Error: "Module not found"**
- Check `requirements.txt` has all dependencies
- Verify all imports are correct

**Error: "Secret not found"**
- Go to Streamlit Cloud → App settings → Secrets
- Verify all secrets are set correctly

### App Deploys But Shows Errors

**"API key not found"**
- Check Streamlit Cloud secrets are set
- Make sure secret names match exactly (case-sensitive)

**"No data showing"**
- Make sure GitHub Actions scanner has run at least once
- Check that data files exist in your GitHub repo

### App Works But No Real-time Updates

- Streamlit Cloud syncs with GitHub on every push
- If you want to see scanner results immediately, pull from GitHub or wait for next scan
- Scanner runs daily at 9:30 AM ET via GitHub Actions

