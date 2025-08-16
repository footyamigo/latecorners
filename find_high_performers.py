#!/usr/bin/env python3
"""
FIND HIGH PERFORMERS
===================
Look for any combinations with >75% hit rate.
Check different groupings and filters.
"""

import os
import psycopg2

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

def connect_db():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        print("✅ Connected to database")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def check_high_win_rate_combos(conn):
    """Find any combinations with >75% win rate"""
    print("\n🎯 SEARCHING FOR >75% WIN RATE COMBINATIONS")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Check by corner count (minimum 5 alerts)
    print("\n📊 BY CORNER COUNT (min 5 alerts):")
    print("-" * 50)
    
    query = """
    SELECT 
        corners_at_alert,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE corners_at_alert IS NOT NULL
    GROUP BY corners_at_alert
    HAVING COUNT(*) >= 5
    ORDER BY win_rate DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    found_high_performer = False
    for corner, total, wins, win_rate in results:
        if win_rate >= 75:
            print(f"🏆 {corner} corners: {win_rate}% win rate ({wins}/{total})")
            found_high_performer = True
        else:
            print(f"   {corner} corners: {win_rate}% win rate ({wins}/{total})")
    
    if not found_high_performer:
        print("❌ No corner counts with >75% win rate found")
    
    # Check by score at alert
    print("\n📊 BY SCORE AT ALERT (min 3 alerts):")
    print("-" * 50)
    
    query = """
    SELECT 
        score_at_alert,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE score_at_alert IS NOT NULL
    GROUP BY score_at_alert
    HAVING COUNT(*) >= 3
    ORDER BY win_rate DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    found_high_performer = False
    for score, total, wins, win_rate in results:
        if win_rate >= 75:
            print(f"🏆 Score {score}: {win_rate}% win rate ({wins}/{total})")
            found_high_performer = True
        elif win_rate >= 60:  # Show promising ones too
            print(f"📈 Score {score}: {win_rate}% win rate ({wins}/{total})")
    
    if not found_high_performer:
        print("❌ No score combinations with >75% win rate found")
    
    # Check by minute sent
    print("\n📊 BY MINUTE SENT (min 3 alerts):")
    print("-" * 50)
    
    query = """
    SELECT 
        minute_sent,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE minute_sent IS NOT NULL
    GROUP BY minute_sent
    HAVING COUNT(*) >= 3
    ORDER BY win_rate DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    found_high_performer = False
    for minute, total, wins, win_rate in results[:10]:  # Top 10
        if win_rate >= 75:
            print(f"🏆 Minute {minute}: {win_rate}% win rate ({wins}/{total})")
            found_high_performer = True
        elif win_rate >= 60:
            print(f"📈 Minute {minute}: {win_rate}% win rate ({wins}/{total})")
    
    if not found_high_performer:
        print("❌ No minute combinations with >75% win rate found")
    
    cursor.close()

def check_combo_patterns(conn):
    """Check combinations of corner count + score"""
    print("\n🔍 COMBINATION PATTERNS (min 3 alerts):")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    query = """
    SELECT 
        corners_at_alert,
        score_at_alert,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE corners_at_alert IS NOT NULL AND score_at_alert IS NOT NULL
    GROUP BY corners_at_alert, score_at_alert
    HAVING COUNT(*) >= 3
    ORDER BY win_rate DESC, total DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Corners':<8} {'Score':<12} {'Total':<6} {'Wins':<6} {'Win Rate':<10}")
    print("-" * 50)
    
    found_high_performer = False
    for corner, score, total, wins, win_rate in results[:15]:  # Top 15
        if win_rate >= 75:
            print(f"🏆 {corner:<8} {score:<12} {total:<6} {wins:<6} {win_rate:<10}%")
            found_high_performer = True
        elif win_rate >= 60:
            print(f"📈 {corner:<8} {score:<12} {total:<6} {wins:<6} {win_rate:<10}%")
        else:
            print(f"   {corner:<8} {score:<12} {total:<6} {wins:<6} {win_rate:<10}%")
    
    if not found_high_performer:
        print("❌ No combination patterns with >75% win rate found")
    
    cursor.close()

def check_specific_scenarios(conn):
    """Check specific high-performing scenarios"""
    print("\n🎲 SPECIFIC SCENARIOS:")
    print("=" * 40)
    
    cursor = conn.cursor()
    
    scenarios = [
        ("Draw games (0-0, 1-1, 2-2)", "score_at_alert IN ('0-0', '1-1', '2-2')"),
        ("Low corner count (5-6)", "corners_at_alert IN (5, 6)"),
        ("Close games", "score_at_alert IN ('0-1', '1-0', '0-0', '1-1')"),
        ("Late game (87+ min)", "minute_sent >= 87"),
        ("Early corners (5-7)", "corners_at_alert BETWEEN 5 AND 7"),
    ]
    
    for scenario_name, condition in scenarios:
        query = f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
            ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
        FROM alerts 
        WHERE {condition}
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            total, wins, losses, win_rate = result
            if win_rate >= 75:
                print(f"🏆 {scenario_name}: {win_rate}% ({wins}/{total})")
            elif win_rate >= 60:
                print(f"📈 {scenario_name}: {win_rate}% ({wins}/{total})")
            else:
                print(f"   {scenario_name}: {win_rate}% ({wins}/{total})")
    
    cursor.close()

def find_best_individual_matches(conn):
    """Find individual matches that performed well to see patterns"""
    print("\n🏅 TOP PERFORMING INDIVIDUAL PATTERNS:")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Get all winning alerts to see patterns
    query = """
    SELECT 
        corners_at_alert,
        score_at_alert,
        minute_sent,
        teams,
        result
    FROM alerts 
    WHERE result = 'WIN'
    ORDER BY corners_at_alert, score_at_alert
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Count patterns
    corner_score_patterns = {}
    minute_patterns = {}
    
    for corner, score, minute, teams, result in results:
        pattern = f"{corner} corners, {score}"
        corner_score_patterns[pattern] = corner_score_patterns.get(pattern, 0) + 1
        
        minute_range = f"{minute//5*5}-{minute//5*5+4}" if minute else "Unknown"
        minute_patterns[minute_range] = minute_patterns.get(minute_range, 0) + 1
    
    print("Most common WINNING patterns:")
    print("-" * 40)
    
    # Sort by frequency
    sorted_patterns = sorted(corner_score_patterns.items(), key=lambda x: x[1], reverse=True)
    
    for pattern, count in sorted_patterns[:10]:
        if count >= 3:
            print(f"🎯 {pattern}: {count} wins")
    
    print(f"\nWinning alerts by minute range:")
    print("-" * 30)
    
    sorted_minutes = sorted(minute_patterns.items(), key=lambda x: x[1], reverse=True)
    for minute_range, count in sorted_minutes[:8]:
        print(f"   {minute_range} min: {count} wins")
    
    cursor.close()

def main():
    print("🔍 SEARCHING FOR >75% WIN RATE COMBINATIONS")
    print("=" * 60)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        check_high_win_rate_combos(conn)
        check_combo_patterns(conn)
        check_specific_scenarios(conn)
        find_best_individual_matches(conn)
        
        print("\n" + "=" * 60)
        print("🎯 SUMMARY:")
        print("   If no combinations show >75% win rate,")
        print("   focus on improving the patterns that are 60%+")
        print("   and avoiding the clearly losing patterns.")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()