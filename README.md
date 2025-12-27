# 🤖 AI-Powered Hedge Fund Auto Trader

A fully autonomous trading system that scans markets, analyzes opportunities with AI, executes trades automatically, and learns from results. Combines the wisdom of Buffett (value investing), Dalio (risk management), and Simons (quantitative analysis) with cutting-edge AI decision-making.

## 🚀 Features

### 🤖 Autonomous AI Trading
- **Fully Automated**: Trades autonomously during market hours
- **AI-Powered**: Uses xAI Grok for intelligent decision-making
- **Confidence Scoring**: 1-10 confidence level for every trade
- **Risk Management**: Automatic position sizing and stop-losses
- **Learning System**: Improves from every trade
- **Real-Time Monitoring**: Tracks positions 24/7
- **Email Alerts**: Notified of all trades instantly

### 📊 Automated Market Scanning
- **200+ Stock Universe**: Tech, finance, healthcare, consumer, energy
- **Multi-Factor Scoring**: Fundamental + Technical + Risk + Timing
- **Smart Categorization**: Hot (80+), Warming (70-79), Watching (60-69)
- **Daily Automation**: Scans at 9:30 AM ET via GitHub Actions
- **Entry/Exit Targets**: Pre-calculated stop-loss and profit targets

### 💻 Web Dashboard
- **Real-Time Overview**: Portfolio value, positions, and P/L
- **AI Insights**: View AI reasoning for every trade
- **Performance Tracking**: Win rate, profit factor, lessons learned
- **Stock Analyzer**: Deep fundamental and technical analysis
- **Portfolio Simulator**: Monte Carlo projections
- **Trade History**: Complete audit trail with CSV export

## 🎯 How It Works

### 1. Market Scanning (Daily at 9:30 AM ET)
```
→ Scan 200+ stocks across 7 sectors
→ Calculate multi-factor scores (0-100):
  • Fundamental (40%): PE ratio, ROE, revenue growth, margins
  • Technical (30%): Moving averages, RSI, volume
  • Risk/Reward (20%): 52-week metrics, beta
  • Timing (10%): Recent momentum
→ Categorize stocks:
  • Hot (80+): Ready to trade NOW
  • Warming (70-79): Close, monitor daily
  • Watching (60-69): Long-term tracking
→ Calculate entry prices, stop-losses, targets
→ Save to JSON files
→ Commit to GitHub
```

### 2. Autonomous Trading (Every 5 min during market hours)
```
→ Load hot stocks (score >= 80)
→ Check existing positions:
  • Monitor stop-loss levels
  • Monitor target levels
  • Exit positions automatically
→ For each hot stock:
  • Fetch real-time market data
  • AI analysis via xAI Grok
  • Get confidence score (1-10)
  • Check risk rules:
    ✓ Confidence >= 7/10
    ✓ Portfolio heat < 6%
    ✓ No duplicate positions
    ✓ Position size <= 10%
  • If approved → Execute trade via Alpaca
  • Send email notification
→ Learn from closed trades
→ Update performance metrics
```

### 3. AI Decision Process
```
INPUT:
  • Stock score breakdown
  • Fundamental metrics
  • Technical indicators
  • Market conditions
  • Past lessons learned

AI ANALYSIS (xAI Grok):
  → Evaluates opportunity
  → Assigns confidence (1-10)
  → Provides reasoning
  → Identifies risks
  → Recommends: BUY / SKIP / WAIT

OUTPUT:
  → Trade execution (if approved)
  → Notification sent
  → Lesson recorded
```

## 🛠️ Setup

### Prerequisites
- Python 3.10+
- Alpaca Paper Trading Account (free at [alpaca.markets](https://alpaca.markets))
- xAI API Key (from [console.x.ai](https://console.x.ai))
- SendGrid Account (optional, for emails)

### Quick Start

1. **Clone and install**
```bash
git clone <your-repo-url>
cd hedge_fund_app
pip install -r requirements.txt
```

2. **Configure API keys**
```bash
cp .env.example .env
# Edit .env and add your keys:
# XAI_API_KEY=xxx
# ALPACA_API_KEY=xxx (paper trading)
# ALPACA_SECRET_KEY=xxx (paper trading)
# SENDGRID_API_KEY=xxx (optional)
```

3. **Run the scanner** (one-time test)
```bash
python scanner/run_daily_scan.py
```

4. **Test autonomous trader** (safe mode)
```bash
cd trader
python run_autonomous.py --mode once --paper
```

5. **Launch dashboard**
```bash
streamlit run app.py
# Open http://localhost:8501
```

### GitHub Actions Setup (Automated Trading)

1. **Push to GitHub**
```bash
git add .
git commit -m "Setup autonomous trader"
git push origin main
```

2. **Add Repository Secrets**
   - Go to Settings → Secrets and variables → Actions
   - Add New Repository Secret for each:
     - `ALPACA_API_KEY`
     - `ALPACA_SECRET_KEY`
     - `XAI_API_KEY`
     - `SENDGRID_API_KEY` (optional)

3. **Enable Workflows**
   - Go to Actions tab
   - Enable workflows if prompted
   - Grant write permissions: Settings → Actions → General → Workflow permissions → Read and write

4. **Done!**
   - Scanner runs daily at 9:30 AM ET
   - Autonomous trader runs every 5 minutes during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)

## 📖 Usage Guide

### Dashboard Overview

**Page 1: Home**
- Portfolio metrics and projections
- Strategy mix (Buffett/Dalio/Simons)
- 5-year financial projections

**Page 2: Stock Analyzer**
- Deep fundamental analysis
- Technical indicators and charts
- AI-powered recommendations
- Position sizing calculator

**Page 3: Portfolio Simulator**
- Monte Carlo simulations
- 5-year projections
- Risk/reward analysis

**Page 4: Stock Scanner**
- Manual scan interface
- Filter by score threshold
- Sector-specific scans

**Page 5: Trade Desk**
- Hot stocks (score 80+)
- Warming stocks (70-79)
- Manual trade logging

**Page 6: Autonomous Trader** ⭐ NEW
- Real-time position monitoring
- AI decision insights
- Performance metrics
- Trade history with AI reasoning
- Learning dashboard

### Running Modes

**Manual Mode** (for testing):
```bash
# Single run
cd trader
python run_autonomous.py --mode once --paper

# Continuous (every 5 min)
python run_autonomous.py --mode continuous --interval 300 --paper
```

**Automated Mode** (production):
- Runs via GitHub Actions automatically
- Every 5 minutes during market hours
- Monday-Friday, 9:30 AM - 4:00 PM ET
- Always paper trading by default

### Email Notifications

To enable email alerts:

1. **Get SendGrid API key** from [sendgrid.com](https://sendgrid.com)

2. **Add to .env**:
```
SENDGRID_API_KEY=your_key_here
```

3. **Update config.yaml**:
```yaml
notifications:
  enabled: true
  email:
    from: "trader@yourapp.com"
    to: "your_email@example.com"
```

4. **Notifications you'll receive**:
   - Trade executed (with AI reasoning)
   - Position closed (with P/L)
   - Daily digest (performance summary)
   - Error alerts

## 📁 Project Structure

```
hedge_fund_app/
├── app.py                          # Main dashboard
├── trader/                         # 🤖 Autonomous trading system
│   ├── autonomous_trader.py        # Core AI trader with Alpaca
│   └── run_autonomous.py           # Execution runner
├── scanner/                        # Market scanning engine
│   ├── stock_universe.py           # 200+ stocks by sector
│   ├── scoring.py                  # Multi-factor scoring
│   ├── market_scanner.py           # Scanner orchestrator
│   └── run_daily_scan.py           # CLI entry point
├── utils/                          # Shared utilities
│   ├── core.py                     # StockAnalyzer, XAIStrategyGenerator
│   ├── storage.py                  # JSON persistence
│   └── notifications.py            # Email alerts (SendGrid)
├── pages/                          # Streamlit UI
│   ├── 01_Stock_Analyzer.py        # Deep analysis + AI
│   ├── 02_Portfolio_Simulator.py   # Monte Carlo
│   ├── 03_Stock_Scanner.py         # Manual scanner
│   ├── 04_Trade_Desk.py            # Hot opportunities
│   └── 05_Autonomous_Trader.py     # 🤖 AI trader dashboard
├── data/                           # Auto-generated data
│   ├── hot_stocks.json             # Score >= 80
│   ├── warming_stocks.json         # Score 70-79
│   ├── watching_stocks.json        # Score 60-69
│   ├── trade_history.json          # All trades
│   ├── trade_lessons.json          # AI learning data
│   └── scan_progress.json          # Scan metadata
├── .github/workflows/
│   ├── daily_scan.yml              # Scanner automation
│   └── autonomous_trading.yml      # 🤖 Trading automation
├── config.yaml                     # Configuration
├── .env                            # API keys (not committed)
├── .env.example                    # Template
└── requirements.txt                # Dependencies
```

## 💰 Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| GitHub Actions | **FREE** | 2000 min/month included |
| Alpaca Paper Trading | **FREE** | Unlimited |
| xAI Grok API | ~$1-5/month | Pay per use |
| SendGrid (optional) | FREE tier | 100 emails/day |
| **Total** | **$1-5/month** | Mostly free! |

## 🛡️ Risk Management

### Built-in Safety Features

1. **Paper Trading Default**: Always safe mode unless explicitly changed
2. **Position Sizing**: Max 10% of portfolio per position
3. **Stop Losses**: Automatic 10% stop on every trade
4. **Portfolio Heat**: Max 6% total risk across all positions
5. **Risk Per Trade**: Max 2% portfolio loss per trade
6. **AI Confidence Threshold**: Min 7/10 required
7. **No Duplicates**: One position per ticker maximum

### Example Trade
```
Portfolio Value: $10,000
Max Loss Per Trade: 2% = $200
Stock: AAPL @ $100
Stop Loss: $90 (10% below entry)
Stop Loss Distance: $10
Shares: $200 / $10 = 20 shares
Position Value: 20 × $100 = $2,000 (20% of portfolio)

❌ Too large! Scale down to 10% max:
Max Position: $10,000 × 10% = $1,000
Shares: 10
Final Position: $1,000 (10% of portfolio)
Max Risk: $100 (1% of portfolio)
```

## 🐛 Troubleshooting

### "ALPACA_API_KEY not set"
```bash
# Check .env file exists and has keys
cat .env

# Should contain:
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret
```

### "XAI API error"
- Verify key is valid at [console.x.ai](https://console.x.ai)
- Check API usage/credits
- Ensure key in .env and GitHub secrets

### "No hot stocks found"
```bash
# Run scanner manually
python scanner/run_daily_scan.py

# Check output
ls data/
cat data/hot_stocks.json
```

### GitHub Actions not running
1. Check Actions tab for errors
2. Verify all secrets are set correctly
3. Check workflow permissions: Settings → Actions → General → Read and write
4. Manually trigger: Actions → Select workflow → Run workflow

### Autonomous trader not executing trades
- Check if market is open (9:30 AM - 4:00 PM ET, Mon-Fri)
- Verify Alpaca keys are valid
- Check if confidence threshold is met (>= 7/10)
- Review portfolio heat (must be < 6%)
- Check logs in GitHub Actions or terminal output

### Email notifications not working
```yaml
# In config.yaml, ensure:
notifications:
  enabled: true  # Must be true
  email:
    to: "your_actual_email@example.com"
```
- Add SENDGRID_API_KEY to .env
- Verify from SendGrid dashboard that API key is active

## 📈 Performance Tracking

The system tracks:
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Total wins ÷ total losses
- **Average Win/Loss**: Mean profit and loss per trade
- **Confidence Correlation**: Performance by AI confidence level
- **Lessons Learned**: Extracted insights from every trade

## 🔧 Customization

### Adjust Trading Parameters

Edit `trader/autonomous_trader.py`:
```python
self.max_position_size = 0.10      # 10% max per position
self.max_loss_per_trade = 0.02     # 2% max loss per trade
self.confidence_threshold = 7      # Min AI confidence (1-10)
self.max_portfolio_heat = 0.06     # 6% max total risk
self.stop_loss_pct = 0.10          # 10% stop loss
self.target_profit_pct = 0.15      # 15% profit target
```

### Modify Stock Universe

Edit `scanner/stock_universe.py` to add/remove stocks.

### Adjust Scoring Algorithm

Edit `scanner/scoring.py` → `StockScorer` class to change weights:
```python
# Current weights:
FUNDAMENTAL_WEIGHT = 0.40  # 40%
TECHNICAL_WEIGHT = 0.30    # 30%
RISK_REWARD_WEIGHT = 0.20  # 20%
TIMING_WEIGHT = 0.10       # 10%
```

### Change Scan Schedule

Edit `.github/workflows/daily_scan.yml`:
```yaml
schedule:
  - cron: '30 13 * * 1-6'  # 9:30 AM ET = 13:30 UTC
```

Edit `.github/workflows/autonomous_trading.yml`:
```yaml
schedule:
  - cron: '*/5 13-20 * * 1-5'  # Every 5 min during market hours
```

## ⚠️ Important Disclaimers

**This software is for educational purposes only.**

- ⚠️ **Not Financial Advice**: This tool does not provide financial advice
- 📄 **Paper Trading Recommended**: Always use paper trading to test strategies
- 💸 **Risk of Loss**: Real money trading carries significant risk of loss
- 📊 **No Guarantees**: Past performance does not guarantee future results
- 👤 **Your Responsibility**: You are solely responsible for your trading decisions
- 🔍 **Do Your Research**: Always conduct your own due diligence
- 💼 **Consult Professionals**: Seek advice from licensed financial advisors

**By using this software, you acknowledge these risks and agree that the developers are not liable for any losses incurred.**

## 🚀 Future Enhancements

- [ ] Backtesting framework
- [ ] Multiple trading strategies (momentum, mean reversion, etc.)
- [ ] Options trading support
- [ ] Real-time sentiment analysis (news, social media)
- [ ] Portfolio correlation analysis
- [ ] Tax loss harvesting
- [ ] Advanced ML pattern recognition
- [ ] Multi-timeframe analysis (1min, 5min, daily)
- [ ] Sector rotation strategies
- [ ] Dynamic position sizing based on volatility

## 📚 Resources

- **Alpaca Docs**: https://docs.alpaca.markets/
- **xAI Grok**: https://docs.x.ai/
- **yfinance**: https://pypi.org/project/yfinance/
- **Streamlit**: https://docs.streamlit.io/
- **GitHub Actions**: https://docs.github.com/en/actions

## 🤝 Contributing

This is a personal project, but suggestions and bug reports are welcome via GitHub Issues.

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For help:
1. Read this README thoroughly
2. Check the Troubleshooting section
3. Review code comments in relevant files
4. Check GitHub Actions logs for errors
5. Open a GitHub Issue with details

---

**Built with:** Python • Streamlit • Alpaca API • xAI Grok • yfinance • GitHub Actions

**Status:** ✅ Fully functional autonomous trading system in paper trading mode

**Last Updated:** December 2025
