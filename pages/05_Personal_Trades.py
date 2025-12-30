"""
Personal Trades - Track and manage your trades with Dexter AI
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.storage import StorageManager
from utils import AIPortfolioManager, BuffettPortfolioManager
from utils.core import StockAnalyzer
from utils.dexter_client import DexterClient
from utils.portfolio_context import PortfolioContext
from utils.polygon_fetcher import PolygonFetcher

st.set_page_config(page_title="Personal Trades", page_icon="📋", layout="wide")

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.title("📋 Personal Trades")
st.markdown("*Track your trades with AI-powered management and insights*")

# Initialize
storage = StorageManager()
portfolio_manager = AIPortfolioManager(storage)
buffett_manager = BuffettPortfolioManager(storage)
analyzer = StockAnalyzer()
portfolio = storage.load_portfolio()

if portfolio is None:
    st.info("👈 Initialize your portfolio in the Auto Trading Hub to start tracking trades")
else:
    # Get portfolio metrics with deployment percentage
    if portfolio.get("philosophy") == "Buffett Buy-and-Hold":
        metrics = buffett_manager.get_portfolio_metrics(portfolio)
        portfolio_value = metrics["total_value"]
        current_cash = metrics["cash"]
        deployed_pct = metrics["deployed_pct"]
        target_deployment = metrics["target_deployment"]
        deployment_gap = metrics["deployment_gap"]
    else:
        # Fallback for non-Buffett portfolios
        portfolio_value = portfolio_manager.get_portfolio_value(portfolio)
        current_cash = portfolio.get("current_cash", 0)
        positions = portfolio.get("positions", {})
        total_position_value = sum(
            pos.get("entry_price", 0) * pos.get("shares", 0) 
            for pos in positions.values()
        )
        total_value = current_cash + total_position_value
        deployed_pct = (total_position_value / total_value * 100) if total_value > 0 else 0
        target_deployment = 80
        deployment_gap = deployed_pct - target_deployment
    
    positions = portfolio.get("positions", {})
    trade_history = portfolio.get("trade_history", [])
    
    # Header metrics with deployment
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Portfolio Value", f"${portfolio_value:,.2f}")
    with col2:
        st.metric("Cash Available", f"${current_cash:,.2f}")
    with col3:
        # Deployment metric with color coding
        delta_color = "normal" if abs(deployment_gap) < 10 else ("inverse" if deployment_gap < -10 else "off")
        st.metric(
            "Deployment",
            f"{deployed_pct:.1f}%",
            f"Target: {target_deployment}%",
            delta_color=delta_color
        )
    with col4:
        st.metric("Active Positions", len(positions))
    with col5:
        total_trades = len(trade_history)
        st.metric("Total Trades", total_trades)
    
    # Deployment status alert
    if deployment_gap < -10:
        st.warning(f"⚠️ Under-deployed: {abs(deployment_gap):.1f}% below target. Consider deploying cash into quality businesses.")
    elif deployment_gap > 10:
        st.info(f"ℹ️ Over-deployed: {deployment_gap:.1f}% above target. Consider building cash reserves.")
    else:
        st.success(f"✅ Properly deployed: Within {abs(deployment_gap):.1f}% of {target_deployment}% target")
    
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Active Positions",
        "📈 Trade History",
        "📰 News & SEC Filings",
        "📊 Portfolio vs Market"
    ])
    
    # ============ TAB 1: ACTIVE POSITIONS ============
    with tab1:
        st.subheader("📊 Active Positions - Managed by Dexter")
        
        if positions:
            # Fetch current prices and calculate P/L
            positions_data = []
            for ticker, pos in positions.items():
                try:
                    fund = analyzer.get_fundamentals(ticker)
                    current_price = fund.get("current_price", pos.get("entry_price", 0))
                    shares = pos.get("shares", 0)
                    entry_price = pos.get("entry_price", 0)
                    cost_basis = entry_price * shares
                    current_value = current_price * shares
                    pnl = current_value - cost_basis
                    pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                    
                    positions_data.append({
                        'ticker': ticker,
                        'shares': shares,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'cost_basis': cost_basis,
                        'current_value': current_value,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                except Exception as e:
                    st.warning(f"Error fetching data for {ticker}: {str(e)}")
            
            if positions_data:
                # Display each position with Dexter management
                for pos_data in positions_data:
                    ticker = pos_data['ticker']
                    
                    with st.expander(
                        f"**{ticker}** | {pos_data['shares']:.2f} shares | "
                        f"P/L: ${pos_data['pnl']:,.2f} ({pos_data['pnl_pct']:+.1f}%)",
                        expanded=False
                    ):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Entry Price", f"${pos_data['entry_price']:.2f}")
                            st.metric("Current Price", f"${pos_data['current_price']:.2f}")
                            st.metric("Shares", f"{pos_data['shares']:.2f}")
                        
                        with col2:
                            st.metric("Cost Basis", f"${pos_data['cost_basis']:,.2f}")
                            st.metric("Current Value", f"${pos_data['current_value']:,.2f}")
                            pnl_color = "normal" if pos_data['pnl'] >= 0 else "inverse"
                            st.metric(
                                "P/L",
                                f"${pos_data['pnl']:,.2f}",
                                f"{pos_data['pnl_pct']:+.1f}%",
                                delta_color=pnl_color
                            )
                        
                        with col3:
                            # Get Dexter's recommendation for this position
                            st.markdown("**🤖 Dexter's Deep Business Analysis:**")
                            
                            # Button to trigger Dexter analysis
                            if st.button(f"🔍 Deep Research: {ticker}", key=f"dexter_{ticker}", use_container_width=True):
                                st.session_state[f'dexter_analyze_{ticker}'] = True
                            
                            # Show analysis if triggered
                            if st.session_state.get(f'dexter_analyze_{ticker}', False):
                                try:
                                    dexter_client = DexterClient()
                                    if dexter_client.health_check():
                                        portfolio_context = PortfolioContext()
                                        context = portfolio_context.get_context()
                                        
                                        # Get current fundamentals for context
                                        try:
                                            fund = analyzer.get_fundamentals(ticker)
                                            current_price = fund.get("current_price", pos_data['current_price'])
                                            company_desc = fund.get("description", "")
                                            pe_ratio = fund.get("pe_ratio", 0)
                                            roe = fund.get("roe", 0)
                                        except:
                                            current_price = pos_data['current_price']
                                            company_desc = ""
                                            pe_ratio = 0
                                            roe = 0
                                        
                                        query = f"""As my hedge fund manager, provide a DEEP BUSINESS ANALYSIS of {ticker}:

CURRENT POSITION:
- Shares: {pos_data['shares']:.2f}
- Entry Price: ${pos_data['entry_price']:.2f}
- Current Price: ${current_price:.2f}
- P/L: ${pos_data['pnl']:,.2f} ({pos_data['pnl_pct']:+.1f}%)

DEEP BUSINESS RESEARCH REQUIRED:

1. **What does this company actually do?**
   - Business model, products/services, customers
   - Industry position and competitive landscape
   - Revenue sources: {company_desc[:200] if company_desc else 'Research required'}

2. **Competitive Moat Assessment:**
   - What protects this business from competition?
   - Type of moat: Brand/Network/Cost/Switching/Scale/Regulatory
   - Sustainability: Will this moat last 10+ years?
   - Evidence: Specific examples

3. **10-Year Business Outlook:**
   - Will this business be stronger or weaker in 2035?
   - Growth drivers and headwinds
   - Industry trends and disruption risks
   - Predictability of cash flows

4. **Management Quality:**
   - Capital allocation track record
   - Honesty and communication
   - Insider ownership and alignment
   - Long-term thinking vs short-term focus

5. **Financial Health:**
   - ROE: {roe:.1f}% (sustainable? 15%+ is quality)
   - P/E: {pe_ratio:.1f}x (reasonable for quality?)
   - Free cash flow generation
   - Debt levels and financial strength

6. **Valuation:**
   - Intrinsic value estimate
   - Margin of safety at ${current_price:.2f}
   - Would Buffett buy this at this price?

INVESTMENT RECOMMENDATION:
Provide a clear signal:
- 🟢 CONTINUE: Keep building position via DCA (specify monthly amount)
- 🟡 HOLD: Maintain current position, no new purchases
- 🔴 REDUCE: Trim position (specify % to reduce)
- ❌ EXIT: Sell entire position (thesis broken)

For CONTINUE, specify:
- Monthly DCA amount: $[X]
- Reasoning: [Why continue building]
- Key risks to watch: [What could break the thesis]

For HOLD/REDUCE/EXIT, specify:
- Reasoning: [Why this action]
- Key risks: [What to watch]

Remember: We follow Buffett's philosophy - hold forever unless thesis breaks. Focus on BUSINESS QUALITY, not stock price movements."""
                                        
                                        with st.spinner("🤖 Dexter analyzing business fundamentals... (This may take 2-3 minutes for deep research)"):
                                            # Use longer timeout for deep business research
                                            result = dexter_client.research(query, portfolio_context=context, timeout=180)
                                            dexter_analysis = result.get('answer', 'Analysis unavailable')
                                            
                                            # Extract signal icon
                                            if "🟢 CONTINUE" in dexter_analysis or "CONTINUE" in dexter_analysis.upper():
                                                signal_icon = "🟢"
                                                signal_text = "CONTINUE INVESTING"
                                            elif "🟡 HOLD" in dexter_analysis or "HOLD" in dexter_analysis.upper():
                                                signal_icon = "🟡"
                                                signal_text = "HOLD POSITION"
                                            elif "🔴 REDUCE" in dexter_analysis or "REDUCE" in dexter_analysis.upper():
                                                signal_icon = "🔴"
                                                signal_text = "REDUCE POSITION"
                                            elif "❌ EXIT" in dexter_analysis or "EXIT" in dexter_analysis.upper():
                                                signal_icon = "❌"
                                                signal_text = "EXIT POSITION"
                                            else:
                                                signal_icon = "🟡"
                                                signal_text = "HOLD"
                                            
                                            st.markdown(f"### {signal_icon} {signal_text}")
                                            st.markdown(dexter_analysis)
                                            
                                            # Store Dexter's analysis
                                            if ticker not in portfolio.get('positions', {}):
                                                portfolio['positions'][ticker] = {}
                                            portfolio['positions'][ticker]['dexter_analysis'] = {
                                                'signal': signal_text,
                                                'analysis': dexter_analysis,
                                                'updated_at': datetime.now().isoformat()
                                            }
                                            storage.save_portfolio(portfolio)
                                    else:
                                        st.info("Dexter service not running. Start NewsAdmin to get AI management.")
                                except Exception as e:
                                    st.warning(f"Dexter analysis unavailable: {str(e)}")
                            
                            # Show cached analysis if available
                            elif ticker in portfolio.get('positions', {}) and 'dexter_analysis' in portfolio['positions'][ticker]:
                                cached = portfolio['positions'][ticker]['dexter_analysis']
                                st.info(f"Last analysis: {cached.get('signal', 'HOLD')}")
                                if st.button(f"🔄 Refresh Analysis", key=f"refresh_{ticker}"):
                                    st.session_state[f'dexter_analyze_{ticker}'] = True
                                    st.rerun()
                            
                            # Manual actions
                            st.divider()
                            st.markdown("**Actions:**")
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button(f"➕ Add Shares", key=f"add_{ticker}"):
                                    st.session_state[f'add_shares_{ticker}'] = True
                                    st.rerun()
                            
                            with col_b:
                                if st.button(f"➖ Reduce Position", key=f"reduce_{ticker}"):
                                    st.session_state[f'reduce_{ticker}'] = True
                                    st.rerun()
        else:
            st.info("No active positions. Record trades in the Stock Analyzer page to see them here.")
    
    # ============ TAB 2: TRADE HISTORY ============
    with tab2:
        st.subheader("📈 Complete Trade History")
        
        if trade_history:
            # Convert to DataFrame
            df_trades = pd.DataFrame(trade_history)
            
            # Format for display
            display_trades = []
            for trade in trade_history:
                display_trades.append({
                    'Date': datetime.fromisoformat(trade.get('timestamp', datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M'),
                    'Ticker': trade.get('ticker', 'N/A'),
                    'Action': trade.get('action', 'BUY'),
                    'Shares': f"{trade.get('shares', 0):.2f}",
                    'Price': f"${trade.get('price', 0):.2f}",
                    'Total': f"${trade.get('total_cost', 0):.2f}",
                    'Notes': trade.get('notes', '')
                })
            
            df_display = pd.DataFrame(display_trades)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Trade statistics
            st.divider()
            st.subheader("📊 Trade Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_invested = sum(t.get('total_cost', 0) for t in trade_history if t.get('action') == 'BUY')
            total_sold = sum(t.get('total_cost', 0) for t in trade_history if t.get('action') == 'SELL')
            
            with col1:
                st.metric("Total Invested", f"${total_invested:,.2f}")
            with col2:
                st.metric("Total Sold", f"${total_sold:,.2f}")
            with col3:
                buy_trades = len([t for t in trade_history if t.get('action') == 'BUY'])
                st.metric("Buy Trades", buy_trades)
            with col4:
                sell_trades = len([t for t in trade_history if t.get('action') == 'SELL'])
                st.metric("Sell Trades", sell_trades)
        else:
            st.info("No trade history yet. Record trades in the Stock Analyzer page.")
    
    # ============ TAB 3: NEWS & SEC FILINGS ============
    with tab3:
        st.subheader("📰 News & SEC Filings")
        st.caption("Recent news and SEC filings for your holdings")
        
        if positions:
            for ticker in positions.keys():
                st.markdown(f"### {ticker}")
                
                try:
                    # Fetch company details
                    fetcher = PolygonFetcher()
                    details = fetcher.get_stock_details(ticker)
                    
                    if details:
                        st.markdown(f"**{details.get('name', ticker)}**")
                        st.caption(f"Exchange: {details.get('primary_exchange', 'N/A')}")
                        
                        # Placeholder for news and SEC filings
                        # In a real implementation, you'd fetch from Polygon news API or SEC EDGAR
                        st.info("💡 News and SEC filings integration coming soon. This will show:")
                        st.markdown("""
                        - Recent news articles
                        - SEC filings (10-K, 10-Q, 8-K)
                        - Earnings announcements
                        - Analyst updates
                        """)
                    else:
                        st.warning(f"Could not fetch details for {ticker}")
                except Exception as e:
                    st.warning(f"Error fetching data for {ticker}: {str(e)}")
                
                st.divider()
        else:
            st.info("No positions to show news for. Add trades to see news and filings.")
    
    # ============ TAB 4: PORTFOLIO VS MARKET ============
    with tab4:
        st.subheader("📊 Portfolio Performance vs Market")
        
        if positions:
            # Calculate portfolio performance
            portfolio_returns = []
            market_returns = []  # Would use SPY or similar benchmark
            
            # Get portfolio return
            total_cost = sum(p.get('entry_price', 0) * p.get('shares', 0) for p in positions.values())
            current_value = 0
            
            for ticker, pos in positions.items():
                try:
                    fund = analyzer.get_fundamentals(ticker)
                    current_price = fund.get("current_price", pos.get("entry_price", 0))
                    current_value += current_price * pos.get("shares", 0)
                except:
                    pass
            
            portfolio_return = ((current_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Portfolio Return", f"{portfolio_return:+.2f}%")
            with col2:
                st.metric("Market Return (SPY)", "N/A", help="Market benchmark comparison coming soon")
            with col3:
                st.metric("Alpha", "N/A", help="Portfolio alpha vs market coming soon")
            
            st.info("💡 Full portfolio vs market comparison coming soon. This will include:")
            st.markdown("""
            - Portfolio return vs S&P 500
            - Alpha calculation
            - Beta calculation
            - Sharpe ratio
            - Drawdown analysis
            - Sector allocation vs market
            """)
        else:
            st.info("No positions to compare. Add trades to see portfolio performance.")

st.divider()
st.caption("📋 **Personal Trades** - Track, manage, and optimize your portfolio with AI-powered insights")

