"""
Run Backtest - Easy command-line interface for backtesting

Usage:
    python run_backtest.py --start 2024-01-01 --end 2024-12-31
    python run_backtest.py --start 2024-01-01 --end 2024-12-31 --capital 50000
    python run_backtest.py --preset ytd
    python run_backtest.py --preset 2024
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from backtesting.backtest_engine import BacktestEngine
from scanner.stock_universe import SP500_TECH, GROWTH_MOVERS, SP500_FINANCIAL


def get_preset_dates(preset: str):
    """Get start/end dates for common presets"""
    today = datetime.now()

    presets = {
        'ytd': (f'{today.year}-01-01', today.strftime('%Y-%m-%d')),
        '2024': ('2024-01-01', '2024-12-31'),
        '2023': ('2023-01-01', '2023-12-31'),
        'q1_2024': ('2024-01-01', '2024-03-31'),
        'q2_2024': ('2024-04-01', '2024-06-30'),
        'q3_2024': ('2024-07-01', '2024-09-30'),
        'q4_2024': ('2024-10-01', '2024-12-31'),
        '6m': ((today - timedelta(days=180)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
        '3m': ((today - timedelta(days=90)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
        '1m': ((today - timedelta(days=30)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
    }

    return presets.get(preset.lower())


def get_stock_universe(universe: str):
    """Get stock list for different universes"""
    universes = {
        'tech': SP500_TECH + GROWTH_MOVERS,
        'sp500_tech': SP500_TECH,
        'growth': GROWTH_MOVERS,
        'financials': SP500_FINANCIAL,
        'faang': ['META', 'AAPL', 'AMZN', 'NFLX', 'GOOGL'],
        'mag7': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
        'test': ['AAPL', 'NVDA', 'MSFT', 'GOOGL', 'META'],  # Small for quick testing
    }

    return universes.get(universe.lower(), universes['test'])


def main():
    parser = argparse.ArgumentParser(description='Run backtesting on historical data')

    # Date selection
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--preset', type=str, help='Use preset date range (ytd, 2024, 2023, q1_2024, 6m, 3m, 1m)')
    date_group.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')

    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD, required if using --start)')

    # Strategy parameters
    parser.add_argument('--capital', type=float, default=100_000, help='Initial capital (default: 100000)')
    parser.add_argument('--confidence', type=int, default=7, help='Min confidence threshold 1-10 (default: 7)')

    # Stock universe
    parser.add_argument(
        '--universe',
        type=str,
        default='test',
        help='Stock universe: tech, sp500_tech, growth, financials, faang, mag7, test (default: test)'
    )

    # AI options
    parser.add_argument(
        '--use-real-ai',
        action='store_true',
        help='Use real AI API (costs money! Default: simulated AI)'
    )

    # Output
    parser.add_argument('--output', type=str, help='Output filename for results (default: data/backtest_results.json)')

    args = parser.parse_args()

    # Determine dates
    if args.preset:
        dates = get_preset_dates(args.preset)
        if not dates:
            print(f"Unknown preset: {args.preset}")
            print("Available presets: ytd, 2024, 2023, q1_2024, q2_2024, q3_2024, q4_2024, 6m, 3m, 1m")
            return 1
        start_date, end_date = dates
    else:
        if not args.end:
            parser.error("--end is required when using --start")
        start_date = args.start
        end_date = args.end

    # Get stock universe
    tickers = get_stock_universe(args.universe)

    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'data/backtest_{args.universe}_{start_date}_to_{end_date}_{timestamp}.json'

    # Warning about real AI
    if args.use_real_ai:
        print("\n" + "!" * 60)
        print("WARNING: Using REAL AI will cost money!")
        print(f"Estimated cost: ${len(tickers) * 0.005 * 100:.2f} (rough estimate)")
        print("!" * 60)
        confirm = input("Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("Cancelled. Using simulated AI instead.")
            args.use_real_ai = False

    # Create and run backtest
    print("\n" + "=" * 60)
    print("BACKTEST CONFIGURATION")
    print("=" * 60)
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Confidence Threshold: {args.confidence}/10")
    print(f"Stock Universe: {args.universe} ({len(tickers)} stocks)")
    print(f"AI Mode: {'REAL ($$!)' if args.use_real_ai else 'SIMULATED (free)'}")
    print(f"Output: {output_file}")
    print("=" * 60)

    engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        initial_capital=args.capital,
        confidence_threshold=args.confidence
    )

    # Run backtest
    results = engine.run_backtest(tickers, use_actual_ai=args.use_real_ai)

    # Print results
    engine.print_results(results)

    # Export results
    engine.export_results(output_file)

    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE!")
    print("=" * 60)
    print(f"Results saved to: {output_file}")

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nBacktest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running backtest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
