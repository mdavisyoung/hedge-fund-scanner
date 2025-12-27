"""Test Alpaca API connection"""
import os
from dotenv import load_dotenv

load_dotenv()

# Show what keys we're using (masked for security)
api_key = os.getenv('ALPACA_API_KEY', '')
secret_key = os.getenv('ALPACA_SECRET_KEY', '')

print("=" * 60)
print("ALPACA API KEY TEST")
print("=" * 60)
print(f"API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else ''}")
print(f"Secret Key: {secret_key[:10]}...{secret_key[-5:] if len(secret_key) > 15 else ''}")
print(f"API Key Length: {len(api_key)}")
print(f"Secret Key Length: {len(secret_key)}")
print()

# Try to connect
try:
    from alpaca.trading.client import TradingClient

    print("Attempting to connect to Alpaca Paper Trading API...")
    print()

    client = TradingClient(api_key, secret_key, paper=True)
    account = client.get_account()

    print("SUCCESS! Connected to Alpaca Paper Trading")
    print("=" * 60)
    print(f"Account Status: {account.status}")
    print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print(f"Cash: ${float(account.cash):,.2f}")
    print(f"Buying Power: ${float(account.buying_power):,.2f}")
    print(f"Account Number: {account.account_number}")
    print("=" * 60)

except Exception as e:
    print("ERROR: Failed to connect to Alpaca")
    print("=" * 60)
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    print()
    print("TROUBLESHOOTING:")
    print("1. Verify you copied the PAPER TRADING keys (not live)")
    print("2. Make sure you copied both Key and Secret correctly")
    print("3. Try regenerating the keys at:")
    print("   https://app.alpaca.markets/paper/dashboard/settings/api")
    print("=" * 60)
