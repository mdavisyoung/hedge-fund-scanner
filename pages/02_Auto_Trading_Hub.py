"""
Auto Trading Hub - Unified Page
Combines: Portfolio Simulator + Stock Scanner + Trade Desk + Autonomous Trader + AI Portfolio
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import StockAnalyzer, AIPortfolioManager, PortfolioSimulator
from utils.storage import StorageManager
from scanner.market_scanner import MarketScanner
from scanner.scoring import TradeScorer
from scanner.stock_universe import get_daily_batch, get_stock_universe_summary

st.set_page_config(page_title="Auto Trading Hub", page_icon="🚀", layout="wide")

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

# Initialize components
@st.cache_resource
def init_components():
    storage = StorageManager()
    portfolio_manager = AIPortfolioManager(storage)
    analyzer = StockAnalyzer()
    scorer = TradeScorer()
    simulator = PortfolioSimulator()
    return storage, portfolio_manager, analyzer, scorer, simulator

storage, portfolio_manager, analyzer, scorer, simulator = init_components()

# Load portfolio
portfolio = storage.load_portfolio()

# Initialize trader (optional, for autonomous trading)
try:
    from trader.autonomous_trader import AutonomousTrader
    @st.cache_resource
    def init_trader():
        try:
            return AutonomousTrader(paper_trading=True), None
        except Exception as e:
            return None, str(e)
    trader, trader_error = init_trader()
except Exception as e:
    trader = None
    trader_error = str(e)

# Sidebar - Unified Settings
with st.sidebar:
    st.title("⚙️ Trading Hub Settings")
    
    # Portfolio initialization/status
    if portfolio is None:
        st.info("👈 Initialize Portfolio")
        initial_cash = st.number_input("Starting Amount ($)", min_value=10.0, value=100.0, step=10.0)
        monthly_contrib = st.number_input("Monthly Contribution ($)", min_value=10.0, value=100.0, step=10.0)
        if st.button("🚀 Initialize Portfolio", use_container_width=True, type="primary"):
            portfolio = portfolio_manager.initialize_portfolio(initial_cash, monthly_contrib)
            storage.save_portfolio(portfolio)
            st.rerun()
    else:
        st.success("✅ Portfolio Active")
        portfolio_value = portfolio_manager.get_portfolio_value(portfolio)
        st.metric("Portfolio Value", f"${portfolio_value:,.2f}")
        st.caption(f"Cash: ${portfolio.get('current_cash', 0):,.2f}")
        st.caption(f"Positions: {len(portfolio.get('positions', {}))}")
        
        # Risk settings
        st.divider()
        st.subheader("Risk Settings")
        current_settings = portfolio.get('settings', {})
        max_loss = st.slider("Max Loss Per Trade (%)", 1.0, 5.0, 
                            current_settings.get('max_loss_per_trade', 2.0), 0.5)
        max_position = st.slider("Max Position Size (%)", 5.0, 30.0,
                                current_settings.get('max_position_size_pct', 20.0), 1.0)
        min_score = st.slider("Min Stock Score", 60, 100,
                             current_settings.get('min_stock_score', 80))
        
        if st.button("💾 Save Settings", use_container_width=True):
            if 'settings' not in portfolio:
                portfolio['settings'] = {}
            portfolio['settings'].update({
                'max_loss_per_trade': max_loss,
                'max_position_size_pct': max_position,
                'min_stock_score': min_score
            })
            storage.save_portfolio(portfolio)
            st.success("Settings saved!")
            st.rerun()
    
    st.divider()
    
    # Quick actions
    st.subheader("Quick Actions")
    if portfolio:
        hot_data = storage.load_hot_stocks()
        hot_count = hot_data.get('count', 0)
        
        if st.button("🔄 Auto-Manage Portfolio", use_container_width=True, type="primary"):
            with st.spinner("Managing portfolio..."):
                hot_stocks = [s['ticker'] for s in hot_data.get('stocks', [])]
                portfolio, activity_log = portfolio_manager.auto_manage_portfolio(portfolio, hot_stocks)
                storage.save_portfolio(portfolio)
                st.session_state['last_activity_log'] = activity_log
                st.session_state['last_activity_time'] = datetime.now().isoformat()
                st.success("Portfolio managed!")
                st.rerun()
        
        if st.button("➕ Add Monthly Contribution", use_container_width=True):
            portfolio = portfolio_manager.add_monthly_contribution(portfolio)
            storage.save_portfolio(portfolio)
            st.success("Contribution added!")
            st.rerun()

# Main Header
st.title("🚀 Auto Trading Hub")
st.markdown("*Unified platform for scanning, trading, managing capital, and learning from results*")

# Status bar
if portfolio:
    portfolio_value = portfolio_manager.get_portfolio_value(portfolio)
    current_cash = portfolio.get("current_cash", 0)
    positions = portfolio.get("positions", {})
    
    hot_data = storage.load_hot_stocks()
    progress = storage.load_scan_progress()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Portfolio Value", f"${portfolio_value:,.2f}")
    with col2:
        st.metric("Cash Available", f"${current_cash:,.2f}")
    with col3:
        st.metric("Active Positions", len(positions))
    with col4:
        st.metric("🔥 Hot Stocks", hot_data.get('count', 0))
    with col5:
        last_scan = progress.get('last_scan')
        if last_scan:
            scan_time = datetime.fromisoformat(last_scan).strftime("%b %d")
            st.metric("Last Scan", scan_time)
        else:
            st.metric("Last Scan", "Never")
else:
    st.info("👈 Initialize your portfolio in the sidebar to begin")

st.divider()

# Activity Log Display
if st.session_state.get('last_activity_log') and portfolio:
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
    
    with st.expander("View Activity Details", expanded=False):
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

# MAIN TABS
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Portfolio Overview",
    "🔍 Scanner & Opportunities", 
    "🤖 Auto Trading",
    "📈 Backtesting",
    "🧠 ML Learning",
    "📋 Copy Trades"
])

# ============ TAB 1: PORTFOLIO OVERVIEW ============
with tab1:
    st.subheader("📊 Portfolio Overview & Capital Management")
    
    if portfolio is None:
        st.info("👈 Initialize your portfolio in the sidebar to begin")
    else:
        # Key metrics
        portfolio_value = portfolio_manager.get_portfolio_value(portfolio)
        total_contributed = portfolio.get("total_contributed", 0)
        total_return = portfolio_value - total_contributed
        total_return_pct = (total_return / total_contributed * 100) if total_contributed > 0 else 0
        current_cash = portfolio.get("current_cash", 0)
        positions = portfolio.get("positions", {})
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Portfolio Value", f"${portfolio_value:,.2f}", 
                     f"${total_return:,.2f} ({total_return_pct:+.1f}%)")
        with col2:
            st.metric("Total Contributed", f"${total_contributed:,.2f}")
        with col3:
            st.metric("Current Cash", f"${current_cash:,.2f}")
        with col4:
            st.metric("Active Positions", len(positions))
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Portfolio value chart
            st.markdown("### Portfolio Growth")
            trade_history = portfolio.get("trade_history", [])
            
            # Build performance timeline
            performance_data = []
            running_value = portfolio.get("initial_cash", 100)
            running_contributions = portfolio.get("initial_cash", 100)
            
            # Add initial point
            created_at = portfolio.get("created_at", datetime.now().isoformat())
            try:
                start_date = datetime.fromisoformat(created_at)
            except:
                start_date = datetime.now()
            
            performance_data.append({
                "Date": start_date,
                "Value": running_value,
                "Contributions": running_contributions
            })
            
            for trade in sorted(trade_history, key=lambda x: x.get("timestamp", "")):
                timestamp = trade.get("timestamp", datetime.now().isoformat())
                try:
                    trade_date = datetime.fromisoformat(timestamp)
                except:
                    trade_date = datetime.now()
                
                if trade.get("action") == "BUY":
                    running_value -= trade.get("total_cost", 0)
                elif trade.get("action") == "SELL":
                    running_value += trade.get("proceeds", 0)
                
                performance_data.append({
                    "Date": trade_date,
                    "Value": running_value,
                    "Contributions": running_contributions
                })
            
            if len(performance_data) > 1:
                df_perf = pd.DataFrame(performance_data)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_perf["Date"],
                    y=df_perf["Value"],
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
                    height=400,
                    title="Portfolio Value Over Time",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e0e0e0"),
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trades yet - chart will appear after first trade")
            
            # Position allocation pie chart
            if positions:
                st.markdown("### Position Allocation")
                pos_data = []
                for ticker, pos in positions.items():
                    try:
                        fund = analyzer.get_fundamentals(ticker)
                        current_price = fund.get("current_price", pos.get("entry_price", 0))
                        pos_value = current_price * pos.get("shares", 0)
                        if pos_value > 0:
                            pos_data.append({"Ticker": ticker, "Value": pos_value})
                    except:
                        pass
                
                if pos_data:
                    df_pos = pd.DataFrame(pos_data)
                    fig = go.Figure(data=[go.Pie(
                        labels=df_pos["Ticker"],
                        values=df_pos["Value"],
                        hole=0.4
                    )])
                    fig.update_layout(
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#e0e0e0")
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Position details table
            st.markdown("### Active Positions")
            if positions:
                pos_table = []
                for ticker, pos in positions.items():
                    try:
                        fund = analyzer.get_fundamentals(ticker)
                        current_price = fund.get("current_price", pos.get("entry_price", 0))
                        entry_price = pos.get("entry_price", 0)
                        shares = pos.get("shares", 0)
                        pnl = (current_price - entry_price) * shares
                        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                        pos_value = current_price * shares
                        
                        pos_table.append({
                            "Ticker": ticker,
                            "Shares": shares,
                            "Entry": f"${entry_price:.2f}",
                            "Current": f"${current_price:.2f}",
                            "Value": f"${pos_value:.2f}",
                            "P&L": f"${pnl:.2f}",
                            "P&L %": f"{pnl_pct:+.1f}%",
                            "Stop": f"${pos.get('stop_loss', 0):.2f}",
                            "Target": f"${pos.get('target', 0):.2f}"
                        })
                    except Exception as e:
                        st.warning(f"Error fetching {ticker}: {str(e)}")
                
                if pos_table:
                    df = pd.DataFrame(pos_table)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No active positions. Use 'Auto-Manage Portfolio' or Scanner to find opportunities.")
            
            # Monte Carlo projection (from Portfolio Simulator)
            st.markdown("### 5-Year Projection")
            monthly_contrib = portfolio.get("monthly_contribution", 100)
            months = list(range(1, 61))
            balance_conservative = [monthly_contrib * m * (1 + 0.07/12)**m for m in months]
            balance_moderate = [monthly_contrib * m * (1 + 0.085/12)**m for m in months]
            balance_aggressive = [monthly_contrib * m * (1 + 0.10/12)**m for m in months]
            
            fig_proj = go.Figure()
            fig_proj.add_trace(go.Scatter(
                x=months, y=balance_conservative,
                name="Conservative (7%)",
                line=dict(color="#ff6b6b", width=2)
            ))
            fig_proj.add_trace(go.Scatter(
                x=months, y=balance_moderate,
                name="Moderate (8.5%)",
                line=dict(color="#4a9eff", width=3)
            ))
            fig_proj.add_trace(go.Scatter(
                x=months, y=balance_aggressive,
                name="Aggressive (10%)",
                line=dict(color="#00d4aa", width=2)
            ))
            fig_proj.update_layout(
                height=300,
                title=f"${monthly_contrib}/month projection",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
                hovermode='x unified'
            )
            st.plotly_chart(fig_proj, use_container_width=True)
        
        # Position sizing calculator (from Portfolio Simulator)
        st.divider()
        st.markdown("### 💼 Position Sizing Calculator")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Input Parameters")
            calc_portfolio_value = st.number_input("Portfolio Value ($)", min_value=100, value=int(portfolio_value), step=100)
            calc_stock_price = st.number_input("Stock Price ($)", min_value=0.01, value=100.0, step=1.0)
            calc_max_loss_pct = st.slider("Max Loss (%)", 1.0, 5.0, max_loss, 0.5)
            calc_stop_loss_pct = st.slider("Stop Loss Distance (%)", 5.0, 20.0, 10.0, 1.0)
            
            if st.button("🧮 Calculate Position", use_container_width=True):
                result = simulator.calculate_position_size(
                    calc_portfolio_value, calc_stock_price, calc_max_loss_pct, calc_stop_loss_pct
                )
                st.session_state['position_result'] = result
        
        with col2:
            st.markdown("#### Calculation Results")
            if 'position_result' in st.session_state:
                result = st.session_state['position_result']
                st.metric("Shares to Buy", f"{result['shares']}")
                st.metric("Position Value", f"${result['position_value']:.2f}")
                st.metric("Stop Loss Price", f"${result['stop_loss_price']:.2f}")
                st.metric("Max Loss Amount", f"${result['max_loss']:.2f}")
                st.metric("Position Size", f"{result['position_pct']:.1f}% of portfolio")
            else:
                st.info("Enter parameters and click 'Calculate Position'")

# ============ TAB 2: SCANNER & OPPORTUNITIES ============
with tab2:
    st.subheader("🔍 Stock Scanner & Trade Opportunities")
    
    # Scanner controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        selected_day = st.selectbox("Scan Day", day_names, index=datetime.now().weekday() % 5)
        day_of_week = day_names.index(selected_day)
    
    with col2:
        min_score = st.slider("Min Score", 0, 100, 60, 5)
    
    with col3:
        run_scan = st.button("🚀 Run Scan", use_container_width=True, type="primary")
    
    # Scanner results summary
    hot_data = storage.load_hot_stocks()
    warming_data = storage.load_warming_stocks()
    watching_data = storage.load_watching_stocks()
    progress = storage.load_scan_progress()
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔥 Hot (80+)", hot_data.get('count', 0))
    with col2:
        st.metric("🟡 Warming (70-79)", warming_data.get('count', 0))
    with col3:
        st.metric("👀 Watching (60-69)", watching_data.get('count', 0))
    with col4:
        last_scan = progress.get('last_scan')
        if last_scan:
            scan_time = datetime.fromisoformat(last_scan).strftime("%b %d, %I:%M%p")
            st.metric("Last Scan", scan_time)
        else:
            st.metric("Last Scan", "Never")
    
    st.divider()
    
    # Run scanner logic
    if run_scan:
        # Load config
        config = storage.load_config()
        use_dynamic = config.get('scanner', {}).get('universe', {}).get('use_dynamic_fetch', False)
        market_filter_settings = config.get('scanner', {}).get('market_filtering', {})
        min_market_cap = market_filter_settings.get('min_market_cap', 50_000_000)
        min_volume = market_filter_settings.get('min_volume', 100_000)
        
        # Get stocks for selected day
        stocks_to_scan = get_daily_batch(
            day_of_week,
            filter_weak_markets=True,
            min_market_cap=min_market_cap,
            use_dynamic=use_dynamic,
            min_volume=min_volume
        )
        
        if not stocks_to_scan:
            st.warning(f"No stocks scheduled for {selected_day}. Try a different day.")
        else:
            st.info(f"Scanning {len(stocks_to_scan)} stocks for {selected_day}...")
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.empty()
            
            scanner = MarketScanner(max_workers=10)
            results = {
                'hot': [],
                'warming': [],
                'watching': [],
                'scanned_at': datetime.now().isoformat(),
                'day_of_week': day_of_week,
                'total_scanned': len(stocks_to_scan)
            }
            
            completed = 0
            current_stocks = []
            
            scanner = MarketScanner(max_workers=10)
            results = {
                'hot': [],
                'warming': [],
                'watching': [],
                'scanned_at': datetime.now().isoformat(),
                'day_of_week': day_of_week,
                'total_scanned': len(stocks_to_scan)
            }
            
            # Limit scan size for UI responsiveness
            limited_scan = stocks_to_scan[:50]
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_ticker = {
                    executor.submit(scanner._scan_single_stock, ticker, min_market_cap, min_volume): ticker 
                    for ticker in limited_scan
                }
                
                for future in as_completed(future_to_ticker):
                    completed += 1
                    ticker = future_to_ticker[future]
                    
                    progress = completed / min(len(stocks_to_scan), 50)
                    progress_bar.progress(progress)
                    
                    current_stocks.append(ticker)
                    if len(current_stocks) > 5:
                        current_stocks.pop(0)
                    
                    status_text.markdown(f"**Progress:** {completed}/{min(len(stocks_to_scan), 50)} ({progress*100:.1f}%) | Currently: {', '.join(current_stocks[-3:])}")
                    results_text = f"🔥 Hot: {len(results['hot'])} | 🟡 Warming: {len(results['warming'])} | 👀 Watching: {len(results['watching'])}"
                    results_container.markdown(f"**Results:** {results_text}")
                    
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
                    except:
                        pass
            
            progress_bar.empty()
            status_text.empty()
            results_container.empty()
            
            # Sort results
            results['hot'].sort(key=lambda x: x['score']['total_score'], reverse=True)
            results['warming'].sort(key=lambda x: x['score']['total_score'], reverse=True)
            results['watching'].sort(key=lambda x: x['score']['total_score'], reverse=True)
            
            # Save results
            storage.save_hot_stocks(results['hot'])
            storage.save_warming_stocks(results['warming'])
            storage.save_watching_stocks(results['watching'])
            
            # Update progress
            progress['last_scan'] = datetime.now().isoformat()
            storage.save_scan_progress(progress)
            
            st.success(f"✅ Scanner complete! Found {len(results['hot'])} hot, {len(results['warming'])} warming, {len(results['watching'])} watching")
            st.rerun()
    
    # Hot opportunities display (from Trade Desk)
    st.markdown("### 🔥 Hot Opportunities - Ready to Trade")
    hot_stocks = hot_data.get('stocks', [])
    
    if not hot_stocks:
        st.info("💤 No hot opportunities yet. Run the scanner to find stocks!")
        st.markdown("""
        **What makes a stock "HOT"?**
        - Score ≥ 80/100
        - Meets fundamental criteria for its type
        - Strong technical setup
        - Good risk/reward ratio
        - Favorable entry timing
        """)
    else:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            stock_types = list(set([s.get('stock_type', 'Unknown') for s in hot_stocks]))
            selected_type = st.multiselect("Stock Type", stock_types, default=stock_types)
        with col2:
            max_price = st.number_input("Max Price ($)", min_value=0, value=1000, step=50)
        with col3:
            min_score_filter = st.slider("Min Score", 80, 100, 80)
        
        # Filter stocks
        filtered = [
            s for s in hot_stocks 
            if s.get('stock_type', 'Unknown') in selected_type 
            and s.get('fundamentals', {}).get('current_price', 0) <= max_price
            and s.get('score', {}).get('total_score', 0) >= min_score_filter
        ]
        
        st.markdown(f"**Showing {len(filtered)} of {len(hot_stocks)} hot stocks**")
        
        # Display as expandable cards
        for stock in filtered[:15]:  # Show top 15
            with st.expander(
                f"**{stock.get('ticker', 'N/A')}** - {stock.get('name', 'N/A')[:40]} | "
                f"Score: {stock.get('score', {}).get('total_score', 0)}/100 | "
                f"${stock.get('fundamentals', {}).get('current_price', 0):.2f}",
                expanded=False
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    trade_plan = stock.get('trade_plan', {})
                    st.markdown("### 📊 Trade Plan")
                    st.markdown(f"**Entry:** ${trade_plan.get('entry_price', 0):.2f} | "
                              f"**Stop Loss:** ${trade_plan.get('stop_loss', 0):.2f} | "
                              f"**Target:** ${trade_plan.get('target', 0):.2f}")
                    
                    fundamentals = stock.get('fundamentals', {})
                    st.markdown("### 📈 Fundamentals")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("P/E Ratio", f"{fundamentals.get('pe_ratio', 0):.1f}")
                    with col_b:
                        st.metric("Revenue Growth", f"{fundamentals.get('revenue_growth', 0):.1f}%")
                    with col_c:
                        st.metric("ROE", f"{fundamentals.get('roe', 0):.1f}%")
                
                with col2:
                    score_data = stock.get('score', {})
                    st.markdown("### 🎯 Score Breakdown")
                    st.markdown(f"**Type:** {stock.get('stock_type', 'Unknown')}")
                    st.markdown(f"**Grade:** {score_data.get('grade', 'N/A')}")
                    
                    breakdown = score_data.get('breakdown', {})
                    if breakdown:
                        fig = go.Figure(go.Bar(
                            x=list(breakdown.values()),
                            y=list(breakdown.keys()),
                            orientation='h',
                            marker=dict(color='#00d4aa')
                        ))
                        fig.update_layout(
                            height=200,
                            margin=dict(l=0, r=0, t=0, b=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=10, color="#e0e0e0"),
                            xaxis=dict(range=[0, 100])
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button(f"📋 Copy Trade", key=f"copy_{stock.get('ticker', '')}"):
                        if 'copied_trades' not in st.session_state:
                            st.session_state['copied_trades'] = []
                        st.session_state['copied_trades'].append({
                            'ticker': stock.get('ticker', ''),
                            'name': stock.get('name', ''),
                            'entry': trade_plan.get('entry_price', 0),
                            'stop': trade_plan.get('stop_loss', 0),
                            'target': trade_plan.get('target', 0),
                            'score': score_data.get('total_score', 0),
                            'copied_at': datetime.now().isoformat()
                        })
                        st.success(f"✅ {stock.get('ticker', '')} added to Copy Trades!")
                        st.rerun()
                with col2:
                    if st.button(f"📈 Analyze", key=f"analyze_{stock.get('ticker', '')}"):
                        st.switch_page("pages/01_Stock_Analyzer.py")
                with col3:
                    if st.button(f"🔄 Refresh", key=f"refresh_{stock.get('ticker', '')}"):
                        st.info("Re-scan feature coming soon!")
    
    # Warming and Watching tabs
    st.divider()
    warm_tab, watch_tab = st.tabs(["🟡 Warming Up", "👀 Watching"])
    
    with warm_tab:
        warming_stocks = warming_data.get('stocks', [])
        if warming_stocks:
            st.markdown(f"**{len(warming_stocks)} stocks close to hot status**")
            warm_df = pd.DataFrame([
                {
                    'Ticker': s.get('ticker', ''),
                    'Name': s.get('name', '')[:30],
                    'Type': s.get('stock_type', ''),
                    'Score': s.get('score', {}).get('total_score', 0),
                    'Price': f"${s.get('fundamentals', {}).get('current_price', 0):.2f}",
                    'Needed': f"{80 - s.get('score', {}).get('total_score', 0):.0f} more points"
                }
                for s in warming_stocks[:20]
            ])
            st.dataframe(warm_df, use_container_width=True, hide_index=True)
        else:
            st.info("No warming stocks yet")
    
    with watch_tab:
        watching_stocks = watching_data.get('stocks', [])
        if watching_stocks:
            st.markdown(f"**{len(watching_stocks)} stocks on the radar**")
            watch_df = pd.DataFrame([
                {
                    'Ticker': s.get('ticker', ''),
                    'Name': s.get('name', '')[:30],
                    'Type': s.get('stock_type', ''),
                    'Score': s.get('score', {}).get('total_score', 0),
                    'Price': f"${s.get('fundamentals', {}).get('current_price', 0):.2f}"
                }
                for s in watching_stocks[:30]
            ])
            st.dataframe(watch_df, use_container_width=True, hide_index=True)
        else:
            st.info("No watching stocks yet")

# ============ TAB 3: AUTO TRADING ============
with tab3:
    st.subheader("🤖 Autonomous Trading")
    
    if trader is None:
        st.error(f"❌ Could not initialize autonomous trader: {trader_error}")
        st.info("💡 Make sure ALPACA_API_KEY and ALPACA_SECRET_KEY are set in your .env file")
        st.info("This feature requires Alpaca paper trading account")
    else:
        # Trading status
        try:
            account = trader.get_account_info()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Account Value", f"${account['portfolio_value']:,.2f}")
            with col2:
                st.metric("Cash Available", f"${account['cash']:,.2f}")
            with col3:
                portfolio_heat = trader.get_portfolio_heat()
                st.metric("Portfolio Heat", f"{portfolio_heat*100:.1f}%")
            with col4:
                mode = "📄 Paper" if account['paper_trading'] else "💰 Live"
                st.metric("Trading Mode", mode)
            
            st.divider()
            
            # Portfolio heat gauge
            st.markdown("### 🔥 Portfolio Risk Heat")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                heat_pct = portfolio_heat * 100
                max_heat_pct = trader.max_portfolio_heat * 100
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=heat_pct,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Current Risk Exposure"},
                    delta={'reference': max_heat_pct},
                    gauge={
                        'axis': {'range': [None, max_heat_pct * 1.5]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, max_heat_pct * 0.5], 'color': "lightgreen"},
                            {'range': [max_heat_pct * 0.5, max_heat_pct], 'color': "yellow"},
                            {'range': [max_heat_pct, max_heat_pct * 1.5], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': max_heat_pct
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.metric("Current Heat", f"{heat_pct:.2f}%")
                st.metric("Max Heat", f"{max_heat_pct:.0f}%")
                if heat_pct >= max_heat_pct:
                    st.error("⚠️ Portfolio heat exceeded!")
                elif heat_pct >= max_heat_pct * 0.8:
                    st.warning("⚡ Approaching limit")
                else:
                    st.success("✅ Within limits")
            
            st.divider()
            
            # Active positions
            st.markdown("### 📈 Active Positions")
            positions_alpaca = trader.get_current_positions()
            
            if not positions_alpaca:
                st.info("No open positions currently")
            else:
                for pos in positions_alpaca:
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                        with col1:
                            st.markdown(f"### {pos['ticker']}")
                        with col2:
                            st.metric("Shares", f"{pos['qty']}")
                        with col3:
                            st.metric("Entry", f"${pos['entry_price']:.2f}")
                        with col4:
                            st.metric("Current", f"${pos['current_price']:.2f}")
                        with col5:
                            pnl_pct = pos['unrealized_pnl_pct']
                            st.metric("P/L", f"{pnl_pct:+.2f}%", f"${pos['unrealized_pnl']:+,.2f}")
                        st.markdown("---")
            
            st.divider()
            
            # Performance metrics
            st.markdown("### 📊 Performance Metrics")
            metrics = trader.performance_metrics
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", metrics['total_trades'])
            with col2:
                st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
            with col3:
                st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
            with col4:
                st.metric("Total P/L", f"{metrics['total_pnl_pct']:+.2f}%")
            
            # Win/Loss breakdown
            if metrics['total_trades'] > 0:
                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure(data=[go.Pie(
                        labels=['Winning Trades', 'Losing Trades'],
                        values=[metrics['winning_trades'], metrics['losing_trades']],
                        marker=dict(colors=['#00CC96', '#EF553B'])
                    )])
                    fig.update_layout(title="Win/Loss Distribution", height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = go.Figure(data=[
                        go.Bar(name='Avg Win', x=['Avg Win'], y=[metrics['avg_win']], marker_color='#00CC96'),
                        go.Bar(name='Avg Loss', x=['Avg Loss'], y=[abs(metrics['avg_loss'])], marker_color='#EF553B')
                    ])
                    fig.update_layout(title="Average Win vs Loss (%)", height=300)
                    st.plotly_chart(fig, use_container_width=True)
            
            # AI Lessons Learned
            st.divider()
            st.markdown("### 🧠 AI Lessons Learned")
            lessons = trader.lessons_learned
            if lessons:
                st.success(f"📚 {len(lessons)} lessons learned from past trades")
                for lesson in reversed(lessons[-10:]):
                    icon = "✅" if lesson['is_winning'] else "❌"
                    st.markdown(f"{icon} {lesson['lesson']}")
                    st.caption(f"{lesson['ticker']} - {datetime.fromisoformat(lesson['timestamp']).strftime('%Y-%m-%d')}")
            else:
                st.info("No lessons learned yet. AI will learn from completed trades.")
        
        except Exception as e:
            st.error(f"Error loading trader data: {e}")

# ============ TAB 4: BACKTESTING ============
with tab4:
    st.subheader("📈 Strategy Backtesting")
    
    st.markdown("Test your trading strategies on historical data")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().replace(year=2023, month=1, day=1).date())
        initial_capital = st.number_input("Initial Capital ($)", value=100000, step=10000)
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
        confidence_threshold = st.slider("Confidence Threshold", 1, 10, 7)
    
    if st.button("▶️ Run Backtest", use_container_width=True, type="primary"):
        with st.spinner("Running backtest... This may take a few minutes."):
            try:
                from backtesting.backtest_engine import BacktestEngine
                backtest = BacktestEngine(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    initial_capital=initial_capital,
                    confidence_threshold=confidence_threshold
                )
                st.info("🚧 Backtest engine initialized. Full backtest results display coming soon!")
                st.caption("The backtest engine is available. Full UI integration is in progress.")
            except Exception as e:
                st.error(f"Backtest error: {e}")
                st.info("Make sure all dependencies are installed")
    
    st.divider()
    st.markdown("### 📚 Backtesting Features")
    st.markdown("""
    **Available Capabilities:**
    - Test strategies on historical data
    - Calculate performance metrics
    - Compare different confidence thresholds
    - Analyze win rates and profit factors
    
    **Coming Soon:**
    - Full results visualization
    - Strategy comparison
    - Risk-adjusted returns
    - Drawdown analysis
    """)

# ============ TAB 5: ML LEARNING ============
with tab5:
    st.subheader("🧠 Machine Learning & Pattern Recognition")
    
    st.info("🚧 Coming Soon: ML analysis of past trades to improve future performance")
    
    st.markdown("### Planned Features:")
    st.markdown("""
    - **Pattern Recognition**: Identify what makes winning trades different from losing ones
    - **Risk Factor Correlation**: Analyze which risk factors correlate with success
    - **Strategy Optimization**: Automatically adjust scoring weights based on historical performance
    - **Trade Classification**: ML-based categorization of trade types and outcomes
    - **Predictive Modeling**: Predict trade success probability based on historical patterns
    - **Performance Attribution**: Understand which factors contribute most to returns
    
    **Data Sources:**
    - Trade history from autonomous trader
    - Scanner scores and outcomes
    - Market conditions at entry/exit
    - AI confidence scores and reasoning
    """)
    
    # Show some basic stats if we have trade data
    if trader and trader.trade_history:
        st.divider()
        st.markdown("### Current Trade Statistics (Pre-ML)")
        closed_trades = [t for t in trader.trade_history if t.get('status') == 'CLOSED']
        if closed_trades:
            st.metric("Total Closed Trades", len(closed_trades))
            wins = [t for t in closed_trades if t.get('pnl_pct', 0) > 0]
            st.metric("Winning Trades", len(wins))
            st.caption(f"Once ML is implemented, these {len(closed_trades)} trades will be analyzed to improve future performance")

# ============ TAB 6: COPY TRADES ============
with tab6:
    st.subheader("📋 Copy Trades - Easy Manual Execution")
    
    st.markdown("**Copy trades that the AI has executed or identified for manual execution in your broker**")
    
    # Initialize copied trades in session state if not exists
    if 'copied_trades' not in st.session_state:
        st.session_state['copied_trades'] = []
    
    copied = st.session_state['copied_trades']
    
    if copied:
        st.markdown(f"**{len(copied)} trades ready to copy**")
        
        for idx, trade in enumerate(copied):
            with st.expander(
                f"**{trade['ticker']}** - {trade.get('name', '')[:40]} | "
                f"Copied {datetime.fromisoformat(trade['copied_at']).strftime('%Y-%m-%d %H:%M')}",
                expanded=True
            ):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Entry Price", f"${trade['entry']:.2f}")
                with col2:
                    st.metric("Stop Loss", f"${trade['stop']:.2f}")
                with col3:
                    st.metric("Target Price", f"${trade['target']:.2f}")
                with col4:
                    if 'score' in trade:
                        st.metric("Score", f"{trade['score']}/100")
                
                # Calculate risk/reward
                risk = trade['entry'] - trade['stop']
                reward = trade['target'] - trade['entry']
                rr_ratio = reward / risk if risk > 0 else 0
                
                st.markdown(f"**Risk/Reward Ratio:** {rr_ratio:.2f}:1")
                
                # Trade details
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Trade Details:**")
                    st.markdown(f"- Entry: ${trade['entry']:.2f}")
                    st.markdown(f"- Stop Loss: ${trade['stop']:.2f} (${risk:.2f} risk)")
                    st.markdown(f"- Target: ${trade['target']:.2f} (${reward:.2f} reward)")
                
                with col2:
                    if portfolio:
                        portfolio_value = portfolio_manager.get_portfolio_value(portfolio)
                        # Calculate position size
                        max_loss_pct = portfolio.get('settings', {}).get('max_loss_per_trade', 2.0)
                        max_loss_amount = portfolio_value * (max_loss_pct / 100)
                        shares_by_risk = int(max_loss_amount / risk) if risk > 0 else 0
                        
                        st.markdown("**Suggested Position Size:**")
                        st.markdown(f"- Based on {max_loss_pct}% max loss")
                        st.markdown(f"- Shares: {shares_by_risk}")
                        st.markdown(f"- Position Value: ${shares_by_risk * trade['entry']:.2f}")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Mark as Executed", key=f"executed_{idx}"):
                        st.success(f"✅ {trade['ticker']} marked as executed!")
                        st.info("💡 Integration with your broker coming soon - for now, manually execute in your broker")
                
                with col2:
                    if st.button(f"❌ Remove", key=f"remove_{idx}"):
                        copied.pop(idx)
                        st.rerun()
        
        # Clear all button
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state['copied_trades'] = []
            st.rerun()
    else:
        st.info("👈 No copied trades yet. Copy trades from the **Scanner & Opportunities** tab!")
        st.markdown("""
        **How to Copy Trades:**
        1. Go to **Scanner & Opportunities** tab
        2. Find a hot stock you want to trade
        3. Click **"📋 Copy Trade"** button
        4. Come back here to see trade details
        5. Execute manually in your broker (or wait for broker integration)
        """)
    
    # Show recent completed trades from autonomous trader (if available)
    st.divider()
    st.markdown("### Recent Completed Trades (Available to Copy)")
    
    if trader:
        try:
            recent_trades = [t for t in trader.trade_history if t.get('status') == 'CLOSED'][-10:]
            if recent_trades:
                for trade in recent_trades:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"**{trade['ticker']}**")
                    with col2:
                        st.caption(f"{trade['action']} {trade['shares']} @ ${trade.get('entry_price', 0):.2f}")
                    with col3:
                        pnl_pct = trade.get('pnl_pct', 0)
                        st.caption(f"P/L: {pnl_pct:+.2f}%")
                    with col4:
                        if st.button(f"Copy", key=f"copy_from_history_{trade['ticker']}"):
                            if 'copied_trades' not in st.session_state:
                                st.session_state['copied_trades'] = []
                            st.session_state['copied_trades'].append({
                                'ticker': trade['ticker'],
                                'name': trade.get('name', trade['ticker']),
                                'entry': trade.get('entry_price', 0),
                                'stop': trade.get('stop_loss', 0),
                                'target': trade.get('target', 0),
                                'copied_at': datetime.now().isoformat()
                            })
                            st.success(f"✅ {trade['ticker']} added!")
                            st.rerun()
            else:
                st.caption("No completed trades yet")
        except:
            st.caption("Autonomous trader not available")
    else:
        st.caption("Autonomous trader not initialized")

st.divider()
st.caption("""
🚀 **Auto Trading Hub** - Unified platform for automated trading and portfolio management
- **Portfolio Overview**: Monitor positions, capital, and performance
- **Scanner & Opportunities**: Find and analyze trade opportunities  
- **Auto Trading**: Monitor autonomous trading system
- **Backtesting**: Test strategies on historical data
- **ML Learning**: Learn from past trades (coming soon)
- **Copy Trades**: Easy manual trade execution

⚠️ **Disclaimer:** Educational purposes only. Not financial advice.
""")

