"""
Test Dexter Integration
Verifies that Dexter API is accessible and working
"""

import sys
sys.path.insert(0, 'utils')

from dexter_client import DexterClient
from portfolio_context import PortfolioContext


def test_connection():
    """Test 1: Check if Dexter service is running"""
    print("\n" + "="*60)
    print("TEST 1: DEXTER CONNECTION")
    print("="*60)
    
    client = DexterClient()
    
    if client.health_check():
        print("[PASS] Dexter service is running!")
        print("   API URL: http://localhost:3000")
        return True
    else:
        print("[FAIL] Dexter service is NOT running!")
        print("\n   Start it with:")
        print("   cd NewsAdmin")
        print("   npm run dev")
        return False


def test_portfolio_context():
    """Test 2: Check portfolio context"""
    print("\n" + "="*60)
    print("TEST 2: PORTFOLIO CONTEXT")
    print("="*60)
    
    try:
        pc = PortfolioContext()
        context = pc.get_context()
        
        print("[PASS] Portfolio context loaded!")
        print(f"\n   Cash: ${context['cash']:,.2f}")
        print(f"   Holdings: {len(context['holdings'])} positions")
        print(f"   Total Value: ${context['total_value']:,.2f}")
        
        if context['holdings']:
            print("\n   Positions:")
            for ticker, data in context['holdings'].items():
                print(f"      - {ticker}: {data['shares']} shares @ ${data['entry_price']:.2f}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Portfolio context error: {e}")
        return False


def test_basic_research():
    """Test 3: Simple research query"""
    print("\n" + "="*60)
    print("TEST 3: BASIC RESEARCH")
    print("="*60)
    
    client = DexterClient()
    
    print("\n   Asking Dexter: 'What is the current price of AAPL?'")
    print("   (This tests basic API communication)")
    print("\n   [Researching...]")
    
    try:
        result = client.research("What is the current price of AAPL?")
        
        if 'error' in result:
            print(f"[FAIL] Research failed: {result['error']}")
            return False
        
        print("\n[PASS] Research completed!")
        print(f"   Iterations: {result.get('iterations', 0)}")
        print(f"   Tasks: {len(result.get('plan', {}).get('tasks', []))}")
        print("\n   Answer Preview:")
        print("   " + "-"*56)
        answer = result.get('answer', 'No answer')
        preview = answer[:200] + "..." if len(answer) > 200 else answer
        print("   " + preview.replace("\n", "\n   "))
        
        return True
    except Exception as e:
        print(f"[FAIL] Research error: {e}")
        return False


def test_portfolio_aware_query():
    """Test 4: Portfolio-aware research"""
    print("\n" + "="*60)
    print("TEST 4: PORTFOLIO-AWARE RESEARCH")
    print("="*60)
    
    client = DexterClient()
    pc = PortfolioContext()
    
    portfolio_context = pc.get_context()
    
    if not portfolio_context['holdings']:
        print("[SKIP] Skipping (no holdings in portfolio)")
        return True
    
    # Pick first holding for test
    first_ticker = list(portfolio_context['holdings'].keys())[0]
    
    print(f"\n   Asking: 'Should I buy more {first_ticker}?'")
    print("   (This tests portfolio context integration)")
    print("\n   [Researching with portfolio context...]")
    
    try:
        result = client.get_recommendation(first_ticker, 'buy', portfolio_context)
        
        if 'error' in result:
            print(f"[FAIL] Research failed: {result['error']}")
            return False
        
        print("\n[PASS] Portfolio-aware research completed!")
        print(f"   Iterations: {result.get('iterations', 0)}")
        print("\n   Answer Preview:")
        print("   " + "-"*56)
        answer = result.get('answer', 'No answer')
        preview = answer[:300] + "..." if len(answer) > 300 else answer
        print("   " + preview.replace("\n", "\n   "))
        
        return True
    except Exception as e:
        print(f"[FAIL] Research error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("DEXTER INTEGRATION TEST SUITE")
    print("="*60)
    print("\nTesting Dexter + Hedge Fund Scanner integration...")
    
    results = {
        "Connection": False,
        "Portfolio Context": False,
        "Basic Research": False,
        "Portfolio-Aware Research": False
    }
    
    # Run tests
    results["Connection"] = test_connection()
    
    if results["Connection"]:
        results["Portfolio Context"] = test_portfolio_context()
        results["Basic Research"] = test_basic_research()
        
        if results["Portfolio Context"]:
            results["Portfolio-Aware Research"] = test_portfolio_aware_query()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED!")
        print("\nYour Dexter integration is working correctly!")
        print("\nNext steps:")
        print("1. Open Streamlit app: http://localhost:8501")
        print("2. Go to 'Chat with Dexter' page")
        print("3. Start asking questions!")
    else:
        failed = [name for name, passed in results.items() if not passed]
        print("[FAILURE] SOME TESTS FAILED")
        print(f"\nFailed tests: {', '.join(failed)}")
        print("\nCheck the error messages above for details.")
        
        if not results["Connection"]:
            print("\nMake sure NewsAdmin is running:")
            print("  cd NewsAdmin")
            print("  npm run dev")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
