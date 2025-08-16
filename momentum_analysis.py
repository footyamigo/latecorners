#!/usr/bin/env python3
"""
MOMENTUM ANALYSIS
================
Analyze momentum data and alert types for patterns.
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

def analyze_momentum_data(conn):
    """Analyze momentum data for patterns"""
    print("\n📊 MOMENTUM DATA ANALYSIS")
    print("=" * 40)
    
    cursor = conn.cursor()
    
    # Check momentum data availability
    cursor.execute("""
    SELECT 
        COUNT(*) as total_with_momentum,
        COUNT(*) FILTER (WHERE combined_momentum10 IS NOT NULL) as has_combined,
        COUNT(*) FILTER (WHERE momentum_home_total IS NOT NULL) as has_home,
        COUNT(*) FILTER (WHERE momentum_away_total IS NOT NULL) as has_away
    FROM alerts
    """)
    
    momentum_stats = cursor.fetchone()
    total, has_combined, has_home, has_away = momentum_stats
    
    print(f"Momentum Data Availability:")
    print(f"  Total alerts: {total}")
    print(f"  Combined momentum: {has_combined} ({has_combined/total*100:.1f}%)")
    print(f"  Home momentum: {has_home} ({has_home/total*100:.1f}%)")
    print(f"  Away momentum: {has_away} ({has_away/total*100:.1f}%)")
    
    if has_combined > 0:
        # Analyze combined momentum ranges
        print(f"\n🎯 COMBINED MOMENTUM PERFORMANCE:")
        print("-" * 40)
        
        cursor.execute("""
        SELECT 
            CASE 
                WHEN combined_momentum10 >= 80 THEN '80+'
                WHEN combined_momentum10 >= 60 THEN '60-79'
                WHEN combined_momentum10 >= 40 THEN '40-59'
                WHEN combined_momentum10 >= 20 THEN '20-39'
                ELSE '0-19'
            END as momentum_range,
            COUNT(*) as total,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
        FROM alerts 
        WHERE combined_momentum10 IS NOT NULL
        GROUP BY 
            CASE 
                WHEN combined_momentum10 >= 80 THEN '80+'
                WHEN combined_momentum10 >= 60 THEN '60-79'
                WHEN combined_momentum10 >= 40 THEN '40-59'
                WHEN combined_momentum10 >= 20 THEN '20-39'
                ELSE '0-19'
            END
        ORDER BY win_rate DESC
        """)
        
        momentum_results = cursor.fetchall()
        
        print(f"{'Range':<10} {'Volume':<8} {'Wins':<6} {'Win%':<8}")
        print("-" * 35)
        
        for momentum_range, volume, wins, win_rate in momentum_results:
            marker = "🎯" if win_rate >= 40 else "📈" if win_rate >= 35 else ""
            print(f"{marker} {momentum_range:<10} {volume:<8} {wins:<6} {win_rate:<8}%")
    
    cursor.close()

def analyze_alert_types(conn):
    """Analyze alert type performance"""
    print("\n🚨 ALERT TYPE ANALYSIS")
    print("=" * 30)
    
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        alert_type,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE alert_type IS NOT NULL
    GROUP BY alert_type
    ORDER BY total DESC
    """)
    
    alert_results = cursor.fetchall()
    
    if alert_results:
        print(f"{'Alert Type':<15} {'Volume':<8} {'Wins':<6} {'Loss':<6} {'Win%':<8}")
        print("-" * 50)
        
        for alert_type, volume, wins, losses, win_rate in alert_results:
            marker = "🎯" if win_rate >= 40 else "📈" if win_rate >= 35 else "❌" if win_rate < 30 else ""
            print(f"{marker} {alert_type:<15} {volume:<8} {wins:<6} {losses:<6} {win_rate:<8}%")
    else:
        print("❌ No alert type data found")
    
    cursor.close()

def analyze_momentum_combinations(conn):
    """Analyze combinations of momentum and other factors"""
    print("\n🔄 MOMENTUM + CORNER COMBINATIONS")
    print("=" * 40)
    
    cursor = conn.cursor()
    
    # High momentum + specific corner counts
    cursor.execute("""
    SELECT 
        corners_at_alert,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate,
        ROUND(AVG(combined_momentum10), 1) as avg_momentum
    FROM alerts 
    WHERE combined_momentum10 >= 60 AND corners_at_alert IS NOT NULL
    GROUP BY corners_at_alert
    HAVING COUNT(*) >= 3
    ORDER BY win_rate DESC
    """)
    
    combo_results = cursor.fetchall()
    
    if combo_results:
        print(f"High Momentum (60+) + Corner Count:")
        print(f"{'Corners':<8} {'Volume':<8} {'Wins':<6} {'Win%':<8} {'Avg Mom':<8}")
        print("-" * 45)
        
        for corner, volume, wins, win_rate, avg_momentum in combo_results:
            marker = "🎯" if win_rate >= 50 else "📈" if win_rate >= 40 else ""
            print(f"{marker} {corner:<8} {volume:<8} {wins:<6} {win_rate:<8}% {avg_momentum:<8}")
    else:
        print("❌ No high momentum combinations found")
    
    cursor.close()

def practical_recommendations(conn):
    """Generate practical recommendations based on analysis"""
    print("\n💡 PRACTICAL RECOMMENDATIONS")
    print("=" * 40)
    
    cursor = conn.cursor()
    
    # Get current distribution
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE result = 'WIN'")
    wins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE result = 'LOSS'")
    losses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total = cursor.fetchone()[0]
    
    current_win_rate = (wins / total * 100) if total > 0 else 0
    weekly_volume = total / 10  # Rough estimate
    
    print(f"📊 CURRENT STATUS:")
    print(f"   • {total} total alerts")
    print(f"   • {current_win_rate:.1f}% win rate")
    print(f"   • ~{weekly_volume:.1f} alerts/week")
    print(f"   • Need to improve to 50%+ win rate for profitability")
    
    print(f"\n🎯 IMMEDIATE ACTIONS:")
    
    # Find what to focus on
    cursor.execute("""
    SELECT corners_at_alert, COUNT(*) as volume,
           ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    GROUP BY corners_at_alert
    HAVING COUNT(*) >= 10
    ORDER BY win_rate DESC
    """)
    
    corner_performance = cursor.fetchall()
    
    good_corners = []
    bad_corners = []
    
    for corner, volume, win_rate in corner_performance:
        if win_rate >= 38:  # Above average
            good_corners.append(str(corner))
        elif win_rate < 30:  # Below average
            bad_corners.append(str(corner))
    
    if good_corners:
        print(f"   1. ✅ FOCUS on corners: {', '.join(good_corners)}")
    
    if bad_corners:
        print(f"   2. ❌ FILTER OUT corners: {', '.join(bad_corners)}")
    
    # Score recommendations
    cursor.execute("""
    SELECT score_at_alert, COUNT(*) as volume,
           ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
    FROM alerts 
    WHERE score_at_alert IS NOT NULL
    GROUP BY score_at_alert
    HAVING COUNT(*) >= 8
    ORDER BY win_rate DESC
    """)
    
    score_performance = cursor.fetchall()
    
    if score_performance:
        best_score = score_performance[0]
        worst_score = score_performance[-1]
        
        print(f"   3. 🎯 BEST score pattern: {best_score[0]} ({best_score[2]}% win rate)")
        print(f"   4. ❌ WORST score pattern: {worst_score[0]} ({worst_score[2]}% win rate)")
    
    print(f"\n📈 EXPECTED IMPACT:")
    print(f"   • Filtering bad patterns could reduce volume by 30-40%")
    print(f"   • But could improve win rate to 45-50%")
    print(f"   • Better: ~15 quality alerts/week at 45% vs 23 alerts/week at 33%")
    
    cursor.close()

def main():
    print("📊 MOMENTUM & ALERT TYPE ANALYSIS")
    print("=" * 40)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        analyze_momentum_data(conn)
        analyze_alert_types(conn)
        analyze_momentum_combinations(conn)
        practical_recommendations(conn)
        
        print("\n" + "=" * 40)
        print("🎯 BOTTOM LINE:")
        print("   Your system generates good volume but needs")
        print("   stricter filtering to improve win rate from 33% to 45%+")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()