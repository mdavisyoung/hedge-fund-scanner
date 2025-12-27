"""
Autonomous Trader Dashboard
Monitor AI-powered autonomous trading
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from trader.autonomous_trader import AutonomousTrader

st.set_page_config(
    page_title="Autonomous Trader",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Autonomous Trader Dashboard")
st.markdown("AI-powered autonomous trading with real-time monitoring")

# Initialize trader
@st.cache_resource
def init_trader():
    """Initialize autonomous trader (cached to avoid recreating)"""
    try:
        trader = AutonomousTrader(paper_trading=True)
        return trader, None
    except Exception as e:
        return None, str(e)

trader, error = init_trader()

if error:
    st.error(f"❌ Failed to initialize trader: {error}")
    st.info("💡 Make sure ALPACA_API_KEY and ALPACA_SECRET_KEY are set in your .env file")
    st.stop()

# Sidebar controls
st.sidebar.header("⚙️ Controls")

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Trading Parameters")
st.sidebar.metric("Max Position Size", f"{trader.max_position_size*100:.0f}%")
st.sidebar.metric("Max Loss Per Trade", f"{trader.max_loss_per_trade*100:.0f}%")
st.sidebar.metric("Confidence Threshold", f"{trader.confidence_threshold}/10")
st.sidebar.metric("Max Portfolio Heat", f"{trader.max_portfolio_heat*100:.0f}%")

# Main dashboard
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📈 Active Positions",
    "📜 Trade History",
    "🧠 AI Insights"
])

# TAB 1: Overview
with tab1:
    # Account info
    try:
        account = trader.get_account_info()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Portfolio Value",
                f"${account['portfolio_value']:,.2f}",
                help="Total account equity"
            )

        with col2:
            st.metric(
                "Cash Available",
                f"${account['cash']:,.2f}",
                help="Available cash for trading"
            )

        with col3:
            st.metric(
                "Buying Power",
                f"${account['buying_power']:,.2f}",
                help="Maximum buying power"
            )

        with col4:
            mode = "📄 Paper" if account['paper_trading'] else "💰 Live"
            st.metric(
                "Trading Mode",
                mode,
                help="Paper trading (simulated) or live trading"
            )

    except Exception as e:
        st.error(f"Error fetching account info: {e}")

    st.markdown("---")

    # Portfolio heat
    try:
        portfolio_heat = trader.get_portfolio_heat()
        heat_pct = portfolio_heat * 100
        max_heat_pct = trader.max_portfolio_heat * 100

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🔥 Portfolio Risk Heat")

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=heat_pct,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Current Risk Exposure"},
                delta={'reference': max_heat_pct, 'increasing': {'color': "red"}},
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
            st.metric(
                "Current Heat",
                f"{heat_pct:.2f}%",
                delta=f"{heat_pct - max_heat_pct:.2f}%",
                delta_color="inverse",
                help="Total portfolio risk across all positions"
            )
            st.metric(
                "Max Heat",
                f"{max_heat_pct:.0f}%",
                help="Maximum allowed portfolio risk"
            )

            if heat_pct >= max_heat_pct:
                st.error("⚠️ Portfolio heat exceeded! No new trades allowed.")
            elif heat_pct >= max_heat_pct * 0.8:
                st.warning("⚡ Portfolio heat approaching limit")
            else:
                st.success("✅ Portfolio heat within limits")

    except Exception as e:
        st.error(f"Error calculating portfolio heat: {e}")

    st.markdown("---")

    # Performance metrics
    st.subheader("📊 Performance Metrics")

    metrics = trader.performance_metrics

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Trades",
            metrics['total_trades'],
            help="Number of completed trades"
        )

    with col2:
        st.metric(
            "Win Rate",
            f"{metrics['win_rate']:.1f}%",
            help="Percentage of winning trades"
        )

    with col3:
        st.metric(
            "Profit Factor",
            f"{metrics['profit_factor']:.2f}",
            help="Ratio of total wins to total losses"
        )

    with col4:
        st.metric(
            "Total P/L",
            f"{metrics['total_pnl_pct']:+.2f}%",
            delta=f"{metrics['total_pnl_pct']:.2f}%",
            help="Total profit/loss percentage"
        )

    # Win/Loss breakdown
    if metrics['total_trades'] > 0:
        col1, col2 = st.columns(2)

        with col1:
            # Win/Loss pie chart
            fig = go.Figure(data=[go.Pie(
                labels=['Winning Trades', 'Losing Trades'],
                values=[metrics['winning_trades'], metrics['losing_trades']],
                marker=dict(colors=['#00CC96', '#EF553B'])
            )])
            fig.update_layout(title="Win/Loss Distribution", height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Avg win/loss bar chart
            fig = go.Figure(data=[
                go.Bar(
                    name='Average Win',
                    x=['Avg Win'],
                    y=[metrics['avg_win']],
                    marker_color='#00CC96'
                ),
                go.Bar(
                    name='Average Loss',
                    x=['Avg Loss'],
                    y=[abs(metrics['avg_loss'])],
                    marker_color='#EF553B'
                )
            ])
            fig.update_layout(
                title="Average Win vs Loss (%)",
                yaxis_title="Percentage",
                height=300,
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)


# TAB 2: Active Positions
with tab2:
    st.subheader("📈 Current Open Positions")

    try:
        positions = trader.get_current_positions()

        if not positions:
            st.info("No open positions currently")
        else:
            # Display positions as cards
            for pos in positions:
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
                        delta_color = "normal" if pnl_pct >= 0 else "inverse"
                        st.metric(
                            "P/L",
                            f"{pnl_pct:+.2f}%",
                            delta=f"${pos['unrealized_pnl']:+,.2f}",
                            delta_color=delta_color
                        )

                    # Find trade record for stop/target info
                    trade_record = next(
                        (t for t in trader.trade_history if t['ticker'] == pos['ticker'] and t['status'] == 'OPEN'),
                        None
                    )

                    if trade_record:
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.caption(f"Stop Loss: ${trade_record.get('stop_loss', 0):.2f}")

                        with col2:
                            st.caption(f"Target: ${trade_record.get('target', 0):.2f}")

                        with col3:
                            confidence = trade_record.get('confidence', 'N/A')
                            st.caption(f"AI Confidence: {confidence}/10")

                        # Show reasoning
                        reasoning = trade_record.get('reasoning', 'No reasoning available')
                        with st.expander("AI Reasoning"):
                            st.write(reasoning)

                    st.markdown("---")

    except Exception as e:
        st.error(f"Error fetching positions: {e}")


# TAB 3: Trade History
with tab3:
    st.subheader("📜 Complete Trade History")

    try:
        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "Open", "Closed"]
            )

        with col2:
            sort_by = st.selectbox(
                "Sort By",
                ["Most Recent", "Highest P/L", "Lowest P/L"]
            )

        # Get trades
        trades = trader.trade_history.copy()

        # Apply status filter
        if status_filter == "Open":
            trades = [t for t in trades if t.get('status') == 'OPEN']
        elif status_filter == "Closed":
            trades = [t for t in trades if t.get('status') == 'CLOSED']

        # Apply sorting
        if sort_by == "Most Recent":
            trades.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        elif sort_by == "Highest P/L":
            trades = [t for t in trades if t.get('status') == 'CLOSED']
            trades.sort(key=lambda x: x.get('pnl_pct', 0), reverse=True)
        elif sort_by == "Lowest P/L":
            trades = [t for t in trades if t.get('status') == 'CLOSED']
            trades.sort(key=lambda x: x.get('pnl_pct', 0))

        if not trades:
            st.info("No trades found")
        else:
            # Display as dataframe
            df_data = []
            for trade in trades:
                row = {
                    'Date': trade.get('timestamp', '')[:10],
                    'Ticker': trade['ticker'],
                    'Action': trade['action'],
                    'Shares': trade['shares'],
                    'Entry': f"${trade['entry_price']:.2f}",
                    'Stop Loss': f"${trade['stop_loss']:.2f}",
                    'Target': f"${trade['target']:.2f}",
                    'Confidence': f"{trade.get('confidence', 'N/A')}/10",
                    'Status': trade['status']
                }

                if trade['status'] == 'CLOSED':
                    row['Exit'] = f"${trade.get('exit_price', 0):.2f}"
                    row['P/L %'] = f"{trade.get('pnl_pct', 0):+.2f}%"
                    row['Exit Reason'] = trade.get('exit_reason', 'N/A')

                df_data.append(row)

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Error loading trade history: {e}")


# TAB 4: AI Insights
with tab4:
    st.subheader("🧠 AI Learning & Insights")

    try:
        lessons = trader.lessons_learned

        if not lessons:
            st.info("No lessons learned yet. AI will learn from completed trades.")
        else:
            st.success(f"📚 {len(lessons)} lessons learned from past trades")

            # Show recent lessons
            st.markdown("### Recent Lessons")

            for lesson in reversed(lessons[-10:]):  # Last 10 lessons
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        icon = "✅" if lesson['is_winning'] else "❌"
                        st.markdown(f"{icon} {lesson['lesson']}")

                    with col2:
                        st.caption(lesson['ticker'])

                    with col3:
                        date = datetime.fromisoformat(lesson['timestamp']).strftime('%Y-%m-%d')
                        st.caption(date)

                    st.markdown("---")

            # Performance by confidence level
            st.markdown("### Performance by AI Confidence Level")

            confidence_data = {}
            for trade in trader.trade_history:
                if trade.get('status') == 'CLOSED' and trade.get('confidence'):
                    conf = int(trade['confidence'])
                    if conf not in confidence_data:
                        confidence_data[conf] = {'wins': 0, 'losses': 0, 'total_pnl': 0}

                    pnl = trade.get('pnl_pct', 0)
                    if pnl > 0:
                        confidence_data[conf]['wins'] += 1
                    else:
                        confidence_data[conf]['losses'] += 1

                    confidence_data[conf]['total_pnl'] += pnl

            if confidence_data:
                conf_df = pd.DataFrame([
                    {
                        'Confidence': conf,
                        'Wins': data['wins'],
                        'Losses': data['losses'],
                        'Win Rate': (data['wins'] / (data['wins'] + data['losses']) * 100) if (data['wins'] + data['losses']) > 0 else 0,
                        'Avg P/L': data['total_pnl'] / (data['wins'] + data['losses']) if (data['wins'] + data['losses']) > 0 else 0
                    }
                    for conf, data in sorted(confidence_data.items())
                ])

                fig = px.scatter(
                    conf_df,
                    x='Confidence',
                    y='Win Rate',
                    size='Wins',
                    color='Avg P/L',
                    hover_data=['Wins', 'Losses'],
                    title="AI Confidence vs Win Rate",
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(conf_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading AI insights: {e}")

# Footer
st.markdown("---")
st.caption("🤖 Autonomous AI Trader - Paper Trading Mode for Safe Testing")
