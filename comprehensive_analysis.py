#!/usr/bin/env python3
"""
COMPREHENSIVE ANALYSIS
=====================
Deep dive into momentum, alert types, and practical adjustments.
Focus on patterns that generate enough volume while maintaining profitability.
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

def check_available_columns(conn):
    """Check what momentum/alert type columns are available"""
    print("\n🔍 CHECKING AVAILABLE COLUMNS")
    print("-" * 40)
    
    cursor = conn.cursor()
    cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'alerts'
    AND column_name LIKE '%momentum%' OR column_name LIKE '%alert%' OR column_name LIKE '%probability%'
    ORDER BY column_name
    """)
    
    momentum_cols = cursor.fetchall()
    
    if momentum_cols:
        print("Available momentum/alert columns:")
        for col_name, data_type in momentum_cols:
            print(f"  {col_name} ({data_type})")
    else:
        print("❌ No momentum/alert type columns found")
    
    # Check sample data for any new columns
    cursor.execute("SELECT * FROM alerts LIMIT 1")
    sample = cursor.fetchone()
    
    cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'alerts'
    ORDER BY ordinal_position
    """)
    all_cols = [row[0] for row in cursor.fetchall()]
    
    print(f"\nAll available columns ({len(all_cols)}):")
    print(all_cols)
    
    cursor.close()
    return all_cols

def analyze_volume_vs_performance(conn):
    """Find combinations with good volume AND performance"""
    print("\n📊 VOLUME vs PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Corner count analysis with volume consideration
    query = """
    SELECT 
        corners_at_alert,
        COUNT(*) as total_alerts,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate,
        ROUND(SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as loss_rate,
        ROUND((SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) - SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END)) * 100.0 / COUNT(*), 1) as net_profit
    FROM alerts 
    WHERE corners_at_alert IS NOT NULL
    GROUP BY corners_at_alert
    ORDER BY total_alerts DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Corner':<8} {'Volume':<8} {'Wins':<6} {'Loss':<6} {'Win%':<8} {'Loss%':<8} {'Net%':<8} {'Weekly Est.':<12}")
    print("-" * 80)
    
    total_alerts = sum(row[1] for row in results)
    weeks_estimated = 229 / 52  # Assuming 229 alerts over some period
    
    for corner, volume, wins, losses, win_rate, loss_rate, net_profit in results:
        weekly_est = volume / weeks_estimated if weeks_estimated > 0 else volume / 10  # Rough estimate
        
        # Highlight good volume + positive performance
        marker = ""
        if volume >= 15 and net_profit > 0:
            marker = "🎯"  # Good volume + profitable
        elif volume >= 20:
            marker = "📈"  # High volume
        elif net_profit > 10:
            marker = "💰"  # Very profitable but low volume
        
        print(f"{marker} {corner:<8} {volume:<8} {wins:<6} {losses:<6} {win_rate:<8}% {loss_rate:<8}% {net_profit:<8}% {weekly_est:<12.1f}")
    
    cursor.close()

def analyze_score_patterns_with_volume(conn):
    """Analyze score patterns considering volume"""
    print("\n🎯 SCORE PATTERNS (Volume + Performance)")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    query = """
    SELECT 
        score_at_alert,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE score_at_alert IS NOT NULL
    GROUP BY score_at_alert
    HAVING COUNT(*) >= 5  -- Only patterns with decent volume
    ORDER BY COUNT(*) DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Score':<10} {'Volume':<8} {'Wins':<6} {'Win%':<8} {'Assessment':<20}")
    print("-" * 60)
    
    for score, volume, wins, win_rate in results:
        assessment = ""
        if win_rate >= 50 and volume >= 10:
            assessment = "🎯 FOCUS ON THIS"
        elif win_rate >= 40 and volume >= 15:
            assessment = "📈 GOOD VOLUME"
        elif win_rate < 30:
            assessment = "❌ AVOID"
        else:
            assessment = "⚖️ NEUTRAL"
        
        print(f"{score:<10} {volume:<8} {wins:<6} {win_rate:<8}% {assessment:<20}")
    
    cursor.close()

def analyze_time_patterns(conn):
    """Analyze performance by time periods"""
    print("\n⏰ TIME PATTERN ANALYSIS")
    print("=" * 40)
    
    cursor = conn.cursor()
    
    # Analyze by 5-minute windows
    query = """
    SELECT 
        CASE 
            WHEN minute_sent BETWEEN 30 AND 35 THEN 'FH: 30-35 min'
            WHEN minute_sent BETWEEN 85 AND 89 THEN 'LG: 85-89 min'
            WHEN minute_sent BETWEEN 80 AND 84 THEN 'LG: 80-84 min'
            WHEN minute_sent >= 90 THEN 'LG: 90+ min'
            ELSE 'Other'
        END as time_window,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE minute_sent IS NOT NULL
    GROUP BY 
        CASE 
            WHEN minute_sent BETWEEN 30 AND 35 THEN 'FH: 30-35 min'
            WHEN minute_sent BETWEEN 85 AND 89 THEN 'LG: 85-89 min'
            WHEN minute_sent BETWEEN 80 AND 84 THEN 'LG: 80-84 min'
            WHEN minute_sent >= 90 THEN 'LG: 90+ min'
            ELSE 'Other'
        END
    ORDER BY total DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'Time Window':<15} {'Volume':<8} {'Wins':<6} {'Win%':<8}")
    print("-" * 40)
    
    for time_window, volume, wins, win_rate in results:
        print(f"{time_window:<15} {volume:<8} {wins:<6} {win_rate:<8}%")
    
    cursor.close()

def find_practical_improvements(conn):
    """Find practical adjustments to improve the system"""
    print("\n💡 PRACTICAL IMPROVEMENT SUGGESTIONS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Find what's dragging down performance
    print("\n🔍 LOSS ANALYSIS - What's causing losses?")
    print("-" * 40)
    
    query = """
    SELECT 
        corners_at_alert,
        score_at_alert,
        COUNT(*) as loss_count
    FROM alerts 
    WHERE result = 'LOSS'
    GROUP BY corners_at_alert, score_at_alert
    HAVING COUNT(*) >= 2
    ORDER BY COUNT(*) DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("Most common LOSING patterns:")
    for corner, score, loss_count in results:
        print(f"❌ {corner} corners, {score} score: {loss_count} losses")
    
    # Find win patterns with good volume
    print("\n✅ WIN PATTERNS WITH VOLUME:")
    print("-" * 30)
    
    query = """
    SELECT 
        corners_at_alert,
        score_at_alert,
        COUNT(*) as win_count
    FROM alerts 
    WHERE result = 'WIN'
    GROUP BY corners_at_alert, score_at_alert
    HAVING COUNT(*) >= 2
    ORDER BY COUNT(*) DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    for corner, score, win_count in results:
        print(f"✅ {corner} corners, {score} score: {win_count} wins")
    
    cursor.close()

def suggest_system_adjustments(conn):
    """Suggest specific system adjustments"""
    print("\n🎯 RECOMMENDED SYSTEM ADJUSTMENTS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Calculate current performance
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE result = 'WIN'")
    total_wins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE result = 'LOSS'")
    total_losses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cursor.fetchone()[0]
    
    current_win_rate = (total_wins / total_alerts * 100) if total_alerts > 0 else 0
    
    print(f"📊 CURRENT PERFORMANCE:")
    print(f"   Win Rate: {current_win_rate:.1f}%")
    print(f"   Total Volume: {total_alerts} alerts")
    print(f"   Weekly Volume: ~{total_alerts/10:.1f} alerts/week (estimated)")
    
    print(f"\n💡 SPECIFIC RECOMMENDATIONS:")
    
    # 1. Corner count filtering
    cursor.execute("""
    SELECT corners_at_alert, 
           COUNT(*) as volume,
           ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    GROUP BY corners_at_alert
    HAVING COUNT(*) >= 10
    ORDER BY win_rate DESC
    """)
    
    good_corners = cursor.fetchall()
    
    profitable_corners = [str(corner) for corner, volume, win_rate in good_corners if win_rate > 35]
    losing_corners = [str(corner) for corner, volume, win_rate in good_corners if win_rate < 30]
    
    if profitable_corners:
        print(f"   1. 🎯 FOCUS on corner counts: {', '.join(profitable_corners)}")
    
    if losing_corners:
        print(f"   2. ❌ AVOID corner counts: {', '.join(losing_corners)}")
    
    # 2. Score filtering
    cursor.execute("""
    SELECT score_at_alert,
           COUNT(*) as volume,
           ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE score_at_alert IS NOT NULL
    GROUP BY score_at_alert
    HAVING COUNT(*) >= 5
    ORDER BY win_rate DESC
    """)
    
    score_results = cursor.fetchall()
    
    good_scores = [score for score, volume, win_rate in score_results if win_rate >= 40]
    bad_scores = [score for score, volume, win_rate in score_results if win_rate < 30]
    
    if good_scores:
        print(f"   3. 🎯 PRIORITIZE scores: {', '.join(good_scores[:5])}")
    
    if bad_scores:
        print(f"   4. ❌ AVOID scores: {', '.join(bad_scores[:3])}")
    
    # Volume recommendations
    print(f"\n📈 VOLUME vs QUALITY BALANCE:")
    print(f"   • Current: {total_alerts} alerts, {current_win_rate:.1f}% win rate")
    
    # If we filtered to only good patterns, what would volume be?
    if profitable_corners:
        filter_condition = f"corners_at_alert IN ({','.join(profitable_corners)})"
        if good_scores:
            score_list = ','.join([f"'{s}'" for s in good_scores[:3]])
            filter_condition += f" AND score_at_alert IN ({score_list})"
        
        cursor.execute(f"""
        SELECT COUNT(*) as filtered_volume,
               ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as filtered_win_rate
        FROM alerts 
        WHERE {filter_condition}
        """)
        
        filtered_result = cursor.fetchone()
        if filtered_result:
            filtered_volume, filtered_win_rate = filtered_result
            print(f"   • With filters: ~{filtered_volume} alerts, {filtered_win_rate:.1f}% win rate")
            print(f"   • Trade-off: {((filtered_volume/total_alerts)*100):.1f}% volume for {(filtered_win_rate-current_win_rate):.1f}% better win rate")
    
    cursor.close()

def main():
    print("🔍 COMPREHENSIVE ANALYSIS FOR SYSTEM OPTIMIZATION")
    print("=" * 60)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        available_cols = check_available_columns(conn)
        analyze_volume_vs_performance(conn)
        analyze_score_patterns_with_volume(conn)
        analyze_time_patterns(conn)
        find_practical_improvements(conn)
        suggest_system_adjustments(conn)
        
        print("\n" + "=" * 60)
        print("🎯 KEY TAKEAWAY:")
        print("   Focus on patterns with BOTH decent volume (10+ alerts)")
        print("   AND positive performance (40%+ win rate)")
        print("   Small high-win-rate patterns aren't sustainable!")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()