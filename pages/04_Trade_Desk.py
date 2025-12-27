# ============================================================================
# FILE 6: pages/04_Trade_Desk.py
# Main UI for viewing and acting on trade opportunities
# ============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.storage import StorageManager

st.set_page_config(page_title="Trade Desk", page_icon="🔥", layout="wide")

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

# Initialize storage
storage = StorageManager()

# Load data
hot_data = storage.load_hot_stocks()
warming_data = storage.load_warming_stocks()
watching_data = storage.load_watching_stocks()
progress = storage.load_scan_progress()

# Header
st.title("🔥 Trade Desk")
st.markdown("*Your personalized trade opportunities, updated daily*")

# Scan status bar
col1, col2, col3, col4 = st.columns(4)

with col1:
    last_scan = progress.get('last_scan')
    if last_scan:
        scan_time = datetime.fromisoformat(last_scan).strftime("%b %d, %I:%M%p")
        st.metric("Last Scan", scan_time)
    else:
        st.metric("Last Scan", "Not yet run")

with col2:
    st.metric("🔥 Hot", hot_data.get('count', 0))

with col3:
    st.metric("🟡 Warming", warming_data.get('count', 0))

with col4:
    st.metric("👀 Watching", watching_data.get('count', 0))

st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Hot Opportunities", "🟡 Warming Up", "👀 Watching", "📊 Trade History"])

# ============ HOT OPPORTUNITIES TAB ============
with tab1:
    st.subheader("🔥 Ready to Trade NOW")
    
    hot_stocks = hot_data.get('stocks', [])
    
    if not hot_stocks:
        st.info("💤 No hot opportunities yet. The scanner runs daily at 9:30am ET. Check back tomorrow!")
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
            stock_types = list(set([s['stock_type'] for s in hot_stocks]))
            selected_type = st.multiselect("Stock Type", stock_types, default=stock_types)
        
        with col2:
            max_price = st.number_input("Max Price ($)", min_value=0, value=1000, step=50)
        
        with col3:
            min_score = st.slider("Min Score", 80, 100, 80)
        
        # Filter stocks
        filtered = [
            s for s in hot_stocks 
            if s['stock_type'] in selected_type 
            and s['fundamentals']['current_price'] <= max_price
            and s['score']['total_score'] >= min_score
        ]
        
        st.markdown(f"**Showing {len(filtered)} of {len(hot_stocks)} hot stocks**")
        
        # Display as cards
        for stock in filtered[:10]:  # Show top 10
            with st.expander(
                f"**{stock['ticker']}** - {stock['name']} | Score: {stock['score']['total_score']}/100 | "
                f"${stock['fundamentals']['current_price']:.2f}",
                expanded=False
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"### 📊 Trade Plan")
                    st.markdown(f"**Entry:** ${stock['trade_plan']['entry_price']}")
                    st.markdown(f"**Stop Loss:** ${stock['trade_plan']['stop_loss']} (-{((stock['trade_plan']['entry_price'] - stock['trade_plan']['stop_loss']) / stock['trade_plan']['entry_price'] * 100):.1f}%)")
                    st.markdown(f"**Target:** ${stock['trade_plan']['target']} (+{((stock['trade_plan']['target'] - stock['trade_plan']['entry_price']) / stock['trade_plan']['entry_price'] * 100):.1f}%)")
                    st.markdown(f"**Risk/Reward:** {stock['trade_plan']['risk_reward_ratio']:.2f}:1")
                    
                    st.markdown(f"### 📈 Fundamentals")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("P/E Ratio", f"{stock['fundamentals']['pe_ratio']:.1f}")
                    with col_b:
                        st.metric("Revenue Growth", f"{stock['fundamentals']['revenue_growth']:.1f}%")
                    with col_c:
                        st.metric("ROE", f"{stock['fundamentals']['roe']:.1f}%")
                
                with col2:
                    st.markdown(f"### 🎯 Score Breakdown")
                    st.markdown(f"**Type:** {stock['stock_type']}")
                    st.markdown(f"**Rating:** {stock['rating']}")
                    st.markdown(f"**Grade:** {stock['score']['grade']}")
                    
                    # Score breakdown chart
                    fig = go.Figure(go.Bar(
                        x=list(stock['score']['breakdown'].values()),
                        y=list(stock['score']['breakdown'].keys()),
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
                    if st.button(f"📝 Log Trade", key=f"log_{stock['ticker']}"):
                        st.session_state[f'logging_{stock["ticker"]}'] = True
                
                with col2:
                    if st.button(f"📈 View Chart", key=f"chart_{stock['ticker']}"):
                        st.switch_page("pages/01_Stock_Analyzer.py")
                
                with col3:
                    if st.button(f"❌ Remove", key=f"remove_{stock['ticker']}"):
                        # Remove from hot list
                        hot_stocks.remove(stock)
                        storage.save_hot_stocks(hot_stocks)
                        st.rerun()
                
                with col4:
                    if st.button(f"🔄 Refresh", key=f"refresh_{stock['ticker']}"):
                        st.info("Re-scan feature coming soon!")
                
                # Trade logging form
                if st.session_state.get(f'logging_{stock["ticker"]}', False):
                    with st.form(f"trade_form_{stock['ticker']}"):
                        st.markdown("### Log This Trade")
                        
                        shares = st.number_input("Shares", min_value=1, value=10)
                        entry_price = st.number_input("Entry Price", value=stock['trade_plan']['entry_price'])
                        notes = st.text_area("Notes (optional)")
                        
                        submitted = st.form_submit_button("✅ Log Trade")
                        
                        if submitted:
                            trade = {
                                'ticker': stock['ticker'],
                                'name': stock['name'],
                                'shares': shares,
                                'entry_price': entry_price,
                                'total_cost': shares * entry_price,
                                'stop_loss': stock['trade_plan']['stop_loss'],
                                'target': stock['trade_plan']['target'],
                                'notes': notes,
                                'score': stock['score']['total_score'],
                                'stock_type': stock['stock_type']
                            }
                            storage.add_trade(trade)
                            st.success(f"✅ Logged: {shares} shares of {stock['ticker']} at ${entry_price:.2f}")
                            st.session_state[f'logging_{stock["ticker"]}'] = False
                            st.rerun()

# ============ WARMING UP TAB ============
with tab2:
    st.subheader("🟡 Almost There - Watch These Closely")
    
    warming_stocks = warming_data.get('stocks', [])
    
    if not warming_stocks:
        st.info("No warming stocks yet. These appear when stocks score 70-79 points.")
    else:
        st.markdown(f"**{len(warming_stocks)} stocks are close to our targets**")
        
        # Create table view
        warming_df = pd.DataFrame([
            {
                'Ticker': s['ticker'],
                'Name': s['name'][:30],
                'Type': s['stock_type'],
                'Score': s['score']['total_score'],
                'Price': f"${s['fundamentals']['current_price']:.2f}",
                'P/E': f"{s['fundamentals']['pe_ratio']:.1f}",
                'Growth': f"{s['fundamentals']['revenue_growth']:.1f}%",
                'What\'s Needed': f"{80 - s['score']['total_score']:.0f} more points"
            }
            for s in warming_stocks[:20]
        ])
        
        st.dataframe(warming_df, use_container_width=True, hide_index=True)
        
        st.markdown("""
        **These stocks get checked daily.** When they hit 80+ score, they'll automatically move to Hot! 🔥
        """)

# ============ WATCHING TAB ============
with tab3:
    st.subheader("👀 Long-Term Tracking")
    
    watching_stocks = watching_data.get('stocks', [])
    
    if not watching_stocks:
        st.info("No watching stocks yet. These appear when stocks score 60-69 points.")
    else:
        st.markdown(f"**{len(watching_stocks)} stocks on the radar**")
        
        watching_df = pd.DataFrame([
            {
                'Ticker': s['ticker'],
                'Name': s['name'][:30],
                'Type': s['stock_type'],
                'Score': s['score']['total_score'],
                'Price': f"${s['fundamentals']['current_price']:.2f}",
            }
            for s in watching_stocks[:30]
        ])
        
        st.dataframe(watching_df, use_container_width=True, hide_index=True)

# ============ TRADE HISTORY TAB ============
with tab4:
    st.subheader("📊 Your Trade History")
    
    history = storage.load_trade_history()
    trades = history.get('trades', [])
    
    if not trades:
        st.info("No trades logged yet. Execute a trade from the Hot tab to start tracking!")
    else:
        st.markdown(f"**{len(trades)} trades logged**")
        
        # Summary metrics
        total_invested = sum(t['total_cost'] for t in trades)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", len(trades))
        with col2:
            st.metric("Total Invested", f"${total_invested:,.2f}")
        with col3:
            avg_score = sum(t['score'] for t in trades) / len(trades)
            st.metric("Avg Trade Score", f"{avg_score:.1f}/100")
        
        # Trade table
        trade_df = pd.DataFrame([
            {
                'Date': datetime.fromisoformat(t['executed_at']).strftime('%Y-%m-%d'),
                'Ticker': t['ticker'],
                'Shares': t['shares'],
                'Entry': f"${t['entry_price']:.2f}",
                'Cost': f"${t['total_cost']:.2f}",
                'Stop': f"${t['stop_loss']:.2f}",
                'Target': f"${t['target']:.2f}",
                'Score': t['score']
            }
            for t in trades
        ])
        
        st.dataframe(trade_df, use_container_width=True, hide_index=True)
        
        # Export
        if st.button("📥 Export History (CSV)"):
            csv = trade_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "trade_history.csv",
                "text/csv"
            )

# Footer
st.divider()
st.caption("""
💡 **How it works:** The scanner runs automatically every morning at 9:30am ET. 
Hot stocks (80+ score) are ready to trade. Warming stocks (70-79) are checked daily and promoted when ready.
⚠️ This is educational only. Not financial advice.
""")

