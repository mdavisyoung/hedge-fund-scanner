"""
Simulated Trader
Replays trading decisions on historical data without real API calls
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json


class SimulatedTrader:
    """Simulates trading without real API calls"""

    def __init__(
        self,
        initial_capital: float = 100_000,
        max_position_size: float = 0.10,
        max_loss_per_trade: float = 0.02,
        stop_loss_pct: float = 0.10,
        target_profit_pct: float = 0.15
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # ticker -> position dict
        self.trade_history = []
        self.daily_snapshots = []

        # Risk parameters
        self.max_position_size = max_position_size
        self.max_loss_per_trade = max_loss_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.target_profit_pct = target_profit_pct

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        position_value = sum(
            pos['shares'] * current_prices.get(ticker, pos['entry_price'])
            for ticker, pos in self.positions.items()
        )
        return self.cash + position_value

    def enter_position(
        self,
        ticker: str,
        entry_price: float,
        current_date: str,
        confidence: float,
        reasoning: str = ""
    ) -> bool:
        """
        Enter a new position

        Args:
            ticker: Stock symbol
            entry_price: Entry price
            current_date: Date of entry
            confidence: AI confidence (1-10)
            reasoning: AI reasoning

        Returns:
            True if trade executed, False otherwise
        """
        # Check if already holding
        if ticker in self.positions:
            return False

        # Calculate position size
        portfolio_value = self.get_portfolio_value({ticker: entry_price})
        max_loss_amount = portfolio_value * self.max_loss_per_trade

        stop_loss_price = entry_price * (1 - self.stop_loss_pct)
        stop_loss_distance = entry_price - stop_loss_price

        if stop_loss_distance <= 0:
            return False

        # Calculate shares based on risk
        shares = int(max_loss_amount / stop_loss_distance)
        position_value = shares * entry_price

        # Check position size doesn't exceed max
        max_position_value = portfolio_value * self.max_position_size
        if position_value > max_position_value:
            shares = int(max_position_value / entry_price)
            position_value = shares * entry_price

        # Check we have enough cash
        if position_value > self.cash:
            shares = int(self.cash / entry_price)
            position_value = shares * entry_price

        if shares <= 0:
            return False

        # Execute trade
        self.cash -= position_value

        self.positions[ticker] = {
            'shares': shares,
            'entry_price': entry_price,
            'entry_date': current_date,
            'stop_loss': stop_loss_price,
            'target': entry_price * (1 + self.target_profit_pct),
            'confidence': confidence,
            'reasoning': reasoning
        }

        # Log trade
        self.trade_history.append({
            'ticker': ticker,
            'action': 'BUY',
            'shares': shares,
            'price': entry_price,
            'value': position_value,
            'date': current_date,
            'confidence': confidence,
            'status': 'OPEN'
        })

        return True

    def check_exits(
        self,
        current_prices: Dict[str, float],
        current_date: str
    ) -> List[Dict]:
        """
        Check if any positions should be exited

        Args:
            current_prices: Dict of ticker -> current price
            current_date: Current date

        Returns:
            List of exit actions taken
        """
        exits = []
        tickers_to_remove = []

        for ticker, pos in self.positions.items():
            current_price = current_prices.get(ticker)
            if current_price is None:
                continue

            exit_reason = None

            # Check stop loss
            if current_price <= pos['stop_loss']:
                exit_reason = 'STOP_LOSS'

            # Check target
            elif current_price >= pos['target']:
                exit_reason = 'TARGET_REACHED'

            if exit_reason:
                # Execute exit
                exit_value = pos['shares'] * current_price
                self.cash += exit_value

                pnl = exit_value - (pos['shares'] * pos['entry_price'])
                pnl_pct = (current_price / pos['entry_price'] - 1) * 100

                # Log exit
                self.trade_history.append({
                    'ticker': ticker,
                    'action': 'SELL',
                    'shares': pos['shares'],
                    'price': current_price,
                    'value': exit_value,
                    'date': current_date,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': exit_reason,
                    'status': 'CLOSED'
                })

                exits.append({
                    'ticker': ticker,
                    'reason': exit_reason,
                    'pnl_pct': pnl_pct,
                    'entry_date': pos['entry_date'],
                    'exit_date': current_date
                })

                tickers_to_remove.append(ticker)

        # Remove closed positions
        for ticker in tickers_to_remove:
            del self.positions[ticker]

        return exits

    def take_snapshot(self, current_prices: Dict[str, float], current_date: str):
        """Record portfolio snapshot for analysis"""
        portfolio_value = self.get_portfolio_value(current_prices)

        self.daily_snapshots.append({
            'date': current_date,
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'num_positions': len(self.positions),
            'return_pct': (portfolio_value / self.initial_capital - 1) * 100
        })

    def get_summary(self) -> Dict:
        """Get summary of backtest results"""
        closed_trades = [t for t in self.trade_history if t['status'] == 'CLOSED']

        if not closed_trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'final_portfolio_value': self.cash,
                'total_return_pct': 0
            }

        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] <= 0]

        total_trades = len(closed_trades)
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0

        avg_win = sum(t['pnl_pct'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl_pct'] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Calculate final portfolio value
        final_value = self.cash  # Assumes all positions closed
        total_return_pct = (final_value / self.initial_capital - 1) * 100

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'initial_capital': self.initial_capital,
            'final_portfolio_value': final_value,
            'total_return_pct': total_return_pct,
            'total_pnl': final_value - self.initial_capital
        }

    def export_results(self, filename: str):
        """Export backtest results to JSON"""
        results = {
            'summary': self.get_summary(),
            'trade_history': self.trade_history,
            'daily_snapshots': self.daily_snapshots,
            'parameters': {
                'initial_capital': self.initial_capital,
                'max_position_size': self.max_position_size,
                'max_loss_per_trade': self.max_loss_per_trade,
                'stop_loss_pct': self.stop_loss_pct,
                'target_profit_pct': self.target_profit_pct
            }
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Results exported to {filename}")


if __name__ == '__main__':
    # Test simulation
    trader = SimulatedTrader(initial_capital=100_000)

    # Simulate some trades
    trader.enter_position('AAPL', 150.00, '2024-01-01', confidence=8)
    trader.enter_position('NVDA', 500.00, '2024-01-02', confidence=9)

    # Simulate price movements
    prices_day1 = {'AAPL': 152.00, 'NVDA': 510.00}
    trader.check_exits(prices_day1, '2024-01-03')
    trader.take_snapshot(prices_day1, '2024-01-03')

    # Exit at target
    prices_day2 = {'AAPL': 175.00, 'NVDA': 580.00}  # AAPL hits target (+16.7%)
    exits = trader.check_exits(prices_day2, '2024-01-10')
    trader.take_snapshot(prices_day2, '2024-01-10')

    print("Exits:", exits)
    print("\nSummary:")
    summary = trader.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
