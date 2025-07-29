#!/usr/bin/env python3
"""
Combined runner for both alert system and web dashboard
SHARED DATA ARCHITECTURE: Dashboard provides data, Alert system consumes it
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
    """Run the main alert system in background thread (reads from dashboard's shared data)"""
    logger.info("🚨 STARTING: Alert system thread (SHARED DATA mode)...")
    
    # Wait for dashboard to initialize its data
    logger.info("⏳ WAITING: 10 seconds for dashboard to populate shared data...")
    time.sleep(10)
    
    try:
        from main import main as main_monitor
        logger.info("🚨 RUNNING: Alert system main loop (using shared dashboard data)...")
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
    """Run the web dashboard (PRIMARY DATA SOURCE for shared architecture)"""
    logger.info("🌐 STARTING: Web dashboard (PRIMARY DATA SOURCE)...")
    try:
        # Import the Flask app AND the background thread starter
        from web_dashboard import app, start_dashboard_background_thread
        
        # CRITICAL: Start the background thread that populates live data
        logger.info("📊 INITIALIZING: Shared data source...")
        start_dashboard_background_thread()
        
        # Give it a moment to start fetching data
        time.sleep(2)
        logger.info("✅ Dashboard background data updater started!")
        
        # Start Flask app
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"🌐 RUNNING: Dashboard on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
    except Exception as e:
        logger.error(f"🌐 FATAL ERROR: Dashboard crashed: {e}")
        raise

if __name__ == "__main__":
    logger.info("STARTING: Combined Late Corner System...")
    logger.info("=" * 50)
    logger.info("📊 ARCHITECTURE: Shared Data System")
    logger.info("🌐 DATA SOURCE: Dashboard (single SportMonks API connection)")
    logger.info("🚨 DATA CONSUMER: Alert System (reads from dashboard)")
    logger.info("💡 BENEFIT: 50% fewer API calls, no rate limit issues")
    logger.info("=" * 50)
    
    # Start dashboard first (it becomes the data provider)
    logger.info("🌐 STARTING: Web dashboard first (data provider)...")
    dashboard_thread = threading.Thread(target=run_web_dashboard, daemon=False)
    dashboard_thread.start()
    
    # Wait a bit for dashboard to start
    time.sleep(5)
    
    # Start alert system second (it becomes the data consumer)
    logger.info("🚨 STARTING: Alert system second (data consumer)...")
    alert_thread = threading.Thread(target=run_alert_system, daemon=False)
    alert_thread.start()
    
    logger.info("✅ Both systems started with shared data architecture!")
    logger.info("📊 Dashboard provides data at: http://localhost:8080")
    logger.info("🚨 Alert system reads from dashboard's shared data")
    logger.info("💰 Ready to catch profitable corner opportunities with optimal efficiency!")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
            logger.info("❤️ HEARTBEAT: Combined system running smoothly with shared data...")
    except KeyboardInterrupt:
        logger.info("👋 Shutting down combined system gracefully...")
    except Exception as e:
        logger.error(f"❌ FATAL: Combined system error: {e}")
        raise 