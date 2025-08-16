#!/usr/bin/env python3
"""
MOMENTUM THRESHOLD ANALYSIS
==========================
Find optimal momentum thresholds for highest win rates.
Analyze combined_momentum10, momentum_home_total, and momentum_away_total.
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

def analyze_combined_momentum_thresholds(conn):
    """Test different combined momentum thresholds"""
    print("\n🎯 COMBINED MOMENTUM THRESHOLD ANALYSIS")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Test various thresholds
    thresholds = [100, 120, 130, 140, 150, 160, 170, 180, 200, 220, 250]
    
    print(f"{'Threshold':<12} {'Total':<8} {'Wins':<6} {'Loss':<6} {'Win%':<8} {'Sample':<8}")
    print("-" * 55)
    
    best_threshold = None
    best_win_rate = 0
    best_volume = 0
    
    for threshold in thresholds:
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
            CASE WHEN COUNT(*) > 0 
                THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                ELSE 0 
            END as win_rate
        FROM alerts 
        WHERE combined_momentum10 >= %s AND combined_momentum10 IS NOT NULL
        """, (threshold,))
        
        result = cursor.fetchone()
        if result:
            total, wins, losses, win_rate = result
            
            # Mark good combinations
            marker = ""
            if total >= 10 and win_rate >= 40:
                marker = "🎯"  # Good volume + performance
            elif total >= 20 and win_rate >= 35:
                marker = "📈"  # Decent volume + performance
            elif win_rate >= 50 and total >= 5:
                marker = "💎"  # High performance
            
            print(f"{marker} >={threshold:<10} {total:<8} {wins:<6} {losses:<6} {win_rate:<8.1f}% {'Good' if total>=10 else 'Low'}")
            
            # Track best performing threshold with decent volume
            if total >= 10 and win_rate > best_win_rate:
                best_win_rate = win_rate
                best_threshold = threshold
                best_volume = total
    
    if best_threshold:
        print(f"\n🏆 BEST COMBINED MOMENTUM THRESHOLD: >={best_threshold}")
        print(f"   Win Rate: {best_win_rate:.1f}%")
        print(f"   Volume: {best_volume} alerts")
    
    cursor.close()

def analyze_individual_momentum_thresholds(conn):
    """Analyze home and away momentum separately"""
    print("\n🏠 HOME vs AWAY MOMENTUM ANALYSIS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Test home momentum thresholds
    print("\n🏠 HOME MOMENTUM THRESHOLDS:")
    print("-" * 40)
    
    thresholds = [30, 40, 50, 60, 70, 80, 90, 100, 120, 150]
    
    print(f"{'Threshold':<12} {'Total':<8} {'Wins':<6} {'Win%':<8}")
    print("-" * 35)
    
    for threshold in thresholds:
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
            CASE WHEN COUNT(*) > 0 
                THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                ELSE 0 
            END as win_rate
        FROM alerts 
        WHERE momentum_home_total >= %s AND momentum_home_total IS NOT NULL
        """, (threshold,))
        
        result = cursor.fetchone()
        if result:
            total, wins, win_rate = result
            
            marker = "🎯" if total >= 10 and win_rate >= 40 else "📈" if total >= 15 and win_rate >= 35 else ""
            print(f"{marker} >={threshold:<10} {total:<8} {wins:<6} {win_rate:<8.1f}%")
    
    # Test away momentum thresholds
    print("\n✈️ AWAY MOMENTUM THRESHOLDS:")
    print("-" * 40)
    
    print(f"{'Threshold':<12} {'Total':<8} {'Wins':<6} {'Win%':<8}")
    print("-" * 35)
    
    for threshold in thresholds:
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
            CASE WHEN COUNT(*) > 0 
                THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                ELSE 0 
            END as win_rate
        FROM alerts 
        WHERE momentum_away_total >= %s AND momentum_away_total IS NOT NULL
        """, (threshold,))
        
        result = cursor.fetchone()
        if result:
            total, wins, win_rate = result
            
            marker = "🎯" if total >= 10 and win_rate >= 40 else "📈" if total >= 15 and win_rate >= 35 else ""
            print(f"{marker} >={threshold:<10} {total:<8} {wins:<6} {win_rate:<8.1f}%")
    
    cursor.close()

def analyze_momentum_ranges(conn):
    """Analyze specific momentum ranges"""
    print("\n📊 MOMENTUM RANGE ANALYSIS")
    print("=" * 40)
    
    cursor = conn.cursor()
    
    # Combined momentum ranges
    print("\n🎯 COMBINED MOMENTUM RANGES:")
    print("-" * 35)
    
    cursor.execute("""
    SELECT 
        CASE 
            WHEN combined_momentum10 >= 200 THEN '200+'
            WHEN combined_momentum10 >= 180 THEN '180-199'
            WHEN combined_momentum10 >= 160 THEN '160-179'
            WHEN combined_momentum10 >= 140 THEN '140-159'
            WHEN combined_momentum10 >= 120 THEN '120-139'
            WHEN combined_momentum10 >= 100 THEN '100-119'
            ELSE '<100'
        END as range_label,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        CASE WHEN COUNT(*) > 0 
            THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
            ELSE 0 
        END as win_rate
    FROM alerts 
    WHERE combined_momentum10 IS NOT NULL
    GROUP BY 
        CASE 
            WHEN combined_momentum10 >= 200 THEN '200+'
            WHEN combined_momentum10 >= 180 THEN '180-199'
            WHEN combined_momentum10 >= 160 THEN '160-179'
            WHEN combined_momentum10 >= 140 THEN '140-159'
            WHEN combined_momentum10 >= 120 THEN '120-139'
            WHEN combined_momentum10 >= 100 THEN '100-119'
            ELSE '<100'
        END
    ORDER BY win_rate DESC
    """)
    
    range_results = cursor.fetchall()
    
    print(f"{'Range':<12} {'Total':<8} {'Wins':<6} {'Win%':<8}")
    print("-" * 35)
    
    for range_label, total, wins, win_rate in range_results:
        marker = "🎯" if total >= 5 and win_rate >= 40 else "📈" if total >= 10 and win_rate >= 35 else ""
        print(f"{marker} {range_label:<12} {total:<8} {wins:<6} {win_rate:<8.1f}%")
    
    cursor.close()

def find_optimal_momentum_combinations(conn):
    """Find optimal combinations of momentum factors"""
    print("\n🔄 OPTIMAL MOMENTUM COMBINATIONS")
    print("=" * 45)
    
    cursor = conn.cursor()
    
    # Test combinations of high momentum
    combinations = [
        ("High Combined (160+)", "combined_momentum10 >= 160"),
        ("High Home (80+)", "momentum_home_total >= 80"),
        ("High Away (80+)", "momentum_away_total >= 80"),
        ("High Combined + High Home", "combined_momentum10 >= 160 AND momentum_home_total >= 80"),
        ("High Combined + High Away", "combined_momentum10 >= 160 AND momentum_away_total >= 80"),
        ("High Home + High Away", "momentum_home_total >= 80 AND momentum_away_total >= 80"),
        ("Balanced High (Combined 140+, Home 60+, Away 60+)", 
         "combined_momentum10 >= 140 AND momentum_home_total >= 60 AND momentum_away_total >= 60"),
    ]
    
    print(f"{'Combination':<35} {'Total':<8} {'Wins':<6} {'Win%':<8}")
    print("-" * 60)
    
    best_combo = None
    best_combo_rate = 0
    best_combo_volume = 0
    
    for combo_name, condition in combinations:
        cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
            CASE WHEN COUNT(*) > 0 
                THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                ELSE 0 
            END as win_rate
        FROM alerts 
        WHERE {condition}
        """)
        
        result = cursor.fetchone()
        if result:
            total, wins, win_rate = result
            
            marker = ""
            if total >= 5 and win_rate >= 45:
                marker = "🎯"
            elif total >= 10 and win_rate >= 40:
                marker = "📈"
            elif win_rate >= 50:
                marker = "💎"
            
            # Truncate combo name if too long
            combo_display = combo_name[:33] + ".." if len(combo_name) > 35 else combo_name
            print(f"{marker} {combo_display:<35} {total:<8} {wins:<6} {win_rate:<8.1f}%")
            
            # Track best with decent volume
            if total >= 5 and win_rate > best_combo_rate:
                best_combo_rate = win_rate
                best_combo = combo_name
                best_combo_volume = total
    
    if best_combo:
        print(f"\n🏆 BEST MOMENTUM COMBINATION:")
        print(f"   {best_combo}")
        print(f"   Win Rate: {best_combo_rate:.1f}%")
        print(f"   Volume: {best_combo_volume} alerts")
    
    cursor.close()

def generate_momentum_recommendations(conn):
    """Generate final momentum-based recommendations"""
    print("\n💡 MOMENTUM THRESHOLD RECOMMENDATIONS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Get current performance
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE result = 'WIN'")
    total_wins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cursor.fetchone()[0]
    
    current_win_rate = (total_wins / total_alerts * 100) if total_alerts > 0 else 0
    
    print(f"📊 CURRENT PERFORMANCE: {current_win_rate:.1f}% win rate ({total_alerts} alerts)")
    
    # Find best performing threshold with reasonable volume
    cursor.execute("""
    SELECT 
        'combined_160' as threshold_type,
        COUNT(*) as volume,
        CASE WHEN COUNT(*) > 0 
            THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
            ELSE 0 
        END as win_rate
    FROM alerts 
    WHERE combined_momentum10 >= 160
    
    UNION ALL
    
    SELECT 
        'combined_140' as threshold_type,
        COUNT(*) as volume,
        CASE WHEN COUNT(*) > 0 
            THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
            ELSE 0 
        END as win_rate
    FROM alerts 
    WHERE combined_momentum10 >= 140
    
    UNION ALL
    
    SELECT 
        'combined_180' as threshold_type,
        COUNT(*) as volume,
        CASE WHEN COUNT(*) > 0 
            THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
            ELSE 0 
        END as win_rate
    FROM alerts 
    WHERE combined_momentum10 >= 180
    
    ORDER BY win_rate DESC
    """)
    
    threshold_results = cursor.fetchall()
    
    print(f"\n🎯 TOP MOMENTUM THRESHOLDS:")
    for threshold_type, volume, win_rate in threshold_results:
        if volume >= 5:  # Only show meaningful sample sizes
            improvement = win_rate - current_win_rate
            print(f"   {threshold_type}: {win_rate:.1f}% win rate ({volume} alerts, +{improvement:.1f}% improvement)")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. Test raising combined momentum threshold to 160+ for better quality")
    print(f"   2. Consider individual home/away momentum filters")
    print(f"   3. Combine momentum filters with corner count filters (5-6 corners)")
    print(f"   4. Monitor volume vs quality trade-offs")
    
    cursor.close()

def main():
    print("🎯 MOMENTUM THRESHOLD ANALYSIS")
    print("=" * 50)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        analyze_combined_momentum_thresholds(conn)
        analyze_individual_momentum_thresholds(conn)
        analyze_momentum_ranges(conn)
        find_optimal_momentum_combinations(conn)
        generate_momentum_recommendations(conn)
        
        print("\n" + "=" * 50)
        print("🎯 SUMMARY:")
        print("   Use momentum thresholds to filter for higher quality alerts")
        print("   Balance volume reduction with win rate improvement")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()