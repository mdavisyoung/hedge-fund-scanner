"""
Stock Scanner Page
Daily stock scanning with multi-factor scoring
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import StockAnalyzer
from scanner.stock_universe import get_daily_batch, get_stock_universe_summary
from scanner.scoring import TradeScorer

st.set_page_config(
    page_title="Stock Scanner",
    page_icon="🔍",
    layout="wide"
)

try:
    with open("custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.title("🔍 Daily Stock Scanner")
st.markdown("*Multi-factor scoring system for trade opportunities*")

# Initialize components
analyzer = StockAnalyzer()
scorer = TradeScorer()

# Sidebar controls
with st.sidebar:
    st.subheader("Scanner Settings")
    
    # Day selection
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_day = st.selectbox("Select Day", day_names, index=datetime.now().weekday())
    day_of_week = day_names.index(selected_day)
    
    # Scan options
    st.divider()
    st.subheader("Scan Options")
    
    min_score = st.slider("Minimum Score", 0, 100, 60, 5)
    max_results = st.slider("Max Results", 10, 100, 20, 10)
    
    # Stock type filter
    stock_type_filter = st.multiselect(
        "Stock Types",
        ["Growth", "Value", "Financial", "Cyclical"],
        default=["Growth", "Value", "Financial", "Cyclical"]
    )
    
    # Run scan button
    run_scan = st.button("🚀 Run Scan", use_container_width=True, type="primary")
    
    # Universe summary
    st.divider()
    st.subheader("Universe Summary")
    summary = get_stock_universe_summary()
    st.metric("Total Stocks", summary["total_unique_stocks"])
    st.caption(f"Tech/Growth: {summary['tech_growth']} | "
              f"Financials: {summary['financials']} | "
              f"Healthcare: {summary['healthcare']}")

# Main content
if run_scan:
    # Get stocks for selected day
    stocks_to_scan = get_daily_batch(day_of_week)
    
    if not stocks_to_scan:
        st.warning(f"No stocks scheduled for {selected_day}. Try a different day.")
    else:
        st.info(f"Scanning {len(stocks_to_scan)} stocks for {selected_day}...")
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for idx, ticker in enumerate(stocks_to_scan[:max_results * 2]):  # Scan extra for filtering
            try:
                # Update progress
                progress = (idx + 1) / min(len(stocks_to_scan), max_results * 2)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing {ticker}... ({idx + 1}/{min(len(stocks_to_scan), max_results * 2)})")
                
                # Get fundamentals
                fundamentals = analyzer.get_fundamentals(ticker)
                if not fundamentals or not fundamentals.get('current_price'):
                    continue
                
                # Get price data
                price_data = analyzer.get_stock_data(ticker, period="6mo")
                
                # Classify stock type
                stock_type = analyzer.classify_stock_type(fundamentals)
                
                # Filter by stock type
                if stock_type not in stock_type_filter:
                    continue
                
                # Score the stock
                score_result = scorer.score_stock(fundamentals, price_data, stock_type)
                
                # Add to results
                results.append({
                    'Ticker': ticker,
                    'Name': fundamentals.get('name', ticker),
                    'Type': stock_type,
                    'Score': score_result['total_score'],
                    'Grade': score_result['grade'],
                    'Price': f"${fundamentals.get('current_price', 0):.2f}",
                    'P/E': fundamentals.get('pe_ratio', 0),
                    'ROE': f"{fundamentals.get('roe', 0):.1f}%",
                    'Revenue Growth': f"{fundamentals.get('revenue_growth', 0):.1f}%",
                    'Fundamental': score_result['breakdown']['fundamental'],
                    'Technical': score_result['breakdown']['technical'],
                    'Risk/Reward': score_result['breakdown']['risk_reward'],
                    'Timing': score_result['breakdown']['timing']
                })
                
            except Exception as e:
                st.warning(f"Error scanning {ticker}: {str(e)}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            # Filter by minimum score
            filtered_results = [r for r in results if r['Score'] >= min_score]
            
            # Sort by score
            filtered_results.sort(key=lambda x: x['Score'], reverse=True)
            
            # Limit to max results
            top_results = filtered_results[:max_results]
            
            st.success(f"Found {len(top_results)} opportunities (score >= {min_score})")
            
            # Display results table
            if top_results:
                df = pd.DataFrame(top_results)
                
                # Color code by grade
                def color_grade(val):
                    if val == 'A':
                        return 'background-color: #00d4aa'
                    elif val == 'B':
                        return 'background-color: #4a9eff'
                    elif val == 'C':
                        return 'background-color: #ffd93d'
                    else:
                        return 'background-color: #ff6b6b'
                
                styled_df = df.style.applymap(color_grade, subset=['Grade'])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Score distribution chart
                st.subheader("📊 Score Distribution")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Grade distribution
                    grade_counts = df['Grade'].value_counts()
                    fig_grades = go.Figure(data=[go.Bar(
                        x=grade_counts.index,
                        y=grade_counts.values,
                        marker_color=['#00d4aa', '#4a9eff', '#ffd93d', '#ff6b6b', '#999999']
                    )])
                    fig_grades.update_layout(
                        title="Grade Distribution",
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#e0e0e0")
                    )
                    st.plotly_chart(fig_grades, use_container_width=True)
                
                with col2:
                    # Score histogram
                    fig_scores = go.Figure(data=[go.Histogram(
                        x=df['Score'],
                        nbinsx=20,
                        marker_color='#4a9eff'
                    )])
                    fig_scores.update_layout(
                        title="Score Distribution",
                        xaxis_title="Score",
                        yaxis_title="Count",
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#e0e0e0")
                    )
                    st.plotly_chart(fig_scores, use_container_width=True)
                
                # Breakdown analysis
                st.subheader("📈 Score Breakdown")
                breakdown_df = df[['Ticker', 'Fundamental', 'Technical', 'Risk/Reward', 'Timing', 'Score']]
                st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
                
                # Export option
                st.divider()
                if st.button("📥 Export Results to CSV", use_container_width=True):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"scanner_results_{selected_day.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
        else:
            st.warning("No stocks met the criteria. Try lowering the minimum score or selecting different stock types.")
else:
    st.info("👈 Configure settings and click 'Run Scan' to find opportunities")
    
    st.markdown("""
    ### 🔍 Scanner Features:
    
    **Multi-Factor Scoring:**
    - **Fundamental (40%)**: Revenue growth, ROE, P/E ratios, profit margins
    - **Technical (30%)**: Moving averages, RSI, volume trends
    - **Risk/Reward (20%)**: Distance from 52-week highs, beta/volatility
    - **Timing (10%)**: Recent momentum, market cap stability
    
    **Daily Batches:**
    - **Monday**: Tech & Growth stocks
    - **Tuesday**: Financials & Energy
    - **Wednesday**: Healthcare & Consumer
    - **Thursday**: Consumer & Small caps
    - **Friday**: Industrials & Small caps
    - **Weekend**: No scheduled scans
    
    **Scoring Grades:**
    - **A (85+)**: Excellent opportunity
    - **B (75-84)**: Good opportunity
    - **C (65-74)**: Moderate opportunity
    - **D (50-64)**: Weak opportunity
    - **F (<50)**: Poor opportunity
    """)

