"""
Chat with Dexter - AI Research Assistant
Portfolio-aware conversational interface
"""

import streamlit as st
import sys
import time
from pathlib import Path
from typing import Dict
from datetime import datetime
import re

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / 'utils'))

from dexter_client import DexterClient, ask_dexter
from portfolio_context import PortfolioContext
from dexter_manager import DexterManager, ensure_dexter_running
from polygon_fetcher import PolygonFetcher

# Page config
st.set_page_config(
    page_title="Chat with Dexter",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #2b313e;
        margin-left: 2rem;
    }
    .dexter-message {
        background-color: #1e2936;
        margin-right: 2rem;
    }
    .portfolio-summary {
        background-color: #1a1f2e;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 3px solid #00d4aa;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🤖 Chat with Dexter")
st.markdown("*AI Research Assistant with Multi-Agent Intelligence*")

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Always recreate client to get latest port detection
if 'dexter_client' not in st.session_state:
    st.session_state.dexter_client = DexterClient()
else:
    # Force health check to detect port on each check
    pass  # Health check will auto-detect port

if 'portfolio_context' not in st.session_state:
    st.session_state.portfolio_context = PortfolioContext()

# Sidebar - Portfolio Summary
with st.sidebar:
    st.header("📊 Your Portfolio")
    
    # Refresh button
    if st.button("🔄 Refresh Portfolio", use_container_width=True):
        st.session_state.portfolio_context = PortfolioContext()
        st.rerun()
    
    # Display portfolio summary
    portfolio_summary = st.session_state.portfolio_context.get_summary_text()
    st.markdown(f'<div class="portfolio-summary">{portfolio_summary}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Dexter status
    st.header("🔌 Dexter Status")
    
    # Auto-start Dexter if not running
    try:
        if 'dexter_manager' not in st.session_state:
            st.session_state.dexter_manager = DexterManager()
        
        is_running = st.session_state.dexter_client.health_check()
        
        if is_running:
            st.success("✅ Connected")
        else:
            st.warning("⚠️ Not Running")
            
            # Auto-start button - always show when not running
            st.markdown("---")
            # Debug: Show button prominently
            st.markdown("### Start Dexter Service")
            auto_start_clicked = st.button("🚀 Auto-Start Dexter", use_container_width=True, type="primary", key="auto_start_dexter")
            
            if auto_start_clicked:
                with st.spinner("Starting Dexter service..."):
                    try:
                        success, message = st.session_state.dexter_manager.start(wait_for_ready=True, timeout=60)
                        if success:
                            st.success(f"✅ {message}")
                            time.sleep(2)  # Give it a moment to be ready
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            st.info("""
                            **Manual Start:**
                            ```bash
                            cd NewsAdmin
                            npm run dev
                            ```
                            """)
                    except Exception as e:
                        st.error(f"Error starting Dexter: {str(e)}")
                        st.info("""
                        **Manual Start:**
                        ```bash
                        cd NewsAdmin
                        npm run dev
                        ```
                        """)
            else:
                st.info("""
                **Click "Auto-Start Dexter" above, or manually start:**
                ```bash
                cd NewsAdmin
                npm run dev
                ```
                """)
    except Exception as e:
        st.error(f"Error initializing Dexter manager: {str(e)}")
        st.info("""
        **Manual Start:**
        ```bash
        cd NewsAdmin
        npm run dev
        ```
        """)
    
    st.divider()
    
    # Quick actions
    st.header("⚡ Quick Actions")
    
    if st.button("📈 Analyze Portfolio", use_container_width=True):
        with st.spinner("Dexter is analyzing your portfolio..."):
            context = st.session_state.portfolio_context.get_context()
            result = st.session_state.dexter_client.portfolio_analysis(context)
            
            st.session_state.chat_history.append({
                'role': 'user',
                'content': 'Analyze my portfolio'
            })
            st.session_state.chat_history.append({
                'role': 'dexter',
                'content': result.get('answer', 'No response'),
                'iterations': result.get('iterations', 0),
                'tasks': len(result.get('plan', {}).get('tasks', []))
            })
            st.rerun()
    
    if st.button("💡 Get Recommendations", use_container_width=True):
        with st.spinner("Dexter is finding opportunities..."):
            context = st.session_state.portfolio_context.get_context()
            query = "What stocks should I consider adding to my portfolio given my current holdings?"
            # Use longer timeout for deep research queries
            timeout = 180 if any(keyword in query.lower() for keyword in ['deep', 'moat', '10-year', 'business analysis', 'management']) else 120
            result = st.session_state.dexter_client.research(query, context, timeout=timeout)
            
            st.session_state.chat_history.append({
                'role': 'user',
                'content': query
            })
            st.session_state.chat_history.append({
                'role': 'dexter',
                'content': result.get('answer', 'No response'),
                'iterations': result.get('iterations', 0),
                'tasks': len(result.get('plan', {}).get('tasks', []))
            })
            st.rerun()
    
    if st.button("🎯 Risk Analysis", use_container_width=True):
        with st.spinner("Dexter is assessing risk..."):
            context = st.session_state.portfolio_context.get_context()
            query = "Analyze the risk profile of my portfolio. What are the main risks?"
            # Use longer timeout for deep research queries
            timeout = 180 if any(keyword in query.lower() for keyword in ['deep', 'moat', '10-year', 'business analysis', 'management']) else 120
            result = st.session_state.dexter_client.research(query, context, timeout=timeout)
            
            st.session_state.chat_history.append({
                'role': 'user',
                'content': query
            })
            st.session_state.chat_history.append({
                'role': 'dexter',
                'content': result.get('answer', 'No response'),
                'iterations': result.get('iterations', 0),
                'tasks': len(result.get('plan', {}).get('tasks', []))
            })
            st.rerun()
    
    st.divider()
    
    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Main chat area
st.markdown("---")

# Display chat history
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Dexter response - render as markdown for proper formatting
            st.markdown("**🤖 Dexter:**")
            # Use st.markdown to properly render the response (fixes formatting issues)
            st.markdown(message['content'], unsafe_allow_html=False)
            
            # Show research metadata
            if 'iterations' in message:
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"🔄 Research Iterations: {message['iterations']}")
                with col2:
                    st.caption(f"✅ Tasks Completed: {message.get('tasks', 0)}")
else:
    # Welcome message
    st.info("""
    👋 **Welcome to Dexter!**
    
    I'm your AI research assistant powered by multi-agent intelligence. I can help you with:
    
    - 📊 **Portfolio Analysis** - Review your holdings and suggest improvements
    - 🔍 **Stock Research** - Deep dive into any company's financials and prospects
    - 💡 **Investment Ideas** - Find opportunities that complement your portfolio
    - 📈 **Strategy Development** - Plan your investment approach
    - 🎯 **Risk Assessment** - Understand and manage portfolio risk
    
    **Try asking:**
    - "Should I buy more NVDA?"
    - "What's the best growth stock for my portfolio?"
    - "How do I reduce risk?"
    - "Compare AAPL vs MSFT for long-term investment"
    
    *I'm aware of your current cash and holdings!*
    """)

# Chat input
st.markdown("---")

# Example queries
with st.expander("💡 Example Questions"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Portfolio-Specific:**
        - Should I rebalance my portfolio?
        - What should I buy with my available cash?
        - Which of my holdings should I sell?
        - Is my portfolio too concentrated?
        """)
    
    with col2:
        st.markdown("""
        **Stock Research:**
        - Analyze NVDA in detail
        - Compare TSLA vs traditional auto makers
        - What are the risks with AAPL?
        - Is JPM a good buy right now?
        """)

# Input form
with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_area(
        "Ask Dexter anything...",
        placeholder="e.g., Should I buy more NVDA?",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        submit_button = st.form_submit_button("💬 Send", use_container_width=True)
    
    with col2:
        include_portfolio = st.form_submit_button("📊 Send with Portfolio", use_container_width=True)

# Helper function to extract tickers and fetch current data
def extract_tickers_and_fetch_data(query: str) -> Dict:
    """
    Extract stock tickers from query and fetch current data from Polygon
    Returns dict with current stock data to include in context
    """
    # Pattern to match stock tickers (1-5 uppercase letters, possibly with $ prefix)
    ticker_pattern = r'\$?([A-Z]{1,5})\b'
    matches = re.findall(ticker_pattern, query.upper())
    
    # Filter out common words that match ticker pattern
    common_words = {'I', 'A', 'AM', 'IS', 'IT', 'AN', 'AS', 'AT', 'BE', 'BY', 'DO', 'GO', 'IF', 'IN', 'ME', 'MY', 'NO', 'OF', 'ON', 'OR', 'SO', 'TO', 'UP', 'US', 'WE', 'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE'}
    tickers = [t for t in set(matches) if t not in common_words and len(t) >= 1]
    
    if not tickers:
        return {}
    
    # Fetch current data for each ticker
    fetcher = PolygonFetcher()
    stock_data = {}
    
    for ticker in tickers[:5]:  # Limit to 5 tickers to avoid rate limits
        try:
            # Get current quote
            quote = fetcher.get_stock_quote(ticker)
            if quote:
                stock_data[ticker] = {
                    'current_price': quote.get('current_price', 0),
                    'volume': quote.get('volume', 0),
                    'high': quote.get('high', 0),
                    'low': quote.get('low', 0),
                    'open': quote.get('open', 0),
                    'timestamp': quote.get('timestamp', 0),
                    'source': 'polygon_current'
                }
            
            # Get company details
            details = fetcher.get_stock_details(ticker)
            if details:
                if ticker not in stock_data:
                    stock_data[ticker] = {}
                stock_data[ticker].update({
                    'name': details.get('name', ticker),
                    'market_cap': details.get('market_cap', 0),
                    'description': details.get('description', ''),
                    'exchange': details.get('primary_exchange', '')
                })
            
            # Get comprehensive price history (1 year for full context)
            history_1y = fetcher.get_price_history(ticker, days=365)
            if history_1y and history_1y.get('bars'):
                bars = history_1y['bars']
                if ticker not in stock_data:
                    stock_data[ticker] = {}
                
                # Calculate key metrics
                closes = [b.get('close', 0) for b in bars if b.get('close', 0) > 0]
                if closes:
                    stock_data[ticker]['price_history'] = {
                        'latest_close': closes[-1],
                        'latest_date': bars[-1].get('date', '') if bars else '',
                        'year_ago_price': closes[0] if len(closes) > 0 else 0,
                        'year_ago_date': bars[0].get('date', '') if bars else '',
                        '52_week_high': max(closes),
                        '52_week_low': min(closes),
                        'total_bars': len(bars),
                        'price_change_1y': ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0,
                        'all_prices': closes  # Full price series for analysis
                    }
            
            # Get financials data (P/E, ROE, revenue growth, etc.)
            try:
                from utils.core import StockAnalyzer
                analyzer = StockAnalyzer()
                fundamentals = analyzer.get_fundamentals(ticker)
                if fundamentals and ticker not in stock_data:
                    stock_data[ticker] = {}
                if fundamentals:
                    stock_data[ticker]['fundamentals'] = {
                        'pe_ratio': fundamentals.get('pe_ratio', 0),
                        'roe': fundamentals.get('roe', 0),
                        'revenue_growth': fundamentals.get('revenue_growth', 0),
                        'earnings_growth': fundamentals.get('earnings_growth', 0),
                        'profit_margin': fundamentals.get('profit_margin', 0),
                        'current_ratio': fundamentals.get('current_ratio', 0),
                        'debt_to_equity': fundamentals.get('debt_to_equity', 0),
                        'market_cap': fundamentals.get('market_cap', 0),
                        'sector': fundamentals.get('sector', ''),
                        'industry': fundamentals.get('industry', '')
                    }
            except Exception as e:
                # If fundamentals fail, continue without them
                pass
                
        except Exception as e:
            st.warning(f"Could not fetch current data for {ticker}: {str(e)}")
            continue
    
    return stock_data

# Handle submission
if (submit_button or include_portfolio) and user_input:
    # Add user message to history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input
    })
    
    # Extract tickers and fetch current data
    current_stock_data = extract_tickers_and_fetch_data(user_input)
    
    # Get portfolio context (always include for hedge fund manager role)
    context = st.session_state.portfolio_context.get_context()
    
    # Add risk settings and monthly contribution info
    try:
        from utils.storage import StorageManager
        storage = StorageManager()
        portfolio = storage.load_portfolio()
        if portfolio:
            context['risk_settings'] = portfolio.get('settings', {
                'max_loss_per_trade': 2.0,
                'max_position_size_pct': 20.0,
                'min_stock_score': 80
            })
            context['monthly_contribution'] = portfolio.get('monthly_contribution', 100)
    except:
        context['risk_settings'] = {'max_loss_per_trade': 2.0, 'max_position_size_pct': 20.0}
        context['monthly_contribution'] = 100
    
    # Add current stock data to context so Dexter uses fresh data
    if current_stock_data:
        if 'current_stock_data' not in context:
            context['current_stock_data'] = {}
        context['current_stock_data'].update(current_stock_data)
        
        # Build comprehensive data summary for Dexter
        data_summary = []
        for ticker, data in current_stock_data.items():
            price = data.get('current_price', 0)
            name = data.get('name', ticker)
            price_info = f"{ticker} ({name}): ${price:.2f}"
            
            # Add price history if available
            if 'price_history' in data:
                ph = data['price_history']
                price_info += f"\n  - 1-Year History: ${ph.get('year_ago_price', 0):.2f} ({ph.get('year_ago_date', '')}) → ${ph.get('latest_close', 0):.2f} ({ph.get('latest_date', '')})"
                price_info += f"\n  - 52W High: ${ph.get('52_week_high', 0):.2f} | 52W Low: ${ph.get('52_week_low', 0):.2f}"
                price_info += f"\n  - 1-Year Return: {ph.get('price_change_1y', 0):+.1f}%"
                price_info += f"\n  - Data Points: {ph.get('total_bars', 0)} trading days"
            
            # Add fundamentals if available
            if 'fundamentals' in data:
                fund = data['fundamentals']
                price_info += f"\n  - P/E Ratio: {fund.get('pe_ratio', 0):.2f} | ROE: {fund.get('roe', 0):.1f}%"
                price_info += f"\n  - Revenue Growth: {fund.get('revenue_growth', 0):+.1f}% | Earnings Growth: {fund.get('earnings_growth', 0):+.1f}%"
                price_info += f"\n  - Profit Margin: {fund.get('profit_margin', 0):.1f}% | Sector: {fund.get('sector', 'N/A')}"
            
            data_summary.append(price_info)
        
        # Build hedge fund manager instructions with context values
        cash_available = context.get('cash', 0)
        monthly_contrib = context.get('monthly_contribution', 100)
        total_value = context.get('total_value', cash_available)
        holdings_list = list(context.get('holdings', {}).keys())
        holdings_text = ', '.join(holdings_list) if holdings_list else 'None'
        
        # Calculate reasonable position sizing limits
        max_position_pct = context.get('risk_settings', {}).get('max_position_size_pct', 20.0)
        max_position_value = total_value * (max_position_pct / 100)
        # Reserve at least 20% of cash for other opportunities
        available_for_this_trade = min(cash_available * 0.8, max_position_value)
        
        hedge_fund_instructions = f"""
[YOUR ROLE: HEDGE FUND MANAGER]
You are the AI hedge fund manager for this portfolio. Your job is to provide ACTIONABLE investment recommendations.

PORTFOLIO STATUS:
- Available Cash: ${cash_available:,.2f}
- Total Portfolio Value: ${total_value:,.2f}
- Monthly Contribution Capacity: ${monthly_contrib:,.2f}/month (recurring)
- Current Holdings: {holdings_text}
- Maximum Position Size: {max_position_pct}% of portfolio (${max_position_value:,.2f})
- Recommended Max for This Trade: ${available_for_this_trade:,.2f} (leaves room for diversification)

CRITICAL POSITION SIZING RULES:
1. **NEVER suggest using ALL available cash on one trade**
2. **Reserve at least 20% of cash for other opportunities** (diversification)
3. **Maximum position size: {max_position_pct}% of total portfolio** (${max_position_value:,.2f})
4. **For this specific trade, suggest no more than: ${available_for_this_trade:,.2f}**
5. **If stock price > ${monthly_contrib:.0f}, suggest DCA over multiple months** (don't wait to save up)

REQUIRED OUTPUT FORMAT:
1. **RECOMMENDATION:** [BUY / SELL / HOLD / AVOID] - [One sentence summary]
2. **POSITION SIZING:** 
   - Recommended investment amount: $[XXX.XX] (MUST be ≤ ${available_for_this_trade:,.2f})
   - Number of shares: [X] shares
   - Position size as % of portfolio: [X]% (MUST be ≤ {max_position_pct}%)
   - Remaining cash after this trade: $[XXX.XX] (for other opportunities)
3. **DOLLAR-COST AVERAGING (DCA) PLAN:**
   - **IMPORTANT:** User adds ${monthly_contrib:.2f} per month to portfolio
   - **If stock price > ${monthly_contrib:.0f}:** Suggest DCA strategy that uses PART of monthly contribution
   - **Example for expensive stocks:** "Invest ${monthly_contrib * 0.5:.0f} per month for X months" (leaves ${monthly_contrib * 0.5:.0f}/month for other trades)
   - **Example for affordable stocks:** "Invest ${monthly_contrib * 0.3:.0f} per month for X months" (leaves ${monthly_contrib * 0.7:.0f}/month for diversification)
   - **Goal:** Build position gradually while maintaining ability to invest in other opportunities
   - **Never suggest using 100% of monthly contribution on one stock**
4. **ENTRY/EXIT STRATEGY:**
   - Entry price: $[X.XX] (current or target)
   - Stop-loss: $[X.XX] (-[X]%)
   - Target price: $[X.XX] (+[X]%)
   - Time horizon: [Short-term / Medium-term / Long-term]
5. **RISK ASSESSMENT:**
   - Maximum risk per trade: [X]% of portfolio
   - Portfolio fit: [How this fits with current holdings: {holdings_text}]
   - Diversification note: [Why leaving cash for other trades is important]
6. **COMPANY OVERVIEW:** [What the company does - REQUIRED in every response]

IMPORTANT:
- **NEVER suggest using all ${cash_available:,.2f} cash on one trade**
- **Always leave at least 20% of cash available** for other opportunities
- **For expensive stocks (price > ${monthly_contrib:.0f}), suggest DCA using PART of monthly contribution**
- **Example:** If monthly contribution is ${monthly_contrib:.2f}, suggest using ${monthly_contrib * 0.4:.0f}-${monthly_contrib * 0.6:.0f} per month for this stock, leaving the rest for other trades
- Make clear BUY/SELL/HOLD recommendations
- Use CURRENT stock prices from the data provided below
- Consider diversification with current holdings: {holdings_text}
- **DO NOT mention "missing data" or "incomplete historical data"** - you have current data from Polygon API
- **Focus on actionable recommendations** using the current data available
"""
        
        if data_summary:
            enhanced_query = f"""{user_input}

{hedge_fund_instructions}

[COMPREHENSIVE STOCK DATA (from Polygon API, {datetime.now().strftime("%Y-%m-%d")}):]
""" + "\n".join(data_summary) + f"""

[DATA AVAILABILITY:]
- Current Price: Real-time as of {datetime.now().strftime("%Y-%m-%d")}
- Historical Data: Full 1-year price history with {len(current_stock_data)} stock(s) analyzed
- Financial Metrics: P/E, ROE, Revenue Growth, Earnings Growth, Profit Margins included
- Company Details: Market cap, sector, industry, business description included
- Price Trends: 52-week high/low, year-over-year returns calculated

[ANALYSIS INSTRUCTIONS:]
- Use the comprehensive data above for your analysis
- You have 1-year price history, not just recent data
- Financial metrics are current and available
- Focus on actionable recommendations using this complete dataset
- If forward guidance or competitive data is needed, note it as a research recommendation (not a data limitation)
- Only mention limitations if they are investment risks (regulatory, competitive threats), not data availability
"""
        else:
            # No stock data detected, but still include hedge fund instructions
            cash_available = context.get('cash', 0)
            monthly_contrib = context.get('monthly_contribution', 100)
            total_value = context.get('total_value', cash_available)
            holdings_list = list(context.get('holdings', {}).keys())
            holdings_text = ', '.join(holdings_list) if holdings_list else 'None'
            
            # Calculate reasonable position sizing limits
            max_position_pct = context.get('risk_settings', {}).get('max_position_size_pct', 20.0)
            max_position_value = total_value * (max_position_pct / 100)
            # Reserve at least 20% of cash for other opportunities
            available_for_this_trade = min(cash_available * 0.8, max_position_value)
            
            hedge_fund_instructions_no_data = f"""
[YOUR ROLE: HEDGE FUND MANAGER]
You are the AI hedge fund manager for this portfolio. Your job is to provide ACTIONABLE investment recommendations.

PORTFOLIO STATUS:
- Available Cash: ${cash_available:,.2f}
- Total Portfolio Value: ${total_value:,.2f}
- Monthly Contribution Capacity: ${monthly_contrib:,.2f}/month (recurring)
- Current Holdings: {holdings_text}
- Maximum Position Size: {max_position_pct}% of portfolio (${max_position_value:,.2f})
- Recommended Max for This Trade: ${available_for_this_trade:,.2f} (leaves room for diversification)

CRITICAL POSITION SIZING RULES:
1. **NEVER suggest using ALL available cash on one trade**
2. **Reserve at least 20% of cash for other opportunities** (diversification)
3. **Maximum position size: {max_position_pct}% of total portfolio** (${max_position_value:,.2f})
4. **For this specific trade, suggest no more than: ${available_for_this_trade:,.2f}**
5. **If stock price > ${monthly_contrib:.0f}, suggest DCA over multiple months** (don't wait to save up)

REQUIRED OUTPUT FORMAT:
1. **RECOMMENDATION:** [BUY / SELL / HOLD / AVOID] - [One sentence summary]
2. **POSITION SIZING:** 
   - Recommended investment amount: $[XXX.XX] (MUST be ≤ ${available_for_this_trade:,.2f})
   - Number of shares: [X] shares
   - Position size as % of portfolio: [X]% (MUST be ≤ {max_position_pct}%)
   - Remaining cash after this trade: $[XXX.XX] (for other opportunities)
3. **DOLLAR-COST AVERAGING (DCA) PLAN:**
   - **IMPORTANT:** User adds ${monthly_contrib:.2f} per month to portfolio
   - **If stock price > ${monthly_contrib:.0f}:** Suggest DCA strategy that uses PART of monthly contribution
   - **Example for expensive stocks:** "Invest ${monthly_contrib * 0.5:.0f} per month for X months" (leaves ${monthly_contrib * 0.5:.0f}/month for other trades)
   - **Example for affordable stocks:** "Invest ${monthly_contrib * 0.3:.0f} per month for X months" (leaves ${monthly_contrib * 0.7:.0f}/month for diversification)
   - **Goal:** Build position gradually while maintaining ability to invest in other opportunities
   - **Never suggest using 100% of monthly contribution on one stock**
4. **ENTRY/EXIT STRATEGY:**
   - Entry price: $[X.XX] (current or target)
   - Stop-loss: $[X.XX] (-[X]%)
   - Target price: $[X.XX] (+[X]%)
   - Time horizon: [Short-term / Medium-term / Long-term]
5. **RISK ASSESSMENT:**
   - Maximum risk per trade: [X]% of portfolio
   - Portfolio fit: [How this fits with current holdings: {holdings_text}]
   - Diversification note: [Why leaving cash for other trades is important]
6. **COMPANY OVERVIEW:** [What the company does - REQUIRED in every response]

IMPORTANT:
- **NEVER suggest using all ${cash_available:,.2f} cash on one trade**
- **Always leave at least 20% of cash available** for other opportunities
- **For expensive stocks (price > ${monthly_contrib:.0f}), suggest DCA using PART of monthly contribution**
- **Example:** If monthly contribution is ${monthly_contrib:.2f}, suggest using ${monthly_contrib * 0.4:.0f}-${monthly_contrib * 0.6:.0f} per month for this stock, leaving the rest for other trades
- Make clear BUY/SELL/HOLD recommendations
- Fetch CURRENT stock prices from Polygon API (do not use old cached data)
- Consider diversification with current holdings: {holdings_text}
"""
            enhanced_query = f"{user_input}\n\n{hedge_fund_instructions_no_data}"
    else:
        # No stock data detected, but still include hedge fund instructions
        cash_available = context.get('cash', 0)
        monthly_contrib = context.get('monthly_contribution', 100)
        total_value = context.get('total_value', cash_available)
        holdings_list = list(context.get('holdings', {}).keys())
        holdings_text = ', '.join(holdings_list) if holdings_list else 'None'
        
        # Calculate reasonable position sizing limits
        max_position_pct = context.get('risk_settings', {}).get('max_position_size_pct', 20.0)
        max_position_value = total_value * (max_position_pct / 100)
        # Reserve at least 20% of cash for other opportunities
        available_for_this_trade = min(cash_available * 0.8, max_position_value)
        
        hedge_fund_instructions_no_data = f"""
[YOUR ROLE: HEDGE FUND MANAGER]
You are the AI hedge fund manager for this portfolio. Your job is to provide ACTIONABLE investment recommendations.

PORTFOLIO STATUS:
- Available Cash: ${cash_available:,.2f}
- Total Portfolio Value: ${total_value:,.2f}
- Monthly Contribution Capacity: ${monthly_contrib:,.2f}/month (recurring)
- Current Holdings: {holdings_text}
- Maximum Position Size: {max_position_pct}% of portfolio (${max_position_value:,.2f})
- Recommended Max for This Trade: ${available_for_this_trade:,.2f} (leaves room for diversification)

CRITICAL POSITION SIZING RULES:
1. **NEVER suggest using ALL available cash on one trade**
2. **Reserve at least 20% of cash for other opportunities** (diversification)
3. **Maximum position size: {max_position_pct}% of total portfolio** (${max_position_value:,.2f})
4. **For this specific trade, suggest no more than: ${available_for_this_trade:,.2f}**
5. **If stock price > ${monthly_contrib:.0f}, suggest DCA over multiple months** (don't wait to save up)

REQUIRED OUTPUT FORMAT:
1. **RECOMMENDATION:** [BUY / SELL / HOLD / AVOID] - [One sentence summary]
2. **POSITION SIZING:** 
   - Recommended investment amount: $[XXX.XX] (MUST be ≤ ${available_for_this_trade:,.2f})
   - Number of shares: [X] shares
   - Position size as % of portfolio: [X]% (MUST be ≤ {max_position_pct}%)
   - Remaining cash after this trade: $[XXX.XX] (for other opportunities)
3. **DOLLAR-COST AVERAGING (DCA) PLAN:**
   - **IMPORTANT:** User adds ${monthly_contrib:.2f} per month to portfolio
   - **If stock price > ${monthly_contrib:.0f}:** Suggest DCA strategy that uses PART of monthly contribution
   - **Example for expensive stocks:** "Invest ${monthly_contrib * 0.5:.0f} per month for X months" (leaves ${monthly_contrib * 0.5:.0f}/month for other trades)
   - **Example for affordable stocks:** "Invest ${monthly_contrib * 0.3:.0f} per month for X months" (leaves ${monthly_contrib * 0.7:.0f}/month for diversification)
   - **Goal:** Build position gradually while maintaining ability to invest in other opportunities
   - **Never suggest using 100% of monthly contribution on one stock**
4. **ENTRY/EXIT STRATEGY:**
   - Entry price: $[X.XX] (current or target)
   - Stop-loss: $[X.XX] (-[X]%)
   - Target price: $[X.XX] (+[X]%)
   - Time horizon: [Short-term / Medium-term / Long-term]
5. **RISK ASSESSMENT:**
   - Maximum risk per trade: [X]% of portfolio
   - Portfolio fit: [How this fits with current holdings: {holdings_text}]
   - Diversification note: [Why leaving cash for other trades is important]
6. **COMPANY OVERVIEW:** [What the company does - REQUIRED in every response]

IMPORTANT:
- **NEVER suggest using all ${cash_available:,.2f} cash on one trade**
- **Always leave at least 20% of cash available** for other opportunities
- **For expensive stocks (price > ${monthly_contrib:.0f}), suggest DCA using PART of monthly contribution**
- **Example:** If monthly contribution is ${monthly_contrib:.2f}, suggest using ${monthly_contrib * 0.4:.0f}-${monthly_contrib * 0.6:.0f} per month for this stock, leaving the rest for other trades
- Make clear BUY/SELL/HOLD recommendations
- Fetch CURRENT stock prices from Polygon API (do not use old cached data)
- Consider diversification with current holdings: {holdings_text}
"""
        enhanced_query = f"{user_input}\n\n{hedge_fund_instructions_no_data}"
    
    # Show thinking indicator
    with st.spinner("🤖 Dexter is researching with current data... (Deep research may take 2-3 minutes)"):
        # Get Dexter's response - use longer timeout for deep research
        timeout = 180 if any(keyword in user_input.lower() for keyword in ['deep', 'moat', '10-year', 'business analysis', 'management', 'competitive']) else 120
        result = st.session_state.dexter_client.research(
            enhanced_query,
            portfolio_context=context,
            timeout=timeout
        )
        
        # Add Dexter's response to history
        st.session_state.chat_history.append({
            'role': 'dexter',
            'content': result.get('answer', 'No response received'),
            'iterations': result.get('iterations', 0),
            'tasks': len(result.get('plan', {}).get('tasks', [])) if result.get('plan') else 0
        })
    
    # Rerun to show new messages
    st.rerun()

# Research examples
st.markdown("---")

with st.expander("📚 Research Capabilities"):
    st.markdown("""
    **What makes Dexter different?**
    
    Dexter uses a **multi-agent system** that:
    
    1. 🧠 **Planning Agent** - Breaks your question into specific research tasks
    2. ⚡ **Action Agent** - Executes tasks using Polygon API and web search
    3. ✅ **Validation Agent** - Ensures data is complete and sufficient
    4. 📝 **Answer Agent** - Synthesizes findings into comprehensive response
    
    **Data Sources:**
    - Polygon API for stock data and financials
    - Web search for recent news and context
    - Your portfolio data for personalized advice
    
    **Example Research Flow:**
    
    *You ask:* "Should I buy TSLA?"
    
    *Dexter:*
    1. Fetches TSLA financials (Q1-Q4 2024)
    2. Searches recent TSLA news
    3. Analyzes your current portfolio composition
    4. Compares TSLA to your existing holdings
    5. Calculates position sizing based on your cash
    6. Synthesizes recommendation with data backing
    
    *Result:* Comprehensive answer in ~10-30 seconds
    """)

# Footer
st.markdown("---")
st.caption("🤖 Dexter AI | Multi-Agent Research System | Powered by Grok-3")
