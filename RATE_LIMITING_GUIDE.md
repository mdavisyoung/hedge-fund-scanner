# Yahoo Finance Rate Limiting Guide

**Last Updated:** 2025-12-27

## Overview

Yahoo Finance has significantly tightened rate limits in 2025. This guide explains how the system handles these limits and best practices for avoiding blocks.

## Current Limits (2025)

Based on community observations:
- **Per Minute:** ~48-60 requests/minute
- **Per Day:** ~900-950 requests/day
- **No official documentation** - limits vary by IP and usage patterns
- **Stricter than previous years** - easier to get blocked

## Our Implementation

### 1. Token Bucket Rate Limiter

**File:** `utils/rate_limiter.py`

**Conservative Limits:**
- 48 requests/minute
- 900 requests/day
- 1 second minimum delay between calls
- Thread-safe with locking

**Usage:**
```python
from utils.rate_limiter import get_yahoo_rate_limiter

limiter = get_yahoo_rate_limiter()
limiter.wait_if_needed()  # Automatically enforces limits
```

### 2. Integrated into StockAnalyzer

All Yahoo Finance calls automatically use rate limiting:

```python
from utils import StockAnalyzer

analyzer = StockAnalyzer(use_polygon=True)
data = analyzer.get_fundamentals('AAPL')  # Rate-limited automatically
```

### 3. Retry Logic with Exponential Backoff

- **Attempt 1:** Immediate
- **Attempt 2:** 2 second delay
- **Attempt 3:** 4 second delay
- **After 3 attempts:** Falls back to Polygon-only data

### 4. Polygon.io as Primary Source

**Key Strategy:** Use Polygon for price data, Yahoo only for fundamentals

This reduces Yahoo Finance calls by ~70%:
- **Without Polygon:** 100% calls to Yahoo
- **With Polygon:** ~30% calls to Yahoo (only for PE, ROE, etc.)

## Best Practices

### ✅ DO

1. **Use Polygon for price data**
   ```python
   analyzer = StockAnalyzer(use_polygon=True)  # Default
   ```

2. **Use bulk downloads for multiple stocks**
   ```python
   analyzer.bulk_download_yahoo(['AAPL', 'MSFT', 'GOOGL'])
   ```

3. **Check rate limiter status before heavy operations**
   ```python
   status = analyzer.yahoo_limiter.get_status()
   if status['safe_to_call']:
       # Proceed with operation
   ```

4. **Cache results to avoid repeated calls**
   ```python
   # Store results and reuse for same ticker/period
   ```

### ❌ DON'T

1. **Don't make rapid sequential calls without rate limiting**
2. **Don't bypass the rate limiter**
3. **Don't use yfinance directly** - always go through StockAnalyzer
4. **Don't ignore 429 errors** - they indicate you're blocked

## Monitoring Rate Limiter

### Check Current Status

```python
from utils import StockAnalyzer

analyzer = StockAnalyzer()
status = analyzer.yahoo_limiter.get_status()

print(f"Remaining this minute: {status['remaining_calls_this_minute']}")
print(f"Remaining today: {status['remaining_calls_today']}")
print(f"Safe to call: {status['safe_to_call']}")
```

### Reset if Needed

```python
analyzer.yahoo_limiter.minute_limiter.reset()
analyzer.yahoo_limiter.day_limiter.reset()
```

## What Happens When Blocked?

1. **First attempt:** Yahoo Finance call with rate limiting
2. **429 Error:** Automatic retry with exponential backoff (2s, 4s)
3. **All retries fail:** Falls back to Polygon-only data
4. **System continues:** No crash, uses default values for missing ratios

## Scanner Impact

### Daily Scanning (700 stocks/day)

**Without rate limiting:**
- Risk of hitting 900/day limit
- Potential IP block

**With our implementation:**
- Polygon handles price data (0 Yahoo calls)
- Yahoo only for fundamentals (~700 calls/day)
- Spread over 24 hours (well under limits)
- Safe operation

### Backtesting

For backtesting, use Polygon exclusively:
```python
engine = BacktestEngine(...)
results = engine.run_backtest(tickers, use_actual_ai=False)
```

## Troubleshooting

### Getting 429 Errors?

1. Check daily limit:
   ```python
   status = analyzer.yahoo_limiter.get_status()
   print(status['remaining_calls_today'])
   ```

2. Wait for daily reset (midnight UTC)

3. Consider waiting 24 hours if blocked

4. Use Polygon-only mode temporarily:
   ```python
   # System will automatically fall back if Yahoo fails
   ```

### Rate Limiting Too Slow?

You can adjust limits (not recommended):
```python
from utils.rate_limiter import YahooFinanceRateLimiter

limiter = YahooFinanceRateLimiter()
limiter.min_delay = 0.5  # Reduce from 1s to 0.5s (risky!)
```

## Testing

### Test Rate Limiter

```bash
# Test the rate limiter implementation
python utils/rate_limiter.py

# Test with real API calls
python test_rate_limiting.py
```

## Sources & References

- [Why yfinance Keeps Getting Blocked (Medium)](https://medium.com/@trading.dude/why-yfinance-keeps-getting-blocked-and-what-to-use-instead-92d84bb2cc01)
- [Rate Limiting Best Practices for yfinance (Sling Academy)](https://www.slingacademy.com/article/rate-limiting-and-api-best-practices-for-yfinance/)
- [yfinance Issue #2422 - Rate Limit Error](https://github.com/ranaroussi/yfinance/issues/2422)
- [yfinance Issue #2125 - 429 Error Suggestions](https://github.com/ranaroussi/yfinance/issues/2125)

## Summary

The hedge fund scanner now has robust rate limiting that:
- ✅ Respects Yahoo Finance limits (48/min, 900/day)
- ✅ Uses Polygon as primary data source
- ✅ Falls back gracefully when Yahoo fails
- ✅ Continues functioning even when blocked
- ✅ Implements industry best practices

You should rarely encounter rate limiting issues with this implementation.
