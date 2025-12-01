#!/usr/bin/env python3
"""
Zenin EEG Application Launcher
Starts the FastAPI backend and opens the browser automatically.
"""
import threading
import time
import webbrowser
import uvicorn
import sys
import os

# Add the backend directory to the path so we can import app.main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    """Open the default browser after a short delay to let the server start"""
    time.sleep(2)
    print("\n🌊 Opening Zenin EEG in your browser...")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 Zenin EEG Pipeline - Starting...")
    print("=" * 60)
    print("\n📍 Server will be available at: http://127.0.0.1:8000")
    print("🌐 Browser will open automatically in 2 seconds...")
    print("\n⏰ Auto-shutdown: Server will stop after 10 minutes of inactivity")
    print("🛑 To stop the server manually: Press Ctrl+C\n")
    
    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the FastAPI server (this blocks until server is stopped)
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Error starting server: {e}")
        sys.exit(1)
