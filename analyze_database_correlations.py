#!/usr/bin/env python3
"""
Comprehensive analysis of PostgreSQL database to find correlations
between match statistics and alert outcomes (WINS, REFUNDS, LOSSES)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from collections import defaultdict, Counter
from datetime import datetime

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

def get_all_alerts(conn):
    """Get all alerts with their statistics"""
    cursor = conn.cursor()
    
    # Get all columns available
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'alerts'
        ORDER BY ordinal_position
    """)
    
    columns = [row['column_name'] for row in cursor.fetchall()]
    print(f"📊 Available columns: {columns}")
    
    # Get all alert data
    cursor.execute("""
        SELECT * FROM alerts 
        WHERE result IS NOT NULL
        ORDER BY created_at DESC
    """)
    
    alerts = cursor.fetchall()
    cursor.close()
    
    print(f"📈 Retrieved {len(alerts)} alerts with results")
    return alerts, columns

def analyze_outcomes(alerts):
    """Analyze overall outcomes"""
    outcomes = Counter([alert['result'] for alert in alerts])
    total = len(alerts)
    
    print(f"\n📊 OVERALL OUTCOMES ({total} total alerts):")
    for outcome, count in outcomes.most_common():
        percentage = (count / total) * 100
        print(f"   {outcome}: {count} ({percentage:.1f}%)")
    
    win_rate = (outcomes.get('WIN', 0) / total) * 100
    refund_rate = (outcomes.get('REFUND', 0) / total) * 100
    profitability = win_rate + refund_rate
    
    print(f"\n💰 PROFITABILITY METRICS:")
    print(f"   Win Rate: {win_rate:.1f}%")
    print(f"   Refund Rate: {refund_rate:.1f}%")
    print(f"   Total Profitability: {profitability:.1f}%")
    
    return outcomes

def analyze_corner_patterns(alerts):
    """Analyze corner count patterns"""
    print(f"\n⚽ CORNER COUNT ANALYSIS:")
    
    corner_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    
    for alert in alerts:
        corners = alert.get('corners_at_alert')
        final_corners = alert.get('final_corners')
        result = alert['result']
        
        if corners is not None:
            corner_outcomes[corners][result] += 1
    
    # Sort by corner count
    print(f"\n📈 PERFORMANCE BY CORNER COUNT AT ALERT:")
    print(f"{'Corners':<8} {'Total':<6} {'Wins':<6} {'Refunds':<8} {'Losses':<7} {'Win%':<6} {'Profit%'}")
    print("-" * 65)
    
    for corners in sorted(corner_outcomes.keys()):
        data = corner_outcomes[corners]
        total = sum(data.values())
        wins = data['WIN']
        refunds = data['REFUND']
        losses = data['LOSS']
        
        win_rate = (wins / total) * 100 if total > 0 else 0
        profit_rate = ((wins + refunds) / total) * 100 if total > 0 else 0
        
        print(f"{corners:<8} {total:<6} {wins:<6} {refunds:<8} {losses:<7} {win_rate:<6.1f} {profit_rate:.1f}%")
    
    return corner_outcomes

def analyze_line_and_odds(alerts):
    """Analyze betting lines and odds patterns"""
    print(f"\n🎯 BETTING LINE ANALYSIS:")
    
    line_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    odds_ranges = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    
    for alert in alerts:
        over_line = alert.get('over_line')
        over_odds = alert.get('over_odds')
        result = alert['result']
        
        if over_line:
            line_outcomes[over_line][result] += 1
        
        if over_odds:
            try:
                odds_val = float(over_odds)
                if odds_val < 1.5:
                    odds_range = "< 1.5"
                elif odds_val < 1.8:
                    odds_range = "1.5-1.8"
                elif odds_val < 2.0:
                    odds_range = "1.8-2.0"
                else:
                    odds_range = "2.0+"
                odds_ranges[odds_range][result] += 1
            except:
                continue
    
    print(f"\n📊 PERFORMANCE BY BETTING LINE:")
    print(f"{'Line':<8} {'Total':<6} {'Wins':<6} {'Refunds':<8} {'Losses':<7} {'Profit%'}")
    print("-" * 55)
    
    for line in sorted(line_outcomes.keys()):
        data = line_outcomes[line]
        total = sum(data.values())
        wins = data['WIN']
        refunds = data['REFUND']
        losses = data['LOSS']
        profit_rate = ((wins + refunds) / total) * 100 if total > 0 else 0
        
        print(f"{line:<8} {total:<6} {wins:<6} {refunds:<8} {losses:<7} {profit_rate:.1f}%")
    
    print(f"\n💰 PERFORMANCE BY ODDS RANGE:")
    print(f"{'Odds':<8} {'Total':<6} {'Wins':<6} {'Refunds':<8} {'Losses':<7} {'Profit%'}")
    print("-" * 55)
    
    for odds_range in ["< 1.5", "1.5-1.8", "1.8-2.0", "2.0+"]:
        if odds_range in odds_ranges:
            data = odds_ranges[odds_range]
            total = sum(data.values())
            wins = data['WIN']
            refunds = data['REFUND']
            losses = data['LOSS']
            profit_rate = ((wins + refunds) / total) * 100 if total > 0 else 0
            
            print(f"{odds_range:<8} {total:<6} {wins:<6} {refunds:<8} {losses:<7} {profit_rate:.1f}%")
    
    return line_outcomes, odds_ranges

def analyze_high_priority_patterns(alerts):
    """Analyze high priority count patterns"""
    print(f"\n🏆 HIGH PRIORITY ANALYSIS:")
    
    priority_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    ratio_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    
    for alert in alerts:
        priority_count = alert.get('high_priority_count')
        priority_ratio = alert.get('high_priority_ratio')
        result = alert['result']
        
        if priority_count is not None:
            priority_outcomes[priority_count][result] += 1
        
        if priority_ratio:
            ratio_outcomes[priority_ratio][result] += 1
    
    print(f"\n📈 PERFORMANCE BY HIGH PRIORITY COUNT:")
    print(f"{'Priority':<9} {'Total':<6} {'Wins':<6} {'Refunds':<8} {'Losses':<7} {'Profit%'}")
    print("-" * 60)
    
    for priority in sorted(priority_outcomes.keys()):
        data = priority_outcomes[priority]
        total = sum(data.values())
        wins = data['WIN']
        refunds = data['REFUND']
        losses = data['LOSS']
        profit_rate = ((wins + refunds) / total) * 100 if total > 0 else 0
        
        print(f"{priority:<9} {total:<6} {wins:<6} {refunds:<8} {losses:<7} {profit_rate:.1f}%")
    
    return priority_outcomes

def analyze_shots_on_target(alerts):
    """Analyze shots on target patterns (if available)"""
    print(f"\n🎯 SHOTS ON TARGET ANALYSIS:")
    
    sot_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    
    # Check if SOT columns exist
    has_sot_data = any(alert.get('total_shots_on_target') is not None for alert in alerts)
    
    if not has_sot_data:
        print("   ⚠️  No shots on target data available yet (new feature)")
        return {}
    
    for alert in alerts:
        total_sot = alert.get('total_shots_on_target')
        result = alert['result']
        
        if total_sot is not None:
            if total_sot < 5:
                sot_range = "< 5"
            elif total_sot < 8:
                sot_range = "5-7"
            elif total_sot < 12:
                sot_range = "8-11"
            else:
                sot_range = "12+"
            
            sot_outcomes[sot_range][result] += 1
    
    print(f"\n📊 PERFORMANCE BY TOTAL SHOTS ON TARGET:")
    print(f"{'SOT Range':<10} {'Total':<6} {'Wins':<6} {'Refunds':<8} {'Losses':<7} {'Profit%'}")
    print("-" * 60)
    
    for sot_range in ["< 5", "5-7", "8-11", "12+"]:
        if sot_range in sot_outcomes:
            data = sot_outcomes[sot_range]
            total = sum(data.values())
            wins = data['WIN']
            refunds = data['REFUND']
            losses = data['LOSS']
            profit_rate = ((wins + refunds) / total) * 100 if total > 0 else 0
            
            print(f"{sot_range:<10} {total:<6} {wins:<6} {refunds:<8} {losses:<7} {profit_rate:.1f}%")
    
    return sot_outcomes

def analyze_elite_scores(alerts):
    """Analyze elite score patterns"""
    print(f"\n⚡ ELITE SCORE ANALYSIS:")
    
    score_outcomes = defaultdict(lambda: {'WIN': 0, 'REFUND': 0, 'LOSS': 0})
    
    for alert in alerts:
        elite_score = alert.get('elite_score')
        result = alert['result']
        
        if elite_score is not None:
            if elite_score < 10:
                score_range = "8-9"
            elif elite_score < 15:
                score_range = "10-14"
            elif elite_score < 20:
                score_range = "15-19"
            else:
                score_range = "20+"
            
            score_outcomes[score_range][result] += 1
    
    print(f"\n📊 PERFORMANCE BY ELITE SCORE:")
    print(f"{'Score':<8} {'Total':<6} {'Wins':<6} {'Refunds':<8} {'Losses':<7} {'Profit%'}")
    print("-" * 55)
    
    for score_range in ["8-9", "10-14", "15-19", "20+"]:
        if score_range in score_outcomes:
            data = score_outcomes[score_range]
            total = sum(data.values())
            wins = data['WIN']
            refunds = data['REFUND']
            losses = data['LOSS']
            profit_rate = ((wins + refunds) / total) * 100 if total > 0 else 0
            
            print(f"{score_range:<8} {total:<6} {wins:<6} {refunds:<8} {losses:<7} {profit_rate:.1f}%")
    
    return score_outcomes

def find_best_patterns(alerts):
    """Find the most successful patterns"""
    print(f"\n🏆 BEST PERFORMING PATTERNS:")
    
    wins = [alert for alert in alerts if alert['result'] == 'WIN']
    refunds = [alert for alert in alerts if alert['result'] == 'REFUND'] 
    losses = [alert for alert in alerts if alert['result'] == 'LOSS']
    
    print(f"\n✅ WINNING PATTERNS ({len(wins)} wins):")
    if wins:
        # Analyze winning patterns
        win_corners = [alert.get('corners_at_alert') for alert in wins if alert.get('corners_at_alert')]
        win_priorities = [alert.get('high_priority_count') for alert in wins if alert.get('high_priority_count')]
        win_scores = [alert.get('elite_score') for alert in wins if alert.get('elite_score')]
        
        if win_corners:
            avg_corners = sum(win_corners) / len(win_corners)
            print(f"   📊 Average corners: {avg_corners:.1f}")
            print(f"   📊 Corner range: {min(win_corners)}-{max(win_corners)}")
        
        if win_priorities:
            avg_priority = sum(win_priorities) / len(win_priorities)
            print(f"   🏆 Average high priority: {avg_priority:.1f}")
        
        if win_scores:
            avg_score = sum(win_scores) / len(win_scores)
            print(f"   ⚡ Average elite score: {avg_score:.1f}")
    
    print(f"\n🔄 REFUND PATTERNS ({len(refunds)} refunds):")
    if refunds:
        refund_corners = [alert.get('corners_at_alert') for alert in refunds if alert.get('corners_at_alert')]
        refund_priorities = [alert.get('high_priority_count') for alert in refunds if alert.get('high_priority_count')]
        
        if refund_corners:
            avg_corners = sum(refund_corners) / len(refund_corners)
            print(f"   📊 Average corners: {avg_corners:.1f}")
        
        if refund_priorities:
            avg_priority = sum(refund_priorities) / len(refund_priorities)
            print(f"   🏆 Average high priority: {avg_priority:.1f}")
    
    print(f"\n❌ LOSS PATTERNS ({len(losses)} losses):")
    if losses:
        loss_corners = [alert.get('corners_at_alert') for alert in losses if alert.get('corners_at_alert')]
        loss_priorities = [alert.get('high_priority_count') for alert in losses if alert.get('high_priority_count')]
        
        if loss_corners:
            avg_corners = sum(loss_corners) / len(loss_corners)
            print(f"   📊 Average corners: {avg_corners:.1f}")
        
        if loss_priorities:
            avg_priority = sum(loss_priorities) / len(loss_priorities)
            print(f"   🏆 Average high priority: {avg_priority:.1f}")

def main():
    print("🔍 COMPREHENSIVE DATABASE CORRELATION ANALYSIS")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Get all alerts
        alerts, columns = get_all_alerts(conn)
        
        if not alerts:
            print("❌ No alerts found in database")
            return
        
        # Run all analyses
        analyze_outcomes(alerts)
        analyze_corner_patterns(alerts)
        analyze_line_and_odds(alerts)
        analyze_high_priority_patterns(alerts)
        analyze_shots_on_target(alerts)
        analyze_elite_scores(alerts)
        find_best_patterns(alerts)
        
        print(f"\n🎯 ANALYSIS COMPLETE")
        print(f"   Total alerts analyzed: {len(alerts)}")
        print(f"   Key finding: Look for patterns with highest profit percentages")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main() 