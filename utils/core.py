import yfinance as yf
import pandas as pd
import requests
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class StockAnalyzer:
    def __init__(self):
        self.cache = {}
    
    def get_stock_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            return df
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None
    
    def get_fundamentals(self, ticker: str) -> Dict:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get exchange information
            exchange = (info.get("exchange", "") or "").upper()
            quote_type = (info.get("quoteType", "") or "").upper()
            market = (info.get("market", "") or "").upper()
            market_cap = info.get("marketCap") or info.get("market_cap", 0)
            avg_volume = info.get("averageVolume") or info.get("average_volume", 0)
            
            # Determine if it's a strong market
            strong_exchanges = ["NYQ", "NYS", "NMS", "NCM", "NGM", "ASE"]  # NYSE, NASDAQ, AMEX
            weak_markets = ["OTC", "OTCQB", "OTCQX", "PINK", "GREY"]
            
            is_strong_market = (
                exchange in strong_exchanges or
                (quote_type == "EQUITY" and 
                 not any(weak in exchange for weak in weak_markets) and
                 "PINK" not in exchange and
                 exchange != "")
            )
            
            return {
                "ticker": ticker,
                "name": info.get("shortName", ticker),
                "exchange": exchange,
                "quote_type": quote_type,
                "market": market,
                "market_cap": market_cap,
                "average_volume": avg_volume,
                "is_strong_market": is_strong_market,
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "price_to_book": info.get("priceToBook", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "roe": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0,
                "current_ratio": info.get("currentRatio", 0),
                "quick_ratio": info.get("quickRatio", 0),
                "revenue_growth": info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else 0,
                "earnings_growth": info.get("earningsGrowth", 0) * 100 if info.get("earningsGrowth") else 0,
                "profit_margin": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0,
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "beta": info.get("beta", 1.0),
                "current_price": info.get("currentPrice", 0),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
            }
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return {}
    
    def classify_stock_type(self, fundamentals: Dict) -> str:
        sector = fundamentals.get("sector", "").lower()
        revenue_growth = fundamentals.get("revenue_growth", 0)
        pe_ratio = fundamentals.get("pe_ratio", 0)
        
        if "financ" in sector or "bank" in sector:
            return "Financial"
        elif revenue_growth > 15 and pe_ratio > 25:
            return "Growth"
        elif pe_ratio < 15 and pe_ratio > 0:
            return "Value"
        else:
            return "Cyclical"
    
    def evaluate_stock(self, ticker: str) -> Dict:
        fundamentals = self.get_fundamentals(ticker)
        if not fundamentals:
            return {"error": "Could not fetch data"}
        
        stock_type = self.classify_stock_type(fundamentals)
        
        thresholds = {
            "Growth": {"revenue_growth_min": 15, "pe_max": 50, "roe_min": 15},
            "Value": {"pe_max": 15, "roe_min": 15, "debt_to_equity_max": 1.0},
            "Financial": {"roe_min": 10, "pe_max": 12},
            "Cyclical": {"pe_max": 20, "current_ratio_min": 1.5}
        }
        
        criteria = thresholds.get(stock_type, thresholds["Cyclical"])
        scores = {}
        
        if stock_type == "Growth":
            scores["revenue_growth"] = fundamentals.get("revenue_growth", 0) >= criteria["revenue_growth_min"]
            scores["pe_ratio"] = 0 < fundamentals.get("pe_ratio", 0) <= criteria["pe_max"]
            scores["roe"] = fundamentals.get("roe", 0) >= criteria["roe_min"]
        elif stock_type == "Value":
            scores["pe_ratio"] = 0 < fundamentals.get("pe_ratio", 0) <= criteria["pe_max"]
            scores["roe"] = fundamentals.get("roe", 0) >= criteria["roe_min"]
            scores["debt_to_equity"] = fundamentals.get("debt_to_equity", 999) <= criteria["debt_to_equity_max"]
        elif stock_type == "Financial":
            scores["roe"] = fundamentals.get("roe", 0) >= criteria["roe_min"]
            scores["pe_ratio"] = 0 < fundamentals.get("pe_ratio", 0) <= criteria["pe_max"]
        else:
            scores["pe_ratio"] = 0 < fundamentals.get("pe_ratio", 0) <= criteria["pe_max"]
            scores["current_ratio"] = fundamentals.get("current_ratio", 0) >= criteria["current_ratio_min"]
        
        passed = sum(scores.values())
        total = len(scores)
        
        return {
            "fundamentals": fundamentals,
            "stock_type": stock_type,
            "criteria": criteria,
            "scores": scores,
            "passed": passed,
            "total": total,
            "rating": "BUY" if passed >= total * 0.7 else "HOLD" if passed >= total * 0.4 else "AVOID"
        }


class XAIStrategyGenerator:
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.base_url = "https://api.x.ai/v1/chat/completions"
        
        self.system_prompt = """You are an expert hedge fund strategist combining Warren Buffett (value investing), Ray Dalio (risk parity), and Jim Simons (quantitative analysis).

ANALYSIS FRAMEWORK:
1. Stock Classification:
   - Growth stocks: Revenue growth >15%, P/E can be higher (<50 acceptable)
   - Value stocks: P/E <15, ROE >15%, strong fundamentals
   - Financial stocks: ROE >10%, P/E <12, regulatory capital ratios
   - Cyclical stocks: Current ratio >1.5, reasonable P/E

2. Risk Management Rules:
   - Maximum 2% portfolio loss per trade (set stop-loss accordingly)
   - Dollar-cost averaging for monthly contributions
   - Diversification across stock types
   - Position sizing: Calculate based on max loss % and stop-loss distance

3. Strategy Approaches:
   - Buffett: Focus on intrinsic value, margin of safety, long-term holds
   - Dalio: Balance risk across asset types, consider macro conditions
   - Simons: Use quantitative metrics, identify statistical patterns

4. Position Sizing Calculation:
   - Max loss amount = Portfolio value × (max_loss_per_trade / 100)
   - Stop-loss distance = Stock price × (stop_loss_pct / 100)
   - Shares = Max loss amount / Stop-loss distance
   - Position value = Shares × Stock price

OUTPUT FORMAT:
Provide a CLEAR, STRUCTURED analysis with these sections:

**RECOMMENDATION:** [BUY/HOLD/AVOID] - [One sentence summary]

**ANALYSIS:**
- Stock Type: [Growth/Value/Financial/Cyclical]
- Key Strengths: [2-3 bullet points]
- Key Concerns: [1-2 bullet points]

**POSITION DETAILS:**
- Entry Price: $[X.XX]
- Recommended Shares: [X] shares
- Position Value: $[XXX.XX]
- Stop-Loss: $[X.XX] (-[X]%)
- Target Price: $[X.XX] (+[X]%)
- Maximum Risk: $[XX.XX] ([X]% of portfolio)

**RISK MANAGEMENT:**
- Exit Conditions: [When to sell]
- Portfolio Fit: [Diversification notes]

Use clear numbers, proper calculations, and simple language. Format with markdown headers and bullet points for easy reading."""
    
    def generate_strategy(self, stock_data: Dict, user_prefs: Dict) -> str:
        if not self.api_key:
            return "⚠️ XAI API key not configured. Add to .env file."
        
        # Extract data from evaluation object structure
        fundamentals = stock_data.get('fundamentals', {})
        ticker = fundamentals.get('ticker', 'Unknown')
        stock_name = fundamentals.get('name', ticker)
        stock_type = stock_data.get('stock_type', 'Unknown')
        current_price = fundamentals.get('current_price', 0)
        pe_ratio = fundamentals.get('pe_ratio', 0)
        revenue_growth = fundamentals.get('revenue_growth', 0)
        roe = fundamentals.get('roe', 0)
        debt_to_equity = fundamentals.get('debt_to_equity', 0)
        current_ratio = fundamentals.get('current_ratio', 0)
        beta = fundamentals.get('beta', 1.0)
        market_cap = fundamentals.get('market_cap', 0)
        
        monthly_budget = user_prefs.get('monthly_contribution', 100)
        risk_tolerance = user_prefs.get('risk_tolerance', 5)
        max_loss_pct = user_prefs.get('max_loss_per_trade', 2)
        
        # Calculate position sizing for context
        # Assume current portfolio value (simplified - could use monthly budget × months)
        portfolio_value = monthly_budget * 12  # Rough estimate
        stop_loss_pct = 10.0  # Default 10% stop-loss
        max_loss_amount = portfolio_value * (max_loss_pct / 100)
        stop_loss_distance = current_price * (stop_loss_pct / 100)
        shares = int(max_loss_amount / stop_loss_distance) if stop_loss_distance > 0 else 0
        position_value = shares * current_price if shares > 0 else 0
        
        prompt = f"""Analyze this stock and provide an investment strategy:

STOCK INFORMATION:
- Ticker: {ticker}
- Company: {stock_name}
- Stock Type: {stock_type}
- Current Price: ${current_price:.2f}
- Market Cap: ${market_cap:,.0f} (if available)

KEY METRICS:
- P/E Ratio: {pe_ratio:.2f}
- Revenue Growth: {revenue_growth:.2f}%
- Return on Equity (ROE): {roe:.2f}%
- Debt-to-Equity: {debt_to_equity:.2f}
- Current Ratio: {current_ratio:.2f}
- Beta: {beta:.2f}

INVESTOR PROFILE:
- Monthly Investment Budget: ${monthly_budget}
- Risk Tolerance: {risk_tolerance}/10 (1=Conservative, 10=Aggressive)
- Maximum Loss Per Trade: {max_loss_pct}% of portfolio

POSITION SIZING CALCULATION (for reference):
- Estimated Portfolio Value: ${portfolio_value:,.0f}
- Maximum Loss Amount: ${max_loss_amount:.2f} (2% of portfolio)
- Stop-Loss Distance: ${stop_loss_distance:.2f} (10% below entry)
- Recommended Shares: {shares} shares
- Position Value: ${position_value:.2f}

Provide a CLEAR, STRUCTURED analysis using the format specified in the system prompt.

IMPORTANT: 
- Use the exact format with **RECOMMENDATION**, **ANALYSIS**, **POSITION DETAILS**, and **RISK MANAGEMENT** sections
- Show ALL calculations clearly
- Use markdown formatting (headers, bullet points)
- Keep language simple and professional
- Double-check all math before outputting"""
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "grok-3",
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"⚠️ API Error: {response.status_code}"
        except Exception as e:
            return f"⚠️ Error: {str(e)}"


class PortfolioSimulator:
    def simulate_monthly_investment(
        self, 
        monthly_amount: float,
        annual_return: float,
        years: int,
        volatility: float = 0.15
    ) -> Tuple[List[float], List[float]]:
        import numpy as np
        
        months = years * 12
        monthly_return = annual_return / 12
        monthly_vol = volatility / np.sqrt(12)
        
        balances = [0]
        contributions = [0]
        
        for month in range(1, months + 1):
            contributions.append(contributions[-1] + monthly_amount)
            random_return = np.random.normal(monthly_return, monthly_vol)
            new_balance = (balances[-1] + monthly_amount) * (1 + random_return)
            balances.append(max(0, new_balance))
        
        return balances, contributions
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        stock_price: float,
        max_loss_pct: float = 2.0,
        stop_loss_pct: float = 10.0
    ) -> Dict:
        max_loss = portfolio_value * (max_loss_pct / 100)
        shares = int(max_loss / (stock_price * (stop_loss_pct / 100)))
        position_value = shares * stock_price
        
        return {
            "shares": shares,
            "position_value": position_value,
            "stop_loss_price": stock_price * (1 - stop_loss_pct / 100),
            "max_loss": max_loss,
            "position_pct": (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
        }


class AIPortfolioManager:
    """
    Automated portfolio manager that starts with $100 and adds $100/month.
    Uses AI to make trading decisions and automatically manage positions.
    """
    
    def __init__(self, storage_manager=None):
        self.storage = storage_manager
        self.analyzer = StockAnalyzer()
        self.strategy_gen = XAIStrategyGenerator()
        self.simulator = PortfolioSimulator()
        
    def initialize_portfolio(self, initial_cash: float = 100.0, monthly_contribution: float = 100.0):
        """Initialize a new portfolio"""
        from datetime import datetime
        
        portfolio = {
            "initial_cash": initial_cash,
            "monthly_contribution": monthly_contribution,
            "current_cash": initial_cash,
            "total_contributed": initial_cash,
            "positions": {},  # {ticker: {shares, entry_price, stop_loss, target, entry_date}}
            "trade_history": [],
            "created_at": datetime.now().isoformat(),
            "last_contribution_date": datetime.now().isoformat(),
            "settings": {
                "max_loss_per_trade": 2.0,  # 2% max loss per trade
                "risk_tolerance": 5,  # 1-10 scale
                "max_position_size_pct": 20.0,  # Max 20% in single position
                "min_stock_score": 80,  # Minimum score to enter trade
            }
        }
        return portfolio
    
    def get_portfolio_value(self, portfolio: Dict) -> float:
        """Calculate total portfolio value (cash + positions)"""
        total = portfolio.get("current_cash", 0)
        
        for ticker, position in portfolio.get("positions", {}).items():
            try:
                current_price = self.analyzer.get_fundamentals(ticker).get("current_price", 0)
                shares = position.get("shares", 0)
                total += current_price * shares
            except:
                # If we can't get price, use entry price
                total += position.get("entry_price", 0) * position.get("shares", 0)
        
        return total
    
    def add_monthly_contribution(self, portfolio: Dict) -> Dict:
        """Add monthly contribution if it's been a month since last contribution"""
        from datetime import datetime, timedelta
        
        last_contrib = datetime.fromisoformat(portfolio.get("last_contribution_date", datetime.now().isoformat()))
        now = datetime.now()
        
        # Check if a month has passed (approximately 30 days)
        if (now - last_contrib).days >= 30:
            monthly_amount = portfolio.get("monthly_contribution", 100.0)
            portfolio["current_cash"] += monthly_amount
            portfolio["total_contributed"] += monthly_amount
            portfolio["last_contribution_date"] = now.isoformat()
        
        return portfolio
    
    def calculate_position_size(self, portfolio: Dict, ticker: str, stock_price: float, 
                                 stop_loss_pct: float = 10.0) -> Dict:
        """Calculate position size based on risk management rules"""
        portfolio_value = self.get_portfolio_value(portfolio)
        max_loss_pct = portfolio.get("settings", {}).get("max_loss_per_trade", 2.0)
        max_position_pct = portfolio.get("settings", {}).get("max_position_size_pct", 20.0)
        
        # Calculate based on max loss
        max_loss_amount = portfolio_value * (max_loss_pct / 100)
        stop_loss_distance = stock_price * (stop_loss_pct / 100)
        
        if stop_loss_distance <= 0:
            return {"shares": 0, "position_value": 0, "max_loss": 0}
        
        shares_by_risk = int(max_loss_amount / stop_loss_distance)
        
        # Calculate based on max position size
        max_position_value = portfolio_value * (max_position_pct / 100)
        shares_by_size = int(max_position_value / stock_price) if stock_price > 0 else 0
        
        # Use the smaller of the two
        shares = min(shares_by_risk, shares_by_size)
        position_value = shares * stock_price
        
        return {
            "shares": shares,
            "position_value": position_value,
            "stop_loss_price": stock_price * (1 - stop_loss_pct / 100),
            "max_loss": max_loss_amount,
            "position_pct": (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
        }
    
    def evaluate_trade_opportunity(self, portfolio: Dict, ticker: str) -> Dict:
        """Evaluate if a stock is a good trade opportunity"""
        evaluation = self.analyzer.evaluate_stock(ticker)
        
        if "error" in evaluation:
            return {"should_trade": False, "reason": evaluation["error"]}
        
        fundamentals = evaluation["fundamentals"]
        stock_price = fundamentals.get("current_price", 0)
        min_score = portfolio.get("settings", {}).get("min_stock_score", 80)
        
        # Get score from scanner if available, otherwise use evaluation
        # For now, use a simple scoring based on criteria passed
        criteria_passed = evaluation.get("passed", 0)
        criteria_total = evaluation.get("total", 1)
        score = (criteria_passed / criteria_total) * 100 if criteria_total > 0 else 0
        
        # Check if we have enough cash
        position_info = self.calculate_position_size(portfolio, ticker, stock_price)
        required_cash = position_info["position_value"]
        available_cash = portfolio.get("current_cash", 0)
        
        # Check if already holding
        existing_position = portfolio.get("positions", {}).get(ticker)
        
        result = {
            "should_trade": False,
            "ticker": ticker,
            "evaluation": evaluation,
            "position_info": position_info,
            "score": score,
            "reason": ""
        }
        
        if existing_position:
            result["reason"] = f"Already holding {ticker}"
            return result
        
        if score < min_score:
            result["reason"] = f"Score {score:.1f} below minimum {min_score}"
            return result
        
        if required_cash > available_cash:
            result["reason"] = f"Insufficient cash. Need ${required_cash:.2f}, have ${available_cash:.2f}"
            return result
        
        if position_info["shares"] == 0:
            result["reason"] = "Position size calculation resulted in 0 shares"
            return result
        
        result["should_trade"] = True
        result["reason"] = "Meets all criteria"
        return result
    
    def execute_buy(self, portfolio: Dict, ticker: str, evaluation_result: Dict) -> Dict:
        """Execute a buy order"""
        from datetime import datetime
        
        position_info = evaluation_result["position_info"]
        evaluation = evaluation_result["evaluation"]
        fundamentals = evaluation["fundamentals"]
        
        shares = position_info["shares"]
        entry_price = fundamentals.get("current_price", 0)
        cost = shares * entry_price
        
        if cost > portfolio.get("current_cash", 0):
            return {"success": False, "error": "Insufficient cash"}
        
        # Create position
        position = {
            "shares": shares,
            "entry_price": entry_price,
            "stop_loss": position_info["stop_loss_price"],
            "target": entry_price * 1.20,  # 20% target
            "entry_date": datetime.now().isoformat(),
            "stock_type": evaluation.get("stock_type", "Unknown"),
            "score": evaluation_result["score"]
        }
        
        portfolio["positions"][ticker] = position
        portfolio["current_cash"] -= cost
        
        # Add to trade history
        trade = {
            "ticker": ticker,
            "action": "BUY",
            "shares": shares,
            "price": entry_price,
            "total_cost": cost,
            "timestamp": datetime.now().isoformat()
        }
        portfolio["trade_history"].append(trade)
        
        return {"success": True, "position": position, "cost": cost}
    
    def check_exit_conditions(self, portfolio: Dict, ticker: str) -> Dict:
        """Check if a position should be exited"""
        position = portfolio.get("positions", {}).get(ticker)
        if not position:
            return {"should_exit": False}
        
        try:
            fundamentals = self.analyzer.get_fundamentals(ticker)
            current_price = fundamentals.get("current_price", 0)
            entry_price = position.get("entry_price", 0)
            stop_loss = position.get("stop_loss", 0)
            target = position.get("target", 0)
            
            # Check stop loss
            if current_price <= stop_loss:
                return {
                    "should_exit": True,
                    "reason": "Stop loss triggered",
                    "exit_price": current_price,
                    "pnl": (current_price - entry_price) * position.get("shares", 0)
                }
            
            # Check target (take partial profit at 20%, full exit if drops back)
            if current_price >= target:
                return {
                    "should_exit": True,
                    "reason": "Target reached",
                    "exit_price": current_price,
                    "pnl": (current_price - entry_price) * position.get("shares", 0)
                }
            
            # Check if fundamentals deteriorated (simplified - could be enhanced)
            evaluation = self.analyzer.evaluate_stock(ticker)
            if "error" not in evaluation:
                criteria_passed = evaluation.get("passed", 0)
                criteria_total = evaluation.get("total", 1)
                current_score = (criteria_passed / criteria_total) * 100 if criteria_total > 0 else 0
                original_score = position.get("score", 80)
                
                if current_score < original_score * 0.7:  # Score dropped 30%+
                    return {
                        "should_exit": True,
                        "reason": "Fundamentals deteriorated",
                        "exit_price": current_price,
                        "pnl": (current_price - entry_price) * position.get("shares", 0)
                    }
            
        except Exception as e:
            return {"should_exit": False, "error": str(e)}
        
        return {"should_exit": False}
    
    def execute_sell(self, portfolio: Dict, ticker: str, exit_info: Dict) -> Dict:
        """Execute a sell order"""
        from datetime import datetime
        
        position = portfolio.get("positions", {}).get(ticker)
        if not position:
            return {"success": False, "error": "Position not found"}
        
        exit_price = exit_info.get("exit_price", 0)
        shares = position.get("shares", 0)
        proceeds = exit_price * shares
        
        # Remove position
        del portfolio["positions"][ticker]
        portfolio["current_cash"] += proceeds
        
        # Add to trade history
        entry_price = position.get("entry_price", 0)
        pnl = exit_info.get("pnl", (exit_price - entry_price) * shares)
        
        trade = {
            "ticker": ticker,
            "action": "SELL",
            "shares": shares,
            "price": exit_price,
            "proceeds": proceeds,
            "pnl": pnl,
            "reason": exit_info.get("reason", "Manual exit"),
            "timestamp": datetime.now().isoformat()
        }
        portfolio["trade_history"].append(trade)
        
        return {"success": True, "proceeds": proceeds, "pnl": pnl}
    
    def auto_manage_portfolio(self, portfolio: Dict, available_stocks: List[str] = None) -> Tuple[Dict, List[str]]:
        """
        Automatically manage portfolio: check exits, add contributions, evaluate new entries
        Returns: (updated_portfolio, activity_log)
        """
        from datetime import datetime
        
        activity_log = []
        
        # Add monthly contribution
        old_contrib = portfolio.get("total_contributed", 0)
        portfolio = self.add_monthly_contribution(portfolio)
        new_contrib = portfolio.get("total_contributed", 0)
        if new_contrib > old_contrib:
            amount = new_contrib - old_contrib
            activity_log.append(f"✅ Added monthly contribution: ${amount:.2f}")
        
        # Check exit conditions for existing positions
        positions_to_exit = []
        for ticker in list(portfolio.get("positions", {}).keys()):
            activity_log.append(f"🔍 Checking exit conditions for {ticker}...")
            exit_check = self.check_exit_conditions(portfolio, ticker)
            if exit_check.get("should_exit", False):
                positions_to_exit.append((ticker, exit_check))
                activity_log.append(f"⚠️ {ticker}: {exit_check.get('reason', 'Exit triggered')}")
        
        # Execute exits
        for ticker, exit_info in positions_to_exit:
            sell_result = self.execute_sell(portfolio, ticker, exit_info)
            if sell_result.get("success", False):
                pnl = exit_info.get("pnl", 0)
                pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"${pnl:.2f}"
                activity_log.append(f"💰 SOLD {ticker}: {exit_info.get('reason', 'Exit')} | P&L: {pnl_str}")
            else:
                activity_log.append(f"❌ Failed to sell {ticker}: {sell_result.get('error', 'Unknown error')}")
        
        # Evaluate new opportunities if we have cash and available stocks
        if available_stocks and portfolio.get("current_cash", 0) > 10:
            activity_log.append(f"🔎 Evaluating {len(available_stocks[:5])} opportunities...")
            for ticker in available_stocks[:5]:  # Check top 5 opportunities
                if ticker in portfolio.get("positions", {}):
                    continue
                
                activity_log.append(f"📊 Analyzing {ticker}...")
                eval_result = self.evaluate_trade_opportunity(portfolio, ticker)
                
                if eval_result.get("should_trade", False):
                    buy_result = self.execute_buy(portfolio, ticker, eval_result)
                    if buy_result.get("success", False):
                        shares = eval_result["position_info"]["shares"]
                        price = eval_result["evaluation"]["fundamentals"]["current_price"]
                        cost = buy_result.get("cost", 0)
                        activity_log.append(f"🟢 BOUGHT {shares} shares of {ticker} @ ${price:.2f} | Cost: ${cost:.2f}")
                        break  # Only enter one position at a time
                    else:
                        activity_log.append(f"❌ Failed to buy {ticker}: {buy_result.get('error', 'Unknown error')}")
                else:
                    reason = eval_result.get("reason", "Does not meet criteria")
                    activity_log.append(f"⏸️ Skipped {ticker}: {reason}")
        elif not available_stocks:
            activity_log.append("ℹ️ No hot stocks available from scanner")
        elif portfolio.get("current_cash", 0) <= 10:
            activity_log.append(f"ℹ️ Insufficient cash (${portfolio.get('current_cash', 0):.2f}) for new positions")
        
        if not activity_log:
            activity_log.append("ℹ️ No actions taken - portfolio is up to date")
        
        portfolio["last_managed"] = datetime.now().isoformat()
        return portfolio, activity_log
