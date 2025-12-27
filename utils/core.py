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
            
            return {
                "ticker": ticker,
                "name": info.get("shortName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap", 0),
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
            print(f"Error: {e}")
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
Provide a clear, well-structured analysis in 3-4 paragraphs covering:
1. Stock analysis and recommendation (BUY/HOLD/AVOID)
2. Entry price, position sizing, and stop-loss levels
3. Risk management and exit conditions
4. Portfolio fit and diversification notes

Use clear numbers, proper calculations, and avoid confusing technical jargon."""
    
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

Provide a clear, professional investment strategy analysis covering:
1. Overall recommendation (BUY/HOLD/AVOID) with reasoning
2. Entry strategy and position sizing recommendations
3. Stop-loss and exit conditions
4. Risk assessment and portfolio fit

Use accurate calculations and clear, readable language. Avoid confusing numbers or incorrect math."""
        
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
