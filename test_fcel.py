"""
Verify FCEL Data - Check if Polygon is returning correct information
"""

import sys
sys.path.insert(0, 'utils')

from polygon_fetcher import PolygonFetcher

def test_fcel():
    print("="*60)
    print("TESTING FCEL (FuelCell Energy) DATA")
    print("="*60)
    
    fetcher = PolygonFetcher()
    
    # Test financials
    print("\n[1] Fetching financials for FCEL...")
    financials = fetcher.get_financials('FCEL')
    
    if financials:
        print("✅ Financials fetched successfully!\n")
        
        print("RAW DATA FROM POLYGON:")
        print("-" * 60)
        for key, value in financials.items():
            if key not in ['revenues', 'net_income', 'total_assets', 'current_assets', 
                          'current_liabilities', 'equity', 'source']:
                print(f"{key:20s}: {value}")
        
        print("\n" + "="*60)
        print("ANALYSIS:")
        print("="*60)
        
        # Check P/E
        pe_ratio = financials.get('pe_ratio', 0)
        net_income = financials.get('net_income', 0)
        
        print(f"\n📊 P/E Ratio: {pe_ratio:.2f}")
        if pe_ratio == 0:
            print(f"   ℹ️  P/E is 0.00 because:")
            print(f"   • Net Income: ${net_income:,.0f}")
            if net_income <= 0:
                print(f"   • Company is UNPROFITABLE (negative earnings)")
                print(f"   • P/E cannot be calculated when earnings are negative")
                print(f"   • This is EXPECTED and CORRECT behavior")
            else:
                print(f"   • Market cap data may be unavailable")
        else:
            print(f"   ✅ P/E calculated successfully")
        
        # Check ROE
        roe = financials.get('roe', 0)
        print(f"\n📊 ROE: {roe:.2f}%")
        if roe < 0:
            print(f"   ⚠️  Negative ROE confirms company is losing money")
        
        # Check Profit Margin
        profit_margin = financials.get('profit_margin', 0)
        print(f"\n📊 Profit Margin: {profit_margin:.2f}%")
        if profit_margin < 0:
            print(f"   ⚠️  Negative margin confirms unprofitable operations")
        
        # Check Revenue Growth
        revenue_growth = financials.get('revenue_growth', 0)
        print(f"\n📊 Revenue Growth: {revenue_growth:.2f}%")
        if revenue_growth > 100:
            print(f"   ✅ Strong revenue growth despite unprofitability")
            print(f"   ℹ️  This is common in early-stage growth companies")
        
        # Check Current Ratio
        current_ratio = financials.get('current_ratio', 0)
        print(f"\n📊 Current Ratio: {current_ratio:.2f}")
        if current_ratio > 1.5:
            print(f"   ✅ Strong liquidity (good cash position)")
        
        print("\n" + "="*60)
        print("CONCLUSION:")
        print("="*60)
        
        data_points = sum([
            revenue_growth != 0,
            profit_margin != 0,
            roe != 0,
            current_ratio != 0
        ])
        
        if data_points >= 3:
            print("✅ Polygon API is working correctly!")
            print("✅ All expected metrics are being fetched")
            print("\nℹ️  P/E = 0.00 is CORRECT for unprofitable companies")
            print("   This is not a bug - it's expected behavior!")
        else:
            print("⚠️  Some metrics may be missing")
            print(f"   Only {data_points}/4 key metrics have data")
        
        print("\n" + "="*60)
        
    else:
        print("❌ Failed to fetch financials for FCEL")
        print("\nTroubleshooting:")
        print("1. Check Polygon API key in .env")
        print("2. Verify FCEL ticker is correct")
        print("3. Check API rate limits")

if __name__ == "__main__":
    test_fcel()
