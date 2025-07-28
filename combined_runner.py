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
import logging

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging for combined runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('combined_runner')

def run_alert_system():
    """Run the main alert system in background thread"""
    logger.info("🚨 STARTING: Alert system thread...")
    try:
        from main import main as main_monitor
        logger.info("🚨 RUNNING: Alert system main loop...")
        asyncio.run(main_monitor())
    except Exception as e:
        logger.error(f"🚨 FATAL ERROR: Alert system crashed: {e}")
        import traceback
        logger.error(f"🚨 TRACEBACK: {traceback.format_exc()}")
        # Don't exit - keep trying to restart
        logger.info("🚨 WAITING: 30 seconds before restart attempt...")
        time.sleep(30)
        logger.info("🚨 RESTARTING: Alert system...")
        run_alert_system()  # Recursive restart

def run_web_dashboard():
    """Run the web dashboard"""
    logger.info("🌐 STARTING: Web dashboard...")
    try:
        # Import the Flask app AND the background thread starter
        from web_dashboard import app, start_dashboard_background_thread
        
        # CRITICAL: Start the background thread that populates live data
        start_dashboard_background_thread()
        
        # Get port from environment (Railway sets PORT automatically)
        port = int(os.environ.get('PORT', 5000))
        host = '0.0.0.0'  # Required for Railway
        
        logger.info(f"🌐 SUCCESS: Web dashboard available at http://localhost:{port}")
        app.run(host=host, port=port, debug=False, threaded=True)
        
    except Exception as e:
        logger.error(f"🌐 ERROR: Web dashboard error: {e}")
        import traceback
        logger.error(f"🌐 TRACEBACK: {traceback.format_exc()}")

def main():
    """Main entry point - starts both systems"""
    logger.info("🚀 STARTING: Combined Late Corner System...")
    logger.info("=" * 50)
    logger.info("🚨 ALERT SYSTEM: Sends Telegram notifications")
    logger.info("🌐 WEB DASHBOARD: Visual interface for monitoring") 
    logger.info("=" * 50)
    
    # Start alert system in background thread (NOT daemon - so it won't die silently)
    alert_thread = threading.Thread(target=run_alert_system, daemon=False)
    alert_thread.start()
    logger.info("🚨 THREAD: Alert system thread started (non-daemon)")
    
    # Give alert system a moment to start
    time.sleep(3)
    
    # Start web dashboard in main thread (Railway needs this)
    run_web_dashboard()

if __name__ == "__main__":
    main() 