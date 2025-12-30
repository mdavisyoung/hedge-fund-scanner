"""
Portfolio Context Manager
Formats portfolio data for Dexter AI consumption
"""

import json
from typing import Dict, List, Optional
from datetime import datetime


class PortfolioContext:
    """
    Manages portfolio state and formats it for Dexter
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize portfolio context
        
        Args:
            storage_path: Path to portfolio state JSON (optional)
        """
        self.storage_path = storage_path or "data/ai_portfolio.json"
        self.portfolio_data = self._load_portfolio()
    
    def _load_portfolio(self) -> Dict:
        """Load portfolio from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default empty portfolio
            return {
                "current_cash": 0.0,
                "positions": {},
                "trade_history": [],
                "total_contributed": 0.0
            }
    
    def get_context(self) -> Dict:
        """
        Get portfolio context formatted for Dexter
        
        Returns:
            Dict with cash, holdings, value, etc.
        """
        cash = self.portfolio_data.get('current_cash', 0.0)
        positions = self.portfolio_data.get('positions', {})
        
        # Format holdings
        holdings = {}
        total_position_value = 0.0
        
        for ticker, position in positions.items():
            shares = position.get('shares', 0)
            entry_price = position.get('entry_price', 0)
            position_value = shares * entry_price
            total_position_value += position_value
            
            holdings[ticker] = {
                'shares': shares,
                'entry_price': entry_price,
                'position_value': position_value,
                'entry_date': position.get('entry_date', ''),
                'stop_loss': position.get('stop_loss', 0),
                'target': position.get('target', 0)
            }
        
        total_value = cash + total_position_value
        
        # Get recent trades
        recent_trades = self.portfolio_data.get('trade_history', [])[-10:]
        
        return {
            'cash': cash,
            'holdings': holdings,
            'total_position_value': total_position_value,
            'total_value': total_value,
            'total_contributed': self.portfolio_data.get('total_contributed', 0.0),
            'recent_trades': recent_trades,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_summary_text(self) -> str:
        """
        Get human-readable portfolio summary
        
        Returns:
            Formatted string summary
        """
        context = self.get_context()
        
        summary = f"""💰 Portfolio Summary:

Cash Available: ${context['cash']:,.2f}
Total Position Value: ${context['total_position_value']:,.2f}
Total Portfolio Value: ${context['total_value']:,.2f}
Total Contributed: ${context['total_contributed']:,.2f}

📊 Current Holdings:"""
        
        if context['holdings']:
            for ticker, data in context['holdings'].items():
                summary += f"\n  • {ticker}: {data['shares']} shares @ ${data['entry_price']:.2f} (Value: ${data['position_value']:.2f})"
        else:
            summary += "\n  No positions currently held"
        
        if context['recent_trades']:
            summary += f"\n\n📈 Recent Trades: {len(context['recent_trades'])} in history"
        
        return summary
    
    def add_to_context(self, additional_info: Dict) -> Dict:
        """
        Add additional information to portfolio context
        
        Args:
            additional_info: Extra context to include
            
        Returns:
            Combined context
        """
        context = self.get_context()
        context.update(additional_info)
        return context
    
    def format_for_query(self, query: str) -> str:
        """
        Enhance user query with portfolio context
        
        Args:
            query: Original user query
            
        Returns:
            Enhanced query with portfolio info
        """
        context = self.get_context()
        
        enhanced_query = f"""{query}

[Portfolio Context]
Cash: ${context['cash']:.2f}
Total Value: ${context['total_value']:.2f}
Holdings: {', '.join([f"{t} ({d['shares']} shares)" for t, d in context['holdings'].items()]) if context['holdings'] else 'None'}
"""
        
        return enhanced_query


# Utility functions
def get_portfolio_context(storage_path: Optional[str] = None) -> Dict:
    """
    Quick function to get portfolio context
    
    Args:
        storage_path: Optional path to portfolio JSON
        
    Returns:
        Portfolio context dict
    """
    pc = PortfolioContext(storage_path)
    return pc.get_context()


def get_portfolio_summary(storage_path: Optional[str] = None) -> str:
    """
    Quick function to get portfolio summary
    
    Args:
        storage_path: Optional path to portfolio JSON
        
    Returns:
        Human-readable summary
    """
    pc = PortfolioContext(storage_path)
    return pc.get_summary_text()


if __name__ == "__main__":
    # Test portfolio context
    pc = PortfolioContext()
    
    print("Portfolio Context:")
    print("=" * 60)
    print(pc.get_summary_text())
    
    print("\n\nRaw Context:")
    print("=" * 60)
    import pprint
    pprint.pprint(pc.get_context())
