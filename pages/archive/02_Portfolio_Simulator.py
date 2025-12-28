import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import PortfolioSimulator, StockAnalyzer

st.set_page_config(page_title="Portfolio Simulator", page_icon="🎲", layout="wide")

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.title("🎲 Portfolio Simulator")
st.markdown("*Monte Carlo simulations and risk analysis*")

simulator = PortfolioSimulator()
analyzer = StockAnalyzer()

# Sidebar
with st.sidebar:
    st.subheader("Simulation Parameters")
    
    monthly_amount = st.number_input("Monthly Contribution ($)", min_value=10, value=100, step=10)
    years = st.slider("Time Horizon (Years)", 1, 30, 5)
    
    st.divider()
    
    st.subheader("Return Assumptions")
    conservative_return = st.slider("Conservative (%)", 0.0, 15.0, 7.0, 0.5)
    moderate_return = st.slider("Moderate (%)", 0.0, 20.0, 8.5, 0.5)
    aggressive_return = st.slider("Aggressive (%)", 0.0, 25.0, 10.0, 0.5)
    
    volatility = st.slider("Volatility (%)", 5.0, 40.0, 15.0, 1.0)
    
    st.divider()
    
    num_simulations = st.selectbox("Simulations", [100, 500, 1000], index=1)
    
    run_sim = st.button("▶️ Run Simulation", use_container_width=True, type="primary")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Monte Carlo", "⚖️ Risk Parity", "💼 Position Sizing"])

with tab1:
    st.subheader("Monte Carlo Simulation")
    st.markdown("Visualize potential portfolio outcomes across multiple scenarios")
    
    if run_sim:
        with st.spinner(f"Running {num_simulations} simulations..."):
            all_sims = {"Conservative": [], "Moderate": [], "Aggressive": []}
            
            returns_map = {
                "Conservative": conservative_return / 100,
                "Moderate": moderate_return / 100,
                "Aggressive": aggressive_return / 100
            }
            
            for strategy, annual_return in returns_map.items():
                for _ in range(num_simulations):
                    balances, _ = simulator.simulate_monthly_investment(
                        monthly_amount, annual_return, years, volatility / 100
                    )
                    all_sims[strategy].append(balances)
            
            # Visualization
            fig = go.Figure()
            colors = {"Conservative": "#ff6b6b", "Moderate": "#4a9eff", "Aggressive": "#00d4aa"}
            months = list(range(years * 12 + 1))
            
            for strategy, sims in all_sims.items():
                sims_array = np.array(sims)
                median = np.median(sims_array, axis=0)
                p10 = np.percentile(sims_array, 10, axis=0)
                p90 = np.percentile(sims_array, 90, axis=0)
                
                # Median line
                fig.add_trace(go.Scatter(
                    x=months, y=median,
                    name=f"{strategy} (Median)",
                    line=dict(color=colors[strategy], width=3)
                ))
                
                # Shaded region
                fig.add_trace(go.Scatter(
                    x=months + months[::-1],
                    y=list(p90) + list(p10[::-1]),
                    fill='toself',
                    fillcolor=colors[strategy].replace(')', ', 0.1)').replace('rgb', 'rgba'),
                    line=dict(color='rgba(255,255,255,0)'),
                    name=f"{strategy} (10-90%)",
                    hoverinfo='skip'
                ))
            
            fig.update_layout(
                title=f"Portfolio Growth ({num_simulations} simulations)",
                xaxis_title="Months",
                yaxis_title="Value ($)",
                height=500,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
                hovermode='x unified'
            )
            
            fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')
            fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary stats
            st.divider()
            st.subheader("📊 Projection Summary")
            
            col1, col2, col3 = st.columns(3)
            
            for idx, (strategy, sims) in enumerate(all_sims.items()):
                final_values = [sim[-1] for sim in sims]
                
                with [col1, col2, col3][idx]:
                    st.markdown(f"### {strategy}")
                    st.metric("Median Final", f"${np.median(final_values):,.0f}")
                    st.metric("10th Percentile", f"${np.percentile(final_values, 10):,.0f}")
                    st.metric("90th Percentile", f"${np.percentile(final_values, 90):,.0f}")
                    
                    total_contrib = monthly_amount * years * 12
                    median_gain = np.median(final_values) - total_contrib
                    st.metric("Median Gain", f"${median_gain:,.0f}", 
                             f"{(median_gain/total_contrib*100):.1f}%")
    else:
        st.info("👈 Configure parameters and click 'Run Simulation'")

with tab2:
    st.subheader("⚖️ Risk Parity Allocation")
    st.markdown("Balance risk across asset classes (Dalio's All-Weather approach)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Traditional 60/40")
        fig1 = go.Figure(data=[go.Pie(
            labels=["Stocks", "Bonds"],
            values=[60, 40],
            marker=dict(colors=["#4a9eff", "#ff6b6b"])
        )])
        fig1.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0"))
        st.plotly_chart(fig1, use_container_width=True)
        
        st.markdown("""
        **Characteristics:**
        - Higher volatility
        - Equity-heavy risk
        - Better in bull markets
        """)
    
    with col2:
        st.markdown("### Risk Parity")
        fig2 = go.Figure(data=[go.Pie(
            labels=["Stocks", "Long-Term Bonds", "Intermediate Bonds", "Commodities"],
            values=[30, 40, 15, 15],
            marker=dict(colors=["#4a9eff", "#00d4aa", "#ffd93d", "#ff6b6b"])
        )])
        fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0"))
        st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("""
        **Characteristics:**
        - Lower volatility
        - Balanced risk exposure
        - All-weather performance
        """)
    
    st.divider()
    st.markdown("### 🎯 Recommended Allocation for Your Portfolio")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Conservative")
        st.markdown("- Stocks: 25%")
        st.markdown("- Bonds: 60%")
        st.markdown("- Commodities: 10%")
        st.markdown("- Cash: 5%")
    
    with col2:
        st.markdown("#### Moderate")
        st.markdown("- Stocks: 40%")
        st.markdown("- Bonds: 45%")
        st.markdown("- Commodities: 10%")
        st.markdown("- Cash: 5%")
    
    with col3:
        st.markdown("#### Aggressive")
        st.markdown("- Stocks: 55%")
        st.markdown("- Bonds: 30%")
        st.markdown("- Commodities: 10%")
        st.markdown("- Cash: 5%")

with tab3:
    st.subheader("💼 Position Sizing Calculator")
    st.markdown("Calculate safe position sizes based on risk management rules")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Input Parameters")
        
        portfolio_value = st.number_input("Portfolio Value ($)", min_value=100, value=1000, step=100)
        stock_price = st.number_input("Stock Price ($)", min_value=0.01, value=100.0, step=1.0)
        max_loss_pct = st.slider("Max Loss (%)", 1.0, 5.0, 2.0, 0.5)
        stop_loss_pct = st.slider("Stop Loss Distance (%)", 5.0, 20.0, 10.0, 1.0)
        
        if st.button("🧮 Calculate Position", use_container_width=True):
            result = simulator.calculate_position_size(
                portfolio_value, stock_price, max_loss_pct, stop_loss_pct
            )
            
            st.session_state['position_result'] = result
    
    with col2:
        st.markdown("### Calculation Results")
        
        if 'position_result' in st.session_state:
            result = st.session_state['position_result']
            
            st.metric("Shares to Buy", f"{result['shares']}")
            st.metric("Position Value", f"${result['position_value']:.2f}")
            st.metric("Stop Loss Price", f"${result['stop_loss_price']:.2f}")
            st.metric("Max Loss Amount", f"${result['max_loss']:.2f}")
            st.metric("Position Size", f"{result['position_pct']:.1f}% of portfolio")
            
            # Visual gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=result['position_pct'],
                title={'text': "Position Size %"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#00d4aa"},
                    'steps': [
                        {'range': [0, 5], 'color': "#00d4aa"},
                        {'range': [5, 10], 'color': "#ffd93d"},
                        {'range': [10, 100], 'color': "#ff6b6b"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 10
                    }
                }
            ))
            
            fig.update_layout(
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 Keep individual positions under 10% for diversification")
        else:
            st.info("Enter parameters and click 'Calculate Position'")
    
    st.divider()
    st.markdown("### 📚 Position Sizing Rules")
    
    st.markdown("""
    **Key Principles:**
    1. **2% Rule**: Never risk more than 2% of portfolio on a single trade
    2. **Stop Loss**: Set stops based on technical levels or volatility
    3. **Diversification**: Limit individual positions to 5-10% of portfolio
    4. **Correlation**: Reduce positions in highly correlated stocks
    5. **Rebalancing**: Adjust positions quarterly or when allocations drift >5%
    
    **Example:** $1,000 portfolio, $100 stock, 2% max loss, 10% stop
    - Max loss: $20
    - Shares: 2 shares
    - Position: $200 (20% of portfolio)
    - Stop price: $90
    """)

st.divider()
st.caption("⚠️ Simulations are probabilistic models, not guarantees. Past performance doesn't predict future results.")
