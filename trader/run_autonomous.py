"""
Run the Autonomous Trader
Continuously monitors opportunities and executes trades
"""

import time
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trader.autonomous_trader import AutonomousTrader
from utils.storage import StorageManager


def main():
    """Run autonomous trading loop"""
    
    print("="*60)
    print("🤖 AUTONOMOUS AI TRADER - STARTING")
    print("="*60)
    
    # Initialize
    trader = AutonomousTrader(paper_trading=True)
    storage = StorageManager()
    
    # Print initial status
    print(trader.get_status_report())
    
    print("\n🔄 Starting trading loop...")
    print("Checks every 5 minutes | Press Ctrl+C to stop\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"🔄 CHECK #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}\n")
            
            # Step 1: Monitor existing positions
            print("👀 Monitoring positions...")
            trader.monitor_positions()
            
            # Step 2: Look for new opportunities
            print("\n🔍 Checking for new opportunities...")
            hot_stocks = storage.load_hot_stocks()
            
            if hot_stocks and hot_stocks.get('stocks'):
                print(f"   Found {len(hot_stocks['stocks'])} hot stocks\n")
                
                # Analyze top 3
                for stock in hot_stocks['stocks'][:3]:
                    print(f"📊 Analyzing {stock['ticker']}...")
                    
                    # Get AI decision
                    decision = trader.analyze_opportunity(
                        stock['ticker'],
                        stock['fundamentals']
                    )
                    
                    # Execute if recommended
                    if decision['action'] == 'BUY':
                        trader.execute_trade(decision)
                    
                    time.sleep(2)  # Rate limit
            else:
                print("   No hot stocks yet. Run: python scanner/run_daily_scan.py")
            
            # Step 3: Print status
            print(trader.get_status_report())
            
            # Step 4: Wait 5 minutes
            print(f"\n⏰ Next check in 5 minutes...")
            time.sleep(300)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping trader...")
        print(trader.get_status_report())
        print("\n✅ Stopped safely. All positions remain open.")


if __name__ == "__main__":
    main()
