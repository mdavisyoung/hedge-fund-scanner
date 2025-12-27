"""
Run Autonomous Trader - OPTIMIZED VERSION

Usage:
    python run_autonomous.py --mode once --paper
    python run_autonomous.py --mode continuous --interval 300 --paper
    
OPTIMIZATIONS:
- Limits hot stocks to top 50 by score
- Checks market hours before scanning
- Better error handling and logging
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from trader.autonomous_trader import AutonomousTrader
from utils.storage import StorageManager


def load_hot_stocks(storage, max_stocks=50):
    """
    Load hot stocks from scanner results.
    OPTIMIZATION: Limits to top N stocks by score to control AI costs.
    
    Args:
        storage: StorageManager instance
        max_stocks: Maximum number of hot stocks to consider (default 50)
    
    Returns:
        List of hot stocks, sorted by score, limited to max_stocks
    """
    hot_stocks = storage.load_hot_stocks()
    
    if not hot_stocks:
        print("📭 No hot stocks found from scanner")
        return []
    
    # Sort by total_score descending
    hot_stocks.sort(key=lambda x: x.get('score', {}).get('total_score', 0), reverse=True)
    
    # Limit to top N
    if len(hot_stocks) > max_stocks:
        print(f"🔥 Found {len(hot_stocks)} hot stocks, limiting to top {max_stocks} by score")
        hot_stocks = hot_stocks[:max_stocks]
    else:
        print(f"🔥 Found {len(hot_stocks)} hot stocks")
    
    return hot_stocks


def run_once(trader: AutonomousTrader, storage: StorageManager, max_hot_stocks=50):
    """
    Run one iteration of autonomous trading.
    
    Steps:
    1. Check market hours
    2. Monitor existing positions
    3. Analyze hot stocks (limited to top N)
    4. Execute trades if criteria met
    """
    print(f"\n{'='*60}")
    print(f"🤖 AUTONOMOUS TRADER RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Check if market is open
    if not trader.is_market_open():
        print("🔒 Market is closed. Skipping this run.")
        print(f"   Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday")
        return
    
    print("✅ Market is open\n")
    
    # Step 1: Monitor existing positions
    print("📊 STEP 1: Monitoring existing positions...")
    actions = trader.monitor_positions()
    
    if actions:
        print(f"   Found {len(actions)} positions needing action:")
        for action in actions:
            print(f"   - {action['ticker']}: {action['reason']} (P/L: {action['pnl_pct']:.2f}%)")
            trader.exit_position(action['ticker'], action['reason'])
    else:
        print("   No positions need action")
    
    # Step 2: Check circuit breaker
    print("\n🛡️ STEP 2: Checking safety limits...")
    if trader.trading_paused:
        print(f"   🛑 Trading paused: {trader.pause_reason}")
        return
    
    if trader.check_daily_loss_limit():
        return
    
    # Check portfolio heat
    current_heat = trader.get_portfolio_heat()
    print(f"   Portfolio heat: {current_heat:.2%} / {trader.max_portfolio_heat:.2%}")
    
    if current_heat >= trader.max_portfolio_heat:
        print("   ⚠️ Portfolio heat at maximum, no new positions allowed")
        return
    
    # Get account info
    account = trader.get_account_info()
    print(f"   Portfolio value: ${account['portfolio_value']:,.2f}")
    print(f"   Cash: ${account['cash']:,.2f}")
    print(f"   Buying power: ${account['buying_power']:,.2f}")
    
    # Step 3: Analyze hot stocks
    print(f"\n🔍 STEP 3: Analyzing hot stocks (limited to top {max_hot_stocks})...")
    hot_stocks = load_hot_stocks(storage, max_stocks=max_hot_stocks)
    
    if not hot_stocks:
        print("   No opportunities to analyze")
        return
    
    # Filter out stocks we already own
    positions = trader.get_current_positions()
    owned_tickers = set(pos['ticker'] for pos in positions)
    hot_stocks = [s for s in hot_stocks if s['ticker'] not in owned_tickers]
    
    if not hot_stocks:
        print("   All hot stocks are already owned")
        return
    
    print(f"   Analyzing {len(hot_stocks)} opportunities...")
    
    # Analyze each hot stock
    trades_executed = 0
    for i, stock in enumerate(hot_stocks, 1):
        ticker = stock['ticker']
        score = stock.get('score', {}).get('total_score', 0)
        
        print(f"\n   [{i}/{len(hot_stocks)}] {ticker} (score: {score:.1f})...")
        
        # AI analysis
        analysis = trader.analyze_opportunity(stock)
        
        confidence = analysis.get('confidence', 0)
        recommendation = analysis.get('recommendation', 'SKIP')
        reasoning = analysis.get('reasoning', 'N/A')
        
        print(f"      AI: {recommendation} (confidence: {confidence}/10)")
        print(f"      Reasoning: {reasoning}")
        
        # Decide whether to trade
        if trader.should_trade(stock, analysis):
            print(f"      ✅ Executing trade...")
            result = trader.execute_trade(stock, analysis)
            
            if result:
                trades_executed += 1
                print(f"      ✅ Trade executed successfully!")
            else:
                print(f"      ❌ Trade execution failed")
        else:
            print(f"      ⏭️ Skipping (criteria not met)")
        
        # Check if we hit portfolio heat limit
        if trader.get_portfolio_heat() >= trader.max_portfolio_heat:
            print(f"\n   🛑 Portfolio heat limit reached, stopping new trades")
            break
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📈 RUN SUMMARY")
    print(f"{'='*60}")
    print(f"Trades executed: {trades_executed}")
    print(f"AI calls made: {trader.ai_call_count_today}")
    print(f"Current positions: {len(trader.get_current_positions())}")
    print(f"Portfolio heat: {trader.get_portfolio_heat():.2%}")
    
    # Performance metrics
    metrics = trader.performance_metrics
    if metrics['total_trades'] > 0:
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"Total trades: {metrics['total_trades']}")
        print(f"Win rate: {metrics['win_rate']:.1f}%")
        print(f"Avg win: {metrics['avg_win']:.2f}%")
        print(f"Avg loss: {metrics['avg_loss']:.2f}%")
        print(f"Profit factor: {metrics['profit_factor']:.2f}")
    
    print(f"{'='*60}\n")


def run_continuous(trader: AutonomousTrader, storage: StorageManager, interval_seconds=300, max_hot_stocks=50):
    """
    Run autonomous trader continuously with specified interval.
    
    Args:
        trader: AutonomousTrader instance
        storage: StorageManager instance  
        interval_seconds: Seconds between runs (default 300 = 5 minutes)
        max_hot_stocks: Max hot stocks to analyze per run
    """
    print(f"\n🚀 Starting continuous autonomous trading")
    print(f"   Interval: {interval_seconds} seconds ({interval_seconds//60} minutes)")
    print(f"   Max hot stocks per run: {max_hot_stocks}")
    print(f"   Press Ctrl+C to stop\n")
    
    run_count = 0
    
    try:
        while True:
            run_count += 1
            
            try:
                run_once(trader, storage, max_hot_stocks=max_hot_stocks)
            except Exception as e:
                print(f"❌ Error in run {run_count}: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"\n⏳ Waiting {interval_seconds} seconds until next run...")
            print(f"   Next run at: {(datetime.now() + timedelta(seconds=interval_seconds)).strftime('%H:%M:%S')}")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped by user after {run_count} runs")
        print(f"Final stats:")
        print(f"  Total positions: {len(trader.get_current_positions())}")
        print(f"  Portfolio heat: {trader.get_portfolio_heat():.2%}")
        print(f"  Total trades: {trader.performance_metrics.get('total_trades', 0)}")


def main():
    parser = argparse.ArgumentParser(description='Run Autonomous AI Trader')
    parser.add_argument(
        '--mode',
        choices=['once', 'continuous'],
        default='once',
        help='Run mode: once or continuous'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Interval in seconds for continuous mode (default: 300 = 5 min)'
    )
    parser.add_argument(
        '--paper',
        action='store_true',
        help='Use paper trading (recommended)'
    )
    parser.add_argument(
        '--max-hot-stocks',
        type=int,
        default=50,
        help='Maximum number of hot stocks to analyze (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Validate trading mode
    if not args.paper:
        confirm = input("⚠️ WARNING: You are about to use REAL MONEY trading. Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("Cancelled. Use --paper flag for paper trading.")
            return
    
    print(f"\n{'='*60}")
    print(f"🤖 AUTONOMOUS AI TRADER")
    print(f"{'='*60}")
    print(f"Mode: {args.mode}")
    if args.mode == 'continuous':
        print(f"Interval: {args.interval} seconds")
    print(f"Trading: {'PAPER' if args.paper else '⚠️ REAL MONEY'}")
    print(f"Max hot stocks: {args.max_hot_stocks}")
    print(f"{'='*60}\n")
    
    # Initialize
    try:
        trader = AutonomousTrader(paper_trading=args.paper)
        storage = StorageManager()
        
        print("✅ Trader initialized successfully\n")
        
        # Run
        if args.mode == 'once':
            run_once(trader, storage, max_hot_stocks=args.max_hot_stocks)
        else:
            run_continuous(trader, storage, interval_seconds=args.interval, max_hot_stocks=args.max_hot_stocks)
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
