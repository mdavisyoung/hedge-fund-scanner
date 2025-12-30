"""
Configuration helper for Streamlit Cloud and local development
Supports both Streamlit secrets and .env files
"""
import os
import streamlit as st
from typing import Optional


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get secret from Streamlit secrets (cloud) or environment variable (local)
    
    Args:
        key: Secret key name
        default: Default value if not found
    
    Returns:
        Secret value or default
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            value = st.secrets[key]
            # Handle nested secrets (e.g., st.secrets['api']['key'])
            if isinstance(value, dict):
                return value
            return str(value)
    except Exception:
        pass
    
    # Fall back to environment variable (for local development)
    return os.getenv(key, default)


def get_api_key(key_name: str) -> Optional[str]:
    """
    Get API key from secrets or environment
    
    Args:
        key_name: API key name (e.g., 'XAI_API_KEY')
    
    Returns:
        API key value or None
    """
    return get_secret(key_name)


def is_streamlit_cloud() -> bool:
    """Check if running on Streamlit Cloud"""
    return os.getenv('STREAMLIT_SHARING_MODE') is not None or \
           os.getenv('STREAMLIT_SERVER_PORT') == '8501' and os.getenv('STREAMLIT_SHARING')

