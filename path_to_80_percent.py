#!/usr/bin/env python3
"""
PATH TO 80% WIN RATE
===================
Analyze what combinations and filters would be needed to achieve 80% hit rate.
Look for ultra-high-performing patterns and system improvements.
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

def find_80_percent_patterns(conn):
    """Find any existing patterns with 80%+ win rate"""
    print("\n🎯 SEARCHING FOR 80%+ WIN RATE PATTERNS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Check ultra-specific combinations
    patterns_to_check = [
        ("Corner + Score + Momentum", """
            SELECT corners_at_alert, score_at_alert, 
                   CASE WHEN combined_momentum10 >= 180 THEN '180+' ELSE '<180' END as momentum_level,
                   COUNT(*) as total,
                   SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                   CASE WHEN COUNT(*) > 0 
                       THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                       ELSE 0 
                   END as win_rate
            FROM alerts 
            GROUP BY corners_at_alert, score_at_alert, 
                     CASE WHEN combined_momentum10 >= 180 THEN '180+' ELSE '<180' END
            HAVING COUNT(*) >= 2
            ORDER BY win_rate DESC
        """),
        
        ("Alert Type + Corner + Score", """
            SELECT alert_type, corners_at_alert, score_at_alert,
                   COUNT(*) as total,
                   SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                   CASE WHEN COUNT(*) > 0 
                       THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                       ELSE 0 
                   END as win_rate
            FROM alerts 
            WHERE alert_type IS NOT NULL
            GROUP BY alert_type, corners_at_alert, score_at_alert
            HAVING COUNT(*) >= 2
            ORDER BY win_rate DESC
        """),
        
        ("Extreme Momentum + Corners", """
            SELECT corners_at_alert,
                   CASE 
                       WHEN combined_momentum10 >= 200 THEN '200+'
                       WHEN combined_momentum10 >= 180 THEN '180-199'
                       ELSE '<180'
                   END as momentum_level,
                   COUNT(*) as total,
                   SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                   CASE WHEN COUNT(*) > 0 
                       THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                       ELSE 0 
                   END as win_rate
            FROM alerts 
            GROUP BY corners_at_alert, 
                     CASE 
                         WHEN combined_momentum10 >= 200 THEN '200+'
                         WHEN combined_momentum10 >= 180 THEN '180-199'
                         ELSE '<180'
                     END
            HAVING COUNT(*) >= 2
            ORDER BY win_rate DESC
        """),
    ]
    
    found_80_plus = False
    
    for pattern_name, query in patterns_to_check:
        print(f"\n📊 {pattern_name.upper()}:")
        print("-" * 40)
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        pattern_found = False
        for row in results[:10]:  # Top 10 results
            *pattern_details, total, wins, win_rate = row
            
            if win_rate >= 80:
                print(f"🎯 {' | '.join(map(str, pattern_details))}: {win_rate:.1f}% ({wins}/{total})")
                found_80_plus = True
                pattern_found = True
            elif win_rate >= 60:
                print(f"📈 {' | '.join(map(str, pattern_details))}: {win_rate:.1f}% ({wins}/{total})")
                pattern_found = True
        
        if not pattern_found:
            print("❌ No high-performing patterns found")
    
    if not found_80_plus:
        print(f"\n💡 NO EXISTING 80%+ PATTERNS FOUND")
        print(f"   Need to implement new filtering strategies!")
    
    cursor.close()

def analyze_winning_streaks(conn):
    """Analyze consecutive wins to understand what works"""
    print("\n🔥 WINNING STREAK ANALYSIS")
    print("=" * 35)
    
    cursor = conn.cursor()
    
    # Get all wins with their context
    cursor.execute("""
    SELECT id, corners_at_alert, score_at_alert, combined_momentum10, 
           momentum_home_total, momentum_away_total, alert_type,
           timestamp
    FROM alerts 
    WHERE result = 'WIN'
    ORDER BY timestamp
    """)
    
    wins = cursor.fetchall()
    
    print(f"📊 WINNING ALERTS BREAKDOWN ({len(wins)} total wins):")
    print("-" * 50)
    
    # Analyze patterns in wins
    corner_wins = {}
    score_wins = {}
    momentum_wins = {}
    alert_type_wins = {}
    
    for win in wins:
        corner = win[1]
        score = win[2] 
        momentum = win[3]
        alert_type = win[6]
        
        corner_wins[corner] = corner_wins.get(corner, 0) + 1
        score_wins[score] = score_wins.get(score, 0) + 1
        
        if momentum:
            momentum_range = "200+" if momentum >= 200 else "180-199" if momentum >= 180 else "160-179" if momentum >= 160 else "<160"
            momentum_wins[momentum_range] = momentum_wins.get(momentum_range, 0) + 1
        
        if alert_type:
            alert_type_wins[alert_type] = alert_type_wins.get(alert_type, 0) + 1
    
    print("🎯 MOST FREQUENT WINNING PATTERNS:")
    print(f"   Corners: {sorted(corner_wins.items(), key=lambda x: x[1], reverse=True)[:5]}")
    print(f"   Scores: {sorted(score_wins.items(), key=lambda x: x[1], reverse=True)[:5]}")
    print(f"   Momentum: {sorted(momentum_wins.items(), key=lambda x: x[1], reverse=True)}")
    print(f"   Alert Types: {sorted(alert_type_wins.items(), key=lambda x: x[1], reverse=True)}")
    
    cursor.close()

def calculate_ultra_strict_filters(conn):
    """Calculate what ultra-strict filters would achieve"""
    print("\n🔍 ULTRA-STRICT FILTERING ANALYSIS")
    print("=" * 45)
    
    cursor = conn.cursor()
    
    # Test increasingly strict combinations
    strict_filters = [
        ("Current System", "1=1"),
        ("Best Corners Only (5-6)", "corners_at_alert IN (5, 6)"),
        ("Best Score Only (1-2)", "score_at_alert = '1-2'"),
        ("High Momentum (180+)", "combined_momentum10 >= 180"),
        ("Perfect Storm: 5-6 corners + 1-2 score", "corners_at_alert IN (5, 6) AND score_at_alert = '1-2'"),
        ("Perfect Storm + High Momentum", "corners_at_alert IN (5, 6) AND score_at_alert = '1-2' AND combined_momentum10 >= 180"),
        ("Ultra-Strict: Fighting Underdog + Perfect Storm", "alert_type = 'FIGHTING_UNDERDOG' AND corners_at_alert IN (5, 6) AND score_at_alert = '1-2'"),
        ("Nuclear Option: Everything Perfect", "alert_type = 'FIGHTING_UNDERDOG' AND corners_at_alert IN (5, 6) AND score_at_alert = '1-2' AND combined_momentum10 >= 180"),
    ]
    
    print(f"{'Filter':<35} {'Alerts':<8} {'Wins':<6} {'Win%':<8} {'Weekly':<8}")
    print("-" * 70)
    
    for filter_name, condition in strict_filters:
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
            weekly_est = total / 10 if total > 0 else 0  # Rough estimate
            
            marker = ""
            if win_rate >= 80:
                marker = "🎯"
            elif win_rate >= 60:
                marker = "📈"
            elif win_rate >= 50:
                marker = "⚡"
            
            # Truncate filter name if too long
            filter_display = filter_name[:33] + ".." if len(filter_name) > 35 else filter_name
            print(f"{marker} {filter_display:<35} {total:<8} {wins:<6} {win_rate:<8.1f}% {weekly_est:<8.1f}")
    
    cursor.close()

def suggest_path_to_80_percent(conn):
    """Suggest specific path to achieve 80% win rate"""
    print("\n🚀 PATH TO 80% WIN RATE")
    print("=" * 30)
    
    cursor = conn.cursor()
    
    print(f"💡 ANALYSIS CONCLUSIONS:")
    
    # Check if ultra-strict filtering gets us close
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        CASE WHEN COUNT(*) > 0 
            THEN SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
            ELSE 0 
        END as win_rate
    FROM alerts 
    WHERE corners_at_alert IN (5, 6) AND score_at_alert = '1-2' AND combined_momentum10 >= 180
    """)
    
    ultra_strict = cursor.fetchone()
    
    if ultra_strict and ultra_strict[0] > 0:
        total, wins, win_rate = ultra_strict
        print(f"   🔍 Ultra-strict filtering achieves: {win_rate:.1f}% win rate ({total} alerts)")
        
        if win_rate >= 80:
            print(f"   🎯 SOLUTION FOUND: Use ultra-strict filters!")
        else:
            gap = 80 - win_rate
            print(f"   📊 Gap to 80%: {gap:.1f} percentage points")
    
    print(f"\n🛠️ RECOMMENDED IMPROVEMENTS:")
    print(f"   1. 📊 ADD MORE DATA POINTS:")
    print(f"      • Time of goals (recent goals = more corners)")
    print(f"      • Player statistics (attacking players on field)")
    print(f"      • Weather conditions (affects play style)")
    print(f"      • League-specific patterns")
    
    print(f"\n   2. 🧠 SMARTER ALGORITHMS:")
    print(f"      • Machine learning on historical patterns")
    print(f"      • Real-time odds movement analysis")
    print(f"      • Team formation analysis")
    print(f"      • Recent form analysis (last 5 games)")
    
    print(f"\n   3. 🎯 ULTRA-SELECTIVE APPROACH:")
    print(f"      • Only alert on PERFECT conditions")
    print(f"      • Wait for multiple signals to align")
    print(f"      • Focus on 2-3 alerts/week instead of 20+")
    print(f"      • Quality over quantity strategy")
    
    print(f"\n   4. 📈 ADDITIONAL FILTERS TO IMPLEMENT:")
    print(f"      • Recent corner rate (corners in last 10 minutes)")
    print(f"      • Goal timing (goals in last 15 minutes)")
    print(f"      • Team desperation level")
    print(f"      • Referee leniency (affects corner decisions)")
    
    print(f"\n   5. 🔄 DYNAMIC THRESHOLDS:")
    print(f"      • Adjust thresholds based on league")
    print(f"      • Higher standards for weekend games")
    print(f"      • Lower standards for cup games")
    print(f"      • Time-based adjustments")
    
    cursor.close()

def identify_data_gaps(conn):
    """Identify what additional data we need"""
    print("\n🔍 DATA GAPS ANALYSIS")
    print("=" * 25)
    
    cursor = conn.cursor()
    
    # Check what data we have vs what we need
    cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'alerts'
    ORDER BY column_name
    """)
    
    available_columns = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 AVAILABLE DATA ({len(available_columns)} columns):")
    for col in available_columns:
        print(f"   ✅ {col}")
    
    print(f"\n❌ MISSING DATA FOR 80% WIN RATE:")
    missing_data = [
        "Goal timing (when were goals scored)",
        "Recent form (team performance last 5 games)", 
        "Player substitutions (attacking players added)",
        "Referee statistics (corner-awarding tendency)",
        "Weather conditions",
        "Team motivation level (league position pressure)",
        "Recent head-to-head corner statistics",
        "Live odds movement (market confidence)",
        "Team attacking formation changes",
        "Injury time likelihood"
    ]
    
    for missing in missing_data:
        print(f"   ❌ {missing}")
    
    print(f"\n💡 QUICK WINS - Data to add immediately:")
    print(f"   🎯 Goal timing in current match")
    print(f"   🎯 Corners in last 15 minutes") 
    print(f"   🎯 Team recent form (wins/losses)")
    print(f"   🎯 Current league position pressure")
    
    cursor.close()

def main():
    print("🎯 PATH TO 80% WIN RATE ANALYSIS")
    print("=" * 40)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        find_80_percent_patterns(conn)
        analyze_winning_streaks(conn)
        calculate_ultra_strict_filters(conn)
        suggest_path_to_80_percent(conn)
        identify_data_gaps(conn)
        
        print("\n" + "=" * 40)
        print("🎯 BOTTOM LINE:")
        print("   80% win rate requires revolutionary changes:")
        print("   • Much stricter filtering (2-3 alerts/week)")
        print("   • Additional data sources")
        print("   • Smarter algorithms")
        print("   • Quality over quantity mindset")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()