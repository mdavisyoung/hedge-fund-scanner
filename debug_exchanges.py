"""
Debug script to see what exchange names the NASDAQ API is actually returning
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
print("🔍 DEBUG: Fetching to see actual exchange names")
print("=" * 60)
print()

from scanner.stock_universe import fetch_all_exchange_tickers

# This will now print the unique exchanges
tickers = fetch_all_exchange_tickers(
    force_refresh=True,
    min_market_cap=50_000_000,
    min_volume=100_000
)

print()
print("=" * 60)
print("RESULTS:")
print("=" * 60)
print(f"Total tickers: {len(tickers)}")
print()
print("Check the DEBUG output above to see what exchange names")
print("are actually being returned by the NASDAQ API.")
print()
print("We need to update the exchange filter to match those names.")
