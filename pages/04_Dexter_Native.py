"""
Chat with Dexter - Native Python Implementation
AI Research Assistant with Multi-Agent Intelligence
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dexter import create_dexter

# Page config
st.set_page_config(
    page_title="Chat with Dexter",
    page_icon="🤖",
    layout="wide"
)

# Title
st.title("🤖 Chat with Dexter - Native Python")
st.markdown("*AI Research Assistant - No Node.js Required!*")

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'dexter' not in st.session_state:
    try:
        st.session_state.dexter = create_dexter()
        st.session_state.dexter_ready = True
    except Exception as e:
        st.session_state.dexter_ready = False
        st.session_state.dexter_error = str(e)

# Sidebar
with st.sidebar:
    st.header("⚙️ Dexter Status")
    
    if st.session_state.get('dexter_ready'):
        st.success("✅ Native Python Dexter Ready!")
        st.info("No Node.js server needed!")
    else:
        st.error(f"❌ Error: {st.session_state.get('dexter_error', 'Unknown')}")
        st.warning("Check your API keys in .env file")
    
    st.divider()
    
    # Quick actions
    st.header("⚡ Quick Examples")
    
    examples = [
        "What is NVDA's current stock price and performance?",
        "Analyze AAPL's recent financials",
        "Compare TSLA vs F for long-term investment",
        "What are the risks with investing in AI stocks?",
    ]
    
    for example in examples:
        if st.button(example, use_container_width=True, key=f"ex_{examples.index(example)}"):
            st.session_state.pending_query = example
            st.rerun()
    
    st.divider()
    
    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Main chat area
st.markdown("---")

# Display chat history
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message['content'])
                
                # Show metadata
                if 'iterations' in message:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"🔄 Iterations: {message['iterations']}")
                    with col2:
                        st.caption(f"✅ Tasks: {message.get('tasks', 0)}")
else:
    # Welcome message
    st.info("""
    👋 **Welcome to Dexter (Native Python)!**
    
    I'm your AI research assistant powered by:
    - 🧠 xAI Grok for intelligent planning
    - 📊 Polygon.io for financial data
    - 🔍 Tavily for web search
    
    **Try asking:**
    - "What is NVDA's current stock price?"
    - "Analyze Apple's recent performance"
    - "Compare Tesla vs traditional automakers"
    - "What are growth stocks to watch?"
    
    *No Node.js server required - pure Python!*
    """)

# Chat input
user_input = st.chat_input("Ask Dexter anything about stocks...")

# Handle pending query from sidebar
if 'pending_query' in st.session_state:
    user_input = st.session_state.pending_query
    del st.session_state.pending_query

# Process input
if user_input and st.session_state.get('dexter_ready'):
    # Add user message
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input
    })
    
    # Show in chat immediately
    with st.chat_message("user"):
        st.write(user_input)
    
    # Get Dexter's response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Dexter is researching... (30-60 seconds)"):
            try:
                result = st.session_state.dexter.research(user_input)
                
                # Display answer
                st.markdown(result['answer'])
                
                # Show metadata
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"🔄 Iterations: {result['iterations']}")
                with col2:
                    st.caption(f"✅ Tasks: {len(result['plan']['tasks'])}")
                
                # Add to history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': result['answer'],
                    'iterations': result['iterations'],
                    'tasks': len(result['plan']['tasks'])
                })
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg,
                    'iterations': 0,
                    'tasks': 0
                })

elif user_input and not st.session_state.get('dexter_ready'):
    st.error("Dexter is not ready. Please check API keys in .env file.")

# Info expander
with st.expander("ℹ️ How Native Python Dexter Works"):
    st.markdown("""
    ### Multi-Agent Architecture
    
    **1. Planning Agent 🧠**
    - Analyzes your query
    - Breaks it into specific research tasks
    - Uses xAI Grok for intelligent planning
    
    **2. Action Agent ⚡**
    - Executes tasks using APIs:
      - Polygon.io for stock data
      - Tavily for web search
    - Fetches real-time information
    
    **3. Validation Agent ✅**
    - Checks if data is sufficient
    - Ensures quality of research
    
    **4. Answer Agent 📝**
    - Synthesizes all findings
    - Creates comprehensive response
    - Cites specific data points
    
    ### Advantages Over Node.js Version
    
    ✅ No separate server needed  
    ✅ Runs natively in Python  
    ✅ Easier to deploy  
    ✅ Better integration with hedge-fund-scanner  
    ✅ Same multi-agent capabilities  
    
    ### API Requirements
    
    Required in `.env`:
    - `XAI_API_KEY` - For Grok AI
    - `POLYGON_API_KEY` - For stock data
    - `TAVILY_API_KEY` - For web search (optional)
    """)

# Footer
st.markdown("---")
st.caption("🤖 Native Python Dexter | Multi-Agent Research | No Node.js Required")
