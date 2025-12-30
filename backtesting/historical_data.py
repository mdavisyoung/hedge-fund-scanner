"""
Historical Data Fetcher
Downloads and caches historical stock data for backtesting
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional
import time


class HistoricalDataFetcher:
    """Fetches and caches historical stock data"""

    def __init__(self, cache_dir: str = "data/backtest_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_stock_history(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a stock

        Args:
            ticker: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Use cached data if available

        Returns:
            DataFrame with OHLCV data, or None if failed
        """
        cache_file = self.cache_dir / f"{ticker}_{start_date}_{end_date}.parquet"

        # Check cache first
        if use_cache and cache_file.exists():
            try:
                return pd.read_parquet(cache_file)
            except Exception as e:
                print(f"Cache read error for {ticker}: {e}")

        # Fetch from yfinance
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)

            if df.empty:
                print(f"No data for {ticker} from {start_date} to {end_date}")
                return None

            # Save to cache
            df.to_parquet(cache_file)

            return df

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def fetch_multiple_stocks(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        delay_seconds: float = 0.5
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple stocks

        Args:
            tickers: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            delay_seconds: Delay between requests (rate limiting)

        Returns:
            Dict mapping ticker to DataFrame
        """
        results = {}

        for i, ticker in enumerate(tickers, 1):
            print(f"Fetching {ticker} ({i}/{len(tickers)})...")

            df = self.fetch_stock_history(ticker, start_date, end_date)
            if df is not None:
                results[ticker] = df

            # Rate limiting
            if i < len(tickers):
                time.sleep(delay_seconds)

        print(f"Successfully fetched {len(results)}/{len(tickers)} stocks")
        return results

    def get_fundamentals_snapshot(
        self,
        ticker: str,
        date: str
    ) -> Dict:
        """
        Get fundamentals snapshot for a specific date

        Note: yfinance provides current fundamentals, not historical.
        This is a limitation - for real backtesting, would need
        historical fundamentals from a paid data provider.

        Args:
            ticker: Stock symbol
            date: Date (YYYY-MM-DD)

        Returns:
            Dict with available fundamentals (will be current, not historical)
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                'ticker': ticker,
                'date': date,
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'market_cap': info.get('marketCap', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'roe': info.get('returnOnEquity', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'beta': info.get('beta', 1.0),
                'note': 'Current fundamentals (not historical)'
            }
        except Exception as e:
            print(f"Error getting fundamentals for {ticker}: {e}")
            return {}

    def calculate_returns(
        self,
        df: pd.DataFrame,
        period: str = 'daily'
    ) -> pd.Series:
        """
        Calculate returns from price data

        Args:
            df: DataFrame with 'Close' column
            period: 'daily', 'weekly', 'monthly'

        Returns:
            Series of returns
        """
        if period == 'daily':
            return df['Close'].pct_change()
        elif period == 'weekly':
            return df['Close'].resample('W').last().pct_change()
        elif period == 'monthly':
            return df['Close'].resample('M').last().pct_change()
        else:
            raise ValueError(f"Unknown period: {period}")

    def get_trading_days(
        self,
        start_date: str,
        end_date: str
    ) -> List[str]:
        """
        Get list of trading days between dates

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of trading days as strings
        """
        # Use SPY as proxy for trading days
        spy = yf.Ticker('SPY')
        df = spy.history(start=start_date, end=end_date)

        trading_days = df.index.strftime('%Y-%m-%d').tolist()
        return trading_days

    def clear_cache(self):
        """Clear all cached data"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print("Cache cleared")


if __name__ == '__main__':
    # Test the fetcher
    fetcher = HistoricalDataFetcher()

    # Fetch sample data
    df = fetcher.fetch_stock_history('AAPL', '2024-01-01', '2024-12-31')

    if df is not None:
        print(f"Fetched {len(df)} days of AAPL data")
        print(df.head())
        print(f"\nReturns: {fetcher.calculate_returns(df).describe()}")
