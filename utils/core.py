import pandas as pd
import requests
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Polygon fetcher
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from polygon_fetcher import PolygonFetcher

class StockAnalyzer:
    def __init__(self, use_polygon: bool = True):
        self.cache = {}
        self.use_polygon = use_polygon
        self.polygon = PolygonFetcher() if use_polygon else None
        
    def get_stock_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Get historical stock data using ONLY Polygon API
        """
        if not self.use_polygon or not self.polygon:
            print(f"[Error] Polygon API not configured")
            return None
            
        try:
            # Convert period to days
            days_map = {
                "1mo": 30, "3mo": 90, "6mo": 180,
                "1y": 365, "2y": 730, "5y": 1825, "max": 3650
            }
            days = days_map.get(period, 365)

            history = self.polygon.get_price_history(ticker, days=days)
            if history and history.get('bars'):
                # Convert to DataFrame
                bars = history['bars']
                df = pd.DataFrame(bars)
                df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('Date', inplace=True)
                df = df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                print(f"[Polygon History] {ticker}: Loaded {len(bars)} bars for period {period}")
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            else:
                print(f"[Warning] No price history found for {ticker}")
                return None
        except Exception as e:
            print(f"[Error] Polygon history fetch failed for {ticker}: {e}")
            return None
            
    def get_fundamentals(self, ticker: str) -> Dict:
        """
        Get stock fundamentals using ONLY Polygon API
        Cleaner, faster, more reliable - no more Yahoo Finance!
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict containing all fundamental metrics
        """
        # Initialize result with defaults
        result = {
            "ticker": ticker,
            "name": ticker,
            "exchange": "",
            "quote_type": "EQUITY",
            "market": "",
            "market_cap": 0,
            "average_volume": 0,
            "is_strong_market": False,
            "current_price": 0,
            "sector": "Unknown",
            "industry": "Unknown",
            "pe_ratio": 0,
            "forward_pe": 0,
            "price_to_book": 0,
            "debt_to_equity": 0,
            "roe": 0,
            "current_ratio": 0,
            "quick_ratio": 0,
            "revenue_growth": 0,
            "earnings_growth": 0,
            "profit_margin": 0,
            "dividend_yield": 0,
            "beta": 1.0,
            "fifty_two_week_high": 0,
            "fifty_two_week_low": 0,
        }

        if not self.use_polygon or not self.polygon:
            print(f"[Error] Polygon API not configured for {ticker}")
            return result

        try:
            # Step 1: Get current quote (price, volume)
            quote = self.polygon.get_stock_quote(ticker)
            if quote:
                result['current_price'] = quote['current_price']
                result['average_volume'] = quote['volume']
                print(f"[Polygon Quote] {ticker}: ${quote['current_price']:.2f}")
            else:
                print(f"[Warning] Could not get quote for {ticker}")
                return result  # Can't proceed without price

            # Step 2: Get company details (market cap, exchange, name, description)
            details = self.polygon.get_stock_details(ticker)
            if details:
                result['market_cap'] = details['market_cap']
                result['exchange'] = details['primary_exchange']
                result['name'] = details.get('name', ticker)
                result['description'] = details.get('description', '')  # Company business description
                result['quote_type'] = details.get('type', 'EQUITY')
                result['market'] = details.get('market', 'stocks')
                
                # Determine if strong market
                strong_exchanges = ["NYQ", "NYS", "NMS", "NCM", "NGM", "ASE", "XNAS", "XNYS"]
                weak_markets = ["OTC", "OTCQB", "OTCQX", "PINK", "GREY"]
                
                result['is_strong_market'] = (
                    details['primary_exchange'] in strong_exchanges and
                    not any(weak in details['primary_exchange'] for weak in weak_markets)
                )
                
                print(f"[Polygon Details] {ticker}: {result['name']}, Market Cap ${details['market_cap']/1e9:.2f}B")
            else:
                print(f"[Warning] Could not get details for {ticker}")

            # Step 3: Get financial ratios (P/E, Current Ratio, ROE, etc.)
            financials = self.polygon.get_financials(ticker)
            if financials:
                result.update({
                    'pe_ratio': financials.get('pe_ratio', 0),
                    'price_to_book': financials.get('price_to_book', 0),
                    'debt_to_equity': financials.get('debt_to_equity', 0),
                    'roe': financials.get('roe', 0),
                    'current_ratio': financials.get('current_ratio', 0),
                    'quick_ratio': financials.get('quick_ratio', 0),
                    'revenue_growth': financials.get('revenue_growth', 0),
                    'earnings_growth': financials.get('earnings_growth', 0),
                    'profit_margin': financials.get('profit_margin', 0),
                    'beta': financials.get('beta', 1.0),
                    'dividend_yield': financials.get('dividend_yield', 0),
                    'forward_pe': financials.get('forward_pe', 0),
                })
                print(f"[Polygon Financials] {ticker}: P/E={financials.get('pe_ratio', 0):.2f}, Current Ratio={financials.get('current_ratio', 0):.2f}, ROE={financials.get('roe', 0):.2f}%")
            else:
                print(f"[Warning] Could not get financials for {ticker} - using defaults")

            # Step 4: Get 52-week high/low from price history
            try:
                history = self.polygon.get_price_history(ticker, days=365)
                if history and history.get('bars'):
                    closes = [bar['close'] for bar in history['bars']]
                    if closes:
                        result['fifty_two_week_high'] = max(closes)
                        result['fifty_two_week_low'] = min(closes)
                        print(f"[Polygon History] {ticker}: 52W High=${result['fifty_two_week_high']:.2f}, Low=${result['fifty_two_week_low']:.2f}")
            except Exception as e:
                print(f"[Warning] Could not get price history for {ticker}: {e}")

        except Exception as e:
            print(f"[Error] Polygon data fetch failed for {ticker}: {e}")
            import traceback
            traceback.print_exc()

        return result

    
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
    """
    Buffett-Style Value Investing Strategy Generator
    Philosophy: Buy wonderful businesses at fair prices and hold forever
    """
    def __init__(self):
        api_key_raw = os.getenv("XAI_API_KEY", "").strip()
        # Remove any whitespace, newlines, or quotes that might have been accidentally included
        self.api_key = api_key_raw.replace("\n", "").replace("\r", "").replace('"', "").replace("'", "").strip()
        self.base_url = "https://api.x.ai/v1/chat/completions"
        # Use grok-3 for strong reasoning and general capabilities
        self.model_name = os.getenv("XAI_MODEL", "grok-3")  # Default to grok-3
        
        # NEW BUFFETT-STYLE SYSTEM PROMPT
        self.system_prompt = """You are Warren Buffett's investment partner, helping build long-term wealth through patient ownership of wonderful American businesses.

CORE PHILOSOPHY:
• We buy BUSINESSES, not stocks (think like owners, not traders)
• Our holding period is FOREVER (10+ years minimum)
• We LOVE market declines (quality businesses on sale)
• Keep 80% of capital ALWAYS invested (can rotate, but stay invested)
• Extremely low turnover: 2-10% annually (like Buffett)

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

**COMPANY OVERVIEW:**
- Business Description: [REQUIRED - Explain what the company does, their products/services, business model, and industry position. This section MUST be included in every response. Use the Business Description provided in the stock information, or if not available, describe what companies in this sector/industry typically do.]

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
        """Generate Buffett-style long-term investment strategy"""
        
        if not self.api_key:
            return "⚠️ XAI API key not configured. Add XAI_API_KEY to .env file."
        
        if "your_xai" in self.api_key.lower() or len(self.api_key) < 30:
            return f"⚠️ **API key not set correctly!**\n\nPlease update `.env` with your actual xAI API key from https://console.x.ai"
        
        if not self.api_key.startswith("xai-") or len(self.api_key) < 50:
            return f"⚠️ Invalid API key format. Key should start with 'xai-' and be 50+ characters."
        
        # Extract data
        fundamentals = stock_data.get('fundamentals', {})
        ticker = fundamentals.get('ticker', 'Unknown')
        stock_name = fundamentals.get('name', ticker)
        company_description = fundamentals.get('description', '')
        stock_type = stock_data.get('stock_type', 'Unknown')
        current_price = fundamentals.get('current_price', 0)
        pe_ratio = fundamentals.get('pe_ratio', 0)
        revenue_growth = fundamentals.get('revenue_growth', 0)
        roe = fundamentals.get('roe', 0)
        debt_to_equity = fundamentals.get('debt_to_equity', 0)
        current_ratio = fundamentals.get('current_ratio', 0)
        profit_margin = fundamentals.get('profit_margin', 0)
        market_cap = fundamentals.get('market_cap', 0)
        sector = fundamentals.get('sector', 'Unknown')
        industry = fundamentals.get('industry', 'Unknown')
        
        monthly_budget = user_prefs.get('monthly_contribution', 100)
        portfolio_value = user_prefs.get('portfolio_value', monthly_budget * 12)
        
        # Calculate DCA parameters
        shares_monthly = monthly_budget / current_price if current_price > 0 else 0
        target_shares_12mo = shares_monthly * 12
        target_value_12mo = target_shares_12mo * current_price
        position_pct = (target_value_12mo / portfolio_value * 100) if portfolio_value > 0 else 0
        
        # Build comprehensive prompt focused on BUSINESS QUALITY
        prompt = f"""Analyze this business for LONG-TERM OWNERSHIP (10+ years) using Buffett's framework:

═══════════════════════════════════════════════════════
📊 BUSINESS OVERVIEW
═══════════════════════════════════════════════════════

Company: {stock_name} ({ticker})
Sector: {sector}
Industry: {industry}

What They Do (REQUIRED - Expand on this):
{company_description if company_description else f"{stock_name} operates in the {industry} industry. Research and describe their business model, products/services, customers, and competitive position."}

Current Price: ${current_price:.2f}
Market Cap: ${market_cap/1e9:.2f}B

═══════════════════════════════════════════════════════
💰 FINANCIAL FUNDAMENTALS
═══════════════════════════════════════════════════════

Profitability:
• ROE: {roe:.1f}% (Is this sustainable? 15%+ is quality)
• Profit Margin: {profit_margin:.1f}% (Pricing power?)
• Revenue Growth: {revenue_growth:.1f}% (Sustainable?)

Valuation:
• P/E Ratio: {pe_ratio:.1f}x (Reasonable for quality?)
• Price/Book: {fundamentals.get('price_to_book', 0):.2f}x

Financial Strength:
• Debt/Equity: {debt_to_equity:.2f} (<1.0 is conservative)
• Current Ratio: {current_ratio:.2f} (>1.5 is strong)

═══════════════════════════════════════════════════════
🎯 INVESTOR CONTEXT
═══════════════════════════════════════════════════════

Portfolio Size: ${portfolio_value:,.2f}
Monthly Budget: ${monthly_budget:.2f}
Investment Horizon: 10-30 years
Goal: Build to $300-500K/year passive income

Philosophy:
• Buy businesses, not stocks
• Hold forever (unless thesis breaks)
• Love market declines (buying opportunities)
• Keep 80% invested always
• Let compounding work over decades

═══════════════════════════════════════════════════════
📈 DCA PARAMETERS (Use these exact numbers)
═══════════════════════════════════════════════════════

Shares per Month: {shares_monthly:.3f} shares
Monthly Investment: ${monthly_budget:.2f}
Target after 12 months: {target_shares_12mo:.2f} shares
Value after 12 months: ${target_value_12mo:,.2f}
% of Portfolio: {position_pct:.1f}%

═══════════════════════════════════════════════════════
🔍 BUFFETT-STYLE ANALYSIS REQUIRED
═══════════════════════════════════════════════════════

Answer these critical questions:

1. MOAT ASSESSMENT:
   - What protects this business from competition?
   - Will they have pricing power in 10 years?
   - Can competitors easily replicate this?
   - Rate the moat: Strong/Moderate/Weak

2. MANAGEMENT QUALITY:
   - Do they allocate capital wisely?
   - Are they honest with shareholders?
   - Do insiders own meaningful shares?
   - Will they create value over 10+ years?

3. PREDICTABILITY:
   - Can we predict cash flows 5-10 years out?
   - Is the business model simple and understandable?
   - What could make this business obsolete?
   - Is this a "forever" hold candidate?

4. VALUATION:
   - Are we paying a fair price for this quality?
   - What's a reasonable intrinsic value?
   - Margin of safety at ${current_price:.2f}?
   - Would Buffett buy this at this price?

5. PORTFOLIO FIT:
   - Does this complement existing holdings?
   - Helps achieve $300-500K/year goal how?
   - Worth {position_pct:.1f}% of portfolio?

═══════════════════════════════════════════════════════
💡 OUTPUT REQUIRED
═══════════════════════════════════════════════════════

Provide your analysis in the EXACT format specified in the system prompt:
1. Business Quality Assessment (with ⭐ moat rating)
2. Valuation (intrinsic value estimate)
3. Recommendation (BUY/HOLD/AVOID with conviction level)
4. 12-Month DCA Plan (month-by-month schedule)
5. Exit Criteria (specific conditions, NOT stop-losses)
6. Behavioral Reminder (encourage patience)

Remember:
• Focus on BUSINESS quality, not stock price
• Think 10+ YEARS out
• Welcome market DECLINES
• Build positions over TIME (DCA)
• Sell RARELY (only if thesis breaks)

"The money is out there - ${monthly_budget}/month for 20 years at 12% = $2.4M. This business can help us get there IF it's wonderful and we hold forever."

═══════════════════════════════════════════════════════"""
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model_name,  # Configurable via XAI_MODEL env var
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 3000  # Increased for comprehensive analysis
                },
                timeout=45
            )
            
            if response.status_code == 200:
                analysis = response.json()["choices"][0]["message"]["content"]
                
                # Add philosophy reminder at the end
                philosophy_footer = """

---

### 🎯 BUFFETT'S WISDOM

> *"The stock market is a device for transferring money from the impatient to the patient."*

**Our Edge:** We think in decades while others think in days.

**Remember:**
- The economy is worth trillions
- People are making more money than ever  
- We only need our small share: $300-500K/year
- **The money IS out there**

Keep 80% invested. Hold forever. Let compounding work. 🚀

---
"""
                return analysis + philosophy_footer
                
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    return f"⚠️ API Error: {error_msg}"
                except:
                    return f"⚠️ API Error {response.status_code}: {response.text[:500]}"
                    
        except Exception as e:
            return f"⚠️ Error generating strategy: {str(e)}"


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
# BUFFETT-STYLE PORTFOLIO MANAGER
# Updated AIPortfolioManager with 80% deployment rule and buy-and-hold philosophy

class BuffettPortfolioManager:
    """
    Automated portfolio manager following Buffett's philosophy:
    - Keep 80% deployed in quality businesses
    - Hold forever unless thesis breaks
    - Love market declines (buy more)
    - Extremely low turnover (2-10% annually)
    """
    
    def __init__(self, storage_manager=None):
        self.storage = storage_manager
        self.analyzer = StockAnalyzer()
        self.strategy_gen = XAIStrategyGenerator()
        
    def initialize_portfolio(self, initial_cash: float = 100.0, monthly_contribution: float = 100.0):
        """Initialize new Buffett-style portfolio"""
        from datetime import datetime
        
        portfolio = {
            "philosophy": "Buffett Buy-and-Hold",
            "target_deployment": 80,  # Keep 80% invested
            "initial_cash": initial_cash,
            "monthly_contribution": monthly_contribution,
            "current_cash": initial_cash,
            "total_contributed": initial_cash,
            "positions": {},
            "trade_history": [],
            "watchlist": {},  # Businesses we want to own
            "created_at": datetime.now().isoformat(),
            "last_contribution_date": datetime.now().isoformat(),
            "settings": {
                "max_position_size_pct": 20.0,  # Max 20% at cost
                "allow_concentration": 25.0,  # Can grow to 25% through appreciation
                "min_position_size_pct": 5.0,  # Meaningful positions only
                "target_holdings": 10,  # 8-15 quality businesses
                "max_holdings": 15,
                "portfolio_turnover_target": 10,  # <10% annual turnover
                "hold_period_min_years": 10,  # Think 10+ years
                "rebalance_threshold": 30,  # Trim if position grows >30%
            }
        }
        return portfolio
    
    def get_portfolio_metrics(self, portfolio: Dict) -> Dict:
        """Calculate portfolio metrics with deployment percentage"""
        cash = portfolio.get("current_cash", 0)
        positions = portfolio.get("positions", {})
        
        # Calculate position values
        total_position_value = 0
        for ticker, position in positions.items():
            try:
                current_price = self.analyzer.get_fundamentals(ticker).get("current_price", 0)
                shares = position.get("shares", 0)
                total_position_value += current_price * shares
            except:
                # Use entry price if can't get current
                total_position_value += position.get("entry_price", 0) * position.get("shares", 0)
        
        total_value = cash + total_position_value
        
        # Deployment metrics
        deployed_pct = (total_position_value / total_value * 100) if total_value > 0 else 0
        target_deployment = portfolio.get("target_deployment", 80)
        deployment_gap = deployed_pct - target_deployment
        
        # Position count
        num_positions = len(positions)
        target_holdings = portfolio.get("settings", {}).get("target_holdings", 10)
        
        return {
            "total_value": total_value,
            "cash": cash,
            "cash_pct": (cash / total_value * 100) if total_value > 0 else 0,
            "total_position_value": total_position_value,
            "deployed_pct": deployed_pct,
            "target_deployment": target_deployment,
            "deployment_gap": deployment_gap,
            "num_positions": num_positions,
            "target_holdings": target_holdings,
            "is_properly_deployed": abs(deployment_gap) < 10,  # Within 10% of target
        }
    
    def should_buy_more(self, portfolio: Dict) -> Tuple[bool, str]:
        """Determine if we should be buying (staying at 80% deployment)"""
        metrics = self.get_portfolio_metrics(portfolio)
        
        # Check deployment level
        if metrics["deployed_pct"] < metrics["target_deployment"] - 5:
            gap = metrics["target_deployment"] - metrics["deployed_pct"]
            return True, f"Under-deployed by {gap:.1f}% - should be buying"
        
        # Check if we need more holdings
        if metrics["num_positions"] < metrics["target_holdings"]:
            needed = metrics["target_holdings"] - metrics["num_positions"]
            return True, f"Only {metrics['num_positions']} holdings - target is {metrics['target_holdings']}"
        
        # Check if we have monthly contribution to deploy
        cash_pct = metrics["cash_pct"]
        if cash_pct > 20:  # More than 20% in cash
            return True, f"Too much cash ({cash_pct:.1f}%) - should deploy"
        
        return False, "Portfolio properly deployed"
    
    def evaluate_business_quality(self, ticker: str) -> Dict:
        """Evaluate if this is a quality business worth owning forever"""
        evaluation = self.analyzer.evaluate_stock(ticker)
        
        if "error" in evaluation:
            return {"is_quality": False, "reason": evaluation["error"]}
        
        fundamentals = evaluation["fundamentals"]
        
        # Buffett's quality checklist
        quality_checks = {
            "high_roe": fundamentals.get("roe", 0) >= 15,  # High returns on equity
            "profitable": fundamentals.get("profit_margin", 0) > 10,  # Strong margins
            "low_debt": fundamentals.get("debt_to_equity", 999) < 1.0,  # Conservative debt
            "strong_liquidity": fundamentals.get("current_ratio", 0) > 1.5,  # Financial strength
            "reasonable_valuation": 0 < fundamentals.get("pe_ratio", 0) < 30,  # Not crazy expensive
        }
        
        quality_score = sum(quality_checks.values())
        max_score = len(quality_checks)
        
        # Need at least 4/5 quality criteria
        is_quality = quality_score >= 4
        
        return {
            "is_quality": is_quality,
            "quality_score": quality_score,
            "max_score": max_score,
            "checks": quality_checks,
            "evaluation": evaluation,
            "reason": f"Quality score: {quality_score}/{max_score}"
        }
    
    def calculate_dca_amount(self, portfolio: Dict, ticker: str) -> float:
        """Calculate how much to invest this month via DCA"""
        monthly_budget = portfolio.get("monthly_contribution", 100)
        metrics = self.get_portfolio_metrics(portfolio)
        
        # Check if we're properly deployed
        deployment_gap = metrics["deployment_gap"]
        
        # If under-deployed, allocate more aggressively
        if deployment_gap < -10:  # More than 10% under target
            return monthly_budget * 1.5  # Buy 50% more
        elif deployment_gap < -5:
            return monthly_budget * 1.2  # Buy 20% more
        else:
            return monthly_budget  # Normal DCA
    
    def execute_dca_buy(self, portfolio: Dict, ticker: str, amount: float) -> Dict:
        """Execute dollar-cost averaging purchase"""
        from datetime import datetime
        
        try:
            fundamentals = self.analyzer.get_fundamentals(ticker)
            current_price = fundamentals.get("current_price", 0)
            
            if current_price <= 0:
                return {"success": False, "error": "Invalid price"}
            
            shares = amount / current_price
            cost = shares * current_price
            
            if cost > portfolio.get("current_cash", 0):
                return {"success": False, "error": "Insufficient cash"}
            
            # Add to existing position or create new
            if ticker in portfolio["positions"]:
                position = portfolio["positions"][ticker]
                
                # Calculate new average entry price
                old_shares = position["shares"]
                old_cost = old_shares * position["entry_price"]
                new_shares = old_shares + shares
                new_avg_price = (old_cost + cost) / new_shares
                
                position["shares"] = new_shares
                position["entry_price"] = new_avg_price
                position["last_purchase"] = datetime.now().isoformat()
                position["purchase_count"] = position.get("purchase_count", 1) + 1
                
            else:
                # New position
                quality_eval = self.evaluate_business_quality(ticker)
                
                position = {
                    "shares": shares,
                    "entry_price": current_price,
                    "entry_date": datetime.now().isoformat(),
                    "last_purchase": datetime.now().isoformat(),
                    "purchase_count": 1,
                    "stock_type": quality_eval["evaluation"].get("stock_type", "Unknown"),
                    "quality_score": quality_eval["quality_score"],
                    "thesis": f"Quality business with {quality_eval['quality_score']}/5 criteria",
                    "hold_forever": True,  # Default assumption
                    "exit_only_if": [
                        "Moat deteriorates",
                        "Significantly overvalued (P/E >50)",
                        "Better opportunity exists",
                        "Position >25% of portfolio"
                    ]
                }
                portfolio["positions"][ticker] = position
            
            # Deduct cash
            portfolio["current_cash"] -= cost
            
            # Record trade
            trade = {
                "ticker": ticker,
                "action": "BUY (DCA)",
                "shares": shares,
                "price": current_price,
                "total_cost": cost,
                "timestamp": datetime.now().isoformat(),
                "reason": "Dollar-cost averaging - building long-term position"
            }
            portfolio["trade_history"].append(trade)
            
            return {
                "success": True,
                "shares": shares,
                "price": current_price,
                "cost": cost,
                "total_shares": portfolio["positions"][ticker]["shares"],
                "avg_price": portfolio["positions"][ticker]["entry_price"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_sell_conditions(self, portfolio: Dict, ticker: str) -> Dict:
        """Check if we should sell (RARE - only if thesis breaks)"""
        position = portfolio.get("positions", {}).get(ticker)
        if not position:
            return {"should_sell": False}
        
        try:
            # Re-evaluate business quality
            quality_eval = self.evaluate_business_quality(ticker)
            original_quality = position.get("quality_score", 5)
            current_quality = quality_eval.get("quality_score", 0)
            
            # Get current metrics
            fundamentals = self.analyzer.get_fundamentals(ticker)
            current_price = fundamentals.get("current_price", 0)
            pe_ratio = fundamentals.get("pe_ratio", 0)
            
            # Calculate position size
            portfolio_value = self.get_portfolio_metrics(portfolio)["total_value"]
            position_value = current_price * position["shares"]
            position_pct = (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
            
            # Sell Condition 1: Fundamentals deteriorated significantly
            if current_quality < 3 and current_quality < original_quality:
                return {
                    "should_sell": True,
                    "reason": "Fundamentals deteriorated",
                    "sell_price": current_price,
                    "details": f"Quality dropped from {original_quality}/5 to {current_quality}/5"
                }
            
            # Sell Condition 2: Extremely overvalued
            if pe_ratio > 60 and not quality_eval.get("is_quality", False):
                return {
                    "should_sell": True,
                    "reason": "Significantly overvalued",
                    "sell_price": current_price,
                    "details": f"P/E of {pe_ratio:.1f} is excessive"
                }
            
            # Sell Condition 3: Concentration risk
            max_position = portfolio.get("settings", {}).get("allow_concentration", 25)
            if position_pct > max_position:
                # Trim, don't exit completely
                return {
                    "should_sell": "TRIM",
                    "reason": "Concentration risk management",
                    "sell_price": current_price,
                    "trim_to_pct": 20,  # Trim back to 20%
                    "details": f"Position is {position_pct:.1f}% of portfolio"
                }
            
            # OTHERWISE: HOLD FOREVER
            return {"should_sell": False, "reason": "Business remains quality - HOLD"}
            
        except Exception as e:
            return {"should_sell": False, "error": str(e)}
    
    def auto_manage_portfolio(self, portfolio: Dict, watchlist_tickers: List[str] = None) -> Tuple[Dict, List[str]]:
        """
        Manage portfolio with Buffett philosophy:
        1. Add monthly contribution
        2. Check if we should sell anything (RARE)
        3. Buy to maintain 80% deployment
        4. Build positions via DCA
        """
        from datetime import datetime
        
        activity_log = []
        
        # Step 1: Add monthly contribution
        old_contrib = portfolio.get("total_contributed", 0)
        portfolio = self.add_monthly_contribution(portfolio)
        new_contrib = portfolio.get("total_contributed", 0)
        
        if new_contrib > old_contrib:
            amount = new_contrib - old_contrib
            activity_log.append(f"✅ Monthly contribution: +${amount:.2f}")
        
        # Step 2: Check sell conditions (RARE)
        for ticker in list(portfolio.get("positions", {}).keys()):
            sell_check = self.check_sell_conditions(portfolio, ticker)
            
            if sell_check.get("should_sell") == "TRIM":
                # Trim for concentration risk
                activity_log.append(f"⚖️ {ticker} too large - trimming to 20% of portfolio")
                # TODO: Implement trim logic
                
            elif sell_check.get("should_sell"):
                # Full exit - thesis broken
                reason = sell_check.get("reason", "Unknown")
                activity_log.append(f"🔴 SELL {ticker}: {reason}")
                activity_log.append(f"   Thesis broken after {self._holding_period(portfolio, ticker)} years")
                # TODO: Implement sell logic
        
        # Step 3: Check deployment level
        metrics = self.get_portfolio_metrics(portfolio)
        activity_log.append(f"📊 Portfolio: ${metrics['total_value']:,.2f} | Deployed: {metrics['deployed_pct']:.1f}% (target: {metrics['target_deployment']}%)")
        
        should_buy, buy_reason = self.should_buy_more(portfolio)
        
        if should_buy:
            activity_log.append(f"🎯 {buy_reason}")
            
            # Step 4: Execute DCA purchases
            if watchlist_tickers:
                # Evaluate each watchlist ticker
                for ticker in watchlist_tickers[:3]:  # Top 3 opportunities
                    
                    # Check if already holding
                    if ticker in portfolio.get("positions", {}):
                        # Continue DCA into existing position
                        dca_amount = self.calculate_dca_amount(portfolio, ticker)
                        
                        if dca_amount <= portfolio.get("current_cash", 0):
                            buy_result = self.execute_dca_buy(portfolio, ticker, dca_amount)
                            
                            if buy_result.get("success"):
                                activity_log.append(f"🟢 DCA into {ticker}: +{buy_result['shares']:.3f} shares @ ${buy_result['price']:.2f}")
                                activity_log.append(f"   Total: {buy_result['total_shares']:.3f} shares @ avg ${buy_result['avg_price']:.2f}")
                    
                    else:
                        # Evaluate new business
                        quality_eval = self.evaluate_business_quality(ticker)
                        
                        if quality_eval.get("is_quality"):
                            dca_amount = self.calculate_dca_amount(portfolio, ticker)
                            
                            if dca_amount <= portfolio.get("current_cash", 0):
                                buy_result = self.execute_dca_buy(portfolio, ticker, dca_amount)
                                
                                if buy_result.get("success"):
                                    activity_log.append(f"🟢 NEW POSITION: {ticker}")
                                    activity_log.append(f"   Quality Score: {quality_eval['quality_score']}/5")
                                    activity_log.append(f"   Bought {buy_result['shares']:.3f} shares @ ${buy_result['price']:.2f}")
                                    activity_log.append(f"   Plan: DCA over 12-24 months")
                                    break  # Start with one new position
                        else:
                            activity_log.append(f"⏸️ {ticker}: {quality_eval.get('reason')}")
            
            else:
                activity_log.append("ℹ️ No watchlist provided - add quality businesses to deploy capital")
        
        else:
            activity_log.append("✅ Portfolio properly deployed - maintain holdings")
        
        # Summary
        activity_log.append("")
        activity_log.append("═" * 60)
        activity_log.append(f"💼 Holdings: {metrics['num_positions']} businesses")
        activity_log.append(f"💰 Cash: ${metrics['cash']:,.2f} ({metrics['cash_pct']:.1f}%)")
        activity_log.append(f"📈 Invested: ${metrics['total_position_value']:,.2f} ({metrics['deployed_pct']:.1f}%)")
        activity_log.append(f"🎯 Target Deployment: {metrics['target_deployment']}%")
        activity_log.append("═" * 60)
        
        portfolio["last_managed"] = datetime.now().isoformat()
        return portfolio, activity_log
    
    def add_monthly_contribution(self, portfolio: Dict) -> Dict:
        """Add monthly contribution if a month has passed"""
        from datetime import datetime, timedelta
        
        last_contrib = datetime.fromisoformat(portfolio.get("last_contribution_date", datetime.now().isoformat()))
        now = datetime.now()
        
        if (now - last_contrib).days >= 30:
            monthly_amount = portfolio.get("monthly_contribution", 100.0)
            portfolio["current_cash"] += monthly_amount
            portfolio["total_contributed"] += monthly_amount
            portfolio["last_contribution_date"] = now.isoformat()
        
        return portfolio
    
    def _holding_period(self, portfolio: Dict, ticker: str) -> float:
        """Calculate holding period in years"""
        from datetime import datetime
        
        position = portfolio.get("positions", {}).get(ticker)
        if not position:
            return 0
        
        entry_date = datetime.fromisoformat(position.get("entry_date", datetime.now().isoformat()))
        now = datetime.now()
        days = (now - entry_date).days
        return days / 365.25


# Usage example:
# manager = BuffettPortfolioManager()
# portfolio = manager.initialize_portfolio(initial_cash=1000, monthly_contribution=500)
# portfolio, activity = manager.auto_manage_portfolio(portfolio, watchlist_tickers=['AAPL', 'MSFT', 'GOOGL'])
