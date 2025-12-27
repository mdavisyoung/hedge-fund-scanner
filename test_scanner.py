"""
Test Scanner - Force scan a few stocks to generate test data
Bypasses day-of-week rules and rate limits
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from scanner.market_scanner import MarketScanner
from scanner.stock_universe import get_stock_batches

def test_scan_small_batch():
    """Scan a small batch of stocks with delays to avoid rate limits"""

    print("=" * 60)
    print("TEST SCANNER - Small Batch")
    print("=" * 60)
    print()

    # Get just a few stocks for testing
    test_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
        'META', 'TSLA', 'AMD', 'NFLX', 'CRM'
    ]

    print(f"Scanning {len(test_stocks)} stocks with delays...")
    print("Stocks:", ", ".join(test_stocks))
    print()

    scanner = MarketScanner()

    # Scan each stock with a delay
    results = []
    for i, ticker in enumerate(test_stocks, 1):
        print(f"[{i}/{len(test_stocks)}] Scanning {ticker}...", end=" ")

        try:
            result = scanner._scan_single_stock(ticker)
            if result:
                score = result['score']['total_score']
                print(f"✓ Score: {score:.1f}")
                results.append(result)
            else:
                print("✗ No data")
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")

        # Wait 3 seconds between requests to avoid rate limits
        if i < len(test_stocks):
            time.sleep(3)

    print()
    print("=" * 60)
    print(f"Scan Complete! Found {len(results)} valid stocks")
    print("=" * 60)
    print()

    # Categorize results
    hot = [s for s in results if s['score']['total_score'] >= 80]
    warming = [s for s in results if 70 <= s['score']['total_score'] < 80]
    watching = [s for s in results if 60 <= s['score']['total_score'] < 70]

    print(f"🔥 Hot (>= 80): {len(hot)}")
    for stock in hot:
        print(f"   {stock['ticker']}: {stock['score']['total_score']:.1f}")

    print(f"\n🟡 Warming (70-79): {len(warming)}")
    for stock in warming:
        print(f"   {stock['ticker']}: {stock['score']['total_score']:.1f}")

    print(f"\n👀 Watching (60-69): {len(watching)}")
    for stock in watching:
        print(f"   {stock['ticker']}: {stock['score']['total_score']:.1f}")

    # Save results
    if results:
        print()
        print("Saving results to data/ folder...")
        scanner.storage.save_hot_stocks(hot)
        scanner.storage.save_warming_stocks(warming)
        scanner.storage.save_watching_stocks(watching)
        print("✅ Results saved!")
        print()
        print("You can now run the autonomous trader:")
        print("  cd trader")
        print("  python run_autonomous.py --mode once --paper")

    return results

if __name__ == "__main__":
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    print()
    print("This will scan 10 major stocks with 3-second delays")
    print("to avoid Yahoo Finance rate limits.")
    print()
    input("Press Enter to continue...")
    print()

    test_scan_small_batch()
