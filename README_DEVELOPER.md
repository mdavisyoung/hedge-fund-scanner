# Developer Guide - Autonomous Hedge Fund Scanner

## Quick Start

### Running Tests
```bash
# Run all system tests
python test_system.py

# Expected: 7/7 tests passing
```

### Running Scanner
```bash
# Run daily market scan
python scanner/run_daily_scan.py

# Check output
cat data/hot_stocks.json
```

### Running Trader (Requires API Keys)
```bash
# Set up .env first with API keys
python trader/run_autonomous.py --mode once --paper
```

### Running Backtests
```bash
# Quick test (5 stocks, 3 months)
python run_backtest.py --preset q1_2024 --universe test

# Full year 2024
python run_backtest.py --preset 2024 --universe tech

# Custom date range
python run_backtest.py --start 2024-01-01 --end 2024-06-30 --universe mag7

# Available universes: test, tech, sp500_tech, growth, financials, faang, mag7
# Available presets: ytd, 2024, 2023, q1_2024, q2_2024, q3_2024, q4_2024, 6m, 3m, 1m
```

---

## Project Structure

```
hedge-fund-scanner/
├── scanner/                      # Stock scanning system
│   ├── run_daily_scan.py        # Entry point (runs at 9:30 AM ET)
│   ├── market_scanner.py        # Main scanning orchestration
│   ├── scoring.py               # Multi-factor scoring algorithm
│   └── stock_universe.py        # Stock list management (3,474 stocks)
│
├── trader/                       # Autonomous trading system
│   ├── run_autonomous.py        # Entry point (runs every 5 min)
│   └── autonomous_trader.py     # AI trading logic
│
├── backtesting/                  # NEW: Backtesting framework
│   ├── __init__.py
│   ├── backtest_engine.py       # Main backtesting orchestration
│   ├── historical_data.py       # Fetch & cache historical data
│   ├── simulated_trader.py      # Trader without real API calls
│   └── performance_metrics.py   # Performance calculations
│
├── utils/                        # Shared utilities
│   ├── storage.py               # JSON persistence
│   ├── notifications.py         # Email alerts
│   └── __init__.py              # Stock analyzer
│
├── data/                         # Data files (gitignored)
│   ├── hot_stocks.json          # Stocks scored >= 80
│   ├── warming_stocks.json      # Stocks scored 70-79
│   ├── watching_stocks.json     # Stocks scored 60-69
│   ├── trade_history.json       # All executed trades
│   ├── trade_lessons.json       # Learning from trades
│   └── exchange_tickers_cache.json  # Cached stock universe
│
├── .github/workflows/            # GitHub Actions automation
│   ├── daily_scan.yml           # Daily scanner (9:30 AM ET)
│   └── autonomous_trading.yml   # Trader (every 5 min)
│
├── test_system.py               # System test suite
├── run_backtest.py              # NEW: Easy backtesting interface
│
├── CLAUDE_NOTES.md              # NEW: Developer notes & reminders
├── SYSTEM_REVIEW.md             # Complete system analysis
├── FIXES_APPLIED.md             # Summary of fixes
└── README_DEVELOPER.md          # This file
```

---

## Key Components Explained

### 1. Scanner System
**Purpose:** Scan stocks daily and score them based on fundamentals, technicals, risk, and timing

**Entry Point:** `scanner/run_daily_scan.py`

**How it works:**
1. Loads stock universe (3,474 stocks from NASDAQ API + curated list)
2. Distributes stocks across weekdays (~700/day)
3. Scores each stock (0-100 scale)
4. Categorizes: Hot (80+), Warming (70-79), Watching (60-69)
5. Saves to JSON files
6. Git commits results

**Scoring Algorithm:**
- 40% Fundamentals (PE, ROE, revenue growth, debt)
- 30% Technicals (moving averages, RSI, volume)
- 20% Risk/Reward (distance from 52-week high, volatility)
- 10% Timing (momentum, market cap stability)

### 2. Trader System
**Purpose:** Analyze hot stocks with AI and execute trades automatically

**Entry Point:** `trader/run_autonomous.py`

**How it works:**
1. Loads hot stocks from scanner output
2. Checks existing positions for stop loss / target
3. Analyzes top 50 hot stocks with xAI Grok API
4. Gets AI confidence (1-10) and recommendation (BUY/SKIP/WAIT)
5. Executes trades if:
   - Confidence >= 7
   - Recommendation == BUY
   - Portfolio heat < 6%
   - Not already holding the stock
6. Position sizing: Max 2% loss per trade, 10% position size
7. Saves trade history and learns from results

### 3. Backtesting System (NEW)
**Purpose:** Test strategies on historical data without using real money or AI API

**Entry Point:** `run_backtest.py`

**How it works:**
1. Downloads historical price data (yfinance)
2. Simulates daily scanning and scoring
3. Simulates AI decisions (without calling real API)
4. Executes trades on historical data
5. Tracks daily portfolio value
6. Calculates comprehensive performance metrics

**Metrics Calculated:**
- Total return, annualized return, volatility
- Sharpe ratio, Sortino ratio, Calmar ratio
- Max drawdown, win rate, profit factor
- Average win/loss, best/worst trades
- Trading frequency, holding periods

---

## Development Workflow

### Daily Development Checklist
```bash
# 1. Update from git
git pull

# 2. Run tests
python test_system.py

# 3. Check stock universe health
python -c "from scanner.stock_universe import fetch_all_exchange_tickers; print(len(fetch_all_exchange_tickers()))"
# Should output: ~3474

# 4. Review CLAUDE_NOTES.md for context
cat CLAUDE_NOTES.md | grep "TODO"

# 5. Make changes...

# 6. Test changes
python test_system.py

# 7. Commit
git add .
git commit -m "Descriptive message"
git push
```

### Adding New Features
1. Read `CLAUDE_NOTES.md` for context
2. Create feature branch (optional)
3. Write tests first (TDD approach)
4. Implement feature
5. Run `python test_system.py`
6. Update `CLAUDE_NOTES.md` with notes
7. Commit with clear message

### Debugging Issues
1. Check `CLAUDE_NOTES.md` for similar issues
2. Run `python test_system.py` to isolate problem
3. Add debug logging
4. Test fix in isolation
5. Document fix in `CLAUDE_NOTES.md`

---

## Important Files to Read

### For Understanding the System
1. **SYSTEM_REVIEW.md** - Complete architectural analysis
2. **FIXES_APPLIED.md** - Summary of bugs fixed
3. **CLAUDE_NOTES.md** - Development notes and reminders
4. **README_DEVELOPER.md** - This file

### For Development
1. **test_system.py** - Test suite (run this frequently!)
2. **scanner/stock_universe.py** - Stock list management
3. **trader/autonomous_trader.py** - Trading logic
4. **backtesting/backtest_engine.py** - Backtesting framework

---

## API Keys Setup

Create `.env` file in root directory:

```bash
# Polygon.io (Primary Data Source - RECOMMENDED)
POLYGON_API_KEY=your_polygon_api_key

# Alpaca (Paper Trading)
ALPACA_API_KEY=your_paper_trading_key
ALPACA_SECRET_KEY=your_paper_trading_secret

# xAI Grok (AI Analysis)
XAI_API_KEY=your_xai_api_key

# SendGrid (Optional - Email Notifications)
SENDGRID_API_KEY=your_sendgrid_key
```

Get API keys:
- **Polygon.io**: https://polygon.io (free tier available, better rate limits than Yahoo)
- **Alpaca**: https://alpaca.markets (free paper trading account)
- **xAI**: https://x.ai/api (requires account)
- **SendGrid**: https://sendgrid.com (free tier available)

**Note:** The system uses Polygon.io as the primary data source for price data and market info, with Yahoo Finance as a fallback for fundamental ratios (PE, ROE, etc.). If you don't have a Polygon API key, the system will fall back to Yahoo Finance, but you may encounter rate limiting.

---

## Common Tasks

### Check System Health
```bash
python test_system.py
```

### View Hot Stocks
```python
from utils.storage import StorageManager

storage = StorageManager()
hot_stocks = storage.load_hot_stocks()

for stock in hot_stocks[:10]:
    print(f"{stock['ticker']}: {stock['score']['total_score']:.1f}")
```

### Manually Analyze a Stock
```python
from trader.autonomous_trader import AutonomousTrader

trader = AutonomousTrader(paper_trading=True)

stock = {
    'ticker': 'AAPL',
    'score': {'total_score': 85},
    'fundamentals': {'current_price': 180},
    'trade_plan': {'entry_price': 180, 'stop_loss': 162, 'target': 207}
}

analysis = trader.analyze_opportunity(stock)
print(f"Confidence: {analysis['confidence']}/10")
print(f"Recommendation: {analysis['recommendation']}")
print(f"Reasoning: {analysis['reasoning']}")
```

### Run Quick Backtest
```bash
# Test strategy on MAG7 stocks for Q1 2024
python run_backtest.py --preset q1_2024 --universe mag7

# View results
cat data/backtest_*.json | python -m json.tool
```

### Clear Caches
```python
# Clear stock universe cache
import os
os.remove('data/exchange_tickers_cache.json')

# Clear backtest cache
from backtesting.historical_data import HistoricalDataFetcher
fetcher = HistoricalDataFetcher()
fetcher.clear_cache()
```

---

## Performance Optimization Tips

### Reduce AI Costs
1. Limit to top 20 stocks instead of 50
2. Cache AI analysis for 1 hour per stock
3. Only re-analyze if score changes significantly
4. Use higher confidence threshold (8 instead of 7)

**Edit:** `trader/run_autonomous.py`
```python
# Change line 117:
hot_stocks = load_hot_stocks(storage, max_stocks=20)  # Was 50

# Change autonomous_trader.py line 62:
self.confidence_threshold = 8  # Was 7
```

### Speed Up Scanner
1. Reduce max_workers (less parallel requests)
2. Cache price data for multiple scans
3. Skip stocks that recently failed

**Edit:** `scanner/run_daily_scan.py`
```python
# Line 29:
scanner = MarketScanner(max_workers=5)  # Was 10
```

---

## Monitoring & Alerts

### Email Alerts (Optional)
Set up SendGrid API key to get email notifications for:
- Trades executed
- Positions closed (profit/loss)
- Daily loss limit hit
- System errors

### Manual Monitoring
```bash
# Watch trade history
tail -f data/trade_history.json

# Check portfolio heat
python -c "from trader.autonomous_trader import AutonomousTrader; t=AutonomousTrader(paper_trading=True); print(f'Portfolio heat: {t.get_portfolio_heat():.2%}')"
```

---

## Risk Management

### Current Safety Features
✅ Paper trading default
✅ 2% max loss per trade
✅ 10% max position size
✅ 6% max portfolio heat (total risk)
✅ 10% stop losses enforced
✅ Daily loss limit (2%)
✅ Market hours checking
✅ No weekend trading

### Before Live Trading
- [ ] Run 2+ weeks paper trading
- [ ] Verify win rate > 50%
- [ ] Verify profit factor > 1.5
- [ ] Add comprehensive logging
- [ ] Add email alerts
- [ ] Start with small capital ($500-1000)
- [ ] Have manual kill switch ready

---

## Troubleshooting

### "Only 210 stocks" Error
✅ **FIXED** - Stock universe now returns 3,474 stocks

If you see this again:
```python
from scanner.stock_universe import fetch_all_exchange_tickers
tickers = fetch_all_exchange_tickers(force_refresh=True)
print(len(tickers))  # Should be ~3474
```

### "AttributeError: is_market_open"
✅ **FIXED** - Added missing methods to autonomous_trader.py

### UnicodeEncodeError on Windows
Replace emoji characters in print statements:
- ✅ → [OK]
- ❌ → [FAIL]
- 🔥 → [HOT]

### Tests Failing
```bash
# Clear caches and retry
rm data/exchange_tickers_cache.json
python test_system.py
```

---

## Contributing

### Code Style
- Use type hints for all functions
- Add docstrings to all functions
- Use logging instead of print (for production code)
- Write tests for new features
- Update CLAUDE_NOTES.md with context

### Before Committing
1. Run `python test_system.py` (all tests must pass)
2. Check for TODO/FIXME: `grep -r "TODO\|FIXME" --include="*.py"`
3. Update CLAUDE_NOTES.md if adding significant features
4. Write descriptive commit messages

---

## Useful Resources

### External APIs
- Alpaca API: https://alpaca.markets/docs/
- xAI Grok: https://x.ai/api
- yfinance: https://github.com/ranaroussi/yfinance

### Documentation
- **SYSTEM_REVIEW.md** - Full architectural analysis
- **FIXES_APPLIED.md** - Bug fixes summary
- **CLAUDE_NOTES.md** - Developer notes

### Quick Commands
```bash
# Run all tests
python test_system.py

# Run scanner
python scanner/run_daily_scan.py

# Run trader (requires API keys)
python trader/run_autonomous.py --mode once --paper

# Run backtest
python run_backtest.py --preset q1_2024 --universe test

# Check stock count
python -c "from scanner.stock_universe import fetch_all_exchange_tickers; print(len(fetch_all_exchange_tickers()))"

# View hot stocks count
python -c "from utils.storage import StorageManager; print(len(StorageManager().load_hot_stocks()))"
```

---

## Questions?

Check these files for answers:
1. **CLAUDE_NOTES.md** - Development context and reminders
2. **SYSTEM_REVIEW.md** - Complete system analysis
3. **FIXES_APPLIED.md** - What was fixed and why

For new development, update **CLAUDE_NOTES.md** with your learnings!

---

**Last Updated:** 2025-12-27
**Status:** System operational, all tests passing (7/7)
**Next Steps:** Set up API keys, run initial tests, then paper trading
