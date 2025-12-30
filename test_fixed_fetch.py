"""
Test the fixed ticker fetch (no exchange filter)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Delete cache first
cache_file = Path("data") / "exchange_tickers_cache.json"
if cache_file.exists():
    os.remove(cache_file)
    print("✅ Deleted old cache\n")

print("=" * 60)
print("🧪 TESTING FIXED FETCH (No Exchange Filter)")
print("=" * 60)
print()
print("The exchange field in NASDAQ API returns 'N/A' for everything.")
print("So we're now filtering by:")
print("  ✅ Market cap >= $50M")
print("  ✅ Volume >= 100k")
print("  ✅ Valid symbol (1-5 letters)")
print()
print("This should give us ~4,000-5,000 stocks!")
print()

from scanner.stock_universe import fetch_all_exchange_tickers

tickers = fetch_all_exchange_tickers(
    force_refresh=True,
    min_market_cap=50_000_000,
    min_volume=100_000
)

print()
print("=" * 60)
print("✅ RESULTS:")
print("=" * 60)
print(f"Total tickers: {len(tickers)}")
print(f"Per day: ~{len(tickers) // 5} stocks")
print()

if len(tickers) > 1000:
    print("🎉 SUCCESS! We're getting thousands of stocks now!")
    print()
    print("Sample tickers:")
    print(f"  First 10: {tickers[:10]}")
    print(f"  Last 10: {tickers[-10:]}")
else:
    print("⚠️  Still only getting {len(tickers)} stocks.")
    print("   Something else is wrong. Check the output above.")
