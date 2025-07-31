#!/usr/bin/env python3
"""
Database Backup Utility
========================
Simple backup/restore for alerts.db on Railway
"""

import os
import shutil
import logging
from datetime import datetime
from database import get_database

logger = logging.getLogger(__name__)

def backup_database():
    """Create a timestamped backup of the database"""
    
    db_path = "alerts.db"
    
    if not os.path.exists(db_path):
        logger.warning("⚠️ No database file found to backup")
        return False
    
    try:
        # Create backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"alerts_backup_{timestamp}.db"
        
        # Copy database
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"✅ Database backed up to: {backup_path}")
        logger.info(f"📊 Backup size: {os.path.getsize(backup_path)} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False

def export_alerts_json():
    """Export all alerts to JSON for extra safety"""
    
    try:
        db = get_database()
        alerts = db.get_all_alerts(limit=1000)  # Get all alerts
        
        if not alerts:
            logger.info("📊 No alerts to export")
            return True
        
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"alerts_export_{timestamp}.json"
        
        with open(export_path, 'w') as f:
            json.dump(alerts, f, indent=2, default=str)
        
        logger.info(f"✅ Alerts exported to: {export_path}")
        logger.info(f"📊 Exported {len(alerts)} alerts")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        return False

def show_database_info():
    """Show current database status"""
    
    db_path = "alerts.db"
    
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        modified = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        print(f"📊 DATABASE INFO:")
        print(f"   📂 Path: {os.path.abspath(db_path)}")
        print(f"   📏 Size: {size} bytes")
        print(f"   🕐 Modified: {modified}")
        
        # Get stats from database
        db = get_database()
        stats = db.get_performance_stats()
        
        if stats:
            print(f"   📈 Total Alerts: {stats['total_alerts']}")
            print(f"   ✅ Wins: {stats['wins']}")
            print(f"   ❌ Losses: {stats['losses']}")
            print(f"   ⏳ Pending: {stats['pending']}")
    else:
        print("❌ Database file not found")

if __name__ == "__main__":
    print("🗄️ RAILWAY DATABASE UTILITY")
    print("="*40)
    
    show_database_info()
    print()
    
    # Create backup
    print("💾 Creating backup...")
    backup_database()
    
    # Export JSON
    print("📋 Exporting JSON...")
    export_alerts_json()
    
    print("\n✅ Backup complete!") 