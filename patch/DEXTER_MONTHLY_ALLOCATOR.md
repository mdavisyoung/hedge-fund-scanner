# 🤖 DEXTER-MANAGED PORTFOLIO ALLOCATION SYSTEM

## Overview

**You invest:** $100/month
**Dexter decides:** Where to allocate it
**Data sources:** Polygon API, Web Search, SEC filings, Portfolio context
**Philosophy:** Buffett-style value investing with AI intelligence

---

## 🎯 How It Works

### Monthly Cycle:

```
Day 1 of Month:
    ↓
Portfolio receives $100
    ↓
Dexter analyzes:
    • Current holdings (review each business)
    • Deployment % (target: 80%)
    • Market opportunities (scan for quality)
    • Portfolio gaps (sector diversity)
    ↓
Dexter researches using:
    • Polygon financials (P/E, ROE, debt, growth)
    • Web search (recent news, developments)
    • SEC filings (if needed)
    • Company fundamentals
    ↓
Dexter decides allocation:
    Option A: DCA into existing position ($100 → 1 stock)
    Option B: Start new position ($100 → new stock)
    Option C: Split across 2 positions ($50 each)
    ↓
Execute automatically
    ↓
Report to user
```

---

## 📊 Dexter's Decision Framework

### Step 1: Portfolio Health Check

**Dexter asks itself:**
```
Current Deployment: X%
Target: 80%
Gap: Need to deploy $Y more

Current Holdings: [AAPL, MSFT, GOOGL]
Quality Scores: [5/5, 4/5, 5/5]
Any thesis broken? [No, No, No]
```

### Step 2: Research Existing Holdings

**For each holding, Dexter researches:**
```
1. Recent News (web search):
   - Any moat threats?
   - Management changes?
   - Competitive pressure?

2. Latest Financials (Polygon):
   - ROE still strong?
   - Revenue growth continuing?
   - Debt increasing?

3. Valuation Check:
   - Current P/E vs historical
   - Price vs intrinsic value
   - Still fairly valued?

4. Position Size:
   - Currently X% of portfolio
   - Should increase/maintain/trim?
```

### Step 3: Scan for New Opportunities

**Dexter searches for:**
```
Quality Criteria:
- ROE >15% (10+ years)
- Strong moat (brand, network, cost)
- Low debt (<1.0 D/E)
- Profitable (margin >10%)
- Reasonable valuation (P/E <30)

Sources:
- Polygon API: Screen for fundamentals
- Web search: Find undervalued quality
- Recent news: Any new opportunities?
```

### Step 4: Make Allocation Decision

**Dexter's logic:**
```python
if deployment < 70%:
    # Under-deployed - buy aggressively
    if found_new_quality_business:
        allocation = "$100 → New Position"
    else:
        allocation = "$100 → Best Existing Position"

elif deployment > 85%:
    # Properly deployed - maintain
    allocation = "$100 → Evenly across top holdings"

elif portfolio_needs_diversification:
    # Too concentrated
    allocation = "$100 → Underweight sector"

else:
    # Normal DCA
    allocation = "$100 → Position with highest conviction"
```

---

## 🔍 Data Sources Dexter Uses

### 1. Polygon API
```
Financial Metrics:
- P/E ratio, ROE, profit margin
- Revenue growth, earnings growth
- Debt/equity, current ratio
- Price history (52-week range)

Company Info:
- Market cap, sector, industry
- Business description
- Primary exchange
```

### 2. Web Search (Tavily)
```
Recent Developments:
- Earnings reports
- Product launches
- Management changes
- Competitive threats
- Regulatory news
- Industry trends
```

### 3. Portfolio Context
```
Current State:
- Cash available: $X
- Holdings: [List with shares, entry prices]
- Total value: $Y
- Deployment: Z%
- Recent trades: [Last 10]
```

### 4. Historical Performance
```
Track Record:
- Which decisions worked?
- Which didn't?
- Learn and improve
```

---

## 💻 Implementation: Monthly Auto-Allocation

### File: `utils/dexter_allocator.py`

```python
"""
Dexter-Managed Monthly Allocation System
Dexter decides how to invest $100/month based on research
"""

from dexter_client import DexterClient
from portfolio_context import PortfolioContext
from core import StockAnalyzer
from datetime import datetime
import json


class DexterAllocator:
    """
    AI Portfolio Manager using Dexter
    Researches and decides monthly allocations
    """
    
    def __init__(self):
        self.dexter = DexterClient()
        self.portfolio = PortfolioContext()
        self.analyzer = StockAnalyzer()
    
    def monthly_allocation(self, budget: float = 100.0) -> Dict:
        """
        Main entry point: Dexter decides allocation
        
        Args:
            budget: Monthly investment amount
            
        Returns:
            Allocation decision and reasoning
        """
        # Get current portfolio state
        context = self.portfolio.get_context()
        
        # Build comprehensive research query for Dexter
        query = self._build_allocation_query(context, budget)
        
        # Dexter researches and decides
        print("🤖 Dexter is researching allocation opportunities...")
        result = self.dexter.research(query, context)
        
        # Parse Dexter's decision
        decision = self._parse_decision(result.get('answer', ''))
        
        # Execute allocation
        if decision.get('execute', False):
            execution_result = self._execute_allocation(decision, context)
            decision['execution'] = execution_result
        
        return decision
    
    def _build_allocation_query(self, context: Dict, budget: float) -> str:
        """Build research query for Dexter"""
        
        holdings = context.get('holdings', {})
        cash = context.get('cash', 0)
        total_value = context.get('total_value', 0)
        deployed_pct = ((total_value - cash) / total_value * 100) if total_value > 0 else 0
        
        # Format holdings info
        holdings_summary = ""
        if holdings:
            holdings_summary = "\n".join([
                f"  • {ticker}: {data['shares']:.2f} shares @ ${data['entry_price']:.2f} "
                f"(Value: ${data['position_value']:.2f}, {data['position_value']/total_value*100:.1f}% of portfolio)"
                for ticker, data in holdings.items()
            ])
        else:
            holdings_summary = "  No positions currently held"
        
        query = f"""You are my AI Portfolio Manager. I have ${budget:.2f} to invest this month.

YOUR JOB: Research opportunities and decide the BEST allocation.

═══════════════════════════════════════════════════════
📊 CURRENT PORTFOLIO STATE
═══════════════════════════════════════════════════════

Total Value: ${total_value:,.2f}
Cash: ${cash:.2f}
Deployment: {deployed_pct:.1f}% (target: 80%)
New Capital: ${budget:.2f}

Current Holdings:
{holdings_summary}

═══════════════════════════════════════════════════════
🎯 YOUR RESEARCH TASKS
═══════════════════════════════════════════════════════

1. REVIEW EXISTING HOLDINGS (if any):
   For each holding:
   • Search recent news (last 30 days)
   • Check latest financials via Polygon
   • Assess if thesis still valid
   • Rate current attractiveness (1-10)

2. EVALUATE DEPLOYMENT LEVEL:
   • Currently {deployed_pct:.1f}% deployed
   • Need to deploy more? Or properly allocated?
   • Any concentration risks?

3. SCAN FOR NEW OPPORTUNITIES:
   • Use Polygon to screen for quality businesses:
     - ROE >15%
     - Low debt (D/E <1.0)
     - Profitable (margin >10%)
     - Reasonable valuation (P/E 15-30)
   • Search for undervalued quality companies
   • Any businesses on sale due to market overreaction?

4. SECTOR DIVERSIFICATION:
   • Current sector allocation
   • Any gaps to fill?
   • Over-concentrated anywhere?

═══════════════════════════════════════════════════════
💡 DECISION CRITERIA (Buffett-Style)
═══════════════════════════════════════════════════════

Prefer to allocate to:
✅ Quality businesses with strong moats
✅ Undervalued relative to intrinsic value
✅ Positions that improve diversification
✅ Businesses we can hold 10+ years

Avoid:
❌ Speculative or momentum stocks
❌ Businesses we don't understand
❌ Over-concentration in one sector
❌ Chasing recent winners

═══════════════════════════════════════════════════════
📋 REQUIRED OUTPUT FORMAT
═══════════════════════════════════════════════════════

Provide your decision in this EXACT format:

**ALLOCATION DECISION**

Budget: ${budget:.2f}
Recommendation: [Single stock / Split allocation / Hold cash]

**OPTION 1: [Ticker]**
Amount: $XX.XX
Shares: X.XX shares @ $YY.YY
Reason: [2-3 sentences - why this is the best use of capital]
Research Summary:
  • Recent News: [Key findings]
  • Financials: [P/E, ROE, Growth, Debt]
  • Valuation: [Fair/Undervalued/Overvalued]
  • Moat: [Strong/Moderate/Weak]
Conviction: [High/Medium/Low]

[If split allocation, add OPTION 2]

**PORTFOLIO IMPACT**
After this allocation:
  • Deployment: {deployed_pct:.1f}% → XX%
  • Sector allocation: [Summary]
  • Position sizes: [Summary]

**REASONING**
[2-3 sentences explaining why this allocation is optimal given current market conditions and portfolio state]

**ALTERNATIVE CONSIDERED**
[Briefly mention what else you looked at and why you didn't choose it]

═══════════════════════════════════════════════════════

IMPORTANT:
• Research THOROUGHLY using all available tools
• Show your work (what you found, why it matters)
• Be data-driven (cite specific metrics)
• Think long-term (10+ years)
• Focus on BUSINESS QUALITY

Begin your research and provide allocation decision:"""

        return query
    
    def _parse_decision(self, answer: str) -> Dict:
        """Parse Dexter's allocation decision"""
        
        decision = {
            'raw_answer': answer,
            'allocations': [],
            'reasoning': '',
            'execute': False
        }
        
        # Extract tickers and amounts
        # This is simplified - in practice, use regex or structured output
        lines = answer.split('\n')
        
        for i, line in enumerate(lines):
            if 'OPTION' in line and ':' in line:
                # Found an allocation option
                ticker = line.split(':')[1].strip().split()[0].upper()
                
                # Look for amount in next few lines
                amount = 0
                shares = 0
                for j in range(i, min(i+5, len(lines))):
                    if 'Amount:' in lines[j]:
                        amount_str = lines[j].split('$')[1].split()[0]
                        amount = float(amount_str.replace(',', ''))
                    if 'shares @' in lines[j]:
                        shares = float(lines[j].split()[0])
                
                decision['allocations'].append({
                    'ticker': ticker,
                    'amount': amount,
                    'shares': shares
                })
        
        # If we found allocations, mark for execution
        if decision['allocations']:
            decision['execute'] = True
        
        return decision
    
    def _execute_allocation(self, decision: Dict, context: Dict) -> Dict:
        """Execute the allocation decision"""
        
        results = []
        
        for allocation in decision['allocations']:
            ticker = allocation['ticker']
            amount = allocation['amount']
            
            # Get current price
            try:
                fundamentals = self.analyzer.get_fundamentals(ticker)
                current_price = fundamentals.get('current_price', 0)
                
                if current_price > 0:
                    shares = amount / current_price
                    
                    # Record the allocation
                    results.append({
                        'ticker': ticker,
                        'shares': shares,
                        'price': current_price,
                        'cost': amount,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'success'
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


def run_monthly_allocation(budget: float = 100.0):
    """
    Run monthly allocation process
    
    Usage:
        result = run_monthly_allocation(100.0)
        print(result['raw_answer'])  # Dexter's full analysis
        print(result['allocations'])  # Parsed decisions
    """
    allocator = DexterAllocator()
    decision = allocator.monthly_allocation(budget)
    
    return decision


if __name__ == "__main__":
    # Test the allocator
    print("="*60)
    print("DEXTER-MANAGED MONTHLY ALLOCATION TEST")
    print("="*60)
    
    result = run_monthly_allocation(100.0)
    
    print("\n" + "="*60)
    print("DEXTER'S DECISION:")
    print("="*60)
    print(result['raw_answer'])
    
    print("\n" + "="*60)
    print("PARSED ALLOCATIONS:")
    print("="*60)
    for alloc in result['allocations']:
        print(f"  {alloc['ticker']}: ${alloc['amount']:.2f} ({alloc['shares']:.3f} shares)")
    
    if result.get('execution'):
        print("\n" + "="*60)
        print("EXECUTION RESULTS:")
        print("="*60)
        for exec_result in result['execution']:
            print(f"  {exec_result}")
```

---

## 🎨 Streamlit UI Integration

### File: `pages/05_Monthly_Allocation.py`

```python
"""
Monthly Allocation Page
Dexter decides where to invest your $100
"""

import streamlit as st
from datetime import datetime
import sys
sys.path.append('utils')

from dexter_allocator import DexterAllocator
from portfolio_context import PortfolioContext

st.set_page_config(page_title="Monthly Allocation", page_icon="💰", layout="wide")

st.title("💰 Monthly Allocation - AI Managed")
st.markdown("*Dexter researches and decides where to invest your $100*")

# Sidebar - Portfolio Summary
with st.sidebar:
    st.header("📊 Portfolio Status")
    
    portfolio = PortfolioContext()
    context = portfolio.get_context()
    
    st.metric("Total Value", f"${context['total_value']:,.2f}")
    st.metric("Cash", f"${context['cash']:,.2f}")
    
    deployed = ((context['total_value'] - context['cash']) / context['total_value'] * 100) if context['total_value'] > 0 else 0
    st.metric("Deployed", f"{deployed:.1f}%", f"Target: 80%")
    
    st.divider()
    
    st.subheader("Current Holdings")
    if context['holdings']:
        for ticker, data in context['holdings'].items():
            st.write(f"**{ticker}**: {data['shares']:.2f} shares")
    else:
        st.info("No positions yet")

# Main content
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎯 This Month's Budget")
    monthly_budget = st.number_input(
        "Amount to invest",
        min_value=10.0,
        max_value=10000.0,
        value=100.0,
        step=10.0,
        help="How much to invest this month"
    )
    
    st.info(f"""
    **How it works:**
    1. Dexter reviews your current portfolio
    2. Researches opportunities using Polygon + Web Search
    3. Decides optimal allocation
    4. Executes automatically (or shows recommendation)
    """)

with col2:
    st.subheader("⚙️ Settings")
    
    auto_execute = st.checkbox(
        "Auto-execute",
        value=False,
        help="Automatically execute Dexter's recommendation"
    )
    
    research_depth = st.select_slider(
        "Research depth",
        options=["Quick", "Standard", "Deep"],
        value="Standard"
    )

st.markdown("---")

# Action button
if st.button("🤖 Ask Dexter for Allocation Decision", type="primary", use_container_width=True):
    
    with st.spinner("🔍 Dexter is researching allocation opportunities..."):
        allocator = DexterAllocator()
        decision = allocator.monthly_allocation(monthly_budget)
    
    # Display Dexter's full analysis
    st.success("✅ Research complete!")
    
    st.subheader("📊 Dexter's Analysis")
    
    with st.expander("🔍 Full Research Report", expanded=True):
        st.markdown(decision['raw_answer'])
    
    # Display parsed allocations
    if decision['allocations']:
        st.subheader("💡 Recommended Allocation")
        
        for i, alloc in enumerate(decision['allocations'], 1):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**Option {i}: {alloc['ticker']}**")
            with col2:
                st.metric("Amount", f"${alloc['amount']:.2f}")
            with col3:
                st.metric("Shares", f"{alloc['shares']:.3f}")
        
        # Execute or show action needed
        if auto_execute and decision.get('execution'):
            st.success("✅ Allocation executed automatically!")
            
            for result in decision['execution']:
                if result['status'] == 'success':
                    st.success(f"✅ Bought {result['shares']:.3f} shares of {result['ticker']} @ ${result['price']:.2f}")
                else:
                    st.error(f"❌ Failed to buy {result['ticker']}: {result.get('reason', 'Unknown error')}")
        
        elif not auto_execute:
            st.warning("⚠️ Auto-execute is OFF - Review and manually execute if desired")
            
            if st.button("✅ Approve and Execute", type="primary"):
                # Execute here
                st.success("Executing allocation...")
                st.rerun()
    
    else:
        st.info("ℹ️ Dexter recommends holding cash this month")

# Historical allocations
st.markdown("---")
st.subheader("📜 Allocation History")

# TODO: Load from storage
st.info("Coming soon: View past allocation decisions and their performance")
```

---

## 🔄 Automated Monthly Workflow

### Option 1: Manual Trigger
User clicks button → Dexter researches → Shows decision → User approves → Executes

### Option 2: Scheduled (Recommended)
```python
# Add to background scheduler
import schedule
import time

def monthly_allocation_job():
    """Runs on 1st of each month"""
    from dexter_allocator import run_monthly_allocation
    
    print(f"Running monthly allocation: {datetime.now()}")
    result = run_monthly_allocation(100.0)
    
    # Save decision to database
    save_allocation_decision(result)
    
    # Optionally: Send email notification
    notify_user(result)

# Schedule for 1st of month at 9 AM
schedule.every().month.at("09:00").do(monthly_allocation_job)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

---

## 📋 Example Dexter Decision

```markdown
**ALLOCATION DECISION**

Budget: $100.00
Recommendation: Split allocation

**OPTION 1: AAPL**
Amount: $60.00
Shares: 0.316 shares @ $190.00
Reason: Strong ecosystem moat continues to strengthen. Recent iPhone 15 
launch exceeded expectations. Services revenue growing 15% YoY. Position 
is only 12% of portfolio - room to grow.

Research Summary:
  • Recent News: Q4 earnings beat estimates, Services hit record high
  • Financials: P/E 28.5, ROE 162%, Revenue Growth 8%, Debt/Equity 1.8
  • Valuation: Fairly valued based on DCF analysis
  • Moat: ⭐⭐⭐⭐⭐ (Ecosystem lock-in is unmatched)
Conviction: High

**OPTION 2: MSFT**
Amount: $40.00
Shares: 0.116 shares @ $345.00
Reason: Cloud (Azure) growing 28% YoY. AI integration accelerating (Copilot). 
This diversifies away from consumer tech into enterprise software.

Research Summary:
  • Recent News: Azure AI demand surging, beating Google Cloud
  • Financials: P/E 32.1, ROE 44%, Revenue Growth 13%, Debt/Equity 0.6
  • Valuation: Slightly premium but justified by AI positioning
  • Moat: ⭐⭐⭐⭐⭐ (Software ecosystem + enterprise relationships)
Conviction: High

**PORTFOLIO IMPACT**
After this allocation:
  • Deployment: 73% → 81% ✅ (hitting target!)
  • Sector allocation: Tech 100% → Need healthcare/consumer next month
  • Position sizes: AAPL 12%→13%, MSFT 0%→5%

**REASONING**
Both businesses are quality with strong moats. AAPL is existing position 
showing continued strength - good to add more. MSFT adds diversification 
within tech (enterprise vs consumer) and positions us for AI revolution. 
Split allocation reduces single-stock risk while maintaining quality focus.

**ALTERNATIVE CONSIDERED**
Considered putting full $100 into AAPL for simplicity, but MSFT's AI 
positioning too compelling to ignore. Also looked at starting healthcare 
position (JNJ) but deployment only 73% - need to get to 80% first, 
then can diversify sectors.
```

---

## ✅ Verification & Tracking

### Track Dexter's Performance

```python
# After each allocation, track:
allocation_record = {
    'date': '2025-12-01',
    'budget': 100.00,
    'dexter_decision': {
        'AAPL': {'amount': 60, 'shares': 0.316, 'price': 190.00},
        'MSFT': {'amount': 40, 'shares': 0.116, 'price': 345.00}
    },
    'reasoning': 'Dexter chose AAPL for moat strength, MSFT for AI positioning',
    'conviction': 'High'
}

# After 3 months, review performance:
- Did allocations work out?
- What worked / didn't work?
- Adjust Dexter's prompts if needed
```

---

## 🎯 Expected Behavior

### Month 1: Building First Position
```
Dexter: "Portfolio empty. Deploy $100 to highest-quality business found."
Decision: $100 → AAPL (strongest moat identified)
Result: 0.526 shares of AAPL
```

### Month 2: Continue DCA
```
Dexter: "AAPL thesis still valid. News positive. Continue building."
Decision: $100 → AAPL
Result: 0.526 shares more (total: 1.052 shares)
```

### Month 3: Diversification
```
Dexter: "AAPL now 15% of portfolio. Time to diversify."
Decision: $100 → MSFT (add new quality business)
Result: 0.290 shares of MSFT (now 2 holdings)
```

### Month 6: Market Dip
```
Dexter: "AAPL down 15% on market selloff. Fundamentals strong. BUY MORE!"
Decision: $100 → AAPL (accelerate DCA)
Result: 0.625 shares at lower price (lowering avg cost)
```

### Month 12: Proper Deployment
```
Dexter: "Portfolio at 82% deployed with 4 quality holdings. Maintain."
Decision: $60 → AAPL, $40 → New position (diversify)
Result: Balanced allocation maintaining 80% deployment
```

---

## 🚀 Implementation Checklist

- [ ] Create `utils/dexter_allocator.py`
- [ ] Create `pages/05_Monthly_Allocation.py`
- [ ] Test allocation query with Dexter
- [ ] Verify Dexter accesses Polygon data
- [ ] Confirm web search works
- [ ] Add execution logic
- [ ] Set up monthly scheduling (optional)
- [ ] Create allocation history tracking

---

## 💡 Key Benefits

**For You:**
- ✅ Hands-off investing ($100/month on autopilot)
- ✅ AI-driven decisions (data, not emotions)
- ✅ Research-backed (Polygon + web + SEC)
- ✅ Buffett philosophy (quality businesses forever)

**Dexter's Advantages:**
- 🤖 Multi-agent research (Planning → Action → Validation → Answer)
- 📊 Access to all data sources
- 🔍 Can read news, financials, trends
- 💡 Learns over time (track what works)
- 🎯 Portfolio-aware (considers current holdings)

**Result:**
- Professional-grade portfolio management
- Systematic, disciplined allocation
- Focus on business quality
- Long-term wealth building

---

**Ready to implement? I can create the actual files or help with testing!** 🚀
