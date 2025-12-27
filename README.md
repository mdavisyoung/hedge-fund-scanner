# 🏦 Personal Hedge Fund Manager with Automated Scanner

A Streamlit-based investment management tool with automated market scanning, inspired by Buffett, Dalio, and Simons.

## 🚀 Features

### Core App
- 📈 Stock analysis with fundamental metrics
- 🤖 AI-powered strategy recommendations (xAI Grok)
- 🎲 Portfolio simulation (Monte Carlo)
- ⚖️ Risk parity allocation
- 💼 Position sizing calculator

### NEW: Automated Scanner
- 🔍 Scans 300+ stocks daily across all sectors
- 🔥 Hot opportunities (score 80+) - Ready to trade
- 🟡 Warming stocks (score 70-79) - Almost there
- 👀 Watching list (score 60-69) - Long-term tracking
- 🤖 Runs automatically via GitHub Actions (FREE)
- ☁️ Access anywhere - phone, tablet, computer

## 📊 How the Scanner Works

### Rolling Weekly Scan
- **Monday**: Tech & Growth stocks (S&P 500 tech + popular movers)
- **Tuesday**: Financials & Energy
- **Wednesday**: Healthcare & Consumer
- **Thursday**: Consumer & Small/Mid caps
- **Friday**: Industrials & remaining Small/Mid caps
- **Saturday**: Re-scan ALL hot + warming stocks (priority check)
- **Sunday**: Rest day

### Smart Tracking
- **Hot stocks** (80+ score): Ready to buy NOW
- **Warming stocks**: Checked DAILY, even on off-days
- **Auto-promotion**: When warming stocks hit 80+, they move to Hot
- **Auto-cleanup**: Stocks below thresholds are removed

## 🛠️ Setup

### Local Setup (One-Time)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Create `.env` file**:
```bash
cp .env.example .env
# Add your xAI API key
```

3. **Test locally**:
```bash
streamlit run app.py
```

### Cloud Deployment (Permanent)

1. **Create GitHub repo** (private recommended)

2. **Push code**:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

3. **Add GitHub Secret**:
   - Go to repo Settings → Secrets → Actions
   - Add `XAI_API_KEY` with your xAI key

4. **Deploy to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repo
   - Add secrets (same XAI_API_KEY)
   - Deploy!

5. **Done!** Scanner runs automatically at 9:30am ET daily

## 📱 Mobile Access

### Add to Home Screen

**iPhone**:
1. Open your Streamlit app in Safari
2. Tap Share → "Add to Home Screen"
3. Now it works like a native app!

**Android**:
1. Open app in Chrome
2. Menu → "Add to Home screen"

## 📁 Project Structure

```
hedge_fund_app/
├── app.py                          # Main dashboard
├── utils.py                        # Core utilities
├── pages/
│   ├── 01_Stock_Analyzer.py       # Stock analysis
│   ├── 02_Portfolio_Simulator.py  # Simulations
│   ├── 03_Stock_Scanner.py        # Manual scanner
│   └── 04_Trade_Desk.py           # Hot opportunities
├── scanner/
│   ├── market_scanner.py          # Scanner engine
│   ├── scoring.py                 # Trade scoring
│   ├── stock_universe.py          # Daily stock batches
│   └── run_daily_scan.py          # Entry point
├── utils/
│   └── storage.py                 # Data persistence
├── data/                          # Scan results (auto-generated)
│   ├── hot_stocks.json
│   ├── warming_stocks.json
│   ├── watching_stocks.json
│   ├── scan_progress.json
│   └── trade_history.json
├── .github/
│   └── workflows/
│       └── daily_scan.yml         # Automated scanning
├── .streamlit/
│   └── config.toml                # UI config
├── config.yaml                    # Scanner settings
└── requirements.txt
```

## 💰 Cost

- **GitHub Actions**: FREE (2000 min/month)
- **Streamlit Cloud**: FREE (personal use)
- **xAI Grok API**: ~$1-5/month (pay per use)
- **Total**: ~$1-5/month

## 🔔 Daily Workflow

1. **8:00am**: Check email for hot stocks (optional notification)
2. **Morning**: Open Trade Desk on phone/computer
3. **Review**: 3-10 hot opportunities with AI insights
4. **Execute**: Trade through your broker
5. **Log**: Click "Log Trade" to track in app
6. **Monitor**: Check warming stocks for future opportunities

## 🐛 Troubleshooting

### Scanner not running?
- Check GitHub Actions tab for errors
- Verify `XAI_API_KEY` secret is set
- Check workflow permissions (Settings → Actions → Read/Write)

### No stocks showing?
- First scan happens next business day at 9:30am ET
- Check `data/scan_progress.json` for last scan time
- Run manually: Actions → Daily Market Scanner → Run workflow

### Streamlit app won't load?
- Check Streamlit Cloud logs
- Verify secrets are set
- Ensure requirements.txt is correct

## 📈 Customization

Edit `scanner/stock_universe.py` to:
- Add/remove stocks from daily batches
- Change sector focus
- Add international stocks

Edit `scanner/scoring.py` to:
- Adjust scoring weights
- Modify thresholds
- Add custom criteria

Edit `.github/workflows/daily_scan.yml` to:
- Change scan time
- Adjust frequency
- Add notifications

## ⚠️ Disclaimer

This tool is for educational purposes only. Not financial advice. 
Always consult a professional advisor before investing.

## 🆘 Support

Questions? Check:
1. This README
2. Code comments
3. GitHub Issues tab
