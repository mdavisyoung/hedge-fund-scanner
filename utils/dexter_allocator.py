"""
Dexter-Managed Monthly Allocation System
AI Portfolio Manager: Dexter decides how to invest $100/month
"""

import sys
sys.path.insert(0, 'utils')

from dexter_client import DexterClient
from portfolio_context import PortfolioContext
from core import StockAnalyzer
from datetime import datetime
import json
import re


class DexterAllocator:
    """
    AI Portfolio Manager using Dexter
    - Researches opportunities monthly
    - Decides optimal allocation
    - Maintains 80% deployment
    - Follows Buffett philosophy
    """
    
    def __init__(self):
        self.dexter = DexterClient()
        self.portfolio = PortfolioContext()
        self.analyzer = StockAnalyzer()
    
    def monthly_allocation(self, budget: float = 100.0) -> dict:
        """
        Main entry point: Dexter researches and decides allocation
        
        Args:
            budget: Monthly investment amount
            
        Returns:
            {
                'raw_answer': Full Dexter analysis,
                'allocations': [{'ticker': 'AAPL', 'amount': 60, 'shares': 0.316, ...}],
                'reasoning': Summary,
                'execute': bool
            }
        """
        # Get current portfolio state
        context = self.portfolio.get_context()
        
        # Build comprehensive research query
        query = self._build_allocation_query(context, budget)
        
        # Dexter researches and decides
        print("🤖 Dexter is analyzing allocation opportunities...")
        print(f"   Budget: ${budget:.2f}")
        print(f"   Current holdings: {len(context['holdings'])}")
        print(f"   Portfolio value: ${context['total_value']:,.2f}")
        
        result = self.dexter.research(query, context)
        
        if 'error' in result:
            return {
                'error': result['error'],
                'raw_answer': result.get('answer', ''),
                'allocations': [],
                'execute': False
            }
        
        # Parse Dexter's decision
        decision = self._parse_decision(result.get('answer', ''), budget)
        decision['raw_answer'] = result.get('answer', '')
        decision['iterations'] = result.get('iterations', 0)
        decision['tasks'] = len(result.get('plan', {}).get('tasks', []))
        
        return decision
    
    def _build_allocation_query(self, context: dict, budget: float) -> str:
        """Build comprehensive research query for Dexter"""
        
        holdings = context.get('holdings', {})
        cash = context.get('cash', 0)
        total_value = context.get('total_value', 0)
        deployed_pct = ((total_value - cash) / total_value * 100) if total_value > 0 else 0
        
        # Format holdings
        if holdings:
            holdings_list = []
            for ticker, data in holdings.items():
                pct = (data['position_value'] / total_value * 100) if total_value > 0 else 0
                holdings_list.append(
                    f"  • {ticker}: {data['shares']:.2f} shares @ ${data['entry_price']:.2f} "
                    f"= ${data['position_value']:.2f} ({pct:.1f}% of portfolio)"
                )
            holdings_summary = "\n".join(holdings_list)
        else:
            holdings_summary = "  No positions currently held - starting fresh!"
        
        query = f"""You are my AI Portfolio Manager. I have ${budget:.2f} to invest this month.

YOUR MISSION: Research opportunities and decide the BEST allocation using ALL available data.

═══════════════════════════════════════════════════════
📊 CURRENT PORTFOLIO STATE
═══════════════════════════════════════════════════════

Total Value: ${total_value:,.2f}
Cash Available: ${cash:.2f}
Deployment: {deployed_pct:.1f}% (target: 80%)
New Capital This Month: ${budget:.2f}

Current Holdings:
{holdings_summary}

═══════════════════════════════════════════════════════
🔍 YOUR RESEARCH TASKS (Use ALL tools available)
═══════════════════════════════════════════════════════

1. REVIEW EXISTING HOLDINGS (if any):
   For each holding:
   • Use getStockAggregates to check recent price action
   • Use getTickerFinancials for latest fundamentals
   • Use webSearch for recent news (last 30 days)
   • Assess: Is thesis still valid? Add more or hold?

2. EVALUATE DEPLOYMENT:
   • Currently {deployed_pct:.1f}% deployed (target: 80%)
   • Under-deployed? → Deploy aggressively
   • Properly deployed? → Maintain positions
   • Over-concentrated? → Diversify

3. SCAN FOR NEW OPPORTUNITIES:
   • Use getTickerFinancials to find quality businesses:
     - ROE >15% sustained
     - Low debt (D/E <1.0)
     - Profitable (margin >10%)
     - Reasonable P/E (15-30 for quality)
   • Use webSearch to find undervalued opportunities
   • Look for businesses on sale (market overreaction)

4. SECTOR DIVERSIFICATION:
   • Current allocation by sector
   • Any gaps to fill?
   • Avoid over-concentration (max 40% per sector)

═══════════════════════════════════════════════════════
🎯 DECISION CRITERIA (Buffett-Style)
═══════════════════════════════════════════════════════

PREFER:
✅ Strong competitive moats (brand, network, cost)
✅ Quality businesses we can hold 10+ years
✅ Undervalued relative to intrinsic value
✅ Improving portfolio diversification
✅ Management we trust

AVOID:
❌ Speculative or momentum plays
❌ Businesses we don't understand
❌ Chasing recent winners
❌ Over-concentration

DEPLOYMENT RULES:
• If <70% deployed: Deploy full ${budget:.2f} to best opportunity
• If 70-85% deployed: Normal DCA allocation
• If >85% deployed: Can hold some cash or diversify

═══════════════════════════════════════════════════════
📋 REQUIRED OUTPUT FORMAT
═══════════════════════════════════════════════════════

**ALLOCATION DECISION**

Budget: ${budget:.2f}
Recommendation: [Single allocation / Split allocation / Hold cash]

**OPTION 1: [TICKER]**
Amount: $XX.XX
Shares: X.XXX shares @ $YYY.YY
Reason: [Why this is the best use of capital - 2-3 sentences]

Research Summary:
  • Recent News: [Key findings from web search]
  • Latest Financials: [P/E, ROE, Growth, Debt from Polygon]
  • Valuation Assessment: [Fair/Undervalued/Overvalued and why]
  • Business Moat: [Strong/Moderate/Weak - what protects them?]
  
Conviction Level: [High 🔥 / Medium ⚡ / Low 💡]

[If split allocation, include OPTION 2 with same format]

**PORTFOLIO IMPACT**

After this allocation:
  • Deployment: {deployed_pct:.1f}% → XX.X%
  • Number of holdings: {len(holdings)} → X
  • Sector allocation: [Summary]
  • Largest position: [Ticker at X%]

**REASONING**

[2-3 sentences explaining why this allocation is optimal given:
 - Current portfolio state
 - Market conditions
 - Opportunities identified
 - Long-term wealth building goal]

**ALTERNATIVES CONSIDERED**

[Briefly mention what else you evaluated and why you didn't choose it]

═══════════════════════════════════════════════════════
⚠️ CRITICAL REQUIREMENTS
═══════════════════════════════════════════════════════

1. MUST use getTickerFinancials for financial data
2. MUST use webSearch for recent news/developments  
3. MUST provide SPECIFIC tickers (not "tech stock")
4. MUST show exact dollar amounts and share counts
5. MUST explain reasoning with data
6. Focus on BUSINESS QUALITY for 10+ year hold

Begin your research now and provide allocation decision:"""

        return query
    
    def _parse_decision(self, answer: str, budget: float) -> dict:
        """Parse Dexter's allocation decision from text"""
        
        decision = {
            'allocations': [],
            'reasoning': '',
            'portfolio_impact': '',
            'execute': False
        }
        
        # Extract allocations using regex
        # Pattern: **OPTION X: TICKER**
        option_pattern = r'\*\*OPTION \d+:\s*([A-Z]+)\*\*'
        options = re.finditer(option_pattern, answer, re.IGNORECASE)
        
        for match in options:
            ticker = match.group(1).upper()
            option_start = match.end()
            
            # Find next option or end
            next_match = re.search(r'\*\*OPTION \d+:', answer[option_start:])
            if next_match:
                option_end = option_start + next_match.start()
            else:
                # Look for portfolio impact section
                impact_match = re.search(r'\*\*PORTFOLIO IMPACT\*\*', answer[option_start:])
                option_end = option_start + impact_match.start() if impact_match else len(answer)
            
            option_text = answer[option_start:option_end]
            
            # Extract amount
            amount_match = re.search(r'Amount:\s*\$?([\d,]+\.?\d*)', option_text)
            amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0
            
            # Extract shares and price
            shares_match = re.search(r'Shares:\s*([\d.]+)\s*shares\s*@\s*\$?([\d,]+\.?\d*)', option_text)
            if shares_match:
                shares = float(shares_match.group(1))
                price = float(shares_match.group(2).replace(',', ''))
            else:
                # Try to get current price from analyzer
                try:
                    fundamentals = self.analyzer.get_fundamentals(ticker)
                    price = fundamentals.get('current_price', 0)
                    shares = amount / price if price > 0 else 0
                except:
                    price = 0
                    shares = 0
            
            # Extract conviction
            conviction = 'Medium'
            if '🔥' in option_text or 'High' in option_text:
                conviction = 'High'
            elif '💡' in option_text or 'Low' in option_text:
                conviction = 'Low'
            
            if amount > 0 and ticker:
                decision['allocations'].append({
                    'ticker': ticker,
                    'amount': amount,
                    'shares': shares,
                    'price': price,
                    'conviction': conviction
                })
        
        # Extract reasoning
        reasoning_match = re.search(r'\*\*REASONING\*\*\s*\n\s*(.+?)(?:\n\n|\*\*)', answer, re.DOTALL)
        if reasoning_match:
            decision['reasoning'] = reasoning_match.group(1).strip()
        
        # Mark for execution if we have allocations
        if decision['allocations']:
            total_allocated = sum(a['amount'] for a in decision['allocations'])
            if abs(total_allocated - budget) < 1:  # Within $1
                decision['execute'] = True
        
        return decision
    
    def execute_allocation(self, decision: dict) -> dict:
        """
        Execute the allocation (record trades)
        
        Returns:
            Execution results for each allocation
        """
        results = []
        
        for allocation in decision['allocations']:
            ticker = allocation['ticker']
            amount = allocation['amount']
            shares = allocation['shares']
            price = allocation['price']
            
            # Verify current price
            try:
                fundamentals = self.analyzer.get_fundamentals(ticker)
                current_price = fundamentals.get('current_price', 0)
                
                if current_price > 0:
                    # Recalculate shares with current price
                    actual_shares = amount / current_price
                    
                    results.append({
                        'ticker': ticker,
                        'shares': actual_shares,
                        'price': current_price,
                        'cost': amount,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'success',
                        'note': f'Bought {actual_shares:.4f} shares @ ${current_price:.2f}'
                    })
                else:
                    results.append({
                        'ticker': ticker,
                        'status': 'failed',
                        'reason': 'Could not get current price'
                    })
            except Exception as e:
                results.append({
                    'ticker': ticker,
                    'status': 'failed',
                    'reason': str(e)
                })
        
        return results


def run_monthly_allocation(budget: float = 100.0) -> dict:
    """
    Convenience function to run monthly allocation
    
    Usage:
        result = run_monthly_allocation(100.0)
        print(result['raw_answer'])  # Full analysis
        print(result['allocations'])  # Parsed decisions
        
        if result['execute']:
            allocator = DexterAllocator()
            execution = allocator.execute_allocation(result)
            print(execution)
    
    Returns:
        Complete allocation decision
    """
    allocator = DexterAllocator()
    decision = allocator.monthly_allocation(budget)
    
    return decision


if __name__ == "__main__":
    # Test the allocator
    print("="*60)
    print("DEXTER-MANAGED MONTHLY ALLOCATION TEST")
    print("="*60)
    print()
    
    result = run_monthly_allocation(100.0)
    
    if 'error' in result:
        print("❌ Error:", result['error'])
        print(result['raw_answer'])
    else:
        print("✅ Research complete!")
        print(f"   Iterations: {result.get('iterations', 0)}")
        print(f"   Tasks: {result.get('tasks', 0)}")
        print()
        
        print("="*60)
        print("DEXTER'S DECISION:")
        print("="*60)
        print(result['raw_answer'])
        print()
        
        if result['allocations']:
            print("="*60)
            print("PARSED ALLOCATIONS:")
            print("="*60)
            for alloc in result['allocations']:
                print(f"  📊 {alloc['ticker']}: ${alloc['amount']:.2f}")
                print(f"      Shares: {alloc['shares']:.4f} @ ${alloc['price']:.2f}")
                print(f"      Conviction: {alloc['conviction']}")
                print()
            
            print("="*60)
            print(f"Execute: {'YES ✅' if result['execute'] else 'NO ⚠️'}")
            print("="*60)
