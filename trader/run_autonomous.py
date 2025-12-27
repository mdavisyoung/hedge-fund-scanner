"""
Autonomous Trader Runner
Continuously monitors hot stocks and executes trades
"""

import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from autonomous_trader import AutonomousTrader


class AutonomousRunner:
    """Orchestrates the autonomous trading loop"""

    def __init__(self, paper_trading=True, check_interval=300):
        """
        Initialize runner

        Args:
            paper_trading: Use paper trading account (default: True)
            check_interval: Seconds between checks (default: 300 = 5 minutes)
        """
        self.trader = AutonomousTrader(paper_trading=paper_trading)
        self.check_interval = check_interval
        self.data_dir = Path("data")

        print(f"🚀 Autonomous Trader initialized")
        print(f"   Paper Trading: {paper_trading}")
        print(f"   Check Interval: {check_interval}s ({check_interval/60:.1f} minutes)")

    def load_hot_stocks(self) -> List[Dict]:
        """Load hot stocks from scanner results"""
        hot_file = self.data_dir / "hot_stocks.json"

        if not hot_file.exists():
            print("⚠️ No hot stocks file found. Run scanner first.")
            return []

        try:
            with open(hot_file, 'r') as f:
                data = json.load(f)
                return data.get('stocks', [])
        except Exception as e:
            print(f"❌ Error loading hot stocks: {e}")
            return []

    def analyze_and_trade(self):
        """Main trading logic - analyze opportunities and execute trades"""
        print(f"\n{'='*60}")
        print(f"🔍 Checking opportunities - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        # Get account info
        account = self.trader.get_account_info()
        print(f"\n💰 Account Status:")
        print(f"   Portfolio Value: ${account['portfolio_value']:,.2f}")
        print(f"   Cash: ${account['cash']:,.2f}")
        print(f"   Buying Power: ${account['buying_power']:,.2f}")

        # Get current positions
        positions = self.trader.get_current_positions()
        print(f"\n📊 Current Positions: {len(positions)}")
        for pos in positions:
            print(f"   {pos['ticker']}: {pos['qty']} shares @ ${pos['entry_price']:.2f}")
            print(f"      Current: ${pos['current_price']:.2f} | P/L: {pos['unrealized_pnl_pct']:+.2f}%")

        # Check portfolio heat
        portfolio_heat = self.trader.get_portfolio_heat()
        print(f"\n🔥 Portfolio Heat: {portfolio_heat:.2%} (max: {self.trader.max_portfolio_heat:.2%})")

        # Monitor existing positions for exits
        print(f"\n👀 Monitoring positions for exit signals...")
        actions_needed = self.trader.monitor_positions()

        for action in actions_needed:
            ticker = action['ticker']
            reason = action['reason']
            print(f"\n🚨 EXIT SIGNAL: {ticker} - {reason}")
            print(f"   Current Price: ${action['current_price']:.2f}")
            print(f"   P/L: {action['pnl_pct']:+.2f}%")

            # Execute exit
            success = self.trader.exit_position(ticker, reason)
            if success:
                print(f"✅ Successfully exited {ticker}")
            else:
                print(f"❌ Failed to exit {ticker}")

        # Load hot stocks
        hot_stocks = self.load_hot_stocks()
        print(f"\n📈 Hot Stocks Available: {len(hot_stocks)}")

        if not hot_stocks:
            print("   No hot stocks to analyze")
            return

        # Analyze each hot stock
        for stock in hot_stocks[:10]:  # Limit to top 10
            ticker = stock['ticker']
            score = stock['score']['total_score']

            print(f"\n{'─'*60}")
            print(f"🎯 Analyzing: {ticker} (Score: {score:.1f}/100)")

            # AI analysis
            analysis = self.trader.analyze_opportunity(stock)
            confidence = analysis.get('confidence', 0)
            recommendation = analysis.get('recommendation', 'SKIP')
            reasoning = analysis.get('reasoning', 'No reasoning provided')

            print(f"   AI Confidence: {confidence}/10")
            print(f"   Recommendation: {recommendation}")
            print(f"   Reasoning: {reasoning[:100]}...")

            # Decide whether to trade
            if self.trader.should_trade(stock, analysis):
                print(f"\n✨ EXECUTING TRADE for {ticker}")
                trade_result = self.trader.execute_trade(stock, analysis)

                if trade_result:
                    print(f"✅ Trade executed successfully!")
                else:
                    print(f"❌ Trade execution failed")
            else:
                print(f"   ⏭️ Skipping {ticker}")

        # Show performance metrics
        metrics = self.trader.performance_metrics
        print(f"\n{'='*60}")
        print(f"📊 Performance Metrics:")
        print(f"   Total Trades: {metrics['total_trades']}")
        print(f"   Win Rate: {metrics['win_rate']:.1f}%")
        print(f"   Avg Win: {metrics['avg_win']:+.2f}%")
        print(f"   Avg Loss: {metrics['avg_loss']:.2f}%")
        print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"   Total P/L: {metrics['total_pnl_pct']:+.2f}%")
        print(f"{'='*60}\n")

    def run_continuous(self):
        """Run the trading loop continuously"""
        print(f"\n🤖 Starting continuous autonomous trading...")
        print(f"   Checking every {self.check_interval/60:.1f} minutes")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                self.analyze_and_trade()

                # Wait before next check
                print(f"⏳ Waiting {self.check_interval/60:.1f} minutes until next check...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print(f"\n\n🛑 Stopping autonomous trader...")
            print(f"   Final metrics:")

            # Show final performance
            metrics = self.trader.performance_metrics
            print(f"\n   Total Trades: {metrics['total_trades']}")
            print(f"   Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   Total P/L: {metrics['total_pnl_pct']:+.2f}%")

            print(f"\n✅ Trader stopped successfully")

    def run_once(self):
        """Run the trading logic one time (useful for testing)"""
        print(f"\n🤖 Running autonomous trader once...\n")
        self.analyze_and_trade()
        print(f"\n✅ Single run complete")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Hedge Fund Trader")
    parser.add_argument(
        '--mode',
        choices=['continuous', 'once'],
        default='continuous',
        help='Run mode: continuous or once (default: continuous)'
    )
    parser.add_argument(
        '--paper',
        action='store_true',
        default=True,
        help='Use paper trading (default: True, always safe)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300 = 5 minutes)'
    )

    args = parser.parse_args()

    # Create runner
    runner = AutonomousRunner(
        paper_trading=args.paper,
        check_interval=args.interval
    )

    # Run based on mode
    if args.mode == 'once':
        runner.run_once()
    else:
        runner.run_continuous()


if __name__ == "__main__":
    main()
