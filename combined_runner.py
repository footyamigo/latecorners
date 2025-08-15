#!/usr/bin/env python3
"""
Combined runner for both alert system and web dashboard
SHARED DATA ARCHITECTURE: Dashboard provides data, Alert system consumes it
UPDATED: Fixed first half cache conflicts - using FirstHalfAnalyzer
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

def run_late_corner_system():
    """Run the late corner alert system (85-89 minutes) in background thread"""
    logger.info("🚨 STARTING: Late corner system thread (85-89 minutes)...")
    
    # Wait for dashboard to initialize its data
    logger.info("⏳ WAITING: 10 seconds for dashboard to populate shared data...")
    time.sleep(10)
    
    try:
        from main import main as main_monitor
        logger.info("🚨 RUNNING: Late corner system (85-89 min) using shared dashboard data...")
        asyncio.run(main_monitor())
    except Exception as e:
        logger.error(f"🚨 FATAL ERROR: Late corner system crashed: {e}")
        import traceback
        logger.error(f"🚨 TRACEBACK: {traceback.format_exc()}")
        # Don't exit - keep trying to restart
        logger.info("🚨 WAITING: 30 seconds before restart attempt...")
        time.sleep(30)
        logger.info("🚨 RESTARTING: Late corner system...")
        run_late_corner_system()  # Recursive restart

def run_first_half_system():
    """Run the DEDICATED first half corner alert system (30-35 minutes) in background thread"""
    logger.info("🏁 STARTING: DEDICATED First half system thread (30-35 minutes)...")
    
    # Wait for other systems to start
    logger.info("⏳ WAITING: 10 seconds for other systems...")
    time.sleep(10)
    
    try:
        # Import and run DEDICATED first half system
        from first_half_dedicated import main as first_half_dedicated_main
        logger.info("🏁 RUNNING: DEDICATED First half system (independent API calls)...")
        asyncio.run(first_half_dedicated_main())
    except Exception as e:
        logger.error(f"🏁 FATAL ERROR: DEDICATED First half system crashed: {e}")
        import traceback
        logger.error(f"🏁 TRACEBACK: {traceback.format_exc()}")
        # Don't exit - keep trying to restart
        logger.info("🏁 WAITING: 30 seconds before restart attempt...")
        time.sleep(30)
        logger.info("🏁 RESTARTING: DEDICATED First half system...")
        run_first_half_system()  # Recursive restart

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
    logger.info("STARTING: Combined Corner Alert System...")
    logger.info("=" * 60)
    logger.info("📊 ARCHITECTURE: Shared Data System")
    logger.info("🌐 DATA SOURCE: Dashboard (single SportMonks API connection)")
    logger.info("🚨 LATE CORNER SYSTEM: 85-89 minutes (reads from dashboard)")
    logger.info("🏁 FIRST HALF SYSTEM: 30-35 minutes (independent monitoring)")
    logger.info("💡 BENEFIT: Complete coverage + 50% fewer API calls")
    logger.info("=" * 60)
    
    # Start dashboard first (it becomes the data provider)
    logger.info("🌐 STARTING: Web dashboard first (data provider)...")
    dashboard_thread = threading.Thread(target=run_web_dashboard, daemon=False)
    dashboard_thread.start()
    
    # Wait a bit for dashboard to start
    time.sleep(5)
    
    # Start late corner system second (it reads from dashboard data)
    logger.info("🚨 STARTING: Late corner system (85-89 min) - data consumer...")
    late_corner_thread = threading.Thread(target=run_late_corner_system, daemon=False)
    late_corner_thread.start()
    
    # Wait a bit more, then start first half system
    time.sleep(3)
    
    # Start first half system third (independent monitoring)
    logger.info("🏁 STARTING: First half system (30-35 min) - independent...")
    first_half_thread = threading.Thread(target=run_first_half_system, daemon=False)
    first_half_thread.start()
    
    logger.info("✅ ALL THREE SYSTEMS STARTED!")
    logger.info("📊 Dashboard: http://localhost:8080")
    logger.info("🚨 Late Corner: 85-89 minutes (Market: Asian Corners)")
    logger.info("🏁 First Half: 30-35 minutes (Market: 1st Half Asian Corners)")
    logger.info("💰 Ready to catch profitable corner opportunities across BOTH halves!")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
            logger.info("❤️ HEARTBEAT: Combined system (Dashboard + Late + First Half) running smoothly...")
    except KeyboardInterrupt:
        logger.info("👋 Shutting down combined system gracefully...")
    except Exception as e:
        logger.error(f"❌ FATAL: Combined system error: {e}")
        raise 