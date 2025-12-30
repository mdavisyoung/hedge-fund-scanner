"""
Performance Metrics Calculator
Calculates standard trading performance metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class PerformanceCalculator:
    """Calculate trading performance metrics"""

    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe Ratio

        Args:
            returns: Series of daily returns
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio
        """
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        if excess_returns.std() == 0:
            return 0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sortino Ratio (like Sharpe but only penalizes downside volatility)

        Args:
            returns: Series of daily returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sortino ratio
        """
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0

        downside_std = downside_returns.std()
        return np.sqrt(252) * excess_returns.mean() / downside_std

    @staticmethod
    def calculate_max_drawdown(portfolio_values: pd.Series) -> Dict:
        """
        Calculate maximum drawdown

        Args:
            portfolio_values: Series of portfolio values over time

        Returns:
            Dict with max_drawdown_pct, peak_date, trough_date, recovery_date
        """
        # Calculate running maximum
        running_max = portfolio_values.expanding().max()

        # Calculate drawdown
        drawdown = (portfolio_values - running_max) / running_max

        max_drawdown_pct = drawdown.min() * 100

        # Find peak, trough, and recovery
        trough_idx = drawdown.idxmin()
        peak_idx = portfolio_values[:trough_idx].idxmax()

        # Find recovery (first time we exceed previous peak after trough)
        recovery_idx = None
        for idx in portfolio_values[trough_idx:].index:
            if portfolio_values[idx] >= running_max[peak_idx]:
                recovery_idx = idx
                break

        return {
            'max_drawdown_pct': max_drawdown_pct,
            'peak_date': str(peak_idx) if peak_idx else None,
            'trough_date': str(trough_idx) if trough_idx else None,
            'recovery_date': str(recovery_idx) if recovery_idx else None,
            'drawdown_days': (trough_idx - peak_idx).days if peak_idx and trough_idx else 0
        }

    @staticmethod
    def calculate_win_metrics(trades: List[Dict]) -> Dict:
        """
        Calculate win/loss metrics

        Args:
            trades: List of closed trades with 'pnl' and 'pnl_pct'

        Returns:
            Dict with win metrics
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'profit_factor': 0
            }

        winning = [t for t in trades if t['pnl'] > 0]
        losing = [t for t in trades if t['pnl'] <= 0]

        total_trades = len(trades)
        win_rate = len(winning) / total_trades * 100 if total_trades > 0 else 0

        avg_win = sum(t['pnl_pct'] for t in winning) / len(winning) if winning else 0
        avg_loss = sum(t['pnl_pct'] for t in losing) / len(losing) if losing else 0

        best_trade = max(t['pnl_pct'] for t in trades) if trades else 0
        worst_trade = min(t['pnl_pct'] for t in trades) if trades else 0

        total_wins = sum(t['pnl'] for t in winning)
        total_losses = abs(sum(t['pnl'] for t in losing))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'profit_factor': profit_factor,
            'expectancy': (win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss)
        }

    @staticmethod
    def calculate_risk_adjusted_returns(
        total_return_pct: float,
        max_drawdown_pct: float,
        volatility: float
    ) -> Dict:
        """
        Calculate risk-adjusted return metrics

        Args:
            total_return_pct: Total return percentage
            max_drawdown_pct: Maximum drawdown percentage (negative)
            volatility: Annualized volatility

        Returns:
            Dict with risk-adjusted metrics
        """
        # Calmar Ratio: Return / Max Drawdown
        calmar_ratio = abs(total_return_pct / max_drawdown_pct) if max_drawdown_pct != 0 else 0

        # Return / Volatility
        return_vol_ratio = total_return_pct / volatility if volatility != 0 else 0

        return {
            'calmar_ratio': calmar_ratio,
            'return_volatility_ratio': return_vol_ratio
        }

    @staticmethod
    def analyze_backtest_results(
        daily_snapshots: List[Dict],
        trades: List[Dict],
        initial_capital: float
    ) -> Dict:
        """
        Comprehensive analysis of backtest results

        Args:
            daily_snapshots: List of daily portfolio snapshots
            trades: List of closed trades
            initial_capital: Starting capital

        Returns:
            Dict with comprehensive metrics
        """
        if not daily_snapshots:
            return {'error': 'No snapshot data available'}

        # Convert snapshots to DataFrame
        df = pd.DataFrame(daily_snapshots)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # Calculate returns
        portfolio_values = df['portfolio_value']
        returns = portfolio_values.pct_change().dropna()

        # Calculate metrics
        total_return_pct = (portfolio_values.iloc[-1] / initial_capital - 1) * 100
        annualized_return = ((portfolio_values.iloc[-1] / initial_capital) ** (252 / len(df)) - 1) * 100

        volatility = returns.std() * np.sqrt(252) * 100

        sharpe = PerformanceCalculator.calculate_sharpe_ratio(returns)
        sortino = PerformanceCalculator.calculate_sortino_ratio(returns)

        drawdown_metrics = PerformanceCalculator.calculate_max_drawdown(portfolio_values)
        win_metrics = PerformanceCalculator.calculate_win_metrics(trades)

        risk_adjusted = PerformanceCalculator.calculate_risk_adjusted_returns(
            total_return_pct,
            drawdown_metrics['max_drawdown_pct'],
            volatility
        )

        # Trading frequency
        trading_days = len(df)
        trades_per_day = len(trades) / trading_days if trading_days > 0 else 0

        return {
            # Returns
            'total_return_pct': total_return_pct,
            'annualized_return_pct': annualized_return,
            'volatility_annualized_pct': volatility,

            # Risk metrics
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            **drawdown_metrics,
            **risk_adjusted,

            # Win/loss metrics
            **win_metrics,

            # Trading activity
            'trading_days': trading_days,
            'trades_per_day': trades_per_day,
            'avg_holding_period_days': PerformanceCalculator._calculate_avg_holding_period(trades),

            # Capital efficiency
            'initial_capital': initial_capital,
            'final_capital': portfolio_values.iloc[-1],
            'max_capital': portfolio_values.max(),
            'min_capital': portfolio_values.min()
        }

    @staticmethod
    def _calculate_avg_holding_period(trades: List[Dict]) -> float:
        """Calculate average holding period in days"""
        if not trades:
            return 0

        holding_periods = []
        for trade in trades:
            if 'entry_date' in trade and 'exit_date' in trade:
                entry = datetime.fromisoformat(trade['entry_date'].split('T')[0])
                exit_date = datetime.fromisoformat(trade['exit_date'].split('T')[0])
                days = (exit_date - entry).days
                holding_periods.append(days)

        return sum(holding_periods) / len(holding_periods) if holding_periods else 0

    @staticmethod
    def print_report(metrics: Dict):
        """Print formatted performance report"""
        print("\n" + "=" * 60)
        print("BACKTEST PERFORMANCE REPORT")
        print("=" * 60)

        print("\nRETURNS:")
        print(f"  Total Return: {metrics['total_return_pct']:.2f}%")
        print(f"  Annualized Return: {metrics['annualized_return_pct']:.2f}%")
        print(f"  Volatility (Annual): {metrics['volatility_annualized_pct']:.2f}%")

        print("\nRISK METRICS:")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Calmar Ratio: {metrics['calmar_ratio']:.2f}")

        print("\nWIN/LOSS METRICS:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.2f}%")
        print(f"  Average Win: {metrics['avg_win']:.2f}%")
        print(f"  Average Loss: {metrics['avg_loss']:.2f}%")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  Expectancy: {metrics['expectancy']:.2f}%")

        print("\nTRADING ACTIVITY:")
        print(f"  Trading Days: {metrics['trading_days']}")
        print(f"  Trades Per Day: {metrics['trades_per_day']:.2f}")
        print(f"  Avg Holding Period: {metrics['avg_holding_period_days']:.1f} days")

        print("\nCAPITAL:")
        print(f"  Initial: ${metrics['initial_capital']:,.2f}")
        print(f"  Final: ${metrics['final_capital']:,.2f}")
        print(f"  Max: ${metrics['max_capital']:,.2f}")
        print(f"  Min: ${metrics['min_capital']:,.2f}")

        print("=" * 60)


if __name__ == '__main__':
    # Test performance calculator
    import json

    # Simulate some backtest results
    daily_snapshots = [
        {'date': '2024-01-01', 'portfolio_value': 100000},
        {'date': '2024-01-02', 'portfolio_value': 101000},
        {'date': '2024-01-03', 'portfolio_value': 99000},
        {'date': '2024-01-04', 'portfolio_value': 102000},
        {'date': '2024-01-05', 'portfolio_value': 105000},
    ]

    trades = [
        {'pnl': 1000, 'pnl_pct': 5, 'entry_date': '2024-01-01', 'exit_date': '2024-01-02'},
        {'pnl': -500, 'pnl_pct': -2, 'entry_date': '2024-01-02', 'exit_date': '2024-01-03'},
        {'pnl': 2000, 'pnl_pct': 8, 'entry_date': '2024-01-03', 'exit_date': '2024-01-05'},
    ]

    metrics = PerformanceCalculator.analyze_backtest_results(
        daily_snapshots,
        trades,
        initial_capital=100000
    )

    PerformanceCalculator.print_report(metrics)
