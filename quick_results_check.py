#!/usr/bin/env python3
"""
QUICK RESULTS CHECKER
====================
Simple script to quickly check which combos bring most wins vs losses.
Answers the key questions:
1. Which corner counts have most wins and least losses?
2. Which stat combinations are most profitable?
3. What patterns should we focus on vs avoid?
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
    print("-" * 40)
    
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
    print("-" * 65)
    
    best_corner = None
    best_profit = -100
    worst_corner = None
    worst_profit = 100
    
    for row in results:
        corner, total, wins, losses, refunds, win_rate, loss_rate = row
        profit = win_rate - loss_rate
        
        print(f"{corner:<8} {total:<8} {wins:<6} {losses:<6} {refunds:<8} {win_rate:<8}% {loss_rate:<8}% {profit:<8.1f}%")
        
        if total >= 5:  # Only consider corners with reasonable sample size
            if profit > best_profit:
                best_profit = profit
                best_corner = corner
            if profit < worst_profit:
                worst_profit = profit
                worst_corner = corner
    
    print(f"\n🏆 BEST: {best_corner} corners (Profit: {best_profit:.1f}%)")
    print(f"💔 WORST: {worst_corner} corners (Profit: {worst_profit:.1f}%)")
    
    cursor.close()

def check_elite_score_performance(conn):
    """Check performance by elite score ranges"""
    print("\n🎖️ ELITE SCORE PERFORMANCE")
    print("-" * 40)
    
    query = """
    SELECT 
        CASE 
            WHEN elite_score < 16 THEN '0-15.9'
            WHEN elite_score < 20 THEN '16-19.9'
            WHEN elite_score < 25 THEN '20-24.9'
            WHEN elite_score < 30 THEN '25-29.9'
            ELSE '30+'
        END as score_range,
        COUNT(*) as total,
        SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN actual_result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE elite_score IS NOT NULL
    GROUP BY 
        CASE 
            WHEN elite_score < 16 THEN '0-15.9'
            WHEN elite_score < 20 THEN '16-19.9'
            WHEN elite_score < 25 THEN '20-24.9'
            WHEN elite_score < 30 THEN '25-29.9'
            ELSE '30+'
        END
    ORDER BY win_rate DESC
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Score Range':<12} {'Total':<8} {'Wins':<6} {'Loss':<6} {'Win Rate':<10}")
    print("-" * 45)
    
    for row in results:
        score_range, total, wins, losses, win_rate = row
        print(f"{score_range:<12} {total:<8} {wins:<6} {losses:<6} {win_rate:<10}%")

def check_probability_thresholds(conn):
    """Check performance at different probability thresholds"""
    print("\n📊 PROBABILITY THRESHOLD PERFORMANCE")
    print("-" * 45)
    
    thresholds = [70, 75, 80, 85, 90, 95]
    
    print(f"{'Threshold':<12} {'Alerts':<8} {'Wins':<6} {'Loss':<6} {'Win Rate':<10}")
    print("-" * 45)
    
    cursor = conn.cursor()
    
    for threshold in thresholds:
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN actual_result = 'LOSS' THEN 1 ELSE 0 END) as losses,
            ROUND(SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
        FROM alerts 
        WHERE total_probability >= %s AND total_probability IS NOT NULL
        """
        
        cursor.execute(query, (threshold,))
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            total, wins, losses, win_rate = result
            print(f">={threshold}%{'':<7} {total:<8} {wins:<6} {losses:<6} {win_rate:<10}%")
    
    cursor.close()

def check_recent_performance(conn):
    """Check recent performance (last 10 alerts)"""
    print("\n📅 RECENT PERFORMANCE (Last 10 Alerts)")
    print("-" * 45)
    
    query = """
    SELECT 
        corners_at_alert,
        actual_result,
        elite_score,
        total_probability,
        created_at::date
    FROM alerts 
    ORDER BY created_at DESC 
    LIMIT 10
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Corners':<8} {'Result':<8} {'Score':<8} {'Prob%':<8} {'Date':<12}")
    print("-" * 50)
    
    wins = 0
    losses = 0
    
    for row in results:
        corners, result, score, prob, date = row
        print(f"{corners:<8} {result:<8} {score or 'N/A':<8} {prob or 'N/A':<8} {date}")
        
        if result == 'WIN':
            wins += 1
        elif result == 'LOSS':
            losses += 1
    
    if len(results) > 0:
        recent_win_rate = (wins / len(results)) * 100
        print(f"\nRecent Win Rate: {recent_win_rate:.1f}% ({wins} wins, {losses} losses)")
    
    cursor.close()

def main():
    """Run quick results check"""
    print("🔍 QUICK RESULTS CHECK")
    print("=" * 50)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        check_corner_performance(conn)
        check_elite_score_performance(conn)
        check_probability_thresholds(conn)
        check_recent_performance(conn)
        
        print("\n" + "=" * 50)
        print("✅ Quick analysis complete!")
        print("\n💡 KEY TAKEAWAYS:")
        print("   - Focus on corner counts with highest profit rates")
        print("   - Consider raising thresholds if higher ones show better win rates")
        print("   - Monitor recent performance trends")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()