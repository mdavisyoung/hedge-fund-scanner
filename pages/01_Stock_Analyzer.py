import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import StockAnalyzer, XAIStrategyGenerator
from utils.portfolio_context import PortfolioContext
# Native Python Dexter
from dexter import create_dexter
from utils.storage import StorageManager
from datetime import datetime
import re

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
storage = StorageManager()

def format_dexter_response(dexter_text: str, fundamentals: dict, monthly_contrib: float) -> str:
    """
    Format Dexter's response to match Stock Analyzer format
    Extracts key sections and ensures proper formatting
    """
    # If Dexter already formatted it well, return as-is
    if "**RECOMMENDATION:**" in dexter_text and "**DOLLAR-COST AVERAGING PLAN**" in dexter_text:
        return dexter_text
    
    # Otherwise, try to extract and reformat
    lines = dexter_text.split('\n')
    formatted = []
    
    for line in lines:
        # Clean up formatting
        line = line.strip()
        if not line:
            continue
        
        # Convert markdown headers to match format
        if line.startswith('##'):
            formatted.append(line.replace('##', '**').replace('**', '**', 1) + '**')
        elif line.startswith('#'):
            formatted.append('**' + line.replace('#', '').strip() + '**')
        else:
            formatted.append(line)
    
    return '\n\n'.join(formatted)

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
            
            # AI Strategy - Using Dexter (Hedge Fund Manager)
            st.subheader("🤖 AI-Generated Strategy")
            
            # Add Deep Business Research button
            col_dex1, col_dex2 = st.columns([1, 1])
            with col_dex1:
                use_dexter_deep = st.checkbox("🔍 Deep Business Research with Dexter", value=True, help="Get comprehensive business analysis including moat, management, and 10-year outlook")
            
            # Get actual portfolio context
            try:
                storage = StorageManager()
                portfolio = storage.load_portfolio()
                if portfolio:
                    portfolio_value = portfolio.get('total_value', monthly_contribution * 12)
                    portfolio_cash = portfolio.get('current_cash', 0)
                else:
                    portfolio_value = monthly_contribution * 12
                    portfolio_cash = 0
            except:
                portfolio_value = monthly_contribution * 12
                portfolio_cash = 0
            
            # Use Dexter for strategy generation (default enabled)
            use_dexter = True  # Always use Dexter now
            dexter_instance = None  # Initialize
            
            if use_dexter:
                # Use native Python Dexter
                try:
                    dexter_instance = create_dexter()
                except Exception as e:
                    st.warning(f"⚠️ **Could not initialize Dexter:** {str(e)}")
                    st.info("Falling back to standard strategy generator.")
                    # Fallback to original
                    with st.spinner("Generating strategy with xAI Grok..."):
                        user_prefs = {
                            "monthly_contribution": monthly_contribution,
                            "risk_tolerance": risk_tolerance,
                            "max_loss_per_trade": max_loss_per_trade,
                            "portfolio_value": portfolio_value
                        }
                        strategy = strategy_gen.generate_strategy(evaluation, user_prefs)
                        st.markdown(strategy)
                    dexter_instance = None
                
                if dexter_instance:
                    # Show appropriate spinner message based on research type
                    spinner_msg = "🤖 Dexter is performing deep business analysis... (This may take 2-3 minutes)" if use_dexter_deep else "🤖 Dexter is analyzing with portfolio context..."
                    with st.spinner(spinner_msg):
                        try:
                            portfolio_context = PortfolioContext()
                            context = portfolio_context.get_context()
                            
                            # Add user preferences to context
                            context['monthly_contribution'] = monthly_contribution
                            context['risk_tolerance'] = risk_tolerance
                            context['max_loss_per_trade'] = max_loss_per_trade
                            context['risk_settings'] = {
                                'max_loss_per_trade': max_loss_per_trade,
                                'max_position_size_pct': 20.0
                            }
                            
                            # Use the EXACT SAME hedge fund manager instructions as Chat with Dexter
                            cash_available = context.get('cash', portfolio_cash)
                            monthly_contrib = context.get('monthly_contribution', monthly_contribution)
                            total_value = context.get('total_value', portfolio_value)
                            holdings_list = list(context.get('holdings', {}).keys())
                            holdings_text = ', '.join(holdings_list) if holdings_list else 'None'
                            
                            # Calculate position sizing limits (SAME as Chat with Dexter)
                            max_position_pct = context.get('risk_settings', {}).get('max_position_size_pct', 20.0)
                            max_position_value = total_value * (max_position_pct / 100)
                            available_for_this_trade = min(cash_available * 0.8, max_position_value)
                            
                            # Build the EXACT SAME hedge fund instructions as Chat with Dexter
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
   - Business Description: [What the company does]
   - Sector: {fundamentals.get('sector', 'Unknown')}
   - Industry: {fundamentals.get('industry', 'Unknown')}
7. **ANALYSIS:**
   - Stock Type: {stock_type}
   - Key Strengths: [2-3 bullet points]
   - Key Concerns: [1-2 bullet points]
8. **IMMEDIATE ACTION (This Month):**
   - Buy [X] shares @ ${fundamentals['current_price']:.2f} = $[XXX.XX] (MUST be ≤ ${available_for_this_trade:,.2f})
   - This uses PART of this month's ${monthly_contrib:.2f} DCA budget (NOT all of it)
   - Stop-Loss: $[X.XX] (-[X]%)
   - Take-Profit: $[X.XX] (+[X]%)
9. **DOLLAR-COST AVERAGING PLAN (Next 12 Months):**
   - Month 1: Buy [X] shares ($[XXX.XX]) → Total: [X] shares
   - Month 2: Buy [X] shares ($[XXX.XX]) → Total: [X] shares
   - [Continue for 12 months - use PART of monthly contribution each month]
10. **TARGET POSITION (After 12 Months):**
   - Total Shares: [X]
   - Total Invested: $[XXX.XX]
   - Position Value: $[XXX.XX] (at current price)
   - Portfolio Allocation: [X]% of portfolio (MUST be ≤ {max_position_pct}%)
11. **RISK MANAGEMENT:**
   - Exit if price drops to $[X.XX] (stop-loss)
   - Take profit at $[X.XX] (+[X]% gain)
   - Max risk: $[XX.XX] ({max_loss_per_trade}% of portfolio)

IMPORTANT:
- **NEVER suggest using all ${cash_available:,.2f} cash on one trade**
- **Always leave at least 20% of cash available** for other opportunities
- **For expensive stocks (price > ${monthly_contrib:.0f}), suggest DCA using PART of monthly contribution**
- **Example:** If monthly contribution is ${monthly_contrib:.2f}, suggest using ${monthly_contrib * 0.4:.0f}-${monthly_contrib * 0.6:.0f} per month for this stock, leaving the rest for other trades
- Make clear BUY/SELL/HOLD recommendations
- Use CURRENT stock price: ${fundamentals['current_price']:.2f}
- Consider diversification with current holdings: {holdings_text}
"""
                            
                            # Build query based on deep research toggle
                            if use_dexter_deep:
                                query = f"""As my hedge fund manager, provide a DEEP BUSINESS ANALYSIS of {ticker}:

Portfolio Context:
- Total Portfolio Value: ${portfolio_value:,.2f}
- Available Cash: ${cash_available:,.2f}
- Monthly Contribution: ${monthly_contribution:.2f}
- Current Holdings: {', '.join(holdings_list) if holdings_list else 'None'}

DEEP BUSINESS RESEARCH REQUIRED:

1. **What does this company actually do?**
   - Business model, products/services, customers
   - Industry position and competitive landscape
   - Revenue sources: {fundamentals.get('description', 'Research required')[:200]}

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
   - ROE: {fundamentals.get('roe', 0):.1f}% (sustainable? 15%+ is quality)
   - P/E: {fundamentals.get('pe_ratio', 0):.1f}x (reasonable for quality?)
   - Free cash flow generation
   - Debt levels and financial strength

6. **Valuation:**
   - Intrinsic value estimate
   - Margin of safety at ${fundamentals['current_price']:.2f}
   - Would Buffett buy this at this price?

INVESTMENT RECOMMENDATION:
{hedge_fund_instructions}

Current stock price: ${fundamentals['current_price']:.2f}
Stock Type: {stock_type}
Fundamentals: P/E={fundamentals.get('pe_ratio', 0):.2f}, ROE={fundamentals.get('roe', 0):.2f}%, Revenue Growth={fundamentals.get('revenue_growth', 0):.2f}%

Remember: Focus on BUSINESS QUALITY for 10+ year ownership, not short-term price movements."""
                            else:
                                query = f"""Provide a comprehensive investment strategy for {ticker}:

{hedge_fund_instructions}

Current stock price: ${fundamentals['current_price']:.2f}
Stock Type: {stock_type}
Fundamentals: P/E={fundamentals.get('pe_ratio', 0):.2f}, ROE={fundamentals.get('roe', 0):.2f}%, Revenue Growth={fundamentals.get('revenue_growth', 0):.2f}%"""
                            
                            # Native Python Dexter doesn't use timeout parameter
                            result = dexter_instance.research(query)
                            strategy_text = result.get('answer', 'No response received')
                            
                            # Check if there was an error
                            if result.get('error'):
                                st.warning(f"⚠️ Dexter returned an error: {result.get('error')}")
                                st.info("Falling back to standard strategy generator...")
                                # Fallback to original
                                user_prefs = {
                                    "monthly_contribution": monthly_contribution,
                                    "risk_tolerance": risk_tolerance,
                                    "max_loss_per_trade": max_loss_per_trade,
                                    "portfolio_value": portfolio_value
                                }
                                strategy = strategy_gen.generate_strategy(evaluation, user_prefs)
                                st.markdown(strategy)
                            else:
                                # Format the response to match Stock Analyzer style
                                formatted_strategy = format_dexter_response(strategy_text, fundamentals, monthly_contribution)
                                st.markdown(formatted_strategy)
                                
                        except Exception as e:
                            st.warning(f"⚠️ Dexter unavailable: {str(e)}. Falling back to standard strategy generator.")
                            # Fallback to original
                            with st.spinner("Generating strategy with xAI Grok..."):
                                user_prefs = {
                                    "monthly_contribution": monthly_contribution,
                                    "risk_tolerance": risk_tolerance,
                                    "max_loss_per_trade": max_loss_per_trade,
                                    "portfolio_value": portfolio_value
                                }
                                strategy = strategy_gen.generate_strategy(evaluation, user_prefs)
                                st.markdown(strategy)
            else:
                # Use original XAIStrategyGenerator
                with st.spinner("Generating strategy with xAI Grok..."):
                    user_prefs = {
                        "monthly_contribution": monthly_contribution,
                        "risk_tolerance": risk_tolerance,
                        "max_loss_per_trade": max_loss_per_trade,
                        "portfolio_value": portfolio_value
                    }
                    strategy = strategy_gen.generate_strategy(evaluation, user_prefs)
                    st.markdown(strategy)
            
            # Trade Entry Form - Always show after analysis
            st.divider()
            
            # Make it very visible
            st.markdown("---")
            st.markdown(f"## 📝 Record Trade: {ticker}")
            st.markdown(f"**Record your purchase of {ticker} to track it in Personal Trades**")
            st.markdown("---")
            
            with st.form(key=f"trade_entry_{ticker}", clear_on_submit=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    trade_price = st.number_input(
                        "Purchase Price ($)",
                        min_value=0.01,
                        value=float(fundamentals['current_price']),
                        step=0.01,
                        format="%.2f",
                        key=f"trade_price_{ticker}"
                    )
                
                with col2:
                    trade_shares = st.number_input(
                        "Shares Purchased",
                        min_value=0.0,
                        value=0.0,
                        step=0.01,
                        format="%.2f",
                        help="Enter the number of shares you purchased",
                        key=f"trade_shares_{ticker}"
                    )
                
                with col3:
                    trade_total = trade_price * trade_shares if trade_shares > 0 else 0.0
                    st.metric("Total Cost", f"${trade_total:.2f}")
                    if trade_shares > 0:
                        st.caption(f"💡 Recording {trade_shares:.2f} shares of {ticker}")
                
                trade_notes = st.text_area(
                    "Notes (optional)",
                    placeholder="e.g., Following Dexter's recommendation, DCA month 1",
                    height=60,
                    key=f"trade_notes_{ticker}"
                )
                
                # Submit button must be last in form
                submit_trade = st.form_submit_button("💾 Record Trade", use_container_width=True, type="primary")
            
            # Handle form submission (outside form context)
            if submit_trade:
                # Get values from session state (they persist after form submission)
                trade_price_val = st.session_state.get(f"trade_price_{ticker}", float(fundamentals['current_price']))
                trade_shares_val = st.session_state.get(f"trade_shares_{ticker}", 0.0)
                trade_notes_val = st.session_state.get(f"trade_notes_{ticker}", "")
                
                if trade_shares_val > 0:
                    try:
                        # Load portfolio
                        portfolio = storage.load_portfolio()
                        if not portfolio:
                            st.error("Please initialize your portfolio first in the Auto Trading Hub sidebar")
                        else:
                            # Add trade to portfolio
                            from utils import AIPortfolioManager
                            portfolio_manager = AIPortfolioManager(storage)
                            
                            # Record the trade
                            trade_total_val = trade_price_val * trade_shares_val
                            trade_data = {
                                'ticker': ticker,
                                'action': 'BUY',
                                'shares': trade_shares_val,
                                'price': trade_price_val,
                                'total_cost': trade_total_val,
                                'timestamp': datetime.now().isoformat(),
                                'notes': trade_notes_val,
                                'source': 'stock_analyzer'
                            }
                            
                            # Update portfolio
                            if ticker not in portfolio.get('positions', {}):
                                portfolio['positions'][ticker] = {
                                    'shares': 0,
                                    'entry_price': 0,
                                    'total_cost': 0,
                                    'entry_date': datetime.now().isoformat()
                                }
                            
                            # Add to position
                            pos = portfolio['positions'][ticker]
                            total_shares = pos['shares'] + trade_shares_val
                            total_cost = pos['total_cost'] + trade_total_val
                            avg_entry = total_cost / total_shares if total_shares > 0 else trade_price_val
                            
                            portfolio['positions'][ticker].update({
                                'shares': total_shares,
                                'entry_price': avg_entry,
                                'total_cost': total_cost
                            })
                            
                            # Update cash
                            portfolio['current_cash'] = portfolio.get('current_cash', 0) - trade_total_val
                            
                            # Add to trade history
                            if 'trade_history' not in portfolio:
                                portfolio['trade_history'] = []
                            portfolio['trade_history'].append(trade_data)
                            
                            # Save
                            storage.save_portfolio(portfolio)
                            
                            st.success(f"✅ Trade recorded! {trade_shares_val:.2f} shares of {ticker} @ ${trade_price_val:.2f}")
                            
                            # Clear form values from session state
                            if f"trade_price_{ticker}" in st.session_state:
                                del st.session_state[f"trade_price_{ticker}"]
                            if f"trade_shares_{ticker}" in st.session_state:
                                del st.session_state[f"trade_shares_{ticker}"]
                            if f"trade_notes_{ticker}" in st.session_state:
                                del st.session_state[f"trade_notes_{ticker}"]
                            
                            # Show link to Personal Trades
                            col_link1, col_link2 = st.columns([1, 1])
                            with col_link1:
                                if st.button("📋 View in Personal Trades", use_container_width=True, type="primary"):
                                    st.switch_page("pages/05_Personal_Trades.py")
                            with col_link2:
                                if st.button("🔄 Analyze Another Stock", use_container_width=True):
                                    st.rerun()
                            
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Error recording trade: {str(e)}")
                else:
                    st.warning("Please enter the number of shares purchased (must be greater than 0)")
            
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
