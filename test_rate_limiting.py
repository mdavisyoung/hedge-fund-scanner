"""
Test Rate Limiting Implementation
Verify that Yahoo Finance calls are properly rate-limited
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils import StockAnalyzer
import time


def test_rate_limiting():
    """Test that rate limiting is working"""
    print("=" * 60)
    print("TESTING YAHOO FINANCE RATE LIMITING")
    print("=" * 60)

    analyzer = StockAnalyzer(use_polygon=True)

    # Check initial status
    status = analyzer.yahoo_limiter.get_status()
    print(f"\nInitial Status:")
    print(f"  Remaining calls this minute: {status['remaining_calls_this_minute']}")
    print(f"  Remaining calls today: {status['remaining_calls_today']}")
    print(f"  Safe to call: {status['safe_to_call']}")

    # Test rapid calls - should be rate limited
    print(f"\nTesting 5 rapid stock lookups...")
    print(f"(Should see 1-second delays between calls)")

    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META']
    start_time = time.time()

    for i, ticker in enumerate(test_tickers, 1):
        call_start = time.time()

        # This will use Polygon for price, Yahoo for fundamentals (rate-limited)
        data = analyzer.get_fundamentals(ticker)

        call_duration = time.time() - call_start

        if data:
            print(f"  [{i}/5] {ticker}: ${data.get('current_price', 0):.2f} "
                  f"(took {call_duration:.1f}s)")
        else:
            print(f"  [{i}/5] {ticker}: FAILED")

    total_time = time.time() - start_time
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Average per call: {total_time/len(test_tickers):.1f}s")

    # Check final status
    final_status = analyzer.yahoo_limiter.get_status()
    print(f"\nFinal Status:")
    print(f"  Remaining calls this minute: {final_status['remaining_calls_this_minute']}")
    print(f"  Remaining calls today: {final_status['remaining_calls_today']}")
    print(f"  Safe to call: {final_status['safe_to_call']}")

    # Verify rate limiting worked
    calls_made = (status['remaining_calls_this_minute'] -
                  final_status['remaining_calls_this_minute'])

    print(f"\n" + "=" * 60)
    if total_time >= len(test_tickers) - 1:  # Should take at least 4 seconds for 5 calls
        print("RATE LIMITING WORKING!")
        print(f"  Calls made: {calls_made}")
        print(f"  Time enforced: {total_time:.1f}s (>= {len(test_tickers)-1}s expected)")
        return True
    else:
        print("WARNING: Rate limiting may not be working properly")
        print(f"  Expected >= {len(test_tickers)-1}s, got {total_time:.1f}s")
        return False


if __name__ == '__main__':
    success = test_rate_limiting()
    sys.exit(0 if success else 1)
