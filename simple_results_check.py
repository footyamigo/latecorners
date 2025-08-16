#!/usr/bin/env python3
"""
SIMPLE RESULTS CHECKER
======================
Quick check of what's working vs what's not in the database.
Uses the actual database schema.
"""

import os
import psycopg2

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

def connect_db():
    """Simple database connection"""
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        print("✅ Connected to database")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def check_corner_performance(conn):
    """Check which corner counts perform best"""
    print("\n🎯 CORNER COUNT PERFORMANCE")
    print("-" * 50)
    
    query = """
    SELECT 
        corners_at_alert,
        COUNT(*) as total_alerts,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN result = 'REFUND' THEN 1 ELSE 0 END) as refunds,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate,
        ROUND(SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as loss_rate
    FROM alerts 
    WHERE corners_at_alert IS NOT NULL
    GROUP BY corners_at_alert
    ORDER BY corners_at_alert
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Corner':<8} {'Total':<8} {'Wins':<6} {'Loss':<6} {'Refund':<8} {'Win%':<8} {'Loss%':<8} {'Profit':<8}")
    print("-" * 70)
    
    best_corner = None
    best_profit = -100
    worst_corner = None
    worst_profit = 100
    
    for row in results:
        corner, total, wins, losses, refunds, win_rate, loss_rate = row
        profit = win_rate - loss_rate
        
        print(f"{corner:<8} {total:<8} {wins:<6} {losses:<6} {refunds:<8} {win_rate:<8}% {loss_rate:<8}% {profit:<8.1f}%")
        
        if total >= 3:  # Only consider corners with reasonable sample size
            if profit > best_profit:
                best_profit = profit
                best_corner = corner
            if profit < worst_profit:
                worst_profit = profit
                worst_corner = corner
    
    print(f"\n🏆 BEST PERFORMING: {best_corner} corners (Profit: {best_profit:.1f}%)")
    print(f"💔 WORST PERFORMING: {worst_corner} corners (Profit: {worst_profit:.1f}%)")
    
    cursor.close()

def check_overall_stats(conn):
    """Check overall performance stats"""
    print("\n📊 OVERALL PERFORMANCE")
    print("-" * 30)
    
    query = """
    SELECT 
        result,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM alerts), 1) as percentage
    FROM alerts 
    GROUP BY result
    ORDER BY count DESC
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    total_query = "SELECT COUNT(*) FROM alerts"
    cursor.execute(total_query)
    total_alerts = cursor.fetchone()[0]
    
    print(f"Total Alerts: {total_alerts}")
    print(f"{'Result':<10} {'Count':<8} {'Percentage':<12}")
    print("-" * 32)
    
    for result, count, percentage in results:
        print(f"{result:<10} {count:<8} {percentage:<12}%")
    
    cursor.close()

def check_recent_alerts(conn):
    """Check recent alert performance"""
    print("\n📅 RECENT ALERTS (Last 15)")
    print("-" * 50)
    
    query = """
    SELECT 
        corners_at_alert,
        result,
        teams,
        timestamp::date as alert_date
    FROM alerts 
    ORDER BY timestamp DESC 
    LIMIT 15
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Corners':<8} {'Result':<8} {'Match':<30} {'Date':<12}")
    print("-" * 60)
    
    wins = 0
    losses = 0
    refunds = 0
    
    for row in results:
        corners, result, teams, date = row
        # Truncate team names if too long
        teams_short = teams[:28] + ".." if len(teams) > 30 else teams
        print(f"{corners:<8} {result:<8} {teams_short:<30} {date}")
        
        if result == 'WIN':
            wins += 1
        elif result == 'LOSS':
            losses += 1
        elif result == 'REFUND':
            refunds += 1
    
    if len(results) > 0:
        recent_win_rate = (wins / len(results)) * 100
        print(f"\nRecent Performance: {recent_win_rate:.1f}% win rate")
        print(f"Breakdown: {wins} wins, {losses} losses, {refunds} refunds")
    
    cursor.close()

def check_minute_performance(conn):
    """Check performance by minute alert was sent"""
    print("\n⏰ PERFORMANCE BY MINUTE")
    print("-" * 40)
    
    query = """
    SELECT 
        CASE 
            WHEN minute_sent BETWEEN 30 AND 35 THEN 'First Half (30-35)'
            WHEN minute_sent BETWEEN 85 AND 89 THEN 'Late Game (85-89)'
            WHEN minute_sent >= 85 THEN 'Late Game (85+)'
            ELSE 'Other'
        END as time_period,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE minute_sent IS NOT NULL
    GROUP BY 
        CASE 
            WHEN minute_sent BETWEEN 30 AND 35 THEN 'First Half (30-35)'
            WHEN minute_sent BETWEEN 85 AND 89 THEN 'Late Game (85-89)'
            WHEN minute_sent >= 85 THEN 'Late Game (85+)'
            ELSE 'Other'
        END
    ORDER BY total DESC
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Time Period':<20} {'Total':<8} {'Wins':<6} {'Loss':<6} {'Win Rate':<10}")
    print("-" * 55)
    
    for row in results:
        time_period, total, wins, losses, win_rate = row
        print(f"{time_period:<20} {total:<8} {wins:<6} {losses:<6} {win_rate:<10}%")
    
    cursor.close()

def main():
    """Run simple results check"""
    print("🔍 SIMPLE RESULTS CHECK")
    print("=" * 50)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        check_overall_stats(conn)
        check_corner_performance(conn)
        check_minute_performance(conn)
        check_recent_alerts(conn)
        
        print("\n" + "=" * 50)
        print("✅ Analysis complete!")
        
        print("\n💡 QUICK INSIGHTS:")
        print("   • Check which corner counts have highest profit rates")
        print("   • Look at first half vs late game performance")
        print("   • Monitor recent trends for system effectiveness")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()