"""
See what fields are ACTUALLY available in the NASDAQ API response
"""

import requests
import json

nasdaq_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25000&offset=0&download=true"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.nasdaq.com/'
}

print("=" * 60)
print("🔍 CHECKING AVAILABLE FIELDS")
print("=" * 60)
print()

response = requests.get(nasdaq_url, headers=headers, timeout=60)
data = response.json()

if 'data' in data and 'headers' in data['data']:
    print("Available column headers:")
    for header in data['data']['headers']:
        print(f"  - {header}")
    print()

if 'data' in data and 'rows' in data['data']:
    rows = data['data']['rows']
    
    print("First complete row (all fields):")
    print("-" * 60)
    first_row = rows[0]
    for key, value in first_row.items():
        print(f"  {key}: {value}")
    
    print()
    print("-" * 60)
    print()
    
    # Check a few well-known stocks
    print("Checking well-known stocks:")
    print("-" * 60)
    
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'JPM']
    
    for symbol in test_symbols:
        stock = next((r for r in rows if r.get('symbol') == symbol), None)
        if stock:
            print(f"\n{symbol}:")
            for key, value in stock.items():
                print(f"  {key}: {value}")
        else:
            print(f"\n{symbol}: NOT FOUND")
    
    print()
    print("=" * 60)
    print("SOLUTION:")
    print("=" * 60)
    print()
    print("Since 'exchange' field is N/A for everything, we have two options:")
    print()
    print("1. Don't filter by exchange at all - just use:")
    print("   - Market cap >= $50M")
    print("   - Volume >= 100k")
    print()
    print("2. Infer exchange from ticker symbol patterns:")
    print("   - NASDAQ: Usually 4-5 letters, tech companies")
    print("   - NYSE: Usually 1-3 letters, traditional companies")
    print()
    print("RECOMMENDATION: Use option 1 (no exchange filter)")
    print("The market cap + volume filters already exclude penny stocks.")
