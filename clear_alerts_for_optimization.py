#!/usr/bin/env python3
"""
Clear Alerts Table for New Optimized System
==========================================
Clears the alerts table to start fresh with our enhanced momentum system
and stricter psychology thresholds for accurate performance tracking.
"""

import os
import sys
from datetime import datetime

# Set database URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

def clear_alerts_table():
    """Clear the alerts table for fresh start with optimized system"""
    
    print("🗑️  CLEARING ALERTS TABLE FOR OPTIMIZATION")
    print("=" * 60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🚀 OPTIMIZATIONS IMPLEMENTED:")
    print("  ✅ Enhanced momentum formula (dangerous attacks = KING)")
    print("  ✅ Stricter psychology thresholds (+60% requirements)")
    print("  ✅ Corner-prediction focused system")
    print("  ✅ Quality over quantity approach")
    print()
    
    print("📊 EXPECTED IMPROVEMENTS:")
    print("  • Alert volume: ~15/day → ~5-8/day")
    print("  • Win rate: ~30% → ~60-70%")
    print("  • Focus: Only explosive corner-creating momentum")
    print()
    
    # Confirm before clearing
    response = input("🤔 Are you sure you want to clear ALL alerts? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Operation cancelled.")
        return False
    
    try:
        # Import database after setting environment variables
        from database_postgres import get_database
        
        print("\n🔗 Connecting to PostgreSQL database...")
        db = get_database()
        
        print("🧹 Clearing alerts table...")
        success = db.truncate_alerts()
        
        if success:
            print("✅ ALERTS TABLE CLEARED SUCCESSFULLY!")
            print()
            print("🚀 READY FOR OPTIMIZED SYSTEM:")
            print("  • All old alerts removed")
            print("  • Fresh start for performance tracking") 
            print("  • New momentum system active")
            print("  • Stricter psychology thresholds active")
            print()
            print("📈 Monitor the new alerts for:")
            print("  • Higher win rates")
            print("  • Better alert quality")
            print("  • Corner storm accuracy")
            print()
            print("🎯 Next step: Deploy optimized system and monitor results!")
            return True
        else:
            print("❌ FAILED TO CLEAR ALERTS TABLE")
            print("Check database connection and permissions.")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_system_status():
    """Show the current optimization status"""
    print("\n📋 CURRENT SYSTEM STATUS:")
    print("  🔧 Momentum System: OPTIMIZED")
    print("     • Dangerous attacks: 12 pts (KING!)")
    print("     • Shots on target: 10 pts")
    print("     • General attacks: 4 pts")
    print("     • Shots off target: 4 pts")
    print()
    print("  🧠 Psychology Thresholds: STRICTER")
    print("     • PANICKING_FAVORITE: 120+ momentum (was 75)")
    print("     • FIGHTING_UNDERDOG: 100+ momentum (was 60)")
    print("     • Combined intensity: 150+ pts (was 100-80)")
    print()
    print("  📱 Alert Format: UPDATED")
    print("     • Shows momentum instead of probability")
    print("     • Clear corner-creation explanation")

if __name__ == "__main__":
    show_system_status()
    print()
    success = clear_alerts_table()
    
    if success:
        print("🎉 OPTIMIZATION DEPLOYMENT READY!")
        sys.exit(0)
    else:
        print("❌ DEPLOYMENT BLOCKED - Fix database issues first")
        sys.exit(1)