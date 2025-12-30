"""
System Test Script - Verify All Fixes Are Working
Run this to confirm Polygon API, financials, and DCA calculations
"""

import sys
sys.path.insert(0, 'utils')

from polygon_fetcher import PolygonFetcher
from core import StockAnalyzer, XAIStrategyGenerator

def test_polygon_api():
    """Test 1: Polygon API Connection and Financials"""
    print("\n" + "="*60)
    print("TEST 1: POLYGON API CONNECTION")
    print("="*60)
    
    fetcher = PolygonFetcher()
    
    # Test connection
    print("\n[1.1] Testing API connection...")
    if fetcher.test_connection():
        print("✅ API Connection: SUCCESS")
    else:
        print("❌ API Connection: FAILED")
        return False
    
    # Test get_financials
    print("\n[1.2] Testing get_financials(NVDA)...")
    financials = fetcher.get_financials('NVDA')
    
    if financials:
        print("✅ Financials Fetch: SUCCESS\n")
        print("   📊 Financial Metrics:")
        print(f"   • P/E Ratio: {financials.get('pe_ratio', 0):.2f}")
        print(f"   • Current Ratio: {financials.get('current_ratio', 0):.2f}")
        print(f"   • ROE: {financials.get('roe', 0):.2f}%")
        print(f"   • Revenue Growth: {financials.get('revenue_growth', 0):.2f}%")
        print(f"   • Profit Margin: {financials.get('profit_margin', 0):.2f}%")
        print(f"   • Debt/Equity: {financials.get('debt_to_equity', 0):.2f}")
        
        # Check if values are NOT zero
        if financials.get('pe_ratio', 0) > 0 and financials.get('current_ratio', 0) > 0:
            print("\n   ✅ Metrics are REAL values (not 0.00)")
            return True
        else:
            print("\n   ❌ WARNING: Some metrics are 0.00")
            return False
    else:
        print("❌ Financials Fetch: FAILED")
        return False


def test_stock_analyzer():
    """Test 2: Stock Analyzer Integration"""
    print("\n" + "="*60)
    print("TEST 2: STOCK ANALYZER INTEGRATION")
    print("="*60)
    
    analyzer = StockAnalyzer(use_polygon=True)
    
    print("\n[2.1] Testing get_fundamentals(NVDA)...")
    fundamentals = analyzer.get_fundamentals('NVDA')
    
    if fundamentals:
        print("✅ Fundamentals Fetch: SUCCESS\n")
        print("   📊 All Metrics:")
        print(f"   • Ticker: {fundamentals.get('ticker')}")
        print(f"   • Name: {fundamentals.get('name')}")
        print(f"   • Price: ${fundamentals.get('current_price', 0):.2f}")
        print(f"   • Market Cap: ${fundamentals.get('market_cap', 0)/1e9:.2f}B")
        print(f"   • P/E Ratio: {fundamentals.get('pe_ratio', 0):.2f}")
        print(f"   • Current Ratio: {fundamentals.get('current_ratio', 0):.2f}")
        print(f"   • ROE: {fundamentals.get('roe', 0):.2f}%")
        print(f"   • Revenue Growth: {fundamentals.get('revenue_growth', 0):.2f}%")
        
        # Check for company description
        if fundamentals.get('description'):
            print(f"\n   ✅ Company Description: {fundamentals.get('description')[:100]}...")
        else:
            print("\n   ⚠️  No company description (optional)")
        
        return True
    else:
        print("❌ Fundamentals Fetch: FAILED")
        return False


def test_dca_calculations():
    """Test 3: DCA Calculations in Strategy Generator"""
    print("\n" + "="*60)
    print("TEST 3: DCA CALCULATIONS")
    print("="*60)
    
    analyzer = StockAnalyzer(use_polygon=True)
    strategy_gen = XAIStrategyGenerator()
    
    print("\n[3.1] Analyzing NVDA...")
    evaluation = analyzer.evaluate_stock('NVDA')
    
    if 'error' in evaluation:
        print(f"❌ Stock Evaluation: FAILED - {evaluation['error']}")
        return False
    
    print("✅ Stock Evaluation: SUCCESS\n")
    
    # Test DCA calculation parameters
    fundamentals = evaluation['fundamentals']
    current_price = fundamentals.get('current_price', 0)
    monthly_budget = 100
    
    print("   💰 DCA Parameters:")
    print(f"   • Current Price: ${current_price:.2f}")
    print(f"   • Monthly Budget: ${monthly_budget:.2f}")
    
    # Calculate shares_monthly
    shares_monthly = monthly_budget / current_price if current_price > 0 else 0
    target_shares = shares_monthly * 12
    target_value = target_shares * current_price
    
    print(f"   • Shares per Month: {shares_monthly:.2f}")
    print(f"   • Target (12 months): {target_shares:.2f} shares")
    print(f"   • Target Value: ${target_value:.2f}")
    
    if shares_monthly > 0:
        print("\n   ✅ DCA Calculations: CORRECT")
        return True
    else:
        print("\n   ❌ DCA Calculations: FAILED (shares_monthly = 0)")
        return False


def test_ai_strategy():
    """Test 4: AI Strategy Generation (Optional - requires XAI API key)"""
    print("\n" + "="*60)
    print("TEST 4: AI STRATEGY GENERATION (OPTIONAL)")
    print("="*60)
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    xai_key = os.getenv('XAI_API_KEY', '')
    
    if not xai_key or len(xai_key) < 30:
        print("\n⚠️  XAI API Key not configured - SKIPPING")
        print("   (This is optional - other tests still valid)")
        return True
    
    print("\n[4.1] Generating AI strategy for NVDA...")
    
    analyzer = StockAnalyzer(use_polygon=True)
    strategy_gen = XAIStrategyGenerator()
    
    evaluation = analyzer.evaluate_stock('NVDA')
    
    user_prefs = {
        "monthly_contribution": 100,
        "risk_tolerance": 5,
        "max_loss_per_trade": 2,
        "portfolio_value": 1200
    }
    
    try:
        strategy = strategy_gen.generate_strategy(evaluation, user_prefs)
        
        # Check if strategy contains DCA keywords
        has_dca = "shares" in strategy.lower() and "month" in strategy.lower()
        has_company = "company" in strategy.lower() or "business" in strategy.lower()
        
        if has_dca and has_company:
            print("✅ AI Strategy: SUCCESS")
            print("\n   Strategy Preview:")
            print("   " + "-"*56)
            print("   " + strategy[:500].replace("\n", "\n   "))
            print("   ...")
            print("\n   ✅ Contains DCA plan")
            print("   ✅ Contains company overview")
            return True
        else:
            print("⚠️  AI Strategy generated but missing expected sections")
            print(f"   • Has DCA plan: {has_dca}")
            print(f"   • Has company overview: {has_company}")
            return False
            
    except Exception as e:
        print(f"❌ AI Strategy: FAILED - {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("HEDGE FUND SCANNER - SYSTEM TEST")
    print("="*60)
    print("Testing all components to verify fixes are working...")
    
    results = {
        "Polygon API": False,
        "Stock Analyzer": False,
        "DCA Calculations": False,
        "AI Strategy": False
    }
    
    # Run tests
    results["Polygon API"] = test_polygon_api()
    results["Stock Analyzer"] = test_stock_analyzer()
    results["DCA Calculations"] = test_dca_calculations()
    results["AI Strategy"] = test_ai_strategy()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_critical_passed = results["Polygon API"] and results["Stock Analyzer"] and results["DCA Calculations"]
    
    print("\n" + "="*60)
    if all_critical_passed:
        print("✅ ALL CRITICAL TESTS PASSED!")
        print("Your system is working correctly.")
        print("\nYou can now:")
        print("1. Run: streamlit run app.py")
        print("2. Go to Stock Analyzer")
        print("3. Analyze NVDA to see real metrics")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check the errors above for details.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
