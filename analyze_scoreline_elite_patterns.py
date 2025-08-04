#!/usr/bin/env python3
"""
Detailed analysis of score lines and elite score patterns from PostgreSQL database
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict, Counter

def connect_to_database():
    """Connect to PostgreSQL database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return None
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        print("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def analyze_score_lines(alerts):
    """Analyze score line patterns in detail"""
    print(f"\n⚽ DETAILED SCORE LINE ANALYSIS:")
    
    # Categorize score lines
    scoreline_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0, 'details': []})
    goal_diff_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    
    for alert in alerts:
        score_at_alert = alert.get('score_at_alert', '')
        result = alert['result']
        elite_score = alert.get('elite_score', 0)
        corners = alert.get('corners_at_alert', 0)
        
        # Track specific score lines
        scoreline_outcomes[score_at_alert][result] += 1
        scoreline_outcomes[score_at_alert]['details'].append({
            'result': result,
            'elite_score': elite_score,
            'corners': corners,
            'teams': alert.get('teams', '')
        })
        
        # Analyze goal difference
        if score_at_alert and '-' in score_at_alert:
            try:
                home_goals, away_goals = map(int, score_at_alert.split('-'))
                goal_diff = abs(home_goals - away_goals)
                
                if goal_diff == 0:
                    diff_category = "Draw"
                elif goal_diff == 1:
                    diff_category = "1-goal diff"
                elif goal_diff == 2:
                    diff_category = "2-goal diff"
                else:
                    diff_category = "3+ goal diff"
                
                goal_diff_outcomes[diff_category][result] += 1
            except:
                continue
    
    # Print score line results
    print(f"\n📊 PERFORMANCE BY SPECIFIC SCORE LINE:")
    print(f"{'Score':<8} {'Total':<6} {'W':<3} {'R':<3} {'L':<3} {'Profit%':<8} {'Avg Elite Score'}")
    print("-" * 70)
    
    for score in sorted(scoreline_outcomes.keys()):
        data = scoreline_outcomes[score]
        wins = data['WIN']
        refunds = data['REFUND'] 
        losses = data['LOSS']
        total = wins + refunds + losses
        
        if total > 0:
            profit_rate = ((wins + refunds) / total) * 100
            avg_elite = sum(detail['elite_score'] for detail in data['details']) / len(data['details'])
            
            print(f"{score:<8} {total:<6} {wins:<3} {refunds:<3} {losses:<3} {profit_rate:<8.1f} {avg_elite:.1f}")
    
    # Print goal difference analysis
    print(f"\n🎯 PERFORMANCE BY GOAL DIFFERENCE:")
    print(f"{'Category':<12} {'Total':<6} {'W':<3} {'R':<3} {'L':<3} {'Profit%'}")
    print("-" * 50)
    
    for category in ["Draw", "1-goal diff", "2-goal diff", "3+ goal diff"]:
        if category in goal_diff_outcomes:
            data = goal_diff_outcomes[category]
            wins = data['WIN']
            refunds = data['REFUND']
            losses = data['LOSS'] 
            total = wins + refunds + losses
            profit_rate = ((wins + refunds) / total) * 100 if total > 0 else 0
            
            print(f"{category:<12} {total:<6} {wins:<3} {refunds:<3} {losses:<3} {profit_rate:.1f}%")
    
    return scoreline_outcomes, goal_diff_outcomes

def analyze_elite_score_patterns(alerts):
    """Analyze elite score patterns in detail"""
    print(f"\n⚡ DETAILED ELITE SCORE ANALYSIS:")
    
    # Group by score ranges and track details
    score_ranges = {
        "8-10": [],
        "11-15": [],
        "16-20": [],
        "20+": []
    }
    
    for alert in alerts:
        elite_score = alert.get('elite_score')
        if elite_score is not None:
            score_at_alert = alert.get('score_at_alert', '')
            result = alert['result']
            corners = alert.get('corners_at_alert', 0)
            
            alert_detail = {
                'score': elite_score,
                'result': result,
                'scoreline': score_at_alert,
                'corners': corners,
                'teams': alert.get('teams', '')
            }
            
            if 8 <= elite_score <= 10:
                score_ranges["8-10"].append(alert_detail)
            elif 11 <= elite_score <= 15:
                score_ranges["11-15"].append(alert_detail)
            elif 16 <= elite_score <= 20:
                score_ranges["16-20"].append(alert_detail)
            else:
                score_ranges["20+"].append(alert_detail)
    
    # Analyze each range
    print(f"\n📈 ELITE SCORE RANGE ANALYSIS:")
    
    for range_name, alerts_in_range in score_ranges.items():
        if not alerts_in_range:
            continue
            
        wins = len([a for a in alerts_in_range if a['result'] == 'WIN'])
        refunds = len([a for a in alerts_in_range if a['result'] == 'REFUND'])
        losses = len([a for a in alerts_in_range if a['result'] == 'LOSS'])
        total = len(alerts_in_range)
        
        profit_rate = ((wins + refunds) / total) * 100
        avg_score = sum(a['score'] for a in alerts_in_range) / total
        avg_corners = sum(a['corners'] for a in alerts_in_range) / total
        
        print(f"\n🎯 {range_name} Range ({total} alerts):")
        print(f"   Profit Rate: {profit_rate:.1f}% ({wins}W-{refunds}R-{losses}L)")
        print(f"   Avg Elite Score: {avg_score:.1f}")
        print(f"   Avg Corners: {avg_corners:.1f}")
        
        # Show common score lines in this range
        scorelines = Counter([a['scoreline'] for a in alerts_in_range])
        print(f"   Common Score Lines: {dict(scorelines.most_common(3))}")

def find_elite_score_scoreline_correlations(alerts):
    """Find correlations between elite scores and score lines"""
    print(f"\n🔍 ELITE SCORE vs SCORE LINE CORRELATIONS:")
    
    scoreline_elite_stats = defaultdict(list)
    
    for alert in alerts:
        score_at_alert = alert.get('score_at_alert', '')
        elite_score = alert.get('elite_score')
        result = alert['result']
        
        if score_at_alert and elite_score is not None:
            scoreline_elite_stats[score_at_alert].append({
                'elite_score': elite_score,
                'result': result
            })
    
    print(f"\n📊 AVERAGE ELITE SCORES BY SCORE LINE:")
    print(f"{'Score Line':<10} {'Count':<6} {'Avg Elite':<10} {'Max Elite':<10} {'Profit%'}")
    print("-" * 60)
    
    for scoreline in sorted(scoreline_elite_stats.keys()):
        data = scoreline_elite_stats[scoreline]
        if len(data) >= 2:  # Only show score lines with 2+ occurrences
            avg_elite = sum(d['elite_score'] for d in data) / len(data)
            max_elite = max(d['elite_score'] for d in data)
            
            wins = len([d for d in data if d['result'] == 'WIN'])
            refunds = len([d for d in data if d['result'] == 'REFUND'])
            profit_rate = ((wins + refunds) / len(data)) * 100
            
            print(f"{scoreline:<10} {len(data):<6} {avg_elite:<10.1f} {max_elite:<10.1f} {profit_rate:.1f}%")

def identify_best_combinations(alerts):
    """Identify best score line + elite score combinations"""
    print(f"\n🏆 BEST PERFORMING COMBINATIONS:")
    
    combinations = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    
    for alert in alerts:
        score_at_alert = alert.get('score_at_alert', '')
        elite_score = alert.get('elite_score')
        result = alert['result']
        
        if score_at_alert and elite_score is not None:
            # Create score range + scoreline combination
            if 8 <= elite_score <= 12:
                elite_range = "8-12"
            elif 13 <= elite_score <= 17:
                elite_range = "13-17"
            else:
                elite_range = "18+"
            
            combo = f"{score_at_alert} + Elite {elite_range}"
            combinations[combo][result] += 1
    
    # Find most profitable combinations
    profitable_combos = []
    for combo, data in combinations.items():
        total = sum(data.values())
        if total >= 2:  # Only consider combinations with 2+ occurrences
            wins = data['WIN']
            refunds = data['REFUND']
            profit_rate = ((wins + refunds) / total) * 100
            profitable_combos.append((combo, profit_rate, total, wins, refunds, data['LOSS']))
    
    # Sort by profit rate
    profitable_combos.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n✅ TOP PERFORMING COMBINATIONS:")
    print(f"{'Combination':<25} {'Profit%':<8} {'Total':<6} {'W-R-L'}")
    print("-" * 50)
    
    for combo, profit_rate, total, wins, refunds, losses in profitable_combos[:10]:
        print(f"{combo:<25} {profit_rate:<8.1f} {total:<6} {wins}-{refunds}-{losses}")

def main():
    print("🔍 SCORE LINE & ELITE SCORE CORRELATION ANALYSIS")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Get all alerts with results
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM alerts 
            WHERE result IS NOT NULL
            ORDER BY created_at DESC
        """)
        alerts = cursor.fetchall()
        cursor.close()
        
        if not alerts:
            print("❌ No alerts found")
            return
        
        print(f"📈 Analyzing {len(alerts)} alerts...")
        
        # Run detailed analyses
        analyze_score_lines(alerts)
        analyze_elite_score_patterns(alerts)
        find_elite_score_scoreline_correlations(alerts)
        identify_best_combinations(alerts)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main() 