"""
Test Polygon API - Check if fundamental data is being fetched correctly
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

print("=" * 60)
print("🧪 TESTING POLYGON API")
print("=" * 60)

# Check if API key is loaded
print(f"\n1️⃣ API Key Check:")
if POLYGON_API_KEY and POLYGON_API_KEY != 'your_polygon_api_key_here':
    print(f"   ✅ API Key loaded: {POLYGON_API_KEY[:20]}...{POLYGON_API_KEY[-10:]}")
else:
    print(f"   ❌ API Key not set or is placeholder")
    exit(1)

# Test 1: Get ticker details
print(f"\n2️⃣ Testing Ticker Details (NVDA):")
url = f"https://api.polygon.io/v3/reference/tickers/NVDA?apiKey={POLYGON_API_KEY}"
try:
    response = requests.get(url, timeout=10)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response received")
        print(f"\n   Raw Response (first 500 chars):")
        print(f"   {str(data)[:500]}...")
        
        if 'results' in data:
            results = data['results']
            print(f"\n   📊 Ticker Info:")
            print(f"      Name: {results.get('name', 'N/A')}")
            print(f"      Market Cap: ${results.get('market_cap', 0):,.0f}")
            print(f"      Primary Exchange: {results.get('primary_exchange', 'N/A')}")
            print(f"      Currency: {results.get('currency_name', 'N/A')}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Get financials
print(f"\n3️⃣ Testing Financial Data (NVDA):")
url = f"https://api.polygon.io/vX/reference/financials?ticker=NVDA&apiKey={POLYGON_API_KEY}"
try:
    response = requests.get(url, timeout=10)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response received")
        
        if 'results' in data and len(data['results']) > 0:
            latest = data['results'][0]
            print(f"\n   📈 Latest Financials:")
            print(f"      Period: {latest.get('fiscal_period', 'N/A')} {latest.get('fiscal_year', 'N/A')}")
            
            # Try to extract key metrics
            financials = latest.get('financials', {})
            balance_sheet = financials.get('balance_sheet', {})
            income_statement = financials.get('income_statement', {})
            
            print(f"\n   💰 Income Statement:")
            print(f"      Revenue: ${income_statement.get('revenues', {}).get('value', 0):,.0f}")
            print(f"      Net Income: ${income_statement.get('net_income_loss', {}).get('value', 0):,.0f}")
            
            print(f"\n   📊 Balance Sheet:")
            print(f"      Total Assets: ${balance_sheet.get('assets', {}).get('value', 0):,.0f}")
            print(f"      Current Assets: ${balance_sheet.get('current_assets', {}).get('value', 0):,.0f}")
            print(f"      Current Liabilities: ${balance_sheet.get('current_liabilities', {}).get('value', 0):,.0f}")
        else:
            print(f"   ⚠️ No financial results found")
            print(f"   Response: {data}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get previous close (for P/E calculation)
print(f"\n4️⃣ Testing Previous Close Price (NVDA):")
url = f"https://api.polygon.io/v2/aggs/ticker/NVDA/prev?adjusted=true&apiKey={POLYGON_API_KEY}"
try:
    response = requests.get(url, timeout=10)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response received")
        
        if 'results' in data and len(data['results']) > 0:
            result = data['results'][0]
            print(f"\n   💵 Price Info:")
            print(f"      Close: ${result.get('c', 0):.2f}")
            print(f"      Volume: {result.get('v', 0):,}")
            print(f"      Date: {result.get('t', 'N/A')}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETE")
print("=" * 60)
