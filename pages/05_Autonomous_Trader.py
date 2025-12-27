# ============================================================================
# FILE: pages/05_Autonomous_Trader.py
# Dashboard for monitoring autonomous AI trader
# ============================================================================

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Autonomous Trader", page_icon="🤖", layout="wide")

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

# Header
st.title("🤖 Autonomous AI Trader")
st.markdown("*Fully automated trading system with AI decision-making*")

# Load trade history
def load_trade_history():
    try:
        with open('data/trade_history_auto.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'trades': [], 'performance': {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0
        }}
    except Exception as e:
        st.error(f"Error loading trade history: {e}")
        return {'trades': [], 'performance': {}}

data = load_trade_history()
trades = data.get('trades', [])
performance = data.get('performance', {})

# Status Banner
st.markdown("---")

# System Status
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎯 System Status")
    
    # Check if trader is running (simplified - in production would ping actual process)
    trader_status = "🟢 ACTIVE" if os.path.exists('data/trade_history_auto.json') else "🔴 NOT RUNNING"
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.metric("Trader Status", trader_status)
    
    with status_col2:
        mode = "📄 PAPER TRADING" if True else "💵 LIVE TRADING"
        st.metric("Trading Mode", mode)
    
    with status_col3:
        open_positions = len([t for t in trades if t.get('status') == 'OPEN'])
        st.metric("Open Positions", open_positions)

with col2:
    st.info("""
    **How to Run:**
    ```bash
    python trader/run_autonomous.py
    ```
    
    Press Ctrl+C to stop safely.
    """)

st.markdown("---")

# Performance Metrics
st.subheader("📊 Performance Overview")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    total_trades = performance.get('total_trades', 0)
    st.metric("Total Trades", total_trades)

with metric_col2:
    win_rate = performance.get('win_rate', 0)
    color = "normal" if win_rate >= 55 else "inverse"
    st.metric("Win Rate", f"{win_rate:.1f}%", delta=f"{win_rate-50:.1f}% vs 50%", delta_color=color)

with metric_col3:
    total_profit = performance.get('total_profit', 0)
    st.metric("Total P/L", f"${total_profit:.2f}", delta=f"${total_profit:.2f}")

with metric_col4:
    winning = performance.get('winning_trades', 0)
    losing = performance.get('losing_trades', 0)
    st.metric("W/L Ratio", f"{winning}/{losing}")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Active Positions", "📊 Trade History", "🧠 AI Insights", "⚙️ Settings"])

# TAB 1: Active Positions
with tab1:
    st.subheader("🔥 Current Positions")
    
    open_trades = [t for t in trades if t.get('status') == 'OPEN']
    
    if open_trades:
        for trade in open_trades:
            with st.expander(f"**{trade['ticker']}** - {trade['shares']} shares @ ${trade['entry_price']:.2f}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Entry:** ${trade['entry_price']:.2f}")
                    st.markdown(f"**Position Value:** ${trade['position_value']:.2f}")
                    st.markdown(f"**Opened:** {datetime.fromisoformat(trade['executed_at']).strftime('%b %d, %I:%M%p')}")
                
                with col2:
                    st.markdown(f"**Stop Loss:** ${trade['stop_loss']:.2f}")
                    st.markdown(f"**Target:** ${trade['target']:.2f}")
                    risk_reward = (trade['target'] - trade['entry_price']) / (trade['entry_price'] - trade['stop_loss'])
                    st.markdown(f"**R/R Ratio:** {risk_reward:.2f}:1")
                
                with col3:
                    st.markdown(f"**Confidence:** {trade['confidence']}/10")
                    st.markdown(f"**Order ID:** {trade['order_id'][:8]}...")
                
                st.markdown(f"**🤖 AI Reasoning:** {trade['reasoning']}")
                
                # Progress bar for price vs targets
                current_range = trade['target'] - trade['stop_loss']
                if current_range > 0:
                    current_pct = ((trade['entry_price'] - trade['stop_loss']) / current_range) * 100
                    st.progress(current_pct / 100, f"Entry point: {current_pct:.0f}% toward target")
    else:
        st.info("No open positions. The AI is scanning for opportunities...")
        st.markdown("""
        **The trader will open positions when:**
        - Hot stocks are available (run scanner)
        - AI confidence >= 7/10
        - Risk/reward ratio >= 2:1
        - Sufficient buying power available
        """)

# TAB 2: Trade History
with tab2:
    st.subheader("📜 Complete Trade History")
    
    closed_trades = [t for t in trades if t.get('status') == 'CLOSED']
    
    if closed_trades:
        # Create DataFrame
        df_trades = pd.DataFrame([{
            'Trade #': t['trade_id'],
            'Ticker': t['ticker'],
            'Shares': t['shares'],
            'Entry': f"${t['entry_price']:.2f}",
            'Exit': f"${t.get('exit_price', 0):.2f}",
            'P/L': f"${t.get('profit_loss', 0):.2f}",
            'P/L %': f"{t.get('profit_pct', 0):.2f}%",
            'Result': t.get('outcome', 'OPEN'),
            'Reason': t.get('exit_reason', 'N/A'),
            'Date': datetime.fromisoformat(t['executed_at']).strftime('%b %d')
        } for t in closed_trades])
        
        # Color code results
        def highlight_result(row):
            if row['Result'] == 'WIN':
                return ['background-color: rgba(0, 255, 0, 0.1)'] * len(row)
            elif row['Result'] == 'LOSS':
                return ['background-color: rgba(255, 0, 0, 0.1)'] * len(row)
            return [''] * len(row)
        
        st.dataframe(
            df_trades.style.apply(highlight_result, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        # P/L Chart
        st.markdown("### 📈 Cumulative P/L Over Time")
        
        cumulative_pl = []
        running_total = 0
        dates = []
        
        for trade in closed_trades:
            running_total += trade.get('profit_loss', 0)
            cumulative_pl.append(running_total)
            dates.append(datetime.fromisoformat(trade['executed_at']))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative_pl,
            mode='lines+markers',
            name='Cumulative P/L',
            line=dict(color='#00ff00' if running_total > 0 else '#ff0000', width=2),
            fill='tozeroy'
        ))
        
        fig.update_layout(
            title='Cumulative Profit/Loss',
            xaxis_title='Date',
            yaxis_title='P/L ($)',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Win/Loss Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Win/Loss Distribution")
            wins = len([t for t in closed_trades if t.get('outcome') == 'WIN'])
            losses = len([t for t in closed_trades if t.get('outcome') == 'LOSS'])
            
            fig = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses'],
                values=[wins, losses],
                marker=dict(colors=['#00ff00', '#ff0000']),
                hole=0.4
            )])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 💰 P/L Distribution")
            pl_values = [t.get('profit_loss', 0) for t in closed_trades]
            
            fig = go.Figure(data=[go.Histogram(
                x=pl_values,
                nbinsx=20,
                marker=dict(color='#00ff00', opacity=0.7)
            )])
            fig.update_layout(
                xaxis_title='P/L ($)',
                yaxis_title='Frequency',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No closed trades yet. Positions will appear here when closed.")

# TAB 3: AI Insights
with tab3:
    st.subheader("🧠 AI Learning & Insights")
    
    # Show lessons learned from closed trades
    closed_with_lessons = [t for t in closed_trades if 'lesson_learned' in t]
    
    if closed_with_lessons:
        st.markdown("### 📚 Lessons Learned")
        
        for trade in closed_with_lessons[-10:]:  # Last 10 lessons
            outcome_emoji = "✅" if trade.get('outcome') == 'WIN' else "❌"
            
            with st.expander(f"{outcome_emoji} {trade['ticker']} - {datetime.fromisoformat(trade['executed_at']).strftime('%b %d')}"):
                st.markdown(f"**Trade Result:** {trade['outcome']} ({trade.get('profit_pct', 0):+.2f}%)")
                st.markdown(f"**Original Reasoning:** {trade['reasoning']}")
                st.markdown(f"**Lesson Learned:** {trade['lesson_learned']}")
    else:
        st.info("Lessons will appear here as the AI closes trades and learns from them.")
    
    st.markdown("---")
    
    # Strategy Insights
    st.markdown("### 📊 Strategy Analysis")
    
    if closed_trades:
        # Calculate metrics by confidence level
        confidence_groups = {}
        for trade in closed_trades:
            conf = trade.get('confidence', 0)
            if conf not in confidence_groups:
                confidence_groups[conf] = {'wins': 0, 'total': 0, 'total_pl': 0}
            
            confidence_groups[conf]['total'] += 1
            if trade.get('outcome') == 'WIN':
                confidence_groups[conf]['wins'] += 1
            confidence_groups[conf]['total_pl'] += trade.get('profit_loss', 0)
        
        # Create confidence analysis chart
        conf_data = []
        for conf, stats in sorted(confidence_groups.items()):
            win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            conf_data.append({
                'Confidence': conf,
                'Win Rate': win_rate,
                'Trades': stats['total'],
                'Avg P/L': stats['total_pl'] / stats['total']
            })
        
        df_conf = pd.DataFrame(conf_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_conf['Confidence'],
            y=df_conf['Win Rate'],
            name='Win Rate %',
            marker=dict(color=df_conf['Win Rate'], colorscale='RdYlGn', showscale=True)
        ))
        
        fig.update_layout(
            title='Win Rate by AI Confidence Level',
            xaxis_title='Confidence (1-10)',
            yaxis_title='Win Rate (%)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_conf, use_container_width=True, hide_index=True)
    else:
        st.info("Strategy insights will appear as trades accumulate.")

# TAB 4: Settings
with tab4:
    st.subheader("⚙️ Trader Configuration")
    
    st.markdown("""
    ### Current Settings
    
    Edit these in `trader/autonomous_trader.py`:
    
    ```python
    self.max_position_size = 0.10      # 10% of portfolio per trade
    self.max_loss_per_trade = 0.02     # 2% max loss per trade  
    self.confidence_threshold = 7      # Only trade if AI confidence >= 7/10
    ```
    
    ### Risk Parameters
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Max Position Size:** 10% of portfolio
        - With $1000 account = max $100 per trade
        - With $10,000 account = max $1000 per trade
        
        **Max Loss Per Trade:** 2% of account
        - With $1000 account = max $20 loss
        - With $10,000 account = max $200 loss
        """)
    
    with col2:
        st.markdown("""
        **Confidence Threshold:** 7/10
        - AI must be at least 70% confident
        - Higher = fewer but higher quality trades
        - Lower = more trades but potentially lower quality
        
        **Risk/Reward Minimum:** 2:1
        - For every $1 risked, potential to make $2
        - Ensures favorable odds even with <50% win rate
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 🔐 API Keys Setup
    
    Make sure your `.env` file has:
    
    ```
    XAI_API_KEY=your_xai_key_here
    ALPACA_API_KEY=your_alpaca_key_here
    ALPACA_SECRET_KEY=your_alpaca_secret_here
    ```
    
    Get Alpaca keys at: https://alpaca.markets/
    - Start with paper trading (free, fake money)
    - Switch to live when proven profitable
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 🚀 Running the Trader
    
    **Option 1: Terminal (Recommended)**
    ```bash
    python trader/run_autonomous.py
    ```
    
    **Option 2: Background Process**
    ```bash
    # Linux/Mac
    nohup python trader/run_autonomous.py &
    
    # Windows
    pythonw trader/run_autonomous.py
    ```
    
    **Option 3: Cloud Deployment**
    - Deploy to AWS/GCP/Azure
    - Run as a cron job or service
    - Ensure secure key storage
    """)

# Footer
st.markdown("---")
st.markdown("""
**⚠️ Important Notes:**
- Always start with paper trading to validate strategy
- Monitor performance for at least 1-3 months before using real money
- The AI learns from each trade - performance improves over time
- Never invest more than you can afford to lose
- This is not financial advice - use at your own risk
""")
