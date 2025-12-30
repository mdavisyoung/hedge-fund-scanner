"""
Test script for native Python Dexter implementation
Run this to verify Dexter is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dexter import create_dexter

def test_dexter():
    """Test Dexter with a simple query"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔬 Testing Native Python Dexter Implementation\n")
    print("="*60)
    
    # Check API keys
    xai_key = os.getenv('XAI_API_KEY')
    polygon_key = os.getenv('POLYGON_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    
    print(f"✓ XAI_API_KEY: {'Found' if xai_key else 'MISSING'}")
    print(f"✓ POLYGON_API_KEY: {'Found' if polygon_key else 'MISSING'}")
    print(f"✓ TAVILY_API_KEY: {'Found' if tavily_key else 'Not configured (optional)'}")
    print("="*60 + "\n")
    
    if not xai_key or not polygon_key:
        print("❌ ERROR: Required API keys missing!")
        print("Please set XAI_API_KEY and POLYGON_API_KEY in your .env file")
        return
    
    try:
        # Create Dexter instance
        print("Creating Dexter instance...")
        dexter = create_dexter()
        print("✅ Dexter initialized successfully!\n")
        
        # Test query
        query = "What is NVDA's current stock price and recent performance?"
        print(f"🔍 Query: {query}\n")
        print("Running research (this may take 30-60 seconds)...\n")
        
        # Execute research
        result = dexter.research(query)
        
        # Display results
        print("="*60)
        print("📊 RESEARCH RESULTS")
        print("="*60)
        print(f"\n{result['answer']}\n")
        print("="*60)
        print(f"✅ Completed in {result['iterations']} iteration(s)")
        print(f"✅ Tasks executed: {len(result['plan']['tasks'])}")
        print(f"✅ Status: {result['plan']['status']}")
        print("\n📋 Task Breakdown:")
        for i, task in enumerate(result['plan']['tasks'], 1):
            status_emoji = "✅" if task['status'] == 'completed' else "❌"
            print(f"  {status_emoji} Task {i}: {task['description']} ({task['status']})")
        
        print("\n" + "="*60)
        print("🎉 DEXTER TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nFull error details:")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_dexter()
