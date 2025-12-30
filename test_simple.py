"""
Simple test - bypasses emoji issues
"""
import os
import sys
from pathlib import Path

# Clear cache
cache_file = Path("data") / "exchange_tickers_cache.json"
if cache_file.exists():
    os.remove(cache_file)
    print("Deleted cache\n")

print("=" * 60)
print("FORCING FRESH IMPORT")
print("=" * 60)
print()

# Force reimport
if 'scanner' in sys.modules:
    del sys.modules['scanner']
if 'scanner.stock_universe' in sys.modules:
    del sys.modules['scanner.stock_universe']

# Import fresh
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.stock_universe import fetch_all_exchange_tickers

print("Calling fetch_all_exchange_tickers...")
print()

tickers = fetch_all_exchange_tickers(
    force_refresh=True,
    min_market_cap=50_000_000,
    min_volume=100_000
)

print()
print("=" * 60)
print("RESULTS:")
print("=" * 60)
print(f"Total: {len(tickers)}")
print()

if len(tickers) > 1000:
    print("SUCCESS!")
    print(f"Sample: {tickers[:20]}")
else:
    print(f"WARNING: Only {len(tickers)} stocks")
    if len(tickers) > 0:
        print(f"Sample: {tickers[:10]}")
