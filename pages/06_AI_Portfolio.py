# ============================================================================
# FILE: pages/05_AI_Portfolio.py
# AI-Powered Automated Portfolio Management
# ============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import AIPortfolioManager, StockAnalyzer
from utils.storage import StorageManager

st.set_page_config(page_title="AI Portfolio Manager", page_icon="🤖", layout="wide")

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.title("🤖 AI Portfolio Manager")
st.markdown("*Automated trading system that starts with $100 and adds $100/month*")

# Initialize managers
storage = StorageManager()
portfolio_manager = AIPortfolioManager(storage)
analyzer = StockAnalyzer()

# Load or initialize portfolio
portfolio = storage.load_portfolio()

# Sidebar controls
with st.sidebar:
    st.subheader("Portfolio Settings")
    
    if portfolio is None:
        st.info("👈 Initialize your portfolio to begin")
        initial_cash = st.number_input("Starting Amount ($)", min_value=10.0, value=100.0, step=10.0)
        monthly_contrib = st.number_input("Monthly Contribution ($)", min_value=10.0, value=100.0, step=10.0)
        
        if st.button("🚀 Initialize Portfolio", use_container_width=True, type="primary"):
            portfolio = portfolio_manager.initialize_portfolio(initial_cash, monthly_contrib)
            storage.save_portfolio(portfolio)
            st.success("Portfolio initialized!")
            st.rerun()
    else:
        st.success("✅ Portfolio Active")
        
        # Display current settings
        st.markdown(f"**Starting Amount:** ${portfolio.get('initial_cash', 0):.2f}")
        st.markdown(f"**Monthly Contribution:** ${portfolio.get('monthly_contribution', 0):.2f}")
        st.markdown(f"**Total Contributed:** ${portfolio.get('total_contributed', 0):.2f}")
        
        st.divider()
        
        # Settings
        st.subheader("Risk Settings")
        max_loss = st.slider("Max Loss Per Trade (%)", 1.0, 5.0, 
                            portfolio.get('settings', {}).get('max_loss_per_trade', 2.0), 0.5)
        risk_tolerance = st.slider("Risk Tolerance", 1, 10, 
                                  portfolio.get('settings', {}).get('risk_tolerance', 5))
        max_position = st.slider("Max Position Size (%)", 5.0, 30.0, 
                                portfolio.get('settings', {}).get('max_position_size_pct', 20.0), 1.0)
        min_score = st.slider("Min Stock Score", 60, 100, 
                             portfolio.get('settings', {}).get('min_stock_score', 80))
        
        if st.button("💾 Save Settings", use_container_width=True):
            portfolio['settings'] = {
                'max_loss_per_trade': max_loss,
                'risk_tolerance': risk_tolerance,
                'max_position_size_pct': max_position,
                'min_stock_score': min_score
            }
            storage.save_portfolio(portfolio)
            st.success("Settings saved!")
            st.rerun()
        
        st.divider()
        
        # Actions
        st.subheader("Actions")
        
        # Check if we have hot stocks
        hot_data = storage.load_hot_stocks()
        hot_count = len(hot_data.get('stocks', []))
        
        if hot_count == 0:
            st.warning(f"⚠️ No hot stocks available. Run scanner first!")
            if st.button("🔍 Run Stock Scanner", use_container_width=True, type="primary"):
                from scanner.market_scanner import MarketScanner
                from scanner.stock_universe import get_daily_batch
                from datetime import datetime
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                today = datetime.now().weekday()
                
                # On weekends, scan Monday's batch for testing
                if today >= 5:  # Saturday (5) or Sunday (6)
                    st.info("📅 Weekend detected - scanning Monday's batch for testing")
                    scan_day = 0  # Monday
                else:
                    scan_day = today
                
                # Get stock list (with market filtering)
                from scanner.stock_universe import get_daily_batch
                tickers = get_daily_batch(scan_day, filter_weak_markets=True, min_market_cap=50_000_000)
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                
                st.info(f"📊 **Scanning {len(tickers)} stocks from {day_names[scan_day]}'s batch**")
                st.caption("💡 **How it works:** Filters to strong markets only (NYSE/NASDAQ/AMEX), minimum $50M market cap, 100k+ volume. Pulls live data from Yahoo Finance API (yfinance) for each stock.")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.empty()
                
                scanner = MarketScanner(max_workers=10)
                results = {
                    'hot': [],
                    'warming': [],
                    'watching': [],
                    'scanned_at': datetime.now().isoformat(),
                    'day_of_week': scan_day,
                    'total_scanned': len(tickers)
                }
                
                # Scan with progress updates (with market filtering)
                min_market_cap = 50_000_000  # $50M minimum
                min_volume = 100_000  # 100k average volume
                completed = 0
                current_stocks = []
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_ticker = {
                        executor.submit(scanner._scan_single_stock, ticker, min_market_cap, min_volume): ticker 
                        for ticker in tickers
                    }
                    
                    for future in as_completed(future_to_ticker):
                        completed += 1
                        ticker = future_to_ticker[future]
                        
                        # Update progress
                        progress = completed / len(tickers)
                        progress_bar.progress(progress)
                        
                        # Show current stock being processed
                        current_stocks.append(ticker)
                        if len(current_stocks) > 5:
                            current_stocks.pop(0)
                        
                        status_text.markdown(f"**Progress:** {completed}/{len(tickers)} stocks ({progress*100:.1f}%) | Currently scanning: {', '.join(current_stocks[-3:])}")
                        
                        # Show results so far
                        results_text = f"🔥 Hot: {len(results['hot'])} | 🟡 Warming: {len(results['warming'])} | 👀 Watching: {len(results['watching'])}"
                        results_container.markdown(f"**Results so far:** {results_text}")
                        
                        try:
                            result = future.result()
                            if result:
                                score = result['score']['total_score']
                                if score >= 80:
                                    results['hot'].append(result)
                                elif score >= 70:
                                    results['warming'].append(result)
                                elif score >= 60:
                                    results['watching'].append(result)
                        except Exception as e:
                            pass  # Skip errors
                
                # Sort results
                results['hot'].sort(key=lambda x: x['score']['total_score'], reverse=True)
                results['warming'].sort(key=lambda x: x['score']['total_score'], reverse=True)
                results['watching'].sort(key=lambda x: x['score']['total_score'], reverse=True)
                
                # Save results
                storage.save_hot_stocks(results['hot'])
                storage.save_warming_stocks(results['warming'])
                storage.save_watching_stocks(results['watching'])
                
                # Update progress
                progress = storage.load_scan_progress()
                progress['last_scan'] = datetime.now().isoformat()
                storage.save_scan_progress(progress)
                
                st.success(f"✅ Scanner complete! Found {len(results['hot'])} hot stocks, {len(results['warming'])} warming, {len(results['watching'])} watching")
                st.rerun()
        else:
            st.success(f"✅ {hot_count} hot stocks available from scanner")
        
        st.divider()
        
        if st.button("🔄 Auto-Manage Portfolio", use_container_width=True, type="primary"):
            with st.spinner("Managing portfolio..."):
                # Get hot stocks from scanner
                hot_data = storage.load_hot_stocks()
                hot_stocks = [s['ticker'] for s in hot_data.get('stocks', [])]
                
                portfolio, activity_log = portfolio_manager.auto_manage_portfolio(portfolio, hot_stocks)
                storage.save_portfolio(portfolio)
                
                # Store activity log in session state to display
                st.session_state['last_activity_log'] = activity_log
                st.session_state['last_activity_time'] = datetime.now().isoformat()
                
                st.success("Portfolio managed!")
                st.rerun()
        
        if st.button("➕ Add Monthly Contribution", use_container_width=True):
            portfolio = portfolio_manager.add_monthly_contribution(portfolio)
            storage.save_portfolio(portfolio)
            st.success("Contribution added!")
            st.rerun()
        
        if st.button("🗑️ Reset Portfolio", use_container_width=True):
            if st.session_state.get('confirm_reset', False):
                portfolio = None
                storage.save_portfolio(None)
                st.success("Portfolio reset!")
                st.rerun()
            else:
                st.session_state['confirm_reset'] = True
                st.warning("Click again to confirm reset")

# Main content
if portfolio is None:
    st.info("""
    ### 🚀 Get Started
    
    This AI Portfolio Manager will:
    - Start with $100 (or your chosen amount)
    - Automatically add $100/month (or your chosen amount)
    - Use AI to analyze stocks and make trading decisions
    - Automatically enter and exit trades based on risk management rules
    - Track all positions and performance
    
    **Click "Initialize Portfolio" in the sidebar to begin!**
    """)
else:
    # Calculate portfolio metrics
    portfolio_value = portfolio_manager.get_portfolio_value(portfolio)
    current_cash = portfolio.get("current_cash", 0)
    total_contributed = portfolio.get("total_contributed", 0)
    total_return = portfolio_value - total_contributed
    total_return_pct = (total_return / total_contributed * 100) if total_contributed > 0 else 0
    
    positions = portfolio.get("positions", {})
    num_positions = len(positions)
    
    # Activity Log Section
    if st.session_state.get('last_activity_log'):
        st.subheader("📋 Last Activity Log")
        activity_log = st.session_state.get('last_activity_log', [])
        last_time = st.session_state.get('last_activity_time')
        
        if last_time:
            try:
                time_obj = datetime.fromisoformat(last_time)
                time_str = time_obj.strftime("%Y-%m-%d %H:%M:%S")
                st.caption(f"Last run: {time_str}")
            except:
                pass
        
        # Display activity log in an expandable section
        with st.expander("View Activity Details", expanded=True):
            for activity in activity_log:
                if "BOUGHT" in activity or "✅" in activity:
                    st.success(activity)
                elif "SOLD" in activity or "💰" in activity:
                    st.info(activity)
                elif "❌" in activity or "Failed" in activity:
                    st.error(activity)
                elif "⚠️" in activity:
                    st.warning(activity)
                else:
                    st.write(activity)
        
        st.divider()
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Portfolio Value", f"${portfolio_value:,.2f}", 
                 f"${total_return:,.2f} ({total_return_pct:+.1f}%)")
    
    with col2:
        st.metric("Cash Available", f"${current_cash:,.2f}")
    
    with col3:
        st.metric("Total Contributed", f"${total_contributed:,.2f}")
    
    with col4:
        st.metric("Active Positions", num_positions)
    
    with col5:
        invested_value = portfolio_value - current_cash
        st.metric("Invested", f"${invested_value:,.2f}")
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Positions", "📈 Performance", "💼 Trade History", "🔍 Find Opportunities"])
    
    # ============ POSITIONS TAB ============
    with tab1:
        if num_positions == 0:
            st.info("No active positions. Use 'Auto-Manage Portfolio' to find and enter trades.")
        else:
            st.subheader("Active Positions")
            
            positions_data = []
            for ticker, position in positions.items():
                try:
                    fundamentals = analyzer.get_fundamentals(ticker)
                    current_price = fundamentals.get("current_price", position.get("entry_price", 0))
                    entry_price = position.get("entry_price", 0)
                    shares = position.get("shares", 0)
                    current_value = current_price * shares
                    cost_basis = entry_price * shares
                    pnl = current_value - cost_basis
                    pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                    
                    positions_data.append({
                        "Ticker": ticker,
                        "Shares": shares,
                        "Entry Price": f"${entry_price:.2f}",
                        "Current Price": f"${current_price:.2f}",
                        "Cost Basis": f"${cost_basis:.2f}",
                        "Current Value": f"${current_value:.2f}",
                        "P&L": f"${pnl:.2f}",
                        "P&L %": f"{pnl_pct:+.1f}%",
                        "Stop Loss": f"${position.get('stop_loss', 0):.2f}",
                        "Target": f"${position.get('target', 0):.2f}",
                        "Type": position.get("stock_type", "Unknown")
                    })
                except Exception as e:
                    st.warning(f"Error fetching data for {ticker}: {str(e)}")
            
            if positions_data:
                df = pd.DataFrame(positions_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Position allocation chart
                if len(positions_data) > 0:
                    fig = go.Figure(data=[go.Pie(
                        labels=[p["Ticker"] for p in positions_data],
                        values=[float(p["Current Value"].replace("$", "").replace(",", "")) for p in positions_data],
                        hole=0.4
                    )])
                    fig.update_layout(
                        title="Position Allocation",
                        height=400,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#e0e0e0")
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # ============ PERFORMANCE TAB ============
    with tab2:
        st.subheader("Portfolio Performance")
        
        # Get trade history for performance chart
        trade_history = portfolio.get("trade_history", [])
        
        if len(trade_history) == 0:
            st.info("No trades yet. Performance data will appear after trades are executed.")
        else:
            # Calculate cumulative performance
            performance_data = []
            running_value = portfolio.get("initial_cash", 100)
            running_contributions = portfolio.get("initial_cash", 100)
            
            for trade in sorted(trade_history, key=lambda x: x.get("timestamp", "")):
                timestamp = trade.get("timestamp", datetime.now().isoformat())
                action = trade.get("action", "")
                
                if action == "BUY":
                    running_value -= trade.get("total_cost", 0)
                elif action == "SELL":
                    running_value += trade.get("proceeds", 0)
                    pnl = trade.get("pnl", 0)
                
                # Check if this is a contribution month
                trade_date = datetime.fromisoformat(timestamp)
                # Simplified: assume contributions happen monthly
                
                performance_data.append({
                    "Date": trade_date,
                    "Portfolio Value": running_value,
                    "Contributions": running_contributions
                })
            
            if performance_data:
                df_perf = pd.DataFrame(performance_data)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_perf["Date"],
                    y=df_perf["Portfolio Value"],
                    name="Portfolio Value",
                    line=dict(color="#00d4aa", width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=df_perf["Date"],
                    y=df_perf["Contributions"],
                    name="Total Contributed",
                    line=dict(color="#4a9eff", width=2, dash="dash")
                ))
                
                fig.update_layout(
                    title="Portfolio Value Over Time",
                    xaxis_title="Date",
                    yaxis_title="Value ($)",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e0e0e0"),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Trades", len(trade_history))
            
            with col2:
                buy_trades = [t for t in trade_history if t.get("action") == "BUY"]
                sell_trades = [t for t in trade_history if t.get("action") == "SELL"]
                st.metric("Completed Trades", len(sell_trades))
            
            with col3:
                total_pnl = sum(t.get("pnl", 0) for t in sell_trades)
                st.metric("Total Realized P&L", f"${total_pnl:,.2f}")
    
    # ============ TRADE HISTORY TAB ============
    with tab3:
        st.subheader("Trade History")
        
        trade_history = portfolio.get("trade_history", [])
        
        if len(trade_history) == 0:
            st.info("No trades yet. Trades will appear here as the AI manages your portfolio.")
        else:
            history_data = []
            for trade in trade_history:
                timestamp = trade.get("timestamp", datetime.now().isoformat())
                try:
                    trade_date = datetime.fromisoformat(timestamp)
                    date_str = trade_date.strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = timestamp
                
                history_data.append({
                    "Date": date_str,
                    "Action": trade.get("action", ""),
                    "Ticker": trade.get("ticker", ""),
                    "Shares": trade.get("shares", 0),
                    "Price": f"${trade.get('price', 0):.2f}",
                    "Amount": f"${trade.get('total_cost', trade.get('proceeds', 0)):.2f}",
                    "P&L": f"${trade.get('pnl', 0):.2f}" if trade.get('pnl') is not None else "—",
                    "Reason": trade.get("reason", "")
                })
            
            df_history = pd.DataFrame(history_data)
            st.dataframe(df_history, use_container_width=True, hide_index=True)
    
    # ============ FIND OPPORTUNITIES TAB ============
    with tab4:
        st.subheader("Find Trading Opportunities")
        
        # Get hot stocks from scanner
        hot_data = storage.load_hot_stocks()
        hot_stocks = hot_data.get('stocks', [])
        
        if len(hot_stocks) == 0:
            st.info("No hot opportunities available. Run the scanner to find stocks.")
        else:
            st.markdown(f"**Found {len(hot_stocks)} hot opportunities from scanner**")
            
            # Evaluate opportunities
            opportunities = []
            for stock in hot_stocks[:10]:  # Check top 10
                ticker = stock.get('ticker', '')
                if ticker in positions:
                    continue
                
                eval_result = portfolio_manager.evaluate_trade_opportunity(portfolio, ticker)
                
                if eval_result.get("should_trade", False):
                    opportunities.append({
                        "ticker": ticker,
                        "name": stock.get('name', ticker),
                        "score": eval_result.get("score", 0),
                        "price": stock.get('fundamentals', {}).get('current_price', 0),
                        "shares": eval_result.get("position_info", {}).get("shares", 0),
                        "position_value": eval_result.get("position_info", {}).get("position_value", 0),
                        "stop_loss": eval_result.get("position_info", {}).get("stop_loss_price", 0),
                        "reason": eval_result.get("reason", "")
                    })
                elif eval_result.get("reason", ""):
                    # Show why it's not a good opportunity
                    pass
            
            if len(opportunities) == 0:
                st.info("No suitable opportunities found. The AI is waiting for better entry points or more cash.")
            else:
                st.markdown(f"**{len(opportunities)} opportunities ready to trade**")
                
                opp_data = []
                for opp in opportunities:
                    opp_data.append({
                        "Ticker": opp["ticker"],
                        "Name": opp["name"][:30],
                        "Score": f"{opp['score']:.1f}",
                        "Price": f"${opp['price']:.2f}",
                        "Shares": opp["shares"],
                        "Position Value": f"${opp['position_value']:.2f}",
                        "Stop Loss": f"${opp['stop_loss']:.2f}",
                        "Action": "✅ Ready"
                    })
                
                df_opp = pd.DataFrame(opp_data)
                st.dataframe(df_opp, use_container_width=True, hide_index=True)
                
                st.info("💡 Click 'Auto-Manage Portfolio' in the sidebar to execute trades automatically.")

st.divider()
st.caption("""
🤖 **How It Works:**
- The AI analyzes stocks using fundamental metrics, technical indicators, and risk management rules
- Trades are automatically entered when opportunities meet your criteria
- Positions are automatically exited when stop-losses are hit, targets are reached, or fundamentals deteriorate
- Monthly contributions are added automatically (or manually via button)
- All trades respect your risk settings (max loss per trade, position sizing, etc.)

⚠️ **Disclaimer:** This is for educational purposes only. Not financial advice. Past performance doesn't guarantee future results.
""")

