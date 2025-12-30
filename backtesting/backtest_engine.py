"""
Backtest Engine
Main orchestration for running backtests on historical data
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backtesting.historical_data import HistoricalDataFetcher
from backtesting.simulated_trader import SimulatedTrader
from backtesting.performance_metrics import PerformanceCalculator

from scanner.market_scanner import MarketScanner
from scanner.scoring import TradeScorer
from utils import StockAnalyzer

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class BacktestEngine:
    """
    Main backtesting engine

    Tests trading strategies on historical data without real money
    """

    def __init__(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float = 100_000,
        confidence_threshold: int = 7
    ):
        """
        Initialize backtest engine

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Starting capital
            confidence_threshold: Minimum AI confidence to trade (1-10)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.confidence_threshold = confidence_threshold

        # Initialize components
        self.data_fetcher = HistoricalDataFetcher()
        self.trader = SimulatedTrader(initial_capital=initial_capital)
        self.scanner = MarketScanner(max_workers=5)
        self.scorer = TradeScorer()
        self.analyzer = StockAnalyzer()

        # Storage
        self.historical_data = {}  # ticker -> DataFrame
        self.scan_results = {}  # date -> scan results

    def fetch_historical_data(self, tickers: List[str]):
        """
        Fetch historical data for all tickers

        Args:
            tickers: List of stock symbols to fetch
        """
        print(f"\nFetching historical data for {len(tickers)} stocks...")
        print(f"Date range: {self.start_date} to {self.end_date}")

        self.historical_data = self.data_fetcher.fetch_multiple_stocks(
            tickers,
            self.start_date,
            self.end_date,
            delay_seconds=0.2  # Faster for backtesting
        )

        print(f"Successfully fetched data for {len(self.historical_data)} stocks")

    def score_stocks_for_date(
        self,
        tickers: List[str],
        target_date: str
    ) -> List[Dict]:
        """
        Score stocks as they would have been scored on a specific date

        Note: This uses current fundamentals (limitation of free data)
        For production backtesting, would need historical fundamentals

        Args:
            tickers: List of tickers to score
            target_date: Date to score for (YYYY-MM-DD)

        Returns:
            List of scored stocks
        """
        scored_stocks = []

        for ticker in tickers:
            try:
                # Get price data up to target date
                if ticker not in self.historical_data:
                    continue

                df = self.historical_data[ticker]
                historical_slice = df[df.index <= target_date]

                if len(historical_slice) < 60:  # Need at least 60 days
                    continue

                # Get fundamentals (limitation: uses current, not historical)
                fundamentals = self.analyzer.get_fundamentals(ticker)
                if not fundamentals:
                    continue

                # Score using historical price data
                stock_type = self.analyzer.classify_stock_type(fundamentals)
                score_result = self.scorer.score_stock(
                    fundamentals,
                    historical_slice,
                    stock_type
                )

                # Get current price as of target date
                current_price = historical_slice['Close'].iloc[-1]

                scored_stocks.append({
                    'ticker': ticker,
                    'score': score_result,
                    'fundamentals': fundamentals,
                    'current_price': current_price,
                    'entry_price': current_price,
                    'stop_loss': current_price * 0.90,
                    'target': current_price * 1.15,
                    'date': target_date
                })

            except Exception as e:
                # Silently skip problematic stocks
                pass

        return scored_stocks

    def simulate_ai_decision(
        self,
        stock: Dict,
        use_actual_ai: bool = False
    ) -> Dict:
        """
        Simulate AI trading decision

        Args:
            stock: Stock data dict
            use_actual_ai: If True, call real AI API (costs money!)

        Returns:
            Dict with confidence, recommendation, reasoning
        """
        if use_actual_ai:
            # Actually call AI (expensive!)
            from trader.autonomous_trader import AutonomousTrader
            trader = AutonomousTrader(paper_trading=True)
            return trader.analyze_opportunity(stock)

        # Otherwise, simulate AI based on score
        # This is a simplified heuristic
        score = stock['score']['total_score']

        if score >= 90:
            confidence = 9
            recommendation = 'BUY'
            reasoning = 'Excellent score across all metrics'
        elif score >= 85:
            confidence = 8
            recommendation = 'BUY'
            reasoning = 'Strong fundamentals and technicals'
        elif score >= 80:
            confidence = 7
            recommendation = 'BUY'
            reasoning = 'Good opportunity with acceptable risk'
        elif score >= 75:
            confidence = 6
            recommendation = 'WAIT'
            reasoning = 'Decent but not compelling'
        else:
            confidence = 5
            recommendation = 'SKIP'
            reasoning = 'Score not high enough'

        return {
            'confidence': confidence,
            'recommendation': recommendation,
            'reasoning': reasoning,
            'simulated': True
        }

    def run_backtest(
        self,
        tickers: List[str],
        use_actual_ai: bool = False
    ) -> Dict:
        """
        Run full backtest

        Args:
            tickers: List of stocks to trade
            use_actual_ai: If True, use real AI API (costs money!)

        Returns:
            Dict with backtest results
        """
        print("\n" + "=" * 60)
        print("STARTING BACKTEST")
        print("=" * 60)
        print(f"Date range: {self.start_date} to {self.end_date}")
        print(f"Initial capital: ${self.initial_capital:,.2f}")
        print(f"Stock universe: {len(tickers)} stocks")
        print(f"Confidence threshold: {self.confidence_threshold}/10")
        print(f"Using {'REAL AI' if use_actual_ai else 'SIMULATED AI'}")
        print("=" * 60)

        # Fetch historical data
        self.fetch_historical_data(tickers)

        # Get trading days
        trading_days = self.data_fetcher.get_trading_days(
            self.start_date,
            self.end_date
        )

        print(f"\nSimulating {len(trading_days)} trading days...")

        # Simulate each trading day
        for i, current_date in enumerate(trading_days, 1):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(trading_days)} days ({i/len(trading_days)*100:.1f}%)")

            # Get current prices for all stocks
            current_prices = {}
            for ticker, df in self.historical_data.items():
                try:
                    price = df[df.index <= current_date]['Close'].iloc[-1]
                    current_prices[ticker] = price
                except:
                    pass

            # Check exits first
            exits = self.trader.check_exits(current_prices, current_date)

            # Take daily snapshot
            self.trader.take_snapshot(current_prices, current_date)

            # Look for new entries (only if we have capacity)
            if len(self.trader.positions) < 5:  # Max 5 positions
                # Score stocks for this date
                scored_stocks = self.score_stocks_for_date(tickers, current_date)

                # Filter to hot stocks (score >= 80)
                hot_stocks = [s for s in scored_stocks if s['score']['total_score'] >= 80]

                # Sort by score
                hot_stocks.sort(key=lambda x: x['score']['total_score'], reverse=True)

                # Analyze top stocks
                for stock in hot_stocks[:10]:  # Analyze top 10
                    # Skip if already holding
                    if stock['ticker'] in self.trader.positions:
                        continue

                    # Simulate AI decision
                    analysis = self.simulate_ai_decision(stock, use_actual_ai)

                    # Decide whether to trade
                    if (analysis['confidence'] >= self.confidence_threshold and
                        analysis['recommendation'] == 'BUY'):

                        # Execute trade
                        success = self.trader.enter_position(
                            stock['ticker'],
                            stock['entry_price'],
                            current_date,
                            analysis['confidence'],
                            analysis['reasoning']
                        )

                        if success:
                            break  # Only one new position per day

        print(f"\nBacktest complete! Simulated {len(trading_days)} trading days")

        # Calculate performance metrics
        summary = self.trader.get_summary()
        metrics = PerformanceCalculator.analyze_backtest_results(
            self.trader.daily_snapshots,
            [t for t in self.trader.trade_history if t['status'] == 'CLOSED'],
            self.initial_capital
        )

        # Combine results
        results = {
            **summary,
            **metrics,
            'backtest_config': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_capital': self.initial_capital,
                'confidence_threshold': self.confidence_threshold,
                'used_actual_ai': use_actual_ai,
                'stock_universe_size': len(tickers)
            }
        }

        return results

    def print_results(self, results: Dict):
        """Print formatted backtest results"""
        PerformanceCalculator.print_report(results)

        print("\nBACKTEST CONFIGURATION:")
        config = results['backtest_config']
        print(f"  Start Date: {config['start_date']}")
        print(f"  End Date: {config['end_date']}")
        print(f"  Stock Universe: {config['stock_universe_size']} stocks")
        print(f"  Confidence Threshold: {config['confidence_threshold']}/10")
        print(f"  AI Type: {'REAL' if config['used_actual_ai'] else 'SIMULATED'}")

    def export_results(self, filename: str):
        """Export backtest results to JSON"""
        results = {
            'summary': self.trader.get_summary(),
            'trade_history': self.trader.trade_history,
            'daily_snapshots': self.trader.daily_snapshots,
            'backtest_config': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_capital': self.initial_capital,
                'confidence_threshold': self.confidence_threshold
            }
        }

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults exported to: {output_path}")


if __name__ == '__main__':
    # Example backtest
    print("Running example backtest...")

    # Test with a small stock universe
    test_tickers = ['AAPL', 'NVDA', 'MSFT', 'GOOGL', 'META']

    # Create backtest engine
    engine = BacktestEngine(
        start_date='2024-01-01',
        end_date='2024-03-31',  # 3 months
        initial_capital=100_000,
        confidence_threshold=7
    )

    # Run backtest (using simulated AI, not real API)
    results = engine.run_backtest(test_tickers, use_actual_ai=False)

    # Print results
    engine.print_results(results)

    # Export results
    engine.export_results('data/backtest_results.json')
