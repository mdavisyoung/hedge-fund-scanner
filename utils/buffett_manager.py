# BUFFETT-STYLE PORTFOLIO MANAGER
# Add this class to utils/core.py or import from here

from typing import Dict, List, Tuple
from utils.core import StockAnalyzer, XAIStrategyGenerator

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




