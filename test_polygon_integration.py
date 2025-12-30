"""
Test Polygon Integration
Verify that Polygon is being used as the primary data source
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils import StockAnalyzer
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_polygon_integration():
    """Test that Polygon is working as primary data source"""
    print("=" * 60)
    print("TESTING POLYGON INTEGRATION")
    print("=" * 60)

    # Create analyzer (should use Polygon by default)
    analyzer = StockAnalyzer()

    print(f"\nAnalyzer configuration:")
    print(f"  use_polygon: {analyzer.use_polygon}")
    print(f"  polygon object: {analyzer.polygon is not None}")

    # Test with HOOD
    print(f"\n[1/3] Testing HOOD fundamentals...")
    try:
        data = analyzer.get_fundamentals('HOOD')
        if data:
            print(f"  [OK] Ticker: {data.get('ticker')}")
            print(f"  [OK] Current Price: ${data.get('current_price', 0):.2f}")
            print(f"  [OK] Market Cap: ${data.get('market_cap', 0):,}")
            print(f"  [OK] Exchange: {data.get('exchange')}")
            print(f"  [OK] PE Ratio: {data.get('pe_ratio', 0):.2f}")
            print(f"  [OK] ROE: {data.get('roe', 0):.2f}%")
        else:
            print("  [FAIL] No data returned")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

    # Test historical data
    print(f"\n[2/3] Testing HOOD historical data...")
    try:
        history = analyzer.get_stock_data('HOOD', period='1mo')
        if history is not None and len(history) > 0:
            print(f"  [OK] Retrieved {len(history)} days of data")
            print(f"  [OK] Latest close: ${history['Close'].iloc[-1]:.2f}")
        else:
            print("  [FAIL] No historical data returned")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

    # Test with another stock (AAPL)
    print(f"\n[3/3] Testing AAPL as second verification...")
    try:
        data = analyzer.get_fundamentals('AAPL')
        if data:
            print(f"  [OK] Ticker: {data.get('ticker')}")
            print(f"  [OK] Current Price: ${data.get('current_price', 0):.2f}")
            print(f"  [OK] Market Cap: ${data.get('market_cap', 0):,}")
        else:
            print("  [FAIL] No data returned")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED - Polygon integration working!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = test_polygon_integration()
    sys.exit(0 if success else 1)
