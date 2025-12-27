"""
Desktop Application Launcher for Personal Hedge Fund Manager
This creates a native desktop window that runs the Streamlit app.
"""
import sys
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
    from PyQt5.QtCore import QUrl, QThread, pyqtSignal
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

try:
    import streamlit.web.cli as stcli
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


if PYQT_AVAILABLE:
    class StreamlitServerThread(QThread):
        """Thread to run Streamlit server"""
        server_ready = pyqtSignal()
        
        def __init__(self, app_path):
            super().__init__()
            self.app_path = app_path
            self.process = None
            
        def run(self):
            """Start Streamlit server"""
            try:
                # Change to app directory
                os.chdir(self.app_path)
                
                # Start Streamlit
                sys.argv = ["streamlit", "run", "app.py", "--server.headless", "true"]
                stcli.main()
            except Exception as e:
                print(f"Error starting Streamlit: {e}")
        
        def stop(self):
            """Stop Streamlit server"""
            if self.process:
                self.process.terminate()


class SimpleDesktopLauncher:
    """Simple desktop launcher using system browser"""
    
    def __init__(self):
        self.app_path = Path(__file__).parent
        self.process = None
        
    def start(self):
        """Start Streamlit in browser"""
        print("Starting Personal Hedge Fund Manager...")
        print("Opening in your default browser...")
        
        # Change to app directory
        os.chdir(self.app_path)
        
        # Start Streamlit server
        subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Open browser
        webbrowser.open("http://localhost:8501")
        
        print("\n" + "="*50)
        print("Personal Hedge Fund Manager is running!")
        print("="*50)
        print("The app should open in your browser.")
        print("If not, navigate to: http://localhost:8501")
        print("\nPress Ctrl+C to stop the server.")
        print("="*50 + "\n")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            sys.exit(0)


if PYQT_AVAILABLE:
    class PyQtDesktopApp(QMainWindow):
        """PyQt desktop application with embedded browser"""
        
        def __init__(self):
            super().__init__()
            self.app_path = Path(__file__).parent
            self.server_thread = None
            self.init_ui()
            self.start_server()
            
        def init_ui(self):
            """Initialize UI"""
            self.setWindowTitle("Personal Hedge Fund Manager")
            self.setGeometry(100, 100, 1200, 800)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # Status label
            self.status_label = QLabel("Starting application...")
            layout.addWidget(self.status_label)
            
            # Web view
            self.web_view = QWebEngineView()
            layout.addWidget(self.web_view)
            
            # Start button
            self.start_btn = QPushButton("Open in Browser")
            self.start_btn.clicked.connect(self.open_browser)
            layout.addWidget(self.start_btn)
            
        def start_server(self):
            """Start Streamlit server in background"""
            self.status_label.setText("Starting Streamlit server...")
            self.server_thread = StreamlitServerThread(self.app_path)
            self.server_thread.server_ready.connect(self.on_server_ready)
            self.server_thread.start()
            
            # Wait and load page
            QApplication.processEvents()
            time.sleep(3)
            self.web_view.setUrl(QUrl("http://localhost:8501"))
            self.status_label.setText("Application ready! Running on http://localhost:8501")
            
        def on_server_ready(self):
            """Called when server is ready"""
            self.web_view.setUrl(QUrl("http://localhost:8501"))
            self.status_label.setText("Application ready!")
            
        def open_browser(self):
            """Open in system browser"""
            webbrowser.open("http://localhost:8501")
            
        def closeEvent(self, event):
            """Handle window close"""
            if self.server_thread:
                self.server_thread.stop()
            event.accept()


def main():
    """Main entry point"""
    app_path = Path(__file__).parent
    
    # Check if Streamlit is available
    if not STREAMLIT_AVAILABLE:
        print("ERROR: Streamlit is not installed.")
        print("Please install it with: pip install streamlit")
        sys.exit(1)
    
    # Try PyQt first, fallback to simple launcher
    if PYQT_AVAILABLE:
        try:
            app = QApplication(sys.argv)
            window = PyQtDesktopApp()
            window.show()
            sys.exit(app.exec_())
        except Exception as e:
            print(f"Error with PyQt: {e}")
            print("Falling back to simple launcher...")
            launcher = SimpleDesktopLauncher()
            launcher.start()
    else:
        print("PyQt5 not available. Using simple launcher.")
        print("For better experience, install PyQt5: pip install PyQt5 PyQtWebEngine")
        print()
        launcher = SimpleDesktopLauncher()
        launcher.start()


if __name__ == "__main__":
    main()

