"""
Test Autonomous Trading System
Tests scanner and trader to ensure everything is working
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add paths
sys.path.append(str(Path(__file__).parent))

import io
import sys
# Fix Windows encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*70)
print("TESTING AUTONOMOUS TRADING SYSTEM")
print("="*70)
print()

# Step 1: Check API Keys
print("[STEP 1] Checking API Keys...")
alpaca_key = os.getenv('ALPACA_API_KEY')
alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
xai_key = os.getenv('XAI_API_KEY')

if not alpaca_key or not alpaca_secret:
    print("[ERROR] ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env file")
    print("   Get them from: https://app.alpaca.markets/paper/dashboard/overview")
    sys.exit(1)
else:
    print(f"   [OK] Alpaca API Key: {alpaca_key[:10]}...{alpaca_key[-4:]}")
    print(f"   [OK] Alpaca Secret: {'*' * 20}")

if not xai_key:
    print("   [WARN] XAI_API_KEY not set - AI analysis will be disabled")
else:
    print(f"   [OK] XAI API Key: {xai_key[:10]}...{xai_key[-4:]}")

print()

# Step 2: Check if hot stocks exist
print("\n[STEP 2] Checking for hot stocks...")
from utils.storage import StorageManager
storage = StorageManager()
hot_stocks = storage.load_hot_stocks()

if not hot_stocks or len(hot_stocks.get('stocks', [])) == 0:
    print("   [WARN] No hot stocks found - need to run scanner first")
    print("   Running scanner now...")
    print()
    
    from scanner.market_scanner import MarketScanner
    scanner = MarketScanner(max_workers=10)
    
    # Run a quick scan (today's batch)
    today = datetime.now().weekday()
    print(f"   Scanning today's batch (day {today})...")
    results = scanner.scan_daily_batch(today, min_market_cap=50_000_000, min_volume=100_000)
    
    # Save results
    storage.save_hot_stocks(results['hot'])
    storage.save_warming_stocks(results['warming'])
    storage.save_watching_stocks(results['watching'])
    
    print(f"   [OK] Scan complete:")
    print(f"      Hot stocks: {len(results['hot'])}")
    print(f"      Warming: {len(results['warming'])}")
    print(f"      Watching: {len(results['watching'])}")
    
    # Reload
    hot_stocks = storage.load_hot_stocks()
else:
    print(f"   [OK] Found {len(hot_stocks.get('stocks', []))} hot stocks")

print()

# Step 3: Test Autonomous Trader
print("\n[STEP 3] Testing Autonomous Trader...")
try:
    from trader.autonomous_trader import AutonomousTrader
    
    print("   Initializing trader (paper trading mode)...")
    trader = AutonomousTrader(paper_trading=True)
    print("   [OK] Trader initialized")
    
    # Check market hours
    is_open = trader.is_market_open()
    print(f"   Market status: {'OPEN' if is_open else 'CLOSED'}")
    
    if not is_open:
        print("   [WARN] Market is closed - trader will skip execution")
        print("   But we can still test the analysis logic...")
    
    # Get account info
    print("\n   Account Information:")
    account = trader.get_account_info()
    print(f"      Portfolio Value: ${account['portfolio_value']:,.2f}")
    print(f"      Cash: ${account['cash']:,.2f}")
    print(f"      Buying Power: ${account['buying_power']:,.2f}")
    print(f"      Paper Trading: {account['paper_trading']}")
    
    # Check positions
    positions = trader.get_current_positions()
    print(f"\n   Current Positions: {len(positions)}")
    if positions:
        for pos in positions:
            print(f"      {pos['ticker']}: {pos['qty']} shares @ ${pos['entry_price']:.2f} (P/L: {pos['unrealized_pnl_pct']:.2f}%)")
    
    # Check portfolio heat
    heat = trader.get_portfolio_heat()
    print(f"\n   Portfolio Heat: {heat:.2%} / {trader.max_portfolio_heat:.2%}")
    
    # Test analysis on first hot stock
    if hot_stocks and len(hot_stocks.get('stocks', [])) > 0:
        test_stock = hot_stocks['stocks'][0]
        ticker = test_stock['ticker']
        score = test_stock.get('score', {}).get('total_score', 0)
        
        print(f"\n   Testing AI Analysis on {ticker} (score: {score:.1f})...")
        analysis = trader.analyze_opportunity(test_stock)
        
        print(f"      Confidence: {analysis.get('confidence', 0)}/10")
        print(f"      Recommendation: {analysis.get('recommendation', 'N/A')}")
        reasoning = analysis.get('reasoning', 'N/A')
        if len(reasoning) > 100:
            reasoning = reasoning[:100] + "..."
        print(f"      Reasoning: {reasoning}")
        
        # Check if should trade
        should_trade = trader.should_trade(test_stock, analysis)
        print(f"      Should Trade: {'YES' if should_trade else 'NO'}")
        
        if should_trade and is_open:
            print(f"\n   [WARN] Would execute trade (market is open)")
            print(f"      This is a TEST - not executing actual trade")
        elif should_trade and not is_open:
            print(f"\n   [WARN] Would execute trade (but market is closed)")
    else:
        print("\n   [WARN] No hot stocks to test analysis")
    
    print("\n   [OK] Trader test complete!")
    
except Exception as e:
    print(f"   [ERROR] Error testing trader: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("\n" + "="*70)
print("ALL TESTS COMPLETE")
print("="*70)
print()
print("Summary:")
print(f"   - API Keys: {'Set' if alpaca_key and alpaca_secret else 'Missing'}")
print(f"   - Hot Stocks: {len(hot_stocks.get('stocks', [])) if hot_stocks else 0}")
try:
    print(f"   - Market Status: {'OPEN' if is_open else 'CLOSED'}")
except:
    print(f"   - Market Status: Unknown")
print(f"   - Trader Ready: OK")
print()
print("To run autonomous trader:")
print("   python trader/run_autonomous.py --mode once --paper")
print()

