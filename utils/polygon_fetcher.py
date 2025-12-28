"""
Polygon Data Fetcher
Fallback data source with better rate limits than Yahoo Finance
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PolygonFetcher:
    """Fetch stock data from Polygon.io API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        self.base_url = 'https://api.polygon.io'

    def get_stock_quote(self, ticker: str) -> Optional[Dict]:
        """
        Get current quote for a stock

        Args:
            ticker: Stock symbol

        Returns:
            Dict with price, volume, etc. or None if failed
        """
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/prev"
            params = {'apiKey': self.api_key}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'OK' and data.get('results'):
                    result = data['results'][0]

                    return {
                        'ticker': ticker,
                        'current_price': result.get('c', 0),  # Close price
                        'open': result.get('o', 0),
                        'high': result.get('h', 0),
                        'low': result.get('l', 0),
                        'volume': result.get('v', 0),
                        'vwap': result.get('vw', 0),  # Volume weighted average price
                        'timestamp': result.get('t', 0),
                        'source': 'polygon'
                    }

            return None

        except Exception as e:
            print(f"Polygon error for {ticker}: {e}")
            return None

    def get_stock_details(self, ticker: str) -> Optional[Dict]:
        """
        Get company details and fundamentals

        Args:
            ticker: Stock symbol

        Returns:
            Dict with company info or None if failed
        """
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/v3/reference/tickers/{ticker}"
            params = {'apiKey': self.api_key}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'OK' and data.get('results'):
                    result = data['results']

                    return {
                        'ticker': ticker,
                        'name': result.get('name', ''),
                        'market_cap': result.get('market_cap', 0),
                        'description': result.get('description', ''),
                        'primary_exchange': result.get('primary_exchange', ''),
                        'type': result.get('type', ''),
                        'currency': result.get('currency_name', ''),
                        'locale': result.get('locale', ''),
                        'market': result.get('market', ''),
                        'active': result.get('active', True),
                        'source': 'polygon'
                    }

            return None

        except Exception as e:
            print(f"Polygon details error for {ticker}: {e}")
            return None

    def get_financials(self, ticker: str) -> Optional[Dict]:
        """
        Get financial data and calculate ratios

        Args:
            ticker: Stock symbol

        Returns:
            Dict with P/E, Current Ratio, ROE, etc. or None if failed
        """
        if not self.api_key:
            return None

        try:
            # Get financials from Polygon
            url = f"{self.base_url}/vX/reference/financials"
            params = {
                'ticker': ticker,
                'apiKey': self.api_key,
                'limit': 4  # Get 4 periods for growth calculations
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('results') and len(data['results']) > 0:
                    latest = data['results'][0]
                    financials = latest.get('financials', {})
                    balance_sheet = financials.get('balance_sheet', {})
                    income_statement = financials.get('income_statement', {})

                    # Get current price for P/E calculation
                    quote = self.get_stock_quote(ticker)
                    current_price = quote['current_price'] if quote else 0

                    # Get company details for market cap
                    details = self.get_stock_details(ticker)
                    market_cap = details['market_cap'] if details else 0

                    # Extract values (Polygon uses nested structure)
                    revenues = income_statement.get('revenues', {}).get('value', 0)
                    net_income = income_statement.get('net_income_loss', {}).get('value', 0)
                    total_assets = balance_sheet.get('assets', {}).get('value', 0)
                    current_assets = balance_sheet.get('current_assets', {}).get('value', 0)
                    current_liabilities = balance_sheet.get('current_liabilities', {}).get('value', 0)
                    equity = balance_sheet.get('equity', {}).get('value', 0)
                    total_liabilities = balance_sheet.get('liabilities', {}).get('value', 0)

                    # Calculate ratios
                    pe_ratio = (market_cap / net_income) if net_income > 0 else 0
                    current_ratio = (current_assets / current_liabilities) if current_liabilities > 0 else 0
                    roe = (net_income / equity * 100) if equity > 0 else 0
                    profit_margin = (net_income / revenues * 100) if revenues > 0 else 0
                    debt_to_equity = (total_liabilities / equity) if equity > 0 else 0
                    price_to_book = (market_cap / equity) if equity > 0 else 0

                    # Get previous period for growth calculation
                    revenue_growth = 0
                    earnings_growth = 0
                    if len(data['results']) > 1:
                        prev = data['results'][1]
                        prev_financials = prev.get('financials', {})
                        prev_income = prev_financials.get('income_statement', {})
                        prev_revenues = prev_income.get('revenues', {}).get('value', 0)
                        prev_net_income = prev_income.get('net_income_loss', {}).get('value', 0)

                        if prev_revenues > 0:
                            revenue_growth = ((revenues - prev_revenues) / prev_revenues * 100)
                        if prev_net_income > 0:
                            earnings_growth = ((net_income - prev_net_income) / prev_net_income * 100)

                    print(f"[Polygon Financials] {ticker}: P/E={pe_ratio:.2f}, Current Ratio={current_ratio:.2f}, ROE={roe:.2f}%")

                    return {
                        'ticker': ticker,
                        'pe_ratio': round(pe_ratio, 2),
                        'current_ratio': round(current_ratio, 2),
                        'roe': round(roe, 2),
                        'profit_margin': round(profit_margin, 2),
                        'debt_to_equity': round(debt_to_equity, 2),
                        'price_to_book': round(price_to_book, 2),
                        'revenue_growth': round(revenue_growth, 2),
                        'earnings_growth': round(earnings_growth, 2),
                        'revenues': revenues,
                        'net_income': net_income,
                        'total_assets': total_assets,
                        'current_assets': current_assets,
                        'current_liabilities': current_liabilities,
                        'equity': equity,
                        'source': 'polygon',
                        'beta': 1.0,  # Polygon doesn't provide beta, use default
                        'dividend_yield': 0,  # Would need separate endpoint
                        'forward_pe': 0,  # Historical data only
                        'quick_ratio': 0  # Would need to calculate from detailed balance sheet
                    }

            return None

        except Exception as e:
            print(f"Polygon financials error for {ticker}: {e}")
            return None

    def get_price_history(
        self,
        ticker: str,
        days: int = 90,
        timespan: str = 'day'
    ) -> Optional[Dict]:
        """
        Get historical price data

        Args:
            ticker: Stock symbol
            days: Number of days of history
            timespan: 'day', 'hour', 'minute'

        Returns:
            Dict with OHLCV data or None if failed
        """
        if not self.api_key:
            return None

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/{timespan}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                'apiKey': self.api_key,
                'adjusted': 'true',
                'sort': 'asc'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Accept both OK and DELAYED status (free tier returns delayed data)
                if data.get('status') in ['OK', 'DELAYED'] and data.get('results'):
                    bars = []
                    for bar in data['results']:
                        bars.append({
                            'timestamp': bar.get('t', 0),
                            'date': datetime.fromtimestamp(bar.get('t', 0) / 1000).strftime('%Y-%m-%d'),
                            'open': bar.get('o', 0),
                            'high': bar.get('h', 0),
                            'low': bar.get('l', 0),
                            'close': bar.get('c', 0),
                            'volume': bar.get('v', 0),
                            'vwap': bar.get('vw', 0)
                        })

                    return {
                        'ticker': ticker,
                        'bars': bars,
                        'count': len(bars),
                        'source': 'polygon',
                        'delayed': data.get('status') == 'DELAYED'
                    }
                else:
                    print(f"Polygon API response issue: status={data.get('status')}, results count={len(data.get('results', []))}")
            else:
                print(f"Polygon API HTTP error: {response.status_code} - {response.text[:200]}")

            return None

        except Exception as e:
            print(f"Polygon history error for {ticker}: {e}")
            return None

    def test_connection(self) -> bool:
        """Test if Polygon API is working"""
        if not self.api_key:
            print("No Polygon API key configured")
            return False

        try:
            # Try fetching AAPL quote as test
            result = self.get_stock_quote('AAPL')
            if result:
                print(f"Polygon API working! AAPL price: ${result['current_price']:.2f}")
                return True
            else:
                print("Polygon API returned no data")
                return False

        except Exception as e:
            print(f"Polygon API test failed: {e}")
            return False


if __name__ == '__main__':
    # Test the Polygon fetcher
    fetcher = PolygonFetcher()

    print("Testing Polygon API...")
    print("=" * 60)

    if fetcher.test_connection():
        print("\nFetching HOOD data from Polygon...")

        # Get quote
        quote = fetcher.get_stock_quote('HOOD')
        if quote:
            print(f"\nQuote:")
            print(f"  Price: ${quote['current_price']:.2f}")
            print(f"  Volume: {quote['volume']:,}")

        # Get details
        details = fetcher.get_stock_details('HOOD')
        if details:
            print(f"\nDetails:")
            print(f"  Name: {details['name']}")
            print(f"  Market Cap: ${details['market_cap']/1e9:.2f}B")
            print(f"  Exchange: {details['primary_exchange']}")

        # Get history
        history = fetcher.get_price_history('HOOD', days=30)
        if history:
            print(f"\nHistory:")
            print(f"  Data points: {history['count']}")
            if history['bars']:
                latest = history['bars'][-1]
                print(f"  Latest close: ${latest['close']:.2f} on {latest['date']}")

    print("\n" + "=" * 60)
