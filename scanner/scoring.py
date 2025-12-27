# ============================================================================
# FILE 2: scanner/scoring.py  
# Multi-factor scoring system for trade opportunities
# ============================================================================

"""
Trade Scoring Engine
Scores stocks 0-100 based on fundamental, technical, and risk factors
"""

import pandas as pd
from datetime import datetime, timedelta


class TradeScorer:
    """Scores potential trades using multi-factor analysis"""
    
    def __init__(self):
        self.weights = {
            'fundamental': 0.40,
            'technical': 0.30,
            'risk_reward': 0.20,
            'timing': 0.10
        }
    
    def score_stock(self, fundamentals, price_data, stock_type):
        """
        Calculate overall trade score
        
        Args:
            fundamentals: Dict from StockAnalyzer.get_fundamentals()
            price_data: DataFrame from StockAnalyzer.get_stock_data()
            stock_type: "Growth", "Value", "Financial", "Cyclical"
            
        Returns:
            Dict with score and breakdown
        """
        scores = {
            'fundamental': self._score_fundamentals(fundamentals, stock_type),
            'technical': self._score_technicals(price_data, fundamentals),
            'risk_reward': self._score_risk_reward(price_data, fundamentals),
            'timing': self._score_timing(price_data, fundamentals)
        }
        
        # Weighted total
        total_score = sum(scores[k] * self.weights[k] for k in scores.keys())
        
        return {
            'total_score': round(total_score, 1),
            'breakdown': scores,
            'grade': self._get_grade(total_score)
        }
    
    def _score_fundamentals(self, fund, stock_type):
        """Score fundamental metrics (0-100)"""
        score = 0
        
        if stock_type == "Growth":
            # Revenue growth (0-30 pts)
            rev_growth = fund.get('revenue_growth', 0)
            if rev_growth >= 25:
                score += 30
            elif rev_growth >= 15:
                score += 20
            elif rev_growth >= 10:
                score += 10
            
            # ROE (0-30 pts)
            roe = fund.get('roe', 0)
            if roe >= 20:
                score += 30
            elif roe >= 15:
                score += 20
            elif roe >= 10:
                score += 10
            
            # Profit margin (0-20 pts)
            margin = fund.get('profit_margin', 0)
            if margin >= 20:
                score += 20
            elif margin >= 10:
                score += 10
            
            # P/E reasonable for growth (0-20 pts)
            pe = fund.get('pe_ratio', 0)
            if 0 < pe < 30:
                score += 20
            elif 30 <= pe < 50:
                score += 10
                
        elif stock_type == "Value":
            # Low P/E (0-40 pts)
            pe = fund.get('pe_ratio', 0)
            if 0 < pe < 12:
                score += 40
            elif 12 <= pe < 15:
                score += 30
            elif 15 <= pe < 20:
                score += 15
            
            # Strong ROE (0-30 pts)
            roe = fund.get('roe', 0)
            if roe >= 15:
                score += 30
            elif roe >= 10:
                score += 20
            
            # Low debt (0-30 pts)
            debt_equity = fund.get('debt_to_equity', 999)
            if debt_equity < 0.5:
                score += 30
            elif debt_equity < 1.0:
                score += 20
            elif debt_equity < 1.5:
                score += 10
                
        elif stock_type == "Financial":
            # ROE (0-50 pts)
            roe = fund.get('roe', 0)
            if roe >= 15:
                score += 50
            elif roe >= 12:
                score += 40
            elif roe >= 10:
                score += 25
            
            # P/E (0-30 pts)
            pe = fund.get('pe_ratio', 0)
            if 0 < pe < 10:
                score += 30
            elif 10 <= pe < 12:
                score += 20
            
            # Dividend (0-20 pts)
            div_yield = fund.get('dividend_yield', 0)
            if div_yield >= 3:
                score += 20
            elif div_yield >= 2:
                score += 10
        
        else:  # Cyclical
            # Current ratio (0-40 pts)
            current_ratio = fund.get('current_ratio', 0)
            if current_ratio >= 2:
                score += 40
            elif current_ratio >= 1.5:
                score += 30
            elif current_ratio >= 1.0:
                score += 15
            
            # P/E (0-30 pts)
            pe = fund.get('pe_ratio', 0)
            if 0 < pe < 15:
                score += 30
            elif 15 <= pe < 20:
                score += 20
            
            # Profit margin (0-30 pts)
            margin = fund.get('profit_margin', 0)
            if margin >= 10:
                score += 30
            elif margin >= 5:
                score += 15
        
        return min(100, score)
    
    def _score_technicals(self, price_data, fund):
        """Score technical indicators (0-100)"""
        if price_data is None or price_data.empty:
            return 50  # Neutral if no data
        
        score = 0
        current_price = fund.get('current_price', 0)
        
        # Moving averages (0-40 pts)
        if len(price_data) >= 50:
            ma_50 = price_data['Close'].tail(50).mean()
            if current_price > ma_50 * 1.02:  # Above 50 MA
                score += 20
            elif current_price > ma_50 * 0.98:  # Near 50 MA
                score += 10
        
        if len(price_data) >= 200:
            ma_200 = price_data['Close'].tail(200).mean()
            if current_price > ma_200:
                score += 20
            elif current_price > ma_200 * 0.95:
                score += 10
        
        # RSI (0-30 pts) - Oversold is opportunity
        if len(price_data) >= 14:
            delta = price_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            if 25 <= current_rsi <= 35:  # Oversold
                score += 30
            elif 35 < current_rsi <= 45:
                score += 20
            elif 45 < current_rsi <= 55:  # Neutral
                score += 15
            elif 55 < current_rsi <= 70:
                score += 10
        
        # Volume trend (0-30 pts)
        if len(price_data) >= 20:
            recent_vol = price_data['Volume'].tail(5).mean()
            avg_vol = price_data['Volume'].tail(20).mean()
            
            if recent_vol > avg_vol * 1.5:  # High volume
                score += 30
            elif recent_vol > avg_vol * 1.2:
                score += 20
            elif recent_vol > avg_vol:
                score += 10
        
        return min(100, score)
    
    def _score_risk_reward(self, price_data, fund):
        """Score risk/reward setup (0-100)"""
        score = 0
        current_price = fund.get('current_price', 0)
        
        # Distance from 52-week high/low (0-50 pts)
        week_52_high = fund.get('fifty_two_week_high', current_price)
        week_52_low = fund.get('fifty_two_week_low', current_price)
        
        if week_52_high > 0:
            pct_from_high = ((week_52_high - current_price) / week_52_high) * 100
            
            if pct_from_high >= 30:  # Deep pullback
                score += 50
            elif pct_from_high >= 20:
                score += 40
            elif pct_from_high >= 10:
                score += 25
            elif pct_from_high <= 5:  # Near highs
                score += 10
        
        # Beta / Volatility (0-50 pts) - Lower is better for risk mgmt
        beta = fund.get('beta', 1.0)
        if beta < 0.8:
            score += 50
        elif beta < 1.0:
            score += 40
        elif beta < 1.2:
            score += 30
        elif beta < 1.5:
            score += 15
        
        return min(100, score)
    
    def _score_timing(self, price_data, fund):
        """Score market timing factors (0-100)"""
        score = 50  # Base neutral score
        
        # Recent momentum (0-50 pts bonus/penalty)
        if price_data is not None and len(price_data) >= 5:
            recent_returns = (price_data['Close'].iloc[-1] / price_data['Close'].iloc[-5] - 1) * 100
            
            if -5 <= recent_returns <= -2:  # Slight pullback
                score += 30
            elif -10 <= recent_returns < -5:  # Moderate pullback
                score += 20
            elif recent_returns > 5:  # Strong momentum
                score += 10
            elif recent_returns < -15:  # Falling knife
                score -= 20
        
        # Market cap stability (0-20 pts)
        market_cap = fund.get('market_cap', 0)
        if market_cap > 100e9:  # > $100B (mega cap)
            score += 20
        elif market_cap > 10e9:  # > $10B (large cap)
            score += 15
        elif market_cap > 2e9:  # > $2B (mid cap)
            score += 10
        
        return max(0, min(100, score))
    
    def _get_grade(self, score):
        """Convert score to letter grade"""
        if score >= 85:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 65:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

