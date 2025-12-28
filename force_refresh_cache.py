"""
Force refresh the ticker cache with the new, more lenient exchange filter.
Run this to re-fetch all tickers from exchanges.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.stock_universe import fetch_all_exchange_tickers

def main():
    print("=" * 60)
    print("🔄 FORCE REFRESH TICKER CACHE")
    print("=" * 60)
    print()
    
    # Delete existing cache
    cache_file = Path("data") / "exchange_tickers_cache.json"
    if cache_file.exists():
        os.remove(cache_file)
        print("✅ Deleted old cache")
    else:
        print("ℹ️  No existing cache found")
    
    print()
    print("📡 Fetching fresh ticker data from exchanges...")
    print("   This will take 2-5 minutes...")
    print()
    
    # Fetch with force_refresh=True
    tickers = fetch_all_exchange_tickers(
        force_refresh=True,
        min_market_cap=50_000_000,
        min_volume=100_000
    )
    
    print()
    print("=" * 60)
    print("✅ REFRESH COMPLETE!")
    print("=" * 60)
    print(f"Total qualifying tickers: {len(tickers)}")
    print(f"Per day average: ~{len(tickers) // 5} stocks")
    print()
    print("You can now run your scanner and it should scan 1000+ stocks!")
    print()

if __name__ == "__main__":
    main()
