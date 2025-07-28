#!/usr/bin/env python3
"""
Combined runner for both alert system and web dashboard
Perfect for Railway deployment with both features
"""

import asyncio
import threading
import time
import os
import sys
from flask import Flask

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_alert_system():
    """Run the main alert system in background thread"""
    print("STARTING: Alert system...")
    try:
        from main import main as main_monitor
        asyncio.run(main_monitor())
    except Exception as e:
        print(f"ERROR: Alert system error: {e}")

def run_web_dashboard():
    """Run the web dashboard"""
    print("STARTING: Web dashboard...")
    try:
        # Import the Flask app from web_dashboard
        from web_dashboard import app
        
        # Get port from environment (Railway sets PORT automatically)
        port = int(os.environ.get('PORT', 5000))
        host = '0.0.0.0'  # Required for Railway
        
        print(f"SUCCESS: Web dashboard available at http://localhost:{port}")
        app.run(host=host, port=port, debug=False, threaded=True)
        
    except Exception as e:
        print(f"ERROR: Web dashboard error: {e}")

def main():
    """Main entry point - starts both systems"""
    print("STARTING: Combined Late Corner System...")
    print("=" * 50)
    print("ALERT SYSTEM: Sends Telegram notifications")
    print("WEB DASHBOARD: Visual interface for monitoring") 
    print("=" * 50)
    
    # Start alert system in background thread
    alert_thread = threading.Thread(target=run_alert_system, daemon=True)
    alert_thread.start()
    
    # Give alert system a moment to start
    time.sleep(2)
    
    # Start web dashboard in main thread (Railway needs this)
    run_web_dashboard()

if __name__ == "__main__":
    main() 