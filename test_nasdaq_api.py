"""
Direct test of NASDAQ API to see raw response
"""

import requests
import json

print("=" * 60)
print("🔍 DIRECT NASDAQ API TEST")
print("=" * 60)
print()

nasdaq_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25000&offset=0&download=true"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.nasdaq.com/'
}

print("📡 Calling NASDAQ API...")
print(f"URL: {nasdaq_url}")
print()

try:
    response = requests.get(nasdaq_url, headers=headers, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ API call successful!")
        print()
        print("Response structure:")
        print(f"  - Keys: {list(data.keys())}")
        
        if 'data' in data:
            print(f"  - data keys: {list(data['data'].keys())}")
            
            if 'rows' in data['data']:
                rows = data['data']['rows']
                print(f"  - Total rows: {len(rows)}")
                print()
                
                # Show first 10 rows
                print("First 10 stock entries:")
                print("-" * 60)
                
                unique_exchanges = set()
                
                for i, row in enumerate(rows[:10]):
                    symbol = row.get('symbol', 'N/A')
                    exchange = row.get('exchange', 'N/A')
                    market_cap = row.get('marketCap', 'N/A')
                    volume = row.get('volume', 'N/A')
                    
                    print(f"{i+1}. {symbol}")
                    print(f"   Exchange: '{exchange}'")
                    print(f"   Market Cap: {market_cap}")
                    print(f"   Volume: {volume}")
                    print()
                    
                    if exchange != 'N/A':
                        unique_exchanges.add(exchange)
                
                # Now check ALL rows for unique exchanges
                print("Collecting ALL unique exchange names...")
                all_unique_exchanges = set()
                
                for row in rows:
                    exchange = row.get('exchange', '')
                    if exchange:
                        all_unique_exchanges.add(exchange.upper())
                
                print()
                print("=" * 60)
                print("UNIQUE EXCHANGES FOUND:")
                print("=" * 60)
                print(f"Total unique: {len(all_unique_exchanges)}")
                print()
                
                for ex in sorted(all_unique_exchanges):
                    # Count how many stocks have this exchange
                    count = sum(1 for row in rows if row.get('exchange', '').upper() == ex)
                    print(f"  '{ex}' - {count} stocks")
                
                print()
                print("=" * 60)
                
    else:
        print(f"❌ API call failed with status {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
