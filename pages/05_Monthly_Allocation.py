"""
Monthly Allocation Page
Dexter AI decides where to invest your money
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / 'utils'))

from dexter_allocator import DexterAllocator, run_monthly_allocation
from portfolio_context import PortfolioContext

# Page config
st.set_page_config(
    page_title="Monthly Allocation - AI Managed",
    page_icon="💰",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .allocation-card {
        background-color: #1e2936;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00d4aa;
        margin-bottom: 1rem;
    }
    .metric-green {
        color: #00d4aa;
        font-weight: bold;
    }
    .metric-red {
        color: #ff4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("💰 Monthly Allocation - AI Managed")
st.markdown("*Dexter researches opportunities and decides where to invest your money*")

# Sidebar - Portfolio Summary
with st.sidebar:
    st.header("📊 Portfolio Status")
    
    portfolio_mgr = PortfolioContext()
    context = portfolio_mgr.get_context()
    
    # Portfolio metrics
    total_value = context['total_value']
    cash = context['cash']
    position_value = context['total_position_value']
    deployed_pct = (position_value / total_value * 100) if total_value > 0 else 0
    
    st.metric("Total Value", f"${total_value:,.2f}")
    st.metric("Cash", f"${cash:,.2f}", f"{cash/total_value*100:.1f}%" if total_value > 0 else "")
    
    # Deployment gauge
    deployment_delta = deployed_pct - 80
    st.metric(
        "Deployed", 
        f"{deployed_pct:.1f}%",
        f"{deployment_delta:+.1f}% vs target",
        delta_color="normal" if abs(deployment_delta) < 10 else "inverse"
    )
    
    st.divider()
    
    # Current holdings
    st.subheader("Current Holdings")
    holdings = context.get('holdings', {})
    
    if holdings:
        for ticker, data in holdings.items():
            shares = data.get('shares', 0)
            entry_price = data.get('entry_price', 0)
            position_val = data.get('position_value', 0)
            pct = (position_val / total_value * 100) if total_value > 0 else 0
            
            with st.expander(f"**{ticker}** ({pct:.1f}%)"):
                st.write(f"Shares: {shares:.4f}")
                st.write(f"Avg Price: ${entry_price:.2f}")
                st.write(f"Value: ${position_val:.2f}")
    else:
        st.info("No positions yet - ready to start!")
    
    st.divider()
    
    # Dexter status
    st.subheader("🤖 Dexter Status")
    allocator = DexterAllocator()
    
    if allocator.dexter.health_check():
        st.success("✅ Connected")
    else:
        st.error("❌ Not Running")
        st.info("Start NewsAdmin to enable Dexter")

# Main content
st.markdown("---")

# Settings section
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("🎯 Monthly Budget")
    monthly_budget = st.number_input(
        "Amount to invest this month",
        min_value=10.0,
        max_value=10000.0,
        value=100.0,
        step=10.0,
        help="How much to invest this month"
    )
    
    st.info(f"""
    **How Dexter works:**
    1. Reviews your current portfolio
    2. Researches opportunities (Polygon + Web)
    3. Evaluates business quality & valuation
    4. Decides optimal allocation
    5. Shows recommendation for approval
    """)

with col2:
    st.subheader("⚙️ Settings")
    
    show_research = st.checkbox(
        "Show full research",
        value=True,
        help="Display Dexter's complete analysis"
    )
    
    research_iterations = st.number_input(
        "Research depth",
        min_value=1,
        max_value=10,
        value=5,
        help="Number of research iterations"
    )

with col3:
    st.subheader("📋 Quick Info")
    st.metric("Target Deployment", "80%")
    st.metric("Current Holdings", len(holdings))
    
    if deployed_pct < 70:
        st.warning("⚠️ Under-deployed")
    elif deployed_pct > 90:
        st.info("ℹ️ Fully deployed")
    else:
        st.success("✅ On target")

st.markdown("---")

# Action button
if st.button("🤖 Ask Dexter for Allocation Decision", type="primary", use_container_width=True):
    
    # Initialize session state for this decision
    if 'current_decision' not in st.session_state:
        st.session_state.current_decision = None
    
    with st.spinner(f"🔍 Dexter is researching allocation opportunities for ${monthly_budget:.2f}..."):
        try:
            decision = run_monthly_allocation(monthly_budget)
            st.session_state.current_decision = decision
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            decision = None

# Display results if we have a decision
if 'current_decision' in st.session_state and st.session_state.current_decision:
    decision = st.session_state.current_decision
    
    if 'error' in decision:
        st.error(f"❌ Dexter encountered an error: {decision['error']}")
        if decision.get('raw_answer'):
            with st.expander("Error Details"):
                st.text(decision['raw_answer'])
    else:
        st.success(f"✅ Research complete! ({decision.get('iterations', 0)} iterations, {decision.get('tasks', 0)} tasks)")
        
        # Show full research if enabled
        if show_research:
            st.subheader("🔍 Dexter's Full Research Report")
            
            with st.expander("📊 Complete Analysis", expanded=False):
                st.markdown(decision.get('raw_answer', 'No analysis available'))
        
        # Display allocations
        if decision.get('allocations'):
            st.markdown("---")
            st.subheader("💡 Recommended Allocation")
            
            total_allocated = sum(a['amount'] for a in decision['allocations'])
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Budget", f"${monthly_budget:.2f}")
            with col2:
                st.metric("Allocated", f"${total_allocated:.2f}")
            with col3:
                remaining = monthly_budget - total_allocated
                st.metric("Remaining", f"${remaining:.2f}")
            
            st.markdown("---")
            
            # Show each allocation
            for i, alloc in enumerate(decision['allocations'], 1):
                ticker = alloc['ticker']
                amount = alloc['amount']
                shares = alloc['shares']
                price = alloc['price']
                conviction = alloc.get('conviction', 'Medium')
                
                # Conviction emoji
                conviction_emoji = {
                    'High': '🔥',
                    'Medium': '⚡',
                    'Low': '💡'
                }.get(conviction, '⚡')
                
                st.markdown(f"""
                <div class="allocation-card">
                    <h3>{conviction_emoji} Option {i}: {ticker}</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
                        <div>
                            <div style="color: #888;">Amount</div>
                            <div class="metric-green">${amount:.2f}</div>
                        </div>
                        <div>
                            <div style="color: #888;">Shares</div>
                            <div class="metric-green">{shares:.4f}</div>
                        </div>
                        <div>
                            <div style="color: #888;">Price</div>
                            <div class="metric-green">${price:.2f}</div>
                        </div>
                    </div>
                    <div style="margin-top: 1rem;">
                        <div style="color: #888;">Conviction Level</div>
                        <div><strong>{conviction}</strong> {conviction_emoji}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Reasoning
            if decision.get('reasoning'):
                st.markdown("### 💭 Dexter's Reasoning")
                st.info(decision['reasoning'])
            
            st.markdown("---")
            
            # Execution section
            st.subheader("🎯 Execute Allocation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Approve & Execute", type="primary", use_container_width=True):
                    with st.spinner("Executing allocation..."):
                        allocator = DexterAllocator()
                        execution_results = allocator.execute_allocation(decision)
                        
                        st.success("✅ Allocation executed!")
                        
                        for result in execution_results:
                            if result['status'] == 'success':
                                st.success(f"✅ {result['ticker']}: {result['note']}")
                            else:
                                st.error(f"❌ {result['ticker']}: {result.get('reason', 'Failed')}")
                        
                        # Clear decision
                        st.session_state.current_decision = None
                        
                        # Suggest rerun
                        st.info("Portfolio updated! Refresh page to see new positions.")
            
            with col2:
                if st.button("❌ Reject & Research Again", use_container_width=True):
                    st.session_state.current_decision = None
                    st.info("Decision rejected. Click 'Ask Dexter' to get new recommendation.")
                    st.rerun()
        
        else:
            st.info("💰 Dexter recommends holding cash this month")
            st.markdown(decision.get('raw_answer', ''))

# Historical allocations section
st.markdown("---")
st.subheader("📜 Allocation History")

with st.expander("View Past Decisions"):
    st.info("Coming soon: Track Dexter's past allocations and their performance")
    # TODO: Load from storage and display
    # Show: Date, Ticker, Amount, Current Value, Return %

# Educational section
st.markdown("---")

with st.expander("📚 How Dexter Makes Decisions"):
    st.markdown("""
    ### Dexter's Multi-Agent Research Process:
    
    **1. Planning Agent** 🧠
    - Analyzes your portfolio state
    - Creates research plan
    - Prioritizes what to investigate
    
    **2. Action Agent** ⚡
    - Fetches stock financials (Polygon)
    - Searches recent news (Web)
    - Gathers competitive data
    - Checks valuations
    
    **3. Validation Agent** ✅
    - Ensures data is complete
    - Verifies research quality
    - Checks for missing info
    
    **4. Answer Agent** 📝
    - Synthesizes all findings
    - Makes allocation decision
    - Provides clear reasoning
    
    ### Data Sources Used:
    - **Polygon API**: Financials, ratios, prices
    - **Web Search**: Recent news, developments
    - **Portfolio Context**: Your current holdings
    - **Historical Data**: Past performance
    
    ### Decision Framework:
    - Focus on business quality (moat, management, financials)
    - Maintain 80% deployment target
    - Diversify across sectors
    - Think 10+ years out
    - Follow Buffett principles
    """)

# Footer
st.markdown("---")
st.caption("🤖 Powered by Dexter AI | Multi-Agent Research System")
