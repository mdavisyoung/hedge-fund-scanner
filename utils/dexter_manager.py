"""
Dexter Service Manager - Automatically starts and manages NewsAdmin service
"""
import os
import sys
import subprocess
import time
import requests
from pathlib import Path
from typing import Optional, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class DexterManager:
    """Manages the Dexter/NewsAdmin service lifecycle"""
    
    def __init__(self, newsadmin_path: Optional[str] = None):
        """
        Initialize Dexter Manager
        
        Args:
            newsadmin_path: Path to NewsAdmin directory (default: auto-detect)
        """
        self.api_url = os.getenv('DEXTER_API_URL', 'http://localhost:3000')
        self.newsadmin_path = newsadmin_path or self._find_newsadmin()
        self.process: Optional[subprocess.Popen] = None
        self.detected_port: Optional[int] = None
        
    def _find_newsadmin(self) -> Optional[str]:
        """Try to find NewsAdmin directory"""
        # Common locations
        possible_paths = [
            os.path.join(os.path.expanduser("~"), "Desktop", "NewsAdmin"),
            os.path.join(os.path.expanduser("~"), "Documents", "NewsAdmin"),
            os.path.join(os.path.expanduser("~"), "NewsAdmin"),
            "C:\\Users\\svfam\\Desktop\\NewsAdmin",  # User's specific path
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                package_json = os.path.join(path, "package.json")
                if os.path.exists(package_json):
                    return path
        
        return None
    
    def is_running(self) -> bool:
        """Check if Dexter service is already running - tries multiple ports"""
        # Try common ports (3000, 3001, 3002, etc.) since Next.js auto-selects if 3000 is busy
        ports_to_try = [3000, 3001, 3002, 3003, 3004]
        
        # If we detected a port before, try that first
        if self.detected_port:
            ports_to_try.insert(0, self.detected_port)
        
        endpoints = [
            "/api/health",
            "/api/dexter/health", 
            "/",  # Root endpoint
        ]
        
        for port in ports_to_try:
            for endpoint in endpoints:
                try:
                    url = f"http://localhost:{port}{endpoint}"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        # Save the detected port
                        self.detected_port = port
                        self.api_url = f"http://localhost:{port}"
                        return True
                except:
                    continue
        
        return False
    
    def is_port_in_use(self, port: int = 3000) -> bool:
        """Check if port 3000 is in use"""
        if not PSUTIL_AVAILABLE:
            # Fallback: try to connect to the port
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                return result == 0
            except:
                return False
        else:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
    
    def start(self, wait_for_ready: bool = True, timeout: int = 60) -> Tuple[bool, str]:
        """
        Start the Dexter/NewsAdmin service
        
        Args:
            wait_for_ready: Wait for service to be ready before returning
            timeout: Maximum wait time in seconds
            
        Returns:
            (success: bool, message: str)
        """
        # Check if already running
        if self.is_running():
            return True, "Dexter service is already running"
        
        # Check if NewsAdmin path exists
        if not self.newsadmin_path:
            return False, "NewsAdmin directory not found. Please set DEXTER_NEWSADMIN_PATH environment variable or place NewsAdmin in Desktop/Documents."
        
        if not os.path.exists(self.newsadmin_path):
            return False, f"NewsAdmin path does not exist: {self.newsadmin_path}"
        
        # Check if npm is available (try multiple ways)
        npm_path = None
        npm_commands = ["npm", "npm.cmd"]
        
        # Try to find npm in PATH
        for cmd in npm_commands:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    check=True,
                    timeout=5,
                    shell=True  # Use shell on Windows to access PATH
                )
                npm_path = cmd
                break
            except:
                continue
        
        # Also try common installation paths on Windows
        if not npm_path:
            common_paths = [
                r"C:\Program Files\nodejs\npm.cmd",
                r"C:\Program Files (x86)\nodejs\npm.cmd",
                os.path.join(os.environ.get("ProgramFiles", ""), "nodejs", "npm.cmd"),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    npm_path = path
                    break
        
        if not npm_path:
            return False, "npm is not installed or not in PATH. Please install Node.js from https://nodejs.org/"
        
        # Start the service
        try:
            print(f"[Dexter Manager] Starting NewsAdmin from: {self.newsadmin_path}")
            
            # Use the found npm path
            npm_cmd = npm_path
            
            # Change to NewsAdmin directory and start
            # On Windows, use shell=True to ensure PATH is available
            # Don't capture output so user can see npm logs in console
            # Set Node.js memory limit to prevent crashes (4GB)
            env = os.environ.copy()
            env["NODE_OPTIONS"] = "--max-old-space-size=4096"
            
            self.process = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=self.newsadmin_path,
                stdout=None,  # Let output go to console
                stderr=None,  # Let errors go to console  
                shell=True,
                env=env  # Pass environment with memory limit
            )
            
            if wait_for_ready:
                # Wait for service to be ready
                if timeout == 0:
                    # Special case: don't wait, just return immediately
                    return True, "Dexter service start command executed (checking in background)"
                
                print("[Dexter Manager] Waiting for service to start...")
                start_time = time.time()
                check_interval = 2  # Check every 2 seconds
                
                while time.time() - start_time < timeout:
                    elapsed = int(time.time() - start_time)
                    if self.is_running():
                        print(f"[Dexter Manager] Service is ready! (took {elapsed}s)")
                        return True, f"Dexter service started successfully (ready in {elapsed}s)"
                    
                    # Show progress every 10 seconds
                    if elapsed % 10 == 0 and elapsed > 0:
                        print(f"[Dexter Manager] Still waiting... ({elapsed}s elapsed)")
                    
                    time.sleep(check_interval)
                
                # Check if process is still running
                process_running = False
                if self.process:
                    try:
                        self.process.poll()  # Returns None if still running
                        process_running = (self.process.returncode is None)
                    except:
                        pass
                
                if process_running:
                    return False, f"Service started but not responding after {timeout} seconds. Check NewsAdmin logs for errors."
                else:
                    return False, f"Service process exited. Check NewsAdmin directory and npm logs for errors."
            else:
                return True, "Dexter service start command executed"
                
        except Exception as e:
            return False, f"Failed to start Dexter service: {str(e)}"
    
    def stop(self) -> Tuple[bool, str]:
        """Stop the Dexter service"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                return True, "Dexter service stopped"
            except:
                try:
                    self.process.kill()
                    return True, "Dexter service force-stopped"
                except Exception as e:
                    return False, f"Failed to stop service: {str(e)}"
        else:
            # Try to find and kill any process on port 3000
            if PSUTIL_AVAILABLE:
                try:
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            for conn in proc.connections():
                                if conn.laddr.port == 3000:
                                    proc.terminate()
                                    return True, "Dexter service stopped (found on port 3000)"
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except:
                    pass
            
            return False, "No running Dexter process found"
    
    def ensure_running(self, auto_start: bool = True) -> Tuple[bool, str]:
        """
        Ensure Dexter service is running, start if needed
        
        Args:
            auto_start: Automatically start if not running
            
        Returns:
            (success: bool, message: str)
        """
        if self.is_running():
            return True, "Dexter service is running"
        
        if auto_start:
            return self.start()
        else:
            return False, "Dexter service is not running. Set auto_start=True to start automatically."


# Convenience function for Streamlit integration
def ensure_dexter_running() -> Tuple[bool, str]:
    """
    Ensure Dexter is running, start if needed
    Returns (success, message) for Streamlit display
    """
    manager = DexterManager()
    return manager.ensure_running(auto_start=True)


if __name__ == "__main__":
    # Test the manager
    print("="*60)
    print("DEXTER SERVICE MANAGER TEST")
    print("="*60)
    
    manager = DexterManager()
    
    print(f"\nNewsAdmin Path: {manager.newsadmin_path or 'NOT FOUND'}")
    print(f"Service URL: {manager.api_url}")
    print(f"Currently Running: {manager.is_running()}")
    
    if not manager.is_running():
        print("\nStarting Dexter service...")
        success, message = manager.start()
        print(f"Result: {message}")
        
        if success:
            print("\n✅ Dexter service is now running!")
            print(f"   URL: {manager.api_url}")
        else:
            print(f"\n❌ Failed to start: {message}")
    else:
        print("\n✅ Dexter service is already running!")

