"""
Automated Dexter Service Starter
Starts NewsAdmin/Dexter service automatically before running Streamlit
"""
import sys
import os
import subprocess
import time
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

try:
    from dexter_manager import DexterManager
except ImportError:
    print("Warning: dexter_manager not available, skipping auto-start")
    DexterManager = None


def main():
    """Main entry point - starts Dexter then Streamlit"""
    print("="*60)
    print("AUTO-START: Dexter + Hedge Fund Scanner")
    print("="*60)
    print()
    
    # Start Dexter if manager is available
    if DexterManager:
        print("[1/2] Checking Dexter service...")
        manager = DexterManager()
        
        if manager.is_running():
            print("   ✓ Dexter is already running")
        else:
            print("   → Starting Dexter service...")
            success, message = manager.start(wait_for_ready=True, timeout=30)
            
            if success:
                print(f"   ✓ {message}")
            else:
                print(f"   ✗ {message}")
                print("   → Continuing anyway (you can start manually)")
    else:
        print("[1/2] Skipping Dexter auto-start (manager not available)")
    
    print()
    print("[2/2] Starting Streamlit app...")
    print()
    print("="*60)
    print("Services:")
    print("  Dexter API:      http://localhost:3000")
    print("  Hedge Scanner:   http://localhost:8501")
    print("="*60)
    print()
    
    # Start Streamlit
    os.chdir(Path(__file__).parent)
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()





