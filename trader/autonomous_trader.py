"""
Autonomous AI Trader
Analyzes stocks, makes trades, learns from results
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import requests
from dotenv import load_dotenv
from pathlib import Path
import yfinance as yf
import sys

# Add parent directory to path for utils import
sys.path.append(str(Path(__file__).parent.parent))
from utils.notifications import NotificationManager

# Load environment variables
try:
    load_dotenv()
except (UnicodeDecodeError, FileNotFoundError):
    # Handle encoding issues or missing .env file
    pass

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestQuoteRequest
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

        if not alpaca_key or not alpaca_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env file")

        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            alpaca_key,
            alpaca_secret,
            paper=paper_trading
        )

        self.data_client = StockHistoricalDataClient(alpaca_key, alpaca_secret)

        # Trading parameters
        self.max_position_size = 0.10  # Max 10% of portfolio per position
        self.max_loss_per_trade = 0.02  # Max 2% loss per trade
        self.confidence_threshold = 7  # Min confidence score (1-10)
        self.max_portfolio_heat = 0.06  # Max 6% total risk across all positions
        self.stop_loss_pct = 0.10  # 10% stop loss
        self.target_profit_pct = 0.15  # 15% target profit

        # Initialize storage
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.lessons_file = self.data_dir / "trade_lessons.json"

        # Load existing data
        self.trade_history = self._load_trade_history()
        self.lessons_learned = self._load_lessons()
        self.performance_metrics = self._calculate_performance_metrics()

        # Initialize notifications
        self.notifier = NotificationManager()

        # Trading state tracking
        self.trading_paused = False
        self.pause_reason = None
        self.ai_call_count_today = 0

    def is_market_open(self) -> bool:
        """Check if US stock market is currently open"""
        try:
            import pytz
        except ImportError:
            # Fallback if pytz not installed
            print("Warning: pytz not installed, using basic time check")
            now = datetime.now()
            if now.weekday() >= 5:  # Weekend
                return False
            return 9 <= now.hour < 16

        et_tz = pytz.timezone('America/New_York')
        now_et = datetime.now(et_tz)

        # Market closed on weekends
        if now_et.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False

        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now_et <= market_close

    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been reached.
        Returns True if limit reached (should pause trading)
        """
        # Get today's closed trades
        today = datetime.now().date()
        today_trades = [
            t for t in self.trade_history
            if t.get('status') == 'CLOSED' and
               datetime.fromisoformat(t.get('exit_timestamp', '2000-01-01')).date() == today
        ]

        if not today_trades:
            return False

        # Calculate total P/L for today
        daily_pnl_pct = sum(t.get('pnl_pct', 0) for t in today_trades)

        # If lost more than 2% today, pause trading
        if daily_pnl_pct <= -2.0:
            self.trading_paused = True
            self.pause_reason = f"Daily loss limit reached: {daily_pnl_pct:.2f}%"
            print(f"🛑 {self.pause_reason}")
            return True

        return False

    def get_account_info(self) -> Dict:
        """Get current account status"""
        account = self.trading_client.get_account()

        return {
            'cash': float(account.cash),
            'portfolio_value': float(account.portfolio_value),
            'buying_power': float(account.buying_power),
            'equity': float(account.equity),
            'paper_trading': self.paper_trading,
            'day_trading_buying_power': float(account.daytrading_buying_power),
            'pattern_day_trader': account.pattern_day_trader
        }

    def get_current_positions(self) -> List[Dict]:
        """Get all current open positions"""
        try:
            positions = self.trading_client.get_all_positions()

            result = []
            for pos in positions:
                current_price = float(pos.current_price)
                entry_price = float(pos.avg_entry_price)
                pnl = float(pos.unrealized_pl)
                pnl_pct = float(pos.unrealized_plpc) * 100

                result.append({
                    'ticker': pos.symbol,
                    'qty': int(pos.qty),
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pnl': pnl,
                    'unrealized_pnl_pct': pnl_pct,
                    'side': pos.side
                })

            return result
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []

    def get_portfolio_heat(self) -> float:
        """Calculate total portfolio risk across all positions"""
        positions = self.get_current_positions()
        account = self.get_account_info()
        portfolio_value = account['portfolio_value']

        if portfolio_value == 0:
            return 0.0

        total_risk = 0.0
        for pos in positions:
            # Risk per position = position_value * stop_loss_pct
            position_value = pos['market_value']
            risk = position_value * self.stop_loss_pct
            total_risk += risk

        return (total_risk / portfolio_value) if portfolio_value > 0 else 0.0

    def analyze_opportunity(self, stock_data: Dict) -> Dict:
        """
        Analyze a trading opportunity using AI
        Returns confidence score (1-10) and reasoning
        """
        if not self.xai_key:
            return {
                'confidence': 0,
                'reasoning': 'XAI API key not configured',
                'recommendation': 'SKIP'
            }

        ticker = stock_data.get('ticker')
        score = stock_data.get('score', {})

        # Get additional market data
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1mo")

            current_price = info.get('currentPrice', 0)
            volume = hist['Volume'].mean() if len(hist) > 0 else 0
            volatility = hist['Close'].pct_change().std() if len(hist) > 0 else 0

        except Exception as e:
            print(f"Error fetching additional data for {ticker}: {e}")
            current_price = stock_data.get('current_price', 0)
            volume = 0
            volatility = 0

        # Build AI prompt
        prompt = f"""Analyze this trading opportunity and provide a confidence score (1-10):

STOCK: {ticker}
Current Price: ${current_price:.2f}
Overall Score: {score.get('total_score', 0):.1f}/100

SCORE BREAKDOWN:
- Fundamental Score: {score.get('fundamental_score', 0):.1f}/40
- Technical Score: {score.get('technical_score', 0):.1f}/30
- Risk/Reward Score: {score.get('risk_reward_score', 0):.1f}/20
- Timing Score: {score.get('timing_score', 0):.1f}/10

ENTRY DETAILS:
- Entry Price: ${stock_data.get('entry_price', current_price):.2f}
- Stop Loss: ${stock_data.get('stop_loss', 0):.2f}
- Target: ${stock_data.get('target', 0):.2f}
- Risk/Reward Ratio: {stock_data.get('risk_reward_ratio', 0):.2f}

MARKET CONDITIONS:
- Average Volume: {volume:,.0f}
- Recent Volatility: {volatility:.4f}

LESSONS LEARNED FROM PAST TRADES:
{self._get_relevant_lessons(ticker)}

Based on this data, provide:
1. Confidence score (1-10, where 10 is highest confidence)
2. Key reasons to BUY or SKIP
3. Specific risks to watch
4. Recommended action: BUY, SKIP, or WAIT

Format your response as JSON:
{{
    "confidence": <1-10>,
    "recommendation": "BUY|SKIP|WAIT",
    "reasoning": "<brief explanation>",
    "risks": ["<risk1>", "<risk2>"],
    "key_factors": ["<factor1>", "<factor2>"]
}}"""

        try:
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.xai_key}"
                },
                json={
                    "model": "grok-3",
                    "messages": [
                        {"role": "system", "content": "You are an expert AI trader analyzing opportunities. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30
            )

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                # Try to parse JSON from response
                analysis = json.loads(content)
                # Increment AI call counter
                self.ai_call_count_today += 1
                return analysis
            else:
                # Still count failed API calls
                self.ai_call_count_today += 1
                return {
                    'confidence': 5,
                    'reasoning': f'API error: {response.status_code}',
                    'recommendation': 'SKIP'
                }

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            # Count API call even if it failed
            self.ai_call_count_today += 1
            return {
                'confidence': 5,
                'reasoning': f'Analysis error: {str(e)}',
                'recommendation': 'SKIP'
            }

    def should_trade(self, stock_data: Dict, analysis: Dict) -> bool:
        """
        Decide whether to execute trade based on:
        - AI confidence score
        - Portfolio heat
        - Risk management rules
        """
        # Check confidence threshold
        confidence = analysis.get('confidence', 0)
        if confidence < self.confidence_threshold:
            print(f"❌ Confidence {confidence} below threshold {self.confidence_threshold}")
            return False

        # Check recommendation
        recommendation = analysis.get('recommendation', 'SKIP')
        if recommendation != 'BUY':
            print(f"❌ Recommendation is {recommendation}, not BUY")
            return False

        # Check portfolio heat
        current_heat = self.get_portfolio_heat()
        if current_heat >= self.max_portfolio_heat:
            print(f"❌ Portfolio heat {current_heat:.2%} exceeds max {self.max_portfolio_heat:.2%}")
            return False

        # Check if we already have a position
        positions = self.get_current_positions()
        ticker = stock_data.get('ticker')
        if any(pos['ticker'] == ticker for pos in positions):
            print(f"❌ Already have position in {ticker}")
            return False

        print(f"✅ All checks passed for {ticker}")
        return True

    def execute_trade(self, stock_data: Dict, analysis: Dict) -> Optional[Dict]:
        """
        Execute a trade via Alpaca
        Returns trade confirmation or None if failed
        """
        ticker = stock_data.get('ticker')
        account = self.get_account_info()
        portfolio_value = account['portfolio_value']

        # Calculate position size
        max_loss_amount = portfolio_value * self.max_loss_per_trade
        entry_price = stock_data.get('entry_price', stock_data.get('current_price', 0))
        stop_loss_price = stock_data.get('stop_loss', entry_price * (1 - self.stop_loss_pct))
        stop_loss_distance = entry_price - stop_loss_price

        if stop_loss_distance <= 0:
            print(f"❌ Invalid stop loss for {ticker}")
            return None

        # Calculate shares based on risk
        shares = int(max_loss_amount / stop_loss_distance)
        position_value = shares * entry_price

        # Check position size doesn't exceed max
        if position_value > portfolio_value * self.max_position_size:
            shares = int((portfolio_value * self.max_position_size) / entry_price)
            position_value = shares * entry_price

        if shares <= 0:
            print(f"❌ Cannot calculate valid position size for {ticker}")
            return None

        print(f"\n📊 Trade Plan for {ticker}:")
        print(f"  Entry: ${entry_price:.2f}")
        print(f"  Stop Loss: ${stop_loss_price:.2f}")
        print(f"  Shares: {shares}")
        print(f"  Position Value: ${position_value:.2f}")
        print(f"  Max Risk: ${max_loss_amount:.2f}")

        try:
            # Create market order
            order_request = MarketOrderRequest(
                symbol=ticker,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(order_request)

            # Log trade
            trade_record = {
                'ticker': ticker,
                'action': 'BUY',
                'shares': shares,
                'entry_price': entry_price,
                'stop_loss': stop_loss_price,
                'target': stock_data.get('target', entry_price * (1 + self.target_profit_pct)),
                'position_value': position_value,
                'confidence': analysis.get('confidence'),
                'reasoning': analysis.get('reasoning'),
                'order_id': str(order.id),
                'timestamp': datetime.now().isoformat(),
                'status': 'OPEN'
            }

            self.trade_history.append(trade_record)
            self._save_trade_history()

            # Send notification
            self.notifier.notify_trade_executed(trade_record)

            print(f"✅ Order submitted for {ticker}: {order.id}")
            return trade_record

        except Exception as e:
            print(f"❌ Error executing trade for {ticker}: {e}")
            return None

    def monitor_positions(self) -> List[Dict]:
        """
        Monitor all open positions and check exit conditions
        Returns list of positions that need action
        """
        positions = self.get_current_positions()
        actions_needed = []

        for pos in positions:
            ticker = pos['ticker']
            current_price = pos['current_price']
            entry_price = pos['entry_price']
            pnl_pct = pos['unrealized_pnl_pct']

            # Find trade record
            trade_record = next(
                (t for t in self.trade_history if t['ticker'] == ticker and t['status'] == 'OPEN'),
                None
            )

            if not trade_record:
                continue

            stop_loss = trade_record.get('stop_loss', entry_price * (1 - self.stop_loss_pct))
            target = trade_record.get('target', entry_price * (1 + self.target_profit_pct))

            # Check stop loss
            if current_price <= stop_loss:
                actions_needed.append({
                    'ticker': ticker,
                    'action': 'SELL',
                    'reason': 'STOP_LOSS',
                    'current_price': current_price,
                    'pnl_pct': pnl_pct
                })

            # Check target
            elif current_price >= target:
                actions_needed.append({
                    'ticker': ticker,
                    'action': 'SELL',
                    'reason': 'TARGET_REACHED',
                    'current_price': current_price,
                    'pnl_pct': pnl_pct
                })

        return actions_needed

    def exit_position(self, ticker: str, reason: str) -> bool:
        """
        Exit a position (sell all shares)
        """
        try:
            # Get current position
            position = next(
                (p for p in self.get_current_positions() if p['ticker'] == ticker),
                None
            )

            if not position:
                print(f"❌ No position found for {ticker}")
                return False

            qty = position['qty']

            # Create sell order
            order_request = MarketOrderRequest(
                symbol=ticker,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(order_request)

            # Update trade record
            for trade in self.trade_history:
                if trade['ticker'] == ticker and trade['status'] == 'OPEN':
                    trade['status'] = 'CLOSED'
                    trade['exit_price'] = position['current_price']
                    trade['exit_reason'] = reason
                    trade['pnl'] = position['unrealized_pnl']
                    trade['pnl_pct'] = position['unrealized_pnl_pct']
                    trade['exit_timestamp'] = datetime.now().isoformat()
                    break

            self._save_trade_history()

            # Learn from trade
            self.learn_from_trade(ticker, reason, position['unrealized_pnl_pct'])

            # Send notification
            closed_trade = next(
                (t for t in self.trade_history if t['ticker'] == ticker and t['status'] == 'CLOSED'),
                None
            )
            if closed_trade:
                self.notifier.notify_position_closed(closed_trade, reason)

            print(f"✅ Exited {ticker}: {reason} - P/L: {position['unrealized_pnl_pct']:.2f}%")
            return True

        except Exception as e:
            print(f"❌ Error exiting {ticker}: {e}")
            return False

    def learn_from_trade(self, ticker: str, exit_reason: str, pnl_pct: float):
        """
        Extract lessons from completed trade
        """
        # Find trade record
        trade = next(
            (t for t in self.trade_history if t['ticker'] == ticker and t['status'] == 'CLOSED'),
            None
        )

        if not trade:
            return

        # Determine if trade was successful
        is_winning = pnl_pct > 0

        # Create lesson
        lesson = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'is_winning': is_winning,
            'pnl_pct': pnl_pct,
            'exit_reason': exit_reason,
            'confidence': trade.get('confidence'),
            'lesson': self._generate_lesson(trade, exit_reason, pnl_pct)
        }

        self.lessons_learned.append(lesson)
        self._save_lessons()

        # Update performance metrics
        self.performance_metrics = self._calculate_performance_metrics()

    def _generate_lesson(self, trade: Dict, exit_reason: str, pnl_pct: float) -> str:
        """Generate lesson text from trade"""
        ticker = trade['ticker']
        confidence = trade.get('confidence', 'N/A')

        if pnl_pct > 0:
            return f"✅ {ticker} (confidence {confidence}) hit target with +{pnl_pct:.2f}% gain. {exit_reason} was correct trigger."
        else:
            return f"❌ {ticker} (confidence {confidence}) stopped out with {pnl_pct:.2f}% loss. Review why {exit_reason} occurred."

    def _get_relevant_lessons(self, ticker: str) -> str:
        """Get lessons learned about similar trades"""
        if not self.lessons_learned:
            return "No previous lessons available."

        # Get last 5 lessons
        recent_lessons = self.lessons_learned[-5:]

        lessons_text = "\n".join([
            f"- {lesson['lesson']}" for lesson in recent_lessons
        ])

        return lessons_text or "No previous lessons available."

    def _load_trade_history(self) -> List[Dict]:
        """Load trade history from file"""
        history_file = self.data_dir / "trade_history.json"

        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    return data.get('trades', [])
            except Exception as e:
                print(f"Error loading trade history: {e}")

        return []

    def _save_trade_history(self):
        """Save trade history to file"""
        history_file = self.data_dir / "trade_history.json"

        try:
            with open(history_file, 'w') as f:
                json.dump({'trades': self.trade_history}, f, indent=2)
        except Exception as e:
            print(f"Error saving trade history: {e}")

    def _load_lessons(self) -> List[Dict]:
        """Load lessons from file"""
        if self.lessons_file.exists():
            try:
                with open(self.lessons_file, 'r') as f:
                    data = json.load(f)
                    return data.get('lessons', [])
            except Exception as e:
                print(f"Error loading lessons: {e}")

        return []

    def _save_lessons(self):
        """Save lessons to file"""
        try:
            with open(self.lessons_file, 'w') as f:
                json.dump({'lessons': self.lessons_learned}, f, indent=2)
        except Exception as e:
            print(f"Error saving lessons: {e}")

    def _calculate_performance_metrics(self) -> Dict:
        """Calculate performance metrics from trade history"""
        closed_trades = [t for t in self.trade_history if t.get('status') == 'CLOSED']

        if not closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'total_pnl_pct': 0.0
            }

        winning = [t for t in closed_trades if t.get('pnl_pct', 0) > 0]
        losing = [t for t in closed_trades if t.get('pnl_pct', 0) <= 0]

        total_trades = len(closed_trades)
        winning_trades = len(winning)
        losing_trades = len(losing)

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        avg_win = sum(t['pnl_pct'] for t in winning) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t['pnl_pct'] for t in losing) / losing_trades if losing_trades > 0 else 0

        total_wins = sum(t['pnl_pct'] for t in winning)
        total_losses = abs(sum(t['pnl_pct'] for t in losing))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        total_pnl_pct = sum(t.get('pnl_pct', 0) for t in closed_trades)

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl_pct': total_pnl_pct
        }
