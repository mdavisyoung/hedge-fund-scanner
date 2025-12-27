"""
Autonomous AI Trader
Analyzes stocks, makes trades, learns from results
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
except ImportError:
    print("Warning: alpaca-py not installed. Run: pip install alpaca-py")

class AutonomousTrader:
    """Fully autonomous AI-powered trader"""
    
    def __init__(self, paper_trading=True):
        self.paper_trading = paper_trading
        
        # Load API keys
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
        self.xai_key = os.getenv('XAI_API_KEY')
        
        # Initialize Alpaca
        self.trading_client = TradingClient(
            alpaca_key, 
            alpaca_secret, 
            paper=paper_trading
        )
        
        # Trading parameters
        self.max_position_size = 0.10
        self.max_loss_per_trade = 0.02
        self.confidence_threshold = 7
        
        self.trade_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0
        }
    
    def get_account_info(self) -> Dict:
        """Get current account status"""
        account = self.trading_client.get_account()
        
        return {
            'cash': float(account.cash),
            'portfolio_value': float(account.portfolio_value),
            'buying_power': float(account.buying_power),
            'equity': float(account.equity),
            'paper_trading': self.paper_trading
        }
