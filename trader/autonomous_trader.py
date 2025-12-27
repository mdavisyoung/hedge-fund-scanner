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
import time

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
        """Initialize trader"""
        self.paper_trading = paper_trading
        
        # Load API keys
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
        self.xai_key = os.getenv('XAI_API_KEY')
        
        if not alpaca_key or not alpaca_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")
        
        # Initialize Alpaca
        self.trading_client = TradingClient(
            alpaca_key, 
            alpaca_secret, 
            paper=paper_trading
        )
        
        # Trading parameters
        self.max_position_size = 0.10  # 10% of portfolio per position
        self.max_loss_per_trade = 0.02  # 2% max loss per trade
        self.confidence_threshold = 7  # Only trade if AI confidence >= 7/10
        
        # Learning
        self.trade_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0
        }
        
        # Load existing history
        self._load_trade_history()
    
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
    
    def analyze_opportunity(self, ticker: str, stock_data: Dict) -> Dict:
        """
        Use AI to analyze trade opportunity
        
        Returns: AI decision with reasoning
        """
        if not self.xai_key:
            return {
                'ticker': ticker,
                'action': 'SKIP',
                'reasoning': 'XAI API key not configured',
                'confidence': 0
            }
        
        current_price = stock_data.get('current_price', 0)
        account = self.get_account_info()
        
        prompt = f"""You are an autonomous hedge fund trader. Analyze this opportunity:

STOCK: {ticker}
Price: ${current_price:.2f}
P/E: {stock_data.get('pe_ratio', 0):.2f}
Revenue Growth: {stock_data.get('revenue_growth', 0):.1f}%
ROE: {stock_data.get('roe', 0):.1f}%
Beta: {stock_data.get('beta', 1.0):.2f}

ACCOUNT:
Cash: ${account['cash']:.2f}
Max Position: {self.max_position_size * 100}% of portfolio
Max Loss: {self.max_loss_per_trade * 100}%

Respond ONLY with this JSON (no other text):
{{
  "action": "BUY" or "SKIP",
  "reasoning": "2-3 sentence explanation",
  "confidence": 1-10,
  "entry_price": {current_price},
  "target_price": suggested target or null,
  "stop_loss": suggested stop or null,
  "position_size_pct": 1-{self.max_position_size*100}
}}

Only BUY if: strong fundamentals + confidence >= 7 + risk/reward >= 2:1"""
        
        try:
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.xai_key}"
                },
                json={
                    "model": "grok-beta",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Clean markdown
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                decision = json.loads(content)
                decision['ticker'] = ticker
                decision['analyzed_at'] = datetime.now().isoformat()
                
                return decision
            else:
                return {
                    'ticker': ticker,
                    'action': 'SKIP',
                    'reasoning': f'API error: {response.status_code}',
                    'confidence': 0
                }
                
        except Exception as e:
            return {
                'ticker': ticker,
                'action': 'SKIP',
                'reasoning': f'Error: {str(e)}',
                'confidence': 0
            }
    
    def execute_trade(self, decision: Dict) -> Optional[Dict]:
        """Execute trade based on AI decision"""
        
        if decision['action'] != 'BUY':
            print(f"⏭️  SKIP: {decision['ticker']} - {decision['reasoning']}")
            return None
        
        if decision['confidence'] < self.confidence_threshold:
            print(f"⏭️  SKIP: {decision['ticker']} - Low confidence ({decision['confidence']}/10)")
            return None
        
        ticker = decision['ticker']
        
        try:
            account = self.get_account_info()
            available_cash = account['cash']
            
            # Calculate position size
            position_value = available_cash * (decision['position_size_pct'] / 100)
            position_value = min(position_value, available_cash * self.max_position_size)
            
            entry_price = decision['entry_price']
            shares = int(position_value / entry_price)
            
            if shares < 1:
                print(f"⏭️  SKIP: {ticker} - Not enough cash for 1 share")
                return None
            
            # Place order
            order_request = MarketOrderRequest(
                symbol=ticker,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(order_request)
            
            trade_record = {
                'trade_id': len(self.trade_history) + 1,
                'ticker': ticker,
                'action': 'BUY',
                'shares': shares,
                'entry_price': entry_price,
                'stop_loss': decision['stop_loss'],
                'target': decision['target_price'],
                'position_value': shares * entry_price,
                'confidence': decision['confidence'],
                'reasoning': decision['reasoning'],
                'order_id': str(order.id),
                'executed_at': datetime.now().isoformat(),
                'status': 'OPEN',
                'outcome': None,
                'profit_loss': 0.0
            }
            
            self.trade_history.append(trade_record)
            self._save_trade_history()
            
            print(f"\n✅ TRADE EXECUTED:")
            print(f"   {ticker}: BUY {shares} shares @ ${entry_price:.2f}")
            print(f"   Total: ${shares * entry_price:.2f}")
            print(f"   Stop: ${decision['stop_loss']:.2f} | Target: ${decision['target_price']:.2f}")
            print(f"   Confidence: {decision['confidence']}/10")
            print(f"   Why: {decision['reasoning']}\n")
            
            return trade_record
            
        except Exception as e:
            print(f"❌ Error executing: {e}")
            return None
    
    def monitor_positions(self):
        """Monitor and manage open positions"""
        try:
            positions = self.trading_client.get_all_positions()
            
            for position in positions:
                ticker = position.symbol
                current_price = float(position.current_price)
                
                # Find trade in history
                open_trade = next(
                    (t for t in self.trade_history 
                     if t['ticker'] == ticker and t['status'] == 'OPEN'),
                    None
                )
                
                if not open_trade:
                    continue
                
                # Check stop loss
                if current_price <= open_trade['stop_loss']:
                    self._close_position(ticker, current_price, 'STOP_LOSS', open_trade)
                
                # Check target
                elif current_price >= open_trade['target']:
                    self._close_position(ticker, current_price, 'TARGET', open_trade)
                    
        except Exception as e:
            print(f"Error monitoring: {e}")
    
    def _close_position(self, ticker: str, exit_price: float, reason: str, trade: Dict):
        """Close a position"""
        try:
            self.trading_client.close_position(ticker)
            
            trade['status'] = 'CLOSED'
            trade['exit_price'] = exit_price
            trade['exit_reason'] = reason
            trade['closed_at'] = datetime.now().isoformat()
            
            profit_pct = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
            profit_amount = (exit_price - trade['entry_price']) * trade['shares']
            
            trade['profit_loss'] = profit_amount
            trade['profit_pct'] = profit_pct
            trade['outcome'] = 'WIN' if profit_amount > 0 else 'LOSS'
            
            self._update_performance(trade)
            self._learn_from_trade(trade)
            
            print(f"\n🔔 CLOSED: {ticker}")
            print(f"   Reason: {reason}")
            print(f"   Entry: ${trade['entry_price']:.2f} → Exit: ${exit_price:.2f}")
            print(f"   P/L: ${profit_amount:.2f} ({profit_pct:+.2f}%)")
            print(f"   Result: {trade['outcome']}\n")
            
            self._save_trade_history()
            
        except Exception as e:
            print(f"Error closing: {e}")
    
    def _update_performance(self, trade: Dict):
        """Update metrics"""
        self.performance_metrics['total_trades'] += 1
        
        if trade['outcome'] == 'WIN':
            self.performance_metrics['winning_trades'] += 1
        else:
            self.performance_metrics['losing_trades'] += 1
        
        self.performance_metrics['total_profit'] += trade['profit_loss']
        
        if self.performance_metrics['total_trades'] > 0:
            self.performance_metrics['win_rate'] = (
                self.performance_metrics['winning_trades'] / 
                self.performance_metrics['total_trades'] * 100
            )
    
    def _learn_from_trade(self, trade: Dict):
        """AI analyzes what worked/didn't"""
        if not self.xai_key:
            return
        
        prompt = f"""Analyze this trade and extract lessons:

Ticker: {trade['ticker']}
Entry: ${trade['entry_price']:.2f} → Exit: ${trade['exit_price']:.2f}
Result: {trade['outcome']} ({trade['profit_pct']:+.2f}%)
Why entered: {trade['reasoning']}
Why exited: {trade['exit_reason']}

Give 2-3 sentence lesson for future trades."""
        
        try:
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.xai_key}"
                },
                json={
                    "model": "grok-beta",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5,
                    "max_tokens": 200
                },
                timeout=30
            )
            
            if response.status_code == 200:
                lesson = response.json()["choices"][0]["message"]["content"]
                trade['lesson_learned'] = lesson
                print(f"📚 LESSON: {lesson}\n")
                
        except Exception as e:
            print(f"Learning error: {e}")
    
    def _save_trade_history(self):
        """Save to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/trade_history_auto.json', 'w') as f:
                json.dump({
                    'trades': self.trade_history,
                    'performance': self.performance_metrics,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Save error: {e}")
    
    def _load_trade_history(self):
        """Load from file"""
        try:
            with open('data/trade_history_auto.json', 'r') as f:
                data = json.load(f)
                self.trade_history = data.get('trades', [])
                self.performance_metrics = data.get('performance', self.performance_metrics)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Load error: {e}")
    
    def get_status_report(self) -> str:
        """Generate status report"""
        account = self.get_account_info()
        
        report = f"""
╔══════════════════════════════════════════════╗
║     AUTONOMOUS TRADER STATUS                 ║
╚══════════════════════════════════════════════╝

💰 ACCOUNT:
   Value: ${account['portfolio_value']:.2f}
   Cash: ${account['cash']:.2f}
   Mode: {'📄 PAPER' if self.paper_trading else '💵 REAL'}

📊 PERFORMANCE:
   Trades: {self.performance_metrics['total_trades']}
   Win Rate: {self.performance_metrics['win_rate']:.1f}%
   Total Profit: ${self.performance_metrics['total_profit']:.2f}

🔥 POSITIONS:
"""
        
        try:
            positions = self.trading_client.get_all_positions()
            if positions:
                for pos in positions:
                    pnl = float(pos.unrealized_plpc) * 100
                    report += f"   {pos.symbol}: {pos.qty} @ ${pos.avg_entry_price} ({pnl:+.2f}%)\n"
            else:
                report += "   None\n"
        except:
            report += "   Error loading\n"
        
        return report
