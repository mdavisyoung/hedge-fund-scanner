# CLAUDE'S DEVELOPMENT NOTES
**Purpose:** Track development context, debugging info, and reminders for ongoing work
**Last Updated:** 2025-12-27

---

## QUICK REFERENCE - SYSTEM STATUS

### ✅ What's Working (As of 2025-12-27)
- Stock universe fetching (3,474 stocks)
- Scanner can score and categorize stocks
- Trader initialization and safety checks
- Market hours verification
- Daily loss limit enforcement
- Data flow between components
- All 7 system tests passing
- **Polygon.io as primary data source (NEW)**
  - Price data: Polygon (fast, reliable)
  - Historical data: Polygon (15-20min delayed on free tier)
  - Fundamentals (PE, ROE): Yahoo Finance fallback with retry logic
  - Graceful degradation when Yahoo is rate-limited

### 🔧 What's In Progress
- [ ] API keys not yet configured
- [ ] No real trades executed yet (waiting for API keys)
- [ ] No backtesting data collected yet
- [ ] Logging needs improvement (using print statements)
- [ ] No monitoring/alerting system

### 🐛 Known Issues
- None (all critical bugs fixed as of 2025-12-27)

### 📋 TODO - High Priority
1. Add comprehensive logging framework
2. Build backtesting system
3. Add retry logic for API failures
4. Create performance monitoring dashboard
5. Reduce AI costs (limit to top 20 stocks)

---

## ARCHITECTURE OVERVIEW

### Data Flow Map
```
scanner/run_daily_scan.py (9:30 AM ET daily)
  ↓
market_scanner.scan_daily_batch()
  ↓
scoring.py (scores stocks)
  ↓
storage.save_hot_stocks() → data/hot_stocks.json
  ↓
trader/run_autonomous.py (every 5 min)
  ↓
autonomous_trader.analyze_opportunity() → xAI Grok API
  ↓
autonomous_trader.execute_trade() → Alpaca API
  ↓
storage.save_trade_history() → data/trade_history.json
```

### Key Files by Purpose

**Scanner Components:**
- `scanner/run_daily_scan.py` - Entry point for daily scans
- `scanner/market_scanner.py` - Main scanning orchestration
- `scanner/scoring.py` - Multi-factor scoring algorithm
- `scanner/stock_universe.py` - Stock list management (FIXED: now returns 3,474 stocks)

**Trader Components:**
- `trader/run_autonomous.py` - Entry point for trading
- `trader/autonomous_trader.py` - AI trading logic (FIXED: added missing methods)

**Utilities:**
- `utils/storage.py` - JSON persistence
- `utils/notifications.py` - Email alerts
- `utils/__init__.py` - Stock analyzer

**Data Files:**
- `data/hot_stocks.json` - Stocks scored >= 80
- `data/warming_stocks.json` - Stocks scored 70-79
- `data/watching_stocks.json` - Stocks scored 60-69
- `data/trade_history.json` - All executed trades
- `data/trade_lessons.json` - Learning from closed trades
- `data/exchange_tickers_cache.json` - Cached stock universe (7 days)

**Configuration:**
- `.env` - API keys (not in git)
- `.github/workflows/daily_scan.yml` - Scanner automation
- `.github/workflows/autonomous_trading.yml` - Trader automation

---

## CRITICAL FIXES APPLIED (2025-12-27)

### Fix #1: Stock Universe Bug
**Problem:** Exchange filter was removing all stocks (NASDAQ API doesn't include 'exchange' field)
**Location:** `scanner/stock_universe.py:177-180`
**Solution:** Removed broken exchange filter
**Result:** 210 stocks → 3,474 stocks ✅

### Fix #2: Missing Trader Methods
**Problem:** `run_autonomous.py` called methods that didn't exist
**Location:** `trader/autonomous_trader.py`
**Added:**
- `is_market_open()` - Line 85-108
- `check_daily_loss_limit()` - Line 110-136
- `trading_paused`, `pause_reason`, `ai_call_count_today` - Line 80-83
**Result:** Trader can now run without crashing ✅

### Fix #3: No Testing
**Problem:** System never tested end-to-end
**Solution:** Created `test_system.py` with 7 tests
**Result:** All tests passing (7/7) ✅

---

## DEBUGGING GUIDE

### Common Issues & Solutions

#### Issue: "ALPACA_API_KEY must be set"
**Cause:** Missing `.env` file
**Fix:**
```bash
# Create .env file in root directory:
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret
XAI_API_KEY=your_xai_key
SENDGRID_API_KEY=your_sendgrid_key  # optional
```

#### Issue: Scanner returns < 1000 stocks
**Cause:** Cache is stale or API failed
**Fix:**
```python
# Force refresh cache
from scanner.stock_universe import fetch_all_exchange_tickers
tickers = fetch_all_exchange_tickers(force_refresh=True)
print(len(tickers))  # Should be ~3,474
```

#### Issue: Trader skips all opportunities
**Cause:** AI confidence threshold too high or all stocks already owned
**Debug:**
```python
# Check what AI is saying
trader = AutonomousTrader(paper_trading=True)
stock = {...}  # Load from hot_stocks.json
analysis = trader.analyze_opportunity(stock)
print(f"Confidence: {analysis['confidence']}")
print(f"Recommendation: {analysis['recommendation']}")
print(f"Reasoning: {analysis['reasoning']}")
```

#### Issue: UnicodeEncodeError on Windows
**Cause:** Emoji characters in print statements
**Fix:** Replace emoji with ASCII:
- ✅ → [OK]
- ❌ → [FAIL]
- 🔥 → [HOT]
- → → to (for arrows)

#### Issue: Market hours check fails
**Cause:** Missing `pytz` library
**Fix:**
```bash
pip install pytz
```

---

## TESTING CHECKLIST

### Before Each Development Session
```bash
# 1. Run system tests
python test_system.py

# 2. Check stock universe
python -c "from scanner.stock_universe import fetch_all_exchange_tickers; print(len(fetch_all_exchange_tickers()))"

# 3. Verify data files exist
ls data/*.json

# 4. Check git status
git status
```

### Manual Testing Workflow
```bash
# Test scanner (no API keys needed)
python scanner/run_daily_scan.py

# Check output
cat data/hot_stocks.json | python -m json.tool | head -50

# Test trader (requires API keys)
python trader/run_autonomous.py --mode once --paper

# Check trade history
cat data/trade_history.json | python -m json.tool
```

### Automated Test Suite
```bash
# Run all tests
python test_system.py

# Expected output:
# [PASS] imports
# [PASS] stock_universe
# [PASS] daily_batch
# [PASS] trader_init
# [PASS] scanner
# [PASS] storage
# [PASS] data_flow
# SUMMARY: 7/7 tests passed
```

---

## BACKTESTING FRAMEWORK (TO BUILD)

### Design Plan

**Goal:** Test trading strategies on historical data without using real money or APIs

**Components Needed:**
1. Historical data fetcher (yfinance)
2. Simulated market environment
3. Performance metrics calculator
4. Strategy comparison tool

**File Structure:**
```
backtesting/
├── __init__.py
├── backtest_engine.py       # Main backtesting engine
├── historical_data.py        # Fetch & cache historical data
├── simulated_trader.py       # Trader without real API calls
├── performance_metrics.py    # Calculate returns, Sharpe, etc.
└── reports.py                # Generate backtest reports
```

**Usage (Future):**
```python
from backtesting import BacktestEngine

# Test strategy on historical data
engine = BacktestEngine(
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=100_000
)

results = engine.run_backtest(
    strategy='autonomous_ai',
    universe=hot_stocks
)

print(f"Total Return: {results['total_return']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
```

### Metrics to Track
- **Returns:** Total, daily, monthly, annualized
- **Risk:** Max drawdown, volatility, beta
- **Win Rate:** % profitable trades
- **Profit Factor:** Gross profit / gross loss
- **Sharpe Ratio:** Risk-adjusted returns
- **AI Accuracy:** How often AI confidence correlates with wins

---

## PERFORMANCE MONITORING

### Key Metrics to Track

**Scanner Performance:**
```python
{
    "scan_duration_seconds": 180,
    "stocks_scanned": 700,
    "hot_stocks_found": 15,
    "warming_stocks_found": 25,
    "api_calls_made": 700,
    "errors_encountered": 3,
    "scan_timestamp": "2025-12-27T09:30:00"
}
```

**Trader Performance:**
```python
{
    "run_timestamp": "2025-12-27T09:35:00",
    "stocks_analyzed": 15,
    "ai_calls_made": 15,
    "trades_executed": 2,
    "trades_skipped": 13,
    "avg_confidence": 6.8,
    "portfolio_heat": 0.04,
    "current_positions": 2
}
```

**Overall System Health:**
```python
{
    "uptime_hours": 72,
    "total_trades": 45,
    "win_rate": 0.58,
    "profit_factor": 1.85,
    "total_return_pct": 12.5,
    "ai_cost_usd": 156.80,
    "last_error": None,
    "status": "healthy"
}
```

### Monitoring Dashboard (Future)
- Real-time portfolio value chart
- Trade history table with P/L
- AI confidence vs win rate correlation
- Daily/weekly/monthly returns
- Cost tracking (AI API calls)
- System health status

---

## CODE QUALITY REMINDERS

### Best Practices to Follow
1. **Always add type hints**
   ```python
   def analyze_stock(ticker: str) -> Dict[str, Any]:
       ...
   ```

2. **Use logging instead of print**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info(f"Scanning {ticker}")
   ```

3. **Add docstrings to all functions**
   ```python
   def calculate_score(fundamentals: Dict) -> float:
       """
       Calculate stock score from fundamentals.

       Args:
           fundamentals: Dict with PE, ROE, etc.

       Returns:
           Score from 0-100
       """
   ```

4. **Handle errors gracefully**
   ```python
   try:
       result = risky_operation()
   except SpecificError as e:
       logger.error(f"Failed: {e}")
       return default_value
   ```

5. **Write tests for new features**
   ```python
   def test_new_feature():
       result = new_feature(test_input)
       assert result == expected_output
   ```

---

## DATA SOURCE ARCHITECTURE (UPDATED 2025-12-27)

### Polygon.io Integration - Primary Data Source

**Why Polygon?**
- Better rate limits than Yahoo Finance (5 requests/min free tier)
- More reliable for price data
- 15-20 minute delayed data on free tier (acceptable for daily scanning)
- Professional API with consistent formatting

**Data Source Strategy:**

1. **Price Data (Primary: Polygon)**
   ```python
   # utils/polygon_fetcher.py
   - get_stock_quote(ticker) → current price, volume
   - get_stock_details(ticker) → market cap, exchange, company info
   - get_price_history(ticker, days) → OHLCV historical data
   ```

2. **Fundamental Ratios (Fallback: Yahoo Finance)**
   ```python
   # utils/core.py - StockAnalyzer.get_fundamentals()
   - PE ratio, ROE, debt-to-equity
   - Revenue growth, earnings growth
   - Current ratio, quick ratio
   - With 3-attempt retry logic + 2s delay
   ```

3. **Hybrid Approach:**
   - Try Polygon first for price/market data (fast, reliable)
   - Try Yahoo Finance for fundamental ratios (with retry)
   - If Yahoo fails → use Polygon-only mode with default ratios
   - System continues functioning even when Yahoo is rate-limited

**Key Files:**
- `utils/polygon_fetcher.py` - NEW: Polygon API wrapper
- `utils/core.py` - UPDATED: StockAnalyzer now uses Polygon by default
- `.env` - POLYGON_API_KEY configuration

**Testing:**
```bash
# Test Polygon integration
python test_polygon_integration.py

# Expected: All tests pass with Polygon data
# Falls back gracefully if Yahoo is rate-limited
```

**API Key Setup:**
```bash
# .env file
POLYGON_API_KEY=SxSVtBXjH15jPsp94nrYnZ3fPMTpGvFr
```

**Benefits:**
- No more Yahoo Finance 429 errors blocking the scanner
- Faster data fetches (Polygon optimized for trading)
- Graceful degradation when fundamentals unavailable
- System remains operational even with partial data

### Yahoo Finance Rate Limiting (UPDATED 2025-12-27)

**Why Rate Limiting?**
- Yahoo Finance tightened limits in 2025
- Community observations: ~48-60 requests/minute safe limit
- ~900-950 requests/day before potential IP blocking
- No official API documentation, limits vary

**Implementation:**

1. **Token Bucket Rate Limiter** (`utils/rate_limiter.py`)
   ```python
   YahooFinanceRateLimiter:
   - 48 requests/minute (conservative)
   - 900 requests/day (conservative)
   - 1 second minimum delay between calls
   - Thread-safe with locking
   ```

2. **Integrated into StockAnalyzer**
   - Automatic rate limiting on all Yahoo Finance calls
   - Exponential backoff on retries (2s, 4s, 8s)
   - Bulk download support for efficiency

3. **Best Practices Applied:**
   - Use `yf.download()` for bulk requests (one call for many tickers)
   - Add delays between requests (1s minimum)
   - Implement caching for repeated queries
   - Exponential backoff on errors
   - Prefer Polygon for price data (reduces Yahoo calls by ~70%)

**Rate Limiter Status:**
```python
from utils import StockAnalyzer
analyzer = StockAnalyzer()
status = analyzer.yahoo_limiter.get_status()
print(status)
# {'remaining_calls_this_minute': 45, 'remaining_calls_today': 850, 'safe_to_call': True}
```

**Sources:**
- [Why yfinance Keeps Getting Blocked](https://medium.com/@trading.dude/why-yfinance-keeps-getting-blocked-and-what-to-use-instead-92d84bb2cc01)
- [Rate Limiting Best Practices for yfinance](https://www.slingacademy.com/article/rate-limiting-and-api-best-practices-for-yfinance/)
- [yfinance Issue #2422 - Rate Limit Error](https://github.com/ranaroussi/yfinance/issues/2422)

---

## API COST TRACKING

### Current Costs (Estimated)

**Polygon.io:**
- Free tier: 5 API calls/minute
- No cost for current usage
- Delayed data (15-20 min) acceptable for daily scanning
- Upgrade to paid tier if need real-time data

**xAI Grok API:**
- Model: grok-3
- Cost: ~$0.005 per call
- Usage: 10-50 calls per run
- Runs: 78 per day (every 5 min during market hours)
- Daily cost: $2-20
- Monthly cost: $40-400

**Optimization Ideas:**
1. Limit to top 20 stocks instead of 50 (-60% cost)
2. Cache AI analysis for 1 hour per stock
3. Only re-analyze if stock score changes significantly
4. Use confidence threshold to skip low-quality stocks early

**Other API Costs:**
- Alpaca: Free for paper trading
- yfinance: Free (rate limited)
- NASDAQ API: Free (rate limited)
- SendGrid: Free tier available

---

## DEVELOPMENT WORKFLOW

### Adding New Features
1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Run test suite
5. Manual testing
6. Update documentation
7. Commit with clear message
8. Create PR (if collaborating)

### Debugging New Issues
1. Check CLAUDE_NOTES.md for similar issues
2. Run test_system.py to isolate problem
3. Add debug logging
4. Test fix in isolation
5. Run full test suite
6. Document fix in CLAUDE_NOTES.md
7. Update FIXES_APPLIED.md if critical

### Before Committing
```bash
# 1. Run tests
python test_system.py

# 2. Check for TODO/FIXME comments
grep -r "TODO\|FIXME" --include="*.py"

# 3. Format code (if using black)
# black .

# 4. Check git diff
git diff

# 5. Commit with descriptive message
git add .
git commit -m "Fix: Description of what was fixed"
```

---

## REMINDERS FOR FUTURE DEVELOPMENT

### Things to Remember
- Stock universe cache expires after 7 days (auto-refresh)
- AI calls are expensive ($5-20/day) - optimize!
- Paper trading is default (safe)
- Market hours: 9:30 AM - 4 PM ET, Mon-Fri
- Scanner runs at 9:30 AM ET via GitHub Actions
- Trader runs every 5 min during market hours
- Stop losses at -10%, targets at +15%
- Max 2% loss per trade, 6% total portfolio heat
- Daily loss limit: -2% (circuit breaker)

### Before Going Live with Real Money
- [ ] Run 2+ weeks paper trading
- [ ] Verify win rate > 50%
- [ ] Verify profit factor > 1.5
- [ ] Add comprehensive logging
- [ ] Add email alerts for all trades
- [ ] Add monitoring dashboard
- [ ] Start with small capital ($500-1000)
- [ ] Have manual kill switch ready
- [ ] Review all trades manually for first week

### Questions to Investigate
1. Can we improve scoring algorithm?
2. Should we add sector rotation detection?
3. Can we reduce AI costs without hurting performance?
4. Should we add options trading?
5. Can we backtest to validate strategy?
6. Should we add multi-timeframe analysis?
7. Can we detect market regime changes?

---

## USEFUL CODE SNIPPETS

### Analyze Stock with Polygon (No Rate Limits!)
```python
from dotenv import load_dotenv
load_dotenv()

from utils.polygon_fetcher import PolygonFetcher

fetcher = PolygonFetcher()

# Get current quote
quote = fetcher.get_stock_quote('HOOD')
print(f"Price: ${quote['current_price']:.2f}")
print(f"Volume: {quote['volume']:,}")

# Get company details
details = fetcher.get_stock_details('HOOD')
print(f"Market Cap: ${details['market_cap']/1e9:.2f}B")

# Get 30-day history
history = fetcher.get_price_history('HOOD', days=30)
print(f"Data points: {history['count']}")
```

### Check Stock Universe Health
```python
from scanner.stock_universe import fetch_all_exchange_tickers

tickers = fetch_all_exchange_tickers(force_refresh=True)
print(f"Total tickers: {len(tickers)}")
print(f"Sample: {tickers[:10]}")

# Should be ~3,474 tickers
assert len(tickers) > 3000, f"Stock universe too small: {len(tickers)}"
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
print(analysis)
```

### Check Trade History
```python
import json
from pathlib import Path

trade_file = Path("data/trade_history.json")
if trade_file.exists():
    with open(trade_file) as f:
        data = json.load(f)
        trades = data.get('trades', [])

        print(f"Total trades: {len(trades)}")
        closed = [t for t in trades if t['status'] == 'CLOSED']
        open_trades = [t for t in trades if t['status'] == 'OPEN']

        print(f"Closed: {len(closed)}")
        print(f"Open: {len(open_trades)}")

        if closed:
            wins = [t for t in closed if t['pnl_pct'] > 0]
            print(f"Win rate: {len(wins)/len(closed)*100:.1f}%")
```

### Manually Run Scanner on Specific Stocks
```python
from scanner.market_scanner import MarketScanner

scanner = MarketScanner(max_workers=5)

# Scan specific tickers
tickers = ['AAPL', 'NVDA', 'TSLA', 'GOOGL', 'MSFT']

results = []
for ticker in tickers:
    result = scanner._scan_single_stock(ticker, min_market_cap=50_000_000)
    if result:
        results.append(result)
        print(f"{ticker}: {result['score']['total_score']:.1f}")
```

### Reset Daily AI Call Counter
```python
from trader.autonomous_trader import AutonomousTrader

trader = AutonomousTrader(paper_trading=True)
trader.ai_call_count_today = 0
print("AI call counter reset")
```

---

## CONTACT & RESOURCES

### Documentation
- Main review: `SYSTEM_REVIEW.md`
- Fixes applied: `FIXES_APPLIED.md`
- This file: `CLAUDE_NOTES.md`

### External APIs
- Alpaca API: https://alpaca.markets/docs/
- xAI Grok: https://x.ai/api
- yfinance: https://github.com/ranaroussi/yfinance
- NASDAQ API: https://www.nasdaq.com/market-activity/stocks/screener

### Useful Commands
```bash
# Quick test
python test_system.py

# Check stock count
python -c "from scanner.stock_universe import fetch_all_exchange_tickers; print(len(fetch_all_exchange_tickers()))"

# View hot stocks
python -c "from utils.storage import StorageManager; s=StorageManager(); h=s.load_hot_stocks(); print(f'Hot stocks: {len(h)}'); [print(f\"{x['ticker']}: {x['score']['total_score']}\") for x in h[:5]]"

# Check trader health
python -c "from trader.autonomous_trader import AutonomousTrader; t=AutonomousTrader(paper_trading=True); print(f'Market open: {t.is_market_open()}')"
```

---

## CHANGELOG

### 2025-12-27 - Initial Setup
- Fixed stock universe bug (210 → 3,474 stocks)
- Fixed missing trader methods
- Created test suite (7/7 passing)
- Created this notes file
- System is operational, ready for testing

### 2025-12-27 - Polygon Integration
- Added Polygon API as fallback data source
- Created `utils/polygon_fetcher.py`
- Polygon has better rate limits than Yahoo Finance
- API key stored in `.env` file
- Successfully tested with HOOD stock
- Can fetch: quotes, company details, price history
- No rate limiting issues!

### Future Entries
Add notes here as development continues...

---

**End of Notes**
*Remember: This file is for tracking development context and quick reference. Update it frequently!*
