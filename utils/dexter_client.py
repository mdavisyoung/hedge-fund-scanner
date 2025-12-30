"""
Dexter API Client for Hedge Fund Scanner
Connects Streamlit app to Dexter multi-agent research system
"""

import requests
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class DexterClient:
    """
    Client for interacting with Dexter AI research assistant
    Dexter uses multi-agent system for deep stock analysis
    """
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Dexter client
        
        Args:
            api_url: Dexter API endpoint (default: localhost:3000)
            api_key: Optional API key for authentication
        """
        # Auto-detect port if not specified
        if not api_url and not os.getenv('DEXTER_API_URL'):
            api_url = self._detect_port()
        
        self.api_url = api_url or os.getenv('DEXTER_API_URL', 'http://localhost:3000')
        self.api_key = api_key or os.getenv('DEXTER_API_KEY', '')
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def _detect_port(self) -> str:
        """Detect which port NewsAdmin is running on"""
        # Try common ports (3000, 3001, 3002, etc.) since Next.js auto-selects if 3000 is busy
        for port in [3000, 3001, 3002, 3003, 3004]:
            try:
                response = requests.get(f"http://localhost:{port}/api/health", timeout=1)
                if response.status_code == 200:
                    return f"http://localhost:{port}"
            except:
                # Try root endpoint
                try:
                    response = requests.get(f"http://localhost:{port}/", timeout=1)
                    if response.status_code == 200:
                        return f"http://localhost:{port}"
                except:
                    continue
        
        # Default to 3000 if none found
        return "http://localhost:3000"
    
    def research(
        self, 
        query: str, 
        portfolio_context: Optional[Dict] = None,
        timeout: int = 120  # Increased to 120 seconds for deep research
    ) -> Dict[str, Any]:
        """
        Send research query to Dexter
        
        Args:
            query: Natural language question/request
            portfolio_context: Optional dict with cash, holdings, etc.
            timeout: Request timeout in seconds
            
        Returns:
            Dict with 'answer', 'plan', 'iterations', 'tasks'
        """
        try:
            # Format request payload - try different formats
            # First try with 'query' field
            payload = {
                "query": query,
                "context": portfolio_context or {}
            }
            
            # Make request to Dexter API
            response = self.session.post(
                f"{self.api_url}/api/dexter",
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500:
                # Server error - endpoint exists but crashed
                error_text = response.text[:1000] if response.text else "Internal server error"
                
                # Try to parse error details from JSON response
                error_details = "Unknown error"
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict):
                        error_details = error_json.get("error", error_json.get("message", str(error_json)))
                        details = error_json.get("details", "")
                        if details:
                            error_details += f"\n\n**Stack trace:**\n```\n{details[:500]}\n```"
                except:
                    error_details = error_text[:500]
                
                # Check if it's a PlanningAgent error or API key error
                is_planning_error = "PlanningAgent" in error_text or "createPlan" in error_text
                is_api_key_error = "API key" in error_text or "Incorrect API key" in error_text or "xAI API key error" in error_text
                
                return {
                    "error": "Server error",
                    "answer": f"⚠️ **Dexter API Error (500)**\n\n**Error:** {error_details}\n\n" + (
                        "**🔑 API Key Issue Detected!**\n\n"
                        "The xAI API key in NewsAdmin's `.env.local` is incorrect or missing.\n\n"
                        "**To fix:**\n"
                        "1. Open `C:\\Users\\svfam\\Desktop\\NewsAdmin\\.env.local`\n"
                        "2. Update `XAI_API_KEY` with the correct key from hedge-fund-scanner's `.env`\n"
                        "3. Restart NewsAdmin: Stop it (Ctrl+C) and run `npm run dev` again\n"
                        "4. The key should match the one in `hedge-fund-scanner/.env`\n\n"
                        if is_api_key_error else
                        "**This is a code error in NewsAdmin's PlanningAgent.**\n\n"
                        "**To fix:**\n"
                        "1. Check NewsAdmin code at `lib/dexter/index.ts` line ~144\n"
                        "2. The `PlanningAgent.createPlan` function is failing\n"
                        "3. Check NewsAdmin terminal for full stack trace\n"
                        "4. Verify all required API keys are set in NewsAdmin's `.env.local`\n"
                        "5. Check if xAI/Grok API is working and has credits\n\n"
                        if is_planning_error else
                        "**Possible causes:**\n"
                        "1. **Code error** - Bug in NewsAdmin's `/api/dexter` endpoint\n"
                        "2. **Memory issue** - NewsAdmin ran out of memory\n"
                        "3. **Missing dependencies** - Required packages not installed\n"
                        "4. **API key issue** - Missing or invalid API keys\n\n"
                        "**To fix:**\n"
                        "1. Check NewsAdmin terminal for error messages\n"
                        "2. Restart NewsAdmin with more memory:\n"
                        "   ```bash\n   cd NewsAdmin\n   $env:NODE_OPTIONS=\"--max-old-space-size=4096\"\n   npm run dev\n   ```\n"
                        "3. Verify all API keys are set in NewsAdmin's `.env.local`\n\n"
                    ) + f"**Server:** {self.api_url}",
                    "plan": None,
                    "iterations": 0
                }
            elif response.status_code == 400:
                # Bad request - might be payload format issue
                error_text = response.text[:500] if response.text else "Bad request"
                # Try alternative payload format
                alt_payload = {
                    "message": query,
                    "portfolio": portfolio_context or {}
                }
                try:
                    alt_response = self.session.post(
                        f"{self.api_url}/api/dexter",
                        json=alt_payload,
                        timeout=timeout,
                        headers={"Content-Type": "application/json"}
                    )
                    if alt_response.status_code == 200:
                        return alt_response.json()
                except:
                    pass
                
                # Try one more format - just the query as a string or different structure
                try:
                    simple_payload = query if isinstance(query, str) else {"text": query}
                    simple_response = self.session.post(
                        f"{self.api_url}/api/dexter",
                        json=simple_payload,
                        timeout=timeout,
                        headers={"Content-Type": "application/json"}
                    )
                    if simple_response.status_code == 200:
                        return simple_response.json()
                except:
                    pass
                
                return {
                    "error": f"Bad request: {error_text}",
                    "answer": f"⚠️ Dexter API returned 400 (Bad Request). The endpoint exists but the request format is incorrect.\n\n**Server Response:** {error_text[:200]}\n\n**Note:** NewsAdmin may have crashed due to memory issues. Check the NewsAdmin terminal for errors.\n\n**To fix:**\n1. Check NewsAdmin API documentation for expected payload format\n2. Verify NewsAdmin is running: `cd NewsAdmin && npm run dev`\n3. Check NewsAdmin logs for memory errors",
                    "plan": None,
                    "iterations": 0
                }
            elif response.status_code == 404:
                return {
                    "error": "Endpoint not found",
                    "answer": f"⚠️ Dexter API endpoint not found. The `/api/dexter` endpoint doesn't exist on NewsAdmin.\n\n**To fix:**\n1. Make sure NewsAdmin has the Dexter API routes implemented\n2. Check that the endpoint is at `/api/dexter`\n3. Verify NewsAdmin is running on {self.api_url}",
                    "plan": None,
                    "iterations": 0
                }
            else:
                error_msg = f"Dexter API error {response.status_code}: {response.text[:200]}"
                print(error_msg)
                return {
                    "error": error_msg,
                    "answer": f"⚠️ Unable to connect to Dexter. Status: {response.status_code}\n\n**Server is running at:** {self.api_url}\n**But endpoint `/api/dexter` returned:** {response.status_code}",
                    "plan": None,
                    "iterations": 0
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "error": "Connection failed",
                "answer": "⚠️ Dexter service is not running. Please start NewsAdmin server:\n\n```bash\ncd NewsAdmin\nnpm run dev\n```",
                "plan": None,
                "iterations": 0
            }
        except requests.exceptions.Timeout:
            return {
                "error": "Timeout",
                "answer": f"⚠️ **Dexter Timeout**\n\nDexter took longer than {timeout} seconds to respond. This can happen with deep business research queries.\n\n**Possible solutions:**\n1. **Wait and retry** - Deep research can take 2-3 minutes\n2. **Check NewsAdmin terminal** - See if it's still processing\n3. **Simplify query** - Try a shorter, more focused question\n4. **Increase timeout** - The timeout is currently {timeout}s\n\n**Note:** Deep business analysis (moat, 10-year outlook, management quality) requires more processing time. If NewsAdmin is still running, try clicking the button again.",
                "plan": None,
                "iterations": 0
            }
        except Exception as e:
            return {
                "error": str(e),
                "answer": f"⚠️ Error communicating with Dexter: {str(e)}",
                "plan": None,
                "iterations": 0
            }
    
    def research_stock(
        self,
        ticker: str,
        portfolio_context: Optional[Dict] = None,
        aspects: List[str] = None
    ) -> Dict[str, Any]:
        """
        Deep research on specific stock
        
        Args:
            ticker: Stock symbol
            portfolio_context: User's current portfolio
            aspects: Specific aspects to focus on (financials, news, comparison, etc.)
            
        Returns:
            Dexter's comprehensive analysis
        """
        # Build query based on aspects
        if aspects:
            aspect_text = ", ".join(aspects)
            query = f"Provide comprehensive analysis of {ticker} focusing on: {aspect_text}."
        else:
            query = f"Provide comprehensive analysis of {ticker} including financials, recent news, and investment outlook."
        
        # Add portfolio context if available
        if portfolio_context:
            holdings = portfolio_context.get('holdings', {})
            if ticker in holdings:
                shares = holdings[ticker].get('shares', 0)
                query += f" I currently hold {shares} shares of {ticker}."
            
            cash = portfolio_context.get('cash', 0)
            query += f" I have ${cash:.2f} in cash available."
        
        return self.research(query, portfolio_context)
    
    def get_recommendation(
        self,
        ticker: str,
        action: str,
        portfolio_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get Dexter's recommendation on specific action
        
        Args:
            ticker: Stock symbol
            action: 'buy', 'sell', 'hold'
            portfolio_context: Current portfolio
            
        Returns:
            Dexter's recommendation and reasoning
        """
        query = f"Should I {action} {ticker}?"
        
        if portfolio_context:
            cash = portfolio_context.get('cash', 0)
            holdings = portfolio_context.get('holdings', {})
            portfolio_value = portfolio_context.get('total_value', 0)
            
            if action == 'buy':
                query += f" I have ${cash:.2f} in cash and my portfolio is worth ${portfolio_value:.2f}."
            elif action == 'sell' and ticker in holdings:
                shares = holdings[ticker].get('shares', 0)
                entry_price = holdings[ticker].get('entry_price', 0)
                query += f" I own {shares} shares bought at ${entry_price:.2f}."
        
        return self.research(query, portfolio_context)
    
    def portfolio_analysis(self, portfolio_context: Dict) -> Dict[str, Any]:
        """
        Comprehensive portfolio analysis
        
        Args:
            portfolio_context: Full portfolio data
            
        Returns:
            Dexter's portfolio review and suggestions
        """
        cash = portfolio_context.get('cash', 0)
        holdings = portfolio_context.get('holdings', {})
        total_value = portfolio_context.get('total_value', 0)
        
        holdings_summary = ", ".join([
            f"{ticker} ({data.get('shares', 0)} shares)"
            for ticker, data in holdings.items()
        ])
        
        query = f"""Analyze my portfolio:
        
Cash: ${cash:.2f}
Holdings: {holdings_summary}
Total Value: ${total_value:.2f}

Provide insights on:
1. Sector diversification
2. Risk concentration
3. Rebalancing suggestions
4. Potential opportunities given current holdings"""
        
        return self.research(query, portfolio_context)
    
    def compare_stocks(
        self,
        tickers: List[str],
        portfolio_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple stocks
        
        Args:
            tickers: List of stock symbols
            portfolio_context: Optional portfolio context
            
        Returns:
            Comparative analysis
        """
        ticker_list = ", ".join(tickers)
        query = f"Compare these stocks: {ticker_list}. Which is the best investment opportunity?"
        
        if portfolio_context:
            cash = portfolio_context.get('cash', 0)
            query += f" I have ${cash:.2f} to invest."
        
        return self.research(query, portfolio_context)
    
    def chat(
        self,
        message: str,
        portfolio_context: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Conversational interface with Dexter
        
        Args:
            message: User's message
            portfolio_context: Current portfolio
            chat_history: Previous messages for context
            
        Returns:
            Dexter's response
        """
        # Include chat history in context if available
        context = portfolio_context or {}
        if chat_history:
            context['chat_history'] = chat_history
        
        return self.research(message, context)
    
    def health_check(self) -> bool:
        """
        Check if Dexter service is running - tries multiple ports and endpoints
        
        Returns:
            True if service is accessible
        """
        # Try multiple ports since Next.js auto-selects if 3000 is busy
        # Try 3002 first since NewsAdmin often ends up there when 3000 is busy
        ports_to_try = [3002, 3000, 3001, 3003, 3004]
        endpoints = ["/api/health", "/api/dexter/health", "/"]
        
        for port in ports_to_try:
            # First verify server is running
            try:
                test_url = f"http://localhost:{port}/"
                response = self.session.get(test_url, timeout=2)
                if response.status_code in [200, 404]:  # Server is running
                    # Now verify the API endpoint exists
                    api_url = f"http://localhost:{port}/api/dexter"
                    try:
                        # Try POST with empty payload - 400/422 means endpoint exists, 404 means it doesn't
                        api_response = self.session.post(api_url, json={}, timeout=2)
                        # Accept 200 (success), 400/422 (bad request but endpoint exists), 405 (method not allowed but endpoint exists)
                        if api_response.status_code in [200, 400, 422, 405]:
                            self.api_url = f"http://localhost:{port}"
                            return True
                    except requests.exceptions.RequestException:
                        # If POST fails, endpoint probably doesn't exist
                        pass
            except:
                continue
        
        return False


# Convenience function for quick usage
def ask_dexter(query: str, portfolio_context: Optional[Dict] = None) -> str:
    """
    Quick function to ask Dexter a question
    
    Args:
        query: Question or request
        portfolio_context: Optional portfolio data
        
    Returns:
        Dexter's answer as string
    """
    client = DexterClient()
    result = client.research(query, portfolio_context)
    return result.get('answer', 'No answer received')


# Example usage
if __name__ == "__main__":
    # Test connection
    client = DexterClient()
    
    print("Testing Dexter connection...")
    if client.health_check():
        print("✅ Dexter is running!")
        
        # Test basic query
        print("\nAsking Dexter about NVDA...")
        result = client.research_stock('NVDA')
        
        print(f"\nAnswer ({result.get('iterations', 0)} iterations):")
        print(result.get('answer', 'No answer'))
        
        if result.get('plan'):
            print(f"\nTasks executed: {len(result['plan'].get('tasks', []))}")
    else:
        print("❌ Dexter service not running")
        print("Start it with: cd NewsAdmin && npm run dev")
