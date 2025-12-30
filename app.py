import streamlit as st

# IMPORTANT: st.set_page_config must be the FIRST Streamlit call
st.set_page_config(
    page_title="Personal Hedge Fund Manager",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import sys
import threading
from pathlib import Path
from dotenv import load_dotenv

# Add utils to path for Dexter
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

# Load environment variables (for local development)
# Streamlit Cloud uses st.secrets instead
try:
    load_dotenv()
except UnicodeDecodeError:
    # Handle encoding issues with .env file
    import io
    try:
        with open('.env', 'rb') as f:
            content = f.read()
            # Try to decode as UTF-8, ignoring errors
            content_str = content.decode('utf-8', errors='ignore')
            # Write back as proper UTF-8
            with open('.env', 'w', encoding='utf-8') as f_out:
                f_out.write(content_str)
        load_dotenv()
    except FileNotFoundError:
        # .env file doesn't exist, that's okay (using Streamlit secrets)
        pass
    except Exception:
        # If still fails, just skip loading .env (using Streamlit secrets)
        pass

# Set environment variables from Streamlit secrets (for cloud deployment)
# This allows utils to access secrets via os.getenv()
try:
    if hasattr(st, 'secrets'):
        # Map Streamlit secrets to environment variables
        secret_keys = ['XAI_API_KEY', 'ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 
                      'POLYGON_API_KEY', 'SENDGRID_API_KEY', 'DEXTER_NEWSADMIN_PATH']
        for key in secret_keys:
            try:
                if key in st.secrets:
                    os.environ[key] = str(st.secrets[key])
            except Exception:
                pass
except Exception:
    # Not running on Streamlit Cloud, use .env file
    pass

# Auto-start Dexter service in background
def _start_dexter_background():
    """Start Dexter service in background thread"""
    import time
    try:
        from dexter_manager import DexterManager
        
        manager = DexterManager()
        if not manager.is_running():
            # Start the service (non-blocking)
            success, message = manager.start(wait_for_ready=False, timeout=0)
            if success:
                # Store manager in session state to keep process reference
                st.session_state.dexter_manager = manager
                st.session_state.dexter_started = True
                st.session_state.dexter_start_message = "Starting Dexter..."
                
                # Wait a bit and check if it's ready (non-blocking check)
                time.sleep(3)
                if manager.is_running():
                    st.session_state.dexter_start_message = "✅ Dexter is ready"
                else:
                    st.session_state.dexter_start_message = "⏳ Dexter is starting (may take 10-15 seconds)..."
            else:
                st.session_state.dexter_start_error = message
        else:
            st.session_state.dexter_manager = manager
            st.session_state.dexter_started = True
            st.session_state.dexter_start_message = "✅ Dexter is already running"
    except ImportError:
        # Dexter manager not available, skip silently
        pass
    except Exception as e:
        # Silently fail - don't break the app if Dexter can't start
        st.session_state.dexter_start_error = str(e)

# Initialize Dexter on first run
if 'dexter_started' not in st.session_state:
    st.session_state.dexter_started = False
    # Start in background thread so it doesn't block Streamlit
    thread = threading.Thread(target=_start_dexter_background, daemon=True)
    thread.start()

def load_css():
    try:
        with open("custom.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

# Sidebar
with st.sidebar:
    st.title("📊 Fund Settings")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # Show Dexter status if available
        if 'dexter_started' in st.session_state:
            if 'dexter_manager' in st.session_state:
                try:
                    is_running = st.session_state.dexter_manager.is_running()
                    if is_running:
                        st.caption("🤖 Dexter: ✅ Running")
                    else:
                        st.caption("🤖 Dexter: ⏳ Starting...")
                except:
                    st.caption("🤖 Dexter: 🔄 Checking...")
    with col2:
        st.button("🌓", on_click=toggle_theme, help="Toggle theme")
    
    st.divider()
    
    st.subheader("Investment Parameters")
    monthly_contribution = st.number_input(
        "Monthly Contribution ($)",
        min_value=10,
        max_value=10000,
        value=100,
        step=10
    )
    
    risk_tolerance = st.slider(
        "Risk Tolerance",
        min_value=1,
        max_value=10,
        value=5,
        help="1=Conservative, 10=Aggressive"
    )
    
    max_loss_per_trade = st.slider(
        "Max Loss Per Trade (%)",
        min_value=1.0,
        max_value=5.0,
        value=2.0,
        step=0.5
    )
    
    st.divider()
    
    st.subheader("Watchlist")
    default_tickers = ["NVDA", "JPM", "HOOD", "AAPL", "MSFT"]
    watchlist = st.multiselect(
        "Select Stocks",
        options=default_tickers,
        default=default_tickers[:3]
    )
    
    st.divider()
    
    st.subheader("Strategy Mix")
    buffett_weight = st.slider("Buffett (Value)", 0, 100, 40)
    dalio_weight = st.slider("Dalio (Risk Parity)", 0, 100, 30)
    simons_weight = st.slider("Simons (Quant)", 0, 100, 30)
    
    total_weight = buffett_weight + dalio_weight + simons_weight
    if total_weight != 100:
        st.warning(f"Weights sum to {total_weight}%. Adjust to 100%.")

# Main content
st.title("🏦 Personal Hedge Fund Manager")
st.markdown("*Inspired by Buffett, Dalio, and Simons*")

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Monthly Investment", f"${monthly_contribution}", "Active")

with col2:
    projected = monthly_contribution * 12 * 1.085
    st.metric("Projected Year 1", f"${projected:,.0f}", "8.5% return")

with col3:
    st.metric("Risk Level", f"{risk_tolerance}/10", f"{max_loss_per_trade}% max loss")

with col4:
    st.metric("Active Stocks", len(watchlist), "Monitored")

st.divider()

# Portfolio overview
st.subheader("📊 Portfolio Overview")

fig_allocation = go.Figure(data=[go.Pie(
    labels=["Growth Stocks", "Value Stocks", "Cash Reserve"],
    values=[50, 35, 15],
    hole=0.4,
    marker=dict(colors=["#00d4aa", "#4a9eff", "#ff6b6b"]),
    textinfo="label+percent",
    textposition="outside"
)])

fig_allocation.update_layout(
    title="Current Allocation",
    height=400,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e0e0e0")
)

col1, col2 = st.columns([1, 1])

with col1:
    st.plotly_chart(fig_allocation, use_container_width=True)

with col2:
    months = list(range(1, 61))
    balance_conservative = [monthly_contribution * m * (1 + 0.07/12)**m for m in months]
    balance_moderate = [monthly_contribution * m * (1 + 0.085/12)**m for m in months]
    balance_aggressive = [monthly_contribution * m * (1 + 0.10/12)**m for m in months]
    
    fig_projection = go.Figure()
    
    fig_projection.add_trace(go.Scatter(
        x=months, y=balance_conservative,
        name="Conservative (7%)",
        line=dict(color="#ff6b6b", width=2),
        fill='tonexty',
        fillcolor='rgba(255,107,107,0.1)'
    ))
    
    fig_projection.add_trace(go.Scatter(
        x=months, y=balance_moderate,
        name="Moderate (8.5%)",
        line=dict(color="#4a9eff", width=3),
        fill='tonexty',
        fillcolor='rgba(74,158,255,0.1)'
    ))
    
    fig_projection.add_trace(go.Scatter(
        x=months, y=balance_aggressive,
        name="Aggressive (10%)",
        line=dict(color="#00d4aa", width=2),
        fill='tonexty',
        fillcolor='rgba(0,212,170,0.1)'
    ))
    
    fig_projection.update_layout(
        title=f"5-Year Projection (${monthly_contribution}/month)",
        xaxis_title="Months",
        yaxis_title="Portfolio Value ($)",
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig_projection, use_container_width=True)

st.divider()

# Strategy insights
st.subheader("💡 Strategy Insights")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🎯 Buffett Approach")
    st.markdown("""
    - **Focus**: Value & Safety
    - **Metrics**: P/E < 15, ROE > 15%
    - **Target**: Long-term holdings
    - **Risk**: Low volatility
    """)

with col2:
    st.markdown("### ⚖️ Dalio Approach")
    st.markdown("""
    - **Focus**: Risk Parity
    - **Metrics**: Diversification balance
    - **Target**: All-weather portfolio
    - **Risk**: Balanced exposure
    """)

with col3:
    st.markdown("### 🔬 Simons Approach")
    st.markdown("""
    - **Focus**: Quantitative signals
    - **Metrics**: Statistical patterns
    - **Target**: Data-driven trades
    - **Risk**: Systematic rules
    """)

st.divider()

# Quick actions
st.subheader("⚡ Quick Actions")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("📈 Analyze Stocks", use_container_width=True):
        st.switch_page("pages/01_Stock_Analyzer.py")

with col2:
    if st.button("🚀 Auto Trading Hub", use_container_width=True, type="primary"):
        st.switch_page("pages/02_Auto_Trading_Hub.py")

with col3:
    if st.button("🔍 Stock Scanner", use_container_width=True):
        st.switch_page("pages/02_Auto_Trading_Hub.py")
        st.session_state['active_tab'] = 'Scanner'

with col4:
    if st.button("🤖 Auto Trader", use_container_width=True):
        st.switch_page("pages/02_Auto_Trading_Hub.py")
        st.session_state['active_tab'] = 'Auto Trading'

with col5:
    if st.button("📋 Personal Trades", use_container_width=True):
        st.switch_page("pages/05_Personal_Trades.py")

st.divider()
st.caption("⚠️ Disclaimer: Educational purposes only. Not financial advice.")
