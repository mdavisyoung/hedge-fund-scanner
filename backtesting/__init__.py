"""
Backtesting Framework for Autonomous Trading System
Test strategies on historical data without risking real money
"""

from .backtest_engine import BacktestEngine
from .historical_data import HistoricalDataFetcher
from .simulated_trader import SimulatedTrader
from .performance_metrics import PerformanceCalculator

__all__ = [
    'BacktestEngine',
    'HistoricalDataFetcher',
    'SimulatedTrader',
    'PerformanceCalculator'
]
