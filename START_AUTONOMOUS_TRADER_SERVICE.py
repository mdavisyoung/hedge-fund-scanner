"""
Autonomous Trader Windows Service
Runs the autonomous trader as a background service that starts on boot
"""
import sys
import os
import time
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def create_windows_task():
    """Create a Windows Scheduled Task to run the trader automatically"""
    script_path = Path(__file__).parent / "trader" / "run_autonomous.py"
    python_exe = sys.executable
    
    # Task name
    task_name = "AutonomousTrader"
    
    # Command to create the task
    # Runs every weekday at 9:25 AM (before market open at 9:30 AM)
    # Stops at 4:15 PM (after market close at 4:00 PM)
    cmd = f'''schtasks /Create /TN "{task_name}" /TR "\\"{python_exe}\\" \\"{script_path}\\" --mode continuous --interval 300 --paper" /SC DAILY /ST 09:25 /ET 16:15 /D MON,TUE,WED,THU,FRI /RL HIGHEST /F'''
    
    print("Creating Windows Scheduled Task...")
    print(f"Task will run: Monday-Friday, 9:25 AM - 4:15 PM ET")
    print(f"Command: {cmd}")
    print()
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Scheduled task created successfully!")
        print()
        print("The autonomous trader will now:")
        print("  - Start automatically at 9:25 AM on weekdays")
        print("  - Run continuously during market hours")
        print("  - Stop at 4:15 PM")
        print()
        print("To view/manage the task:")
        print("  - Open Task Scheduler")
        print("  - Look for 'AutonomousTrader'")
        print()
        print("To delete the task:")
        print(f"  schtasks /Delete /TN \"{task_name}\" /F")
    else:
        print("❌ Failed to create scheduled task")
        print("Error:", result.stderr)
        print()
        print("You may need to run this script as Administrator")
        return False
    
    return True


def main():
    """Main entry point"""
    print("="*60)
    print("AUTONOMOUS TRADER - WINDOWS SERVICE SETUP")
    print("="*60)
    print()
    
    # Check if running as admin (recommended for task creation)
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    
    if not is_admin:
        print("⚠️  WARNING: Not running as Administrator")
        print("Task creation may fail. Consider running as Administrator.")
        print()
    
    choice = input("Create Windows Scheduled Task? (y/n): ").strip().lower()
    
    if choice == 'y':
        success = create_windows_task()
        if success:
            print()
            print("Setup complete!")
            print("The trader will start automatically on next boot (or immediately if market is open)")
    else:
        print()
        print("Scheduled task not created.")
        print()
        print("To run manually, use:")
        print("  python trader/run_autonomous.py --mode continuous --interval 300 --paper")
        print()
        print("Or use the batch file:")
        print("  START_AUTONOMOUS_TRADER.bat")


if __name__ == "__main__":
    main()

