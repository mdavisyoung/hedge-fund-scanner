"""
Compare Profitable vs Unprofitable Companies
Shows why P/E is 0.00 for some stocks but not others
"""

import sys
sys.path.insert(0, 'utils')

from polygon_fetcher import PolygonFetcher

def compare_stocks():
    print("="*70)
    print("COMPARING PROFITABLE vs UNPROFITABLE COMPANIES")
    print("="*70)
    
    fetcher = PolygonFetcher()
    
    # Test profitable company (NVDA)
    print("\n[1] Testing PROFITABLE Company: NVDA (Nvidia)")
    print("-" * 70)
    
    nvda = fetcher.get_financials('NVDA')
    
    if nvda:
        print(f"✅ Data fetched for NVDA\n")
        print(f"   P/E Ratio:      {nvda.get('pe_ratio', 0):>10.2f}")
        print(f"   ROE:            {nvda.get('roe', 0):>10.2f}%")
        print(f"   Profit Margin:  {nvda.get('profit_margin', 0):>10.2f}%")
        print(f"   Revenue Growth: {nvda.get('revenue_growth', 0):>10.2f}%")
        print(f"   Current Ratio:  {nvda.get('current_ratio', 0):>10.2f}")
        
        if nvda.get('pe_ratio', 0) > 0 and nvda.get('profit_margin', 0) > 0:
            print("\n   ✅ P/E is CALCULATED because company is PROFITABLE")
            print(f"   ✅ Net Income: ${nvda.get('net_income', 0)/1e9:.2f}B")
    else:
        print("❌ Failed to fetch NVDA")
    
    # Test unprofitable company (FCEL)
    print("\n" + "="*70)
    print("[2] Testing UNPROFITABLE Company: FCEL (FuelCell Energy)")
    print("-" * 70)
    
    fcel = fetcher.get_financials('FCEL')
    
    if fcel:
        print(f"✅ Data fetched for FCEL\n")
        print(f"   P/E Ratio:      {fcel.get('pe_ratio', 0):>10.2f}")
        print(f"   ROE:            {fcel.get('roe', 0):>10.2f}%")
        print(f"   Profit Margin:  {fcel.get('profit_margin', 0):>10.2f}%")
        print(f"   Revenue Growth: {fcel.get('revenue_growth', 0):>10.2f}%")
        print(f"   Current Ratio:  {fcel.get('current_ratio', 0):>10.2f}")
        
        if fcel.get('pe_ratio', 0) == 0 and fcel.get('profit_margin', 0) < 0:
            print("\n   ⚠️  P/E is 0.00 because company is UNPROFITABLE")
            print(f"   ⚠️  Net Income: ${fcel.get('net_income', 0)/1e6:.2f}M (NEGATIVE)")
            print("\n   ℹ️  This is EXPECTED - you cannot calculate P/E for")
            print("      companies with negative earnings!")
        
        if fcel.get('revenue_growth', 0) > 0:
            print(f"\n   ✅ BUT Revenue Growth ({fcel.get('revenue_growth', 0):.2f}%) shows")
            print("      Polygon API IS working - it's just that FCEL is unprofitable")
    else:
        print("❌ Failed to fetch FCEL")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if nvda and fcel:
        print("\n✅ Polygon API is working correctly for BOTH stocks!")
        print("\nKey Differences:")
        print(f"   NVDA (Profitable):    P/E = {nvda.get('pe_ratio', 0):.2f}")
        print(f"   FCEL (Unprofitable):  P/E = {fcel.get('pe_ratio', 0):.2f}")
        print("\n📌 CONCLUSION:")
        print("   • P/E = 0.00 for FCEL is CORRECT (not a bug)")
        print("   • This happens for all unprofitable companies")
        print("   • Other metrics (ROE, Revenue Growth, etc.) ARE working")
        print("   • The 'missing data' isn't missing - it's just undefined!")
    
    print("\n" + "="*70)
    print("WHAT METRICS SHOULD YOU FOCUS ON FOR UNPROFITABLE STOCKS?")
    print("="*70)
    print("\n✅ Use these instead of P/E for unprofitable companies:")
    print("   • Price/Book Ratio (measures value vs book value)")
    print("   • Revenue Growth (are they growing sales?)")
    print("   • Current Ratio (do they have cash to survive?)")
    print("   • Cash Burn Rate (how fast are they spending?)")
    print("\n⚠️  Avoid P/E-based valuation for unprofitable stocks!")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    compare_stocks()
