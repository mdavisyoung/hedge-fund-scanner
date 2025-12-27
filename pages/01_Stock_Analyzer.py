import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import StockAnalyzer, XAIStrategyGenerator

st.set_page_config(page_title="Stock Analyzer", page_icon="📈", layout="wide")

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.title("📈 Stock Analyzer")
st.markdown("*Deep-dive analysis with AI-powered recommendations*")

analyzer = StockAnalyzer()
strategy_gen = XAIStrategyGenerator()

with st.sidebar:
    st.subheader("Analysis Settings")
    
    ticker = st.text_input("Ticker Symbol", value="NVDA").upper()
    time_period = st.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    
    st.divider()
    st.subheader("Your Preferences")
    monthly_contribution = st.number_input("Monthly Budget ($)", min_value=10, value=100)
    risk_tolerance = st.slider("Risk Tolerance", 1, 10, 5)
    max_loss_per_trade = st.slider("Max Loss Per Trade (%)", 1.0, 5.0, 2.0, 0.5)
    
    analyze_button = st.button("🔍 Analyze", use_container_width=True, type="primary")

if analyze_button and ticker:
    with st.spinner(f"Analyzing {ticker}..."):
        evaluation = analyzer.evaluate_stock(ticker)
        
        if "error" in evaluation:
            st.error(f"❌ {evaluation['error']}")
        else:
            fundamentals = evaluation["fundamentals"]
            stock_type = evaluation["stock_type"]
            scores = evaluation["scores"]
            rating = evaluation["rating"]
            
            # Header metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Price", f"${fundamentals['current_price']:.2f}")
            
            with col2:
                color = "🟢" if rating == "BUY" else "🟡" if rating == "HOLD" else "🔴"
                st.metric("Rating", f"{color} {rating}")
            
            with col3:
                st.metric("Stock Type", stock_type)
            
            with col4:
                score_pct = (evaluation['passed'] / evaluation['total']) * 100
                st.metric("Score", f"{evaluation['passed']}/{evaluation['total']}", f"{score_pct:.0f}%")
            
            st.divider()
            
            # Price chart
            st.subheader("📊 Price Chart with Strategy Overlays")
            
            hist_data = analyzer.get_stock_data(ticker, time_period)
            
            if hist_data is not None and not hist_data.empty:
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f"{ticker} Price Action", "Volume")
                )
                
                # Candlestick
                fig.add_trace(
                    go.Candlestick(
                        x=hist_data.index,
                        open=hist_data['Open'],
                        high=hist_data['High'],
                        low=hist_data['Low'],
                        close=hist_data['Close'],
                        name="Price"
                    ),
                    row=1, col=1
                )
                
                # Stop-loss line
                current_price = fundamentals['current_price']
                stop_loss = current_price * (1 - max_loss_per_trade / 100)
                
                fig.add_hline(
                    y=stop_loss,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Stop Loss: ${stop_loss:.2f}",
                    row=1, col=1
                )
                
                # 52-week high/low
                fig.add_hline(
                    y=fundamentals['fifty_two_week_high'],
                    line_dash="dot",
                    line_color="green",
                    annotation_text="52W High",
                    row=1, col=1
                )
                
                fig.add_hline(
                    y=fundamentals['fifty_two_week_low'],
                    line_dash="dot",
                    line_color="orange",
                    annotation_text="52W Low",
                    row=1, col=1
                )
                
                # Volume
                colors = ['red' if hist_data['Close'].iloc[i] < hist_data['Open'].iloc[i] 
                         else 'green' for i in range(len(hist_data))]
                
                fig.add_trace(
                    go.Bar(x=hist_data.index, y=hist_data['Volume'], name="Volume", marker_color=colors, showlegend=False),
                    row=2, col=1
                )
                
                fig.update_layout(
                    height=600,
                    xaxis_rangeslider_visible=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e0e0e0"),
                    hovermode='x unified'
                )
                
                fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')
                fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')
                
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Fundamentals
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Fundamental Metrics")
                
                metrics_data = {
                    "Metric": ["P/E Ratio", "Forward P/E", "Price/Book", "ROE", "Revenue Growth", 
                              "Profit Margin", "Debt/Equity", "Current Ratio", "Beta", "Dividend Yield"],
                    "Value": [
                        f"{fundamentals['pe_ratio']:.2f}",
                        f"{fundamentals['forward_pe']:.2f}",
                        f"{fundamentals['price_to_book']:.2f}",
                        f"{fundamentals['roe']:.2f}%",
                        f"{fundamentals['revenue_growth']:.2f}%",
                        f"{fundamentals['profit_margin']:.2f}%",
                        f"{fundamentals['debt_to_equity']:.2f}",
                        f"{fundamentals['current_ratio']:.2f}",
                        f"{fundamentals['beta']:.2f}",
                        f"{fundamentals['dividend_yield']:.2f}%"
                    ],
                    "Status": []
                }
                
                criteria = evaluation['criteria']
                
                for metric in metrics_data["Metric"]:
                    status = "—"
                    if metric == "P/E Ratio" and 'pe_max' in criteria:
                        status = "✅" if fundamentals['pe_ratio'] <= criteria['pe_max'] else "❌"
                    elif metric == "ROE" and 'roe_min' in criteria:
                        status = "✅" if fundamentals['roe'] >= criteria['roe_min'] else "❌"
                    elif metric == "Revenue Growth" and 'revenue_growth_min' in criteria:
                        status = "✅" if fundamentals['revenue_growth'] >= criteria['revenue_growth_min'] else "❌"
                    elif metric == "Debt/Equity" and 'debt_to_equity_max' in criteria:
                        status = "✅" if fundamentals['debt_to_equity'] <= criteria['debt_to_equity_max'] else "❌"
                    elif metric == "Current Ratio" and 'current_ratio_min' in criteria:
                        status = "✅" if fundamentals['current_ratio'] >= criteria['current_ratio_min'] else "❌"
                    
                    metrics_data["Status"].append(status)
                
                df_metrics = pd.DataFrame(metrics_data)
                st.dataframe(df_metrics, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("🎯 Criteria Evaluation")
                
                st.markdown(f"**Stock Type:** {stock_type}")
                st.markdown("**Evaluation Criteria:**")
                
                for key, value in criteria.items():
                    metric_name = key.replace("_", " ").title()
                    st.markdown(f"- {metric_name}: {value}")
                
                st.divider()
                
                st.markdown("**Criteria Met:**")
                for criterion, passed in scores.items():
                    icon = "✅" if passed else "❌"
                    metric_name = criterion.replace("_", " ").title()
                    st.markdown(f"{icon} {metric_name}")
            
            st.divider()
            
            # AI Strategy
            st.subheader("🤖 AI-Generated Strategy")
            
            with st.spinner("Generating strategy with xAI Grok..."):
                user_prefs = {
                    "monthly_contribution": monthly_contribution,
                    "risk_tolerance": risk_tolerance,
                    "max_loss_per_trade": max_loss_per_trade
                }
                
                strategy = strategy_gen.generate_strategy(evaluation, user_prefs)
                st.markdown(strategy)
            
            # Export options
            st.divider()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Export CSV", use_container_width=True):
                    csv = pd.DataFrame([fundamentals]).to_csv(index=False)
                    st.download_button("Download", csv, f"{ticker}_analysis.csv", "text/csv")
            
            with col2:
                if st.button("📊 Export Chart", use_container_width=True):
                    st.info("Click camera icon in chart toolbar")
            
            with col3:
                if st.button("🔄 Analyze Another", use_container_width=True):
                    st.rerun()

else:
    st.info("👈 Enter ticker and click 'Analyze' to begin")
    
    st.markdown("""
    ### 📊 Features:
    - Comprehensive fundamentals
    - Stock classification (Growth/Value/Financial/Cyclical)
    - Interactive price charts with overlays
    - Criteria evaluation
    - AI-powered strategy recommendations
    - Risk management calculations
    
    ### 💡 Try These Tickers:
    - **NVDA** (Growth/Tech)
    - **JPM** (Financial/Value)
    - **HOOD** (Growth/Financial)
    - **AAPL** (Growth/Tech)
    """)
