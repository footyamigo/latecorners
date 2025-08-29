#!/usr/bin/env python3
"""
Debug script to investigate why momentum is showing all zeros
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sportmonks_client import SportmonksClient
from live_data_collector import LiveDataCollector

async def debug_zero_momentum():
    """Debug why momentum calculations are showing zero"""
    
    print("🔍 DEBUGGING ZERO MOMENTUM ISSUE")
    print(f"⏰ Time: {datetime.now()}")
    print("=" * 60)
    
    # Initialize clients
    sportmonks = SportmonksClient()
    collector = LiveDataCollector()
    
    try:
        # Method 1: Check direct SportMonks API
        print("\n📡 METHOD 1: Direct SportMonks API")
        print("-" * 40)
        
        live_matches = sportmonks.get_live_matches(filter_by_minute=False)
        if not live_matches:
            print("❌ No live matches from SportMonks API")
        else:
            print(f"✅ Found {len(live_matches)} live matches")
            
            # Check the first match in detail
            for i, match in enumerate(live_matches[:2]):  # First 2 matches
                print(f"\n🔍 MATCH {i+1}: {match.get('id', 'Unknown ID')}")
                
                # Check basic info
                participants = match.get('participants', [])
                home_team = "Unknown"
                away_team = "Unknown"
                
                for p in participants:
                    location = p.get('meta', {}).get('location', '')
                    if location == 'home':
                        home_team = p.get('name', 'Unknown')
                    elif location == 'away':
                        away_team = p.get('name', 'Unknown')
                
                print(f"   🏠 Teams: {home_team} vs {away_team}")
                
                # Check minute
                periods = match.get('periods', [])
                minute = 0
                for period in periods:
                    if period.get('ticking', False):
                        minute = period.get('minutes', 0)
                        break
                print(f"   ⏱️ Minute: {minute}")
                
                # CHECK RAW STATISTICS
                raw_stats = match.get('statistics', [])
                print(f"   📊 Raw statistics count: {len(raw_stats)}")
                
                if not raw_stats:
                    print("   ❌ NO STATISTICS FOUND IN API RESPONSE")
                else:
                    print(f"   📋 First 5 raw statistics:")
                    for j, stat in enumerate(raw_stats[:5]):
                        type_id = stat.get('type_id')
                        location = stat.get('location', 'unknown')
                        value = stat.get('data', {}).get('value', 0)
                        print(f"      [{j}] Type {type_id}: {location} = {value}")
                
                # Parse with SportMonks client
                print(f"   🔄 Parsing with SportMonks client...")
                parsed_stats = sportmonks._parse_live_match_data(match)
                
                if parsed_stats:
                    print(f"   ✅ Parsed successfully:")
                    print(f"      Shots on target: {parsed_stats.shots_on_target}")
                    print(f"      Shots off target: {parsed_stats.shots_off_target}")
                    print(f"      Dangerous attacks: {parsed_stats.dangerous_attacks}")
                    print(f"      Attacks: {parsed_stats.attacks}")
                    print(f"      Possession: {parsed_stats.possession}")
                    
                    # Calculate momentum for this match
                    home_momentum = 0
                    away_momentum = 0
                    
                    # Home team momentum calculation
                    home_momentum += parsed_stats.shots_on_target['home'] * 12  # +12 per shot on target
                    home_momentum += parsed_stats.shots_off_target['home'] * 8   # +8 per shot off target  
                    home_momentum += parsed_stats.dangerous_attacks['home'] * 12 # +12 per dangerous attack
                    home_momentum += parsed_stats.attacks['home'] * 6           # +6 per attack
                    home_momentum += parsed_stats.possession['home'] * 0.5      # +0.5 per % possession
                    
                    # Away team momentum calculation  
                    away_momentum += parsed_stats.shots_on_target['away'] * 12
                    away_momentum += parsed_stats.shots_off_target['away'] * 8
                    away_momentum += parsed_stats.dangerous_attacks['away'] * 12
                    away_momentum += parsed_stats.attacks['away'] * 6
                    away_momentum += parsed_stats.possession['away'] * 0.5
                    
                    print(f"   ⚡ MOMENTUM CALCULATION:")
                    print(f"      Home momentum: {home_momentum} pts")
                    print(f"      Away momentum: {away_momentum} pts") 
                    print(f"      Combined: {home_momentum + away_momentum} pts")
                else:
                    print(f"   ❌ Failed to parse match data")
        
        # Method 2: Check dashboard data
        print(f"\n📊 METHOD 2: Dashboard Data Source")
        print("-" * 40)
        
        try:
            from web_dashboard import live_matches_data
            dashboard_matches = list(live_matches_data) if live_matches_data else []
            
            if not dashboard_matches:
                print("❌ No matches in dashboard buffer")
            else:
                print(f"✅ Found {len(dashboard_matches)} matches in dashboard")
                
                # Check first dashboard match
                for i, match in enumerate(dashboard_matches[:2]):
                    print(f"\n🔍 DASHBOARD MATCH {i+1}:")
                    print(f"   Match ID: {match.get('match_id', 'Unknown')}")
                    print(f"   Teams: {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}")
                    print(f"   Minute: {match.get('minute', 0)}")
                    
                    # Check statistics structure
                    stats = match.get('statistics', {})
                    print(f"   📊 Statistics structure: {type(stats)}")
                    
                    if isinstance(stats, dict):
                        home_stats = stats.get('home', {})
                        away_stats = stats.get('away', {})
                        print(f"   🏠 Home stats: {home_stats}")
                        print(f"   🏃 Away stats: {away_stats}")
                        
                        # Check specific momentum-related stats
                        for team, team_stats in [('home', home_stats), ('away', away_stats)]:
                            print(f"   {team.upper()} momentum stats:")
                            print(f"      shots_on_target: {team_stats.get('shots_on_target', 'MISSING')}")
                            print(f"      shots_off_target: {team_stats.get('shots_off_target', 'MISSING')}")
                            print(f"      dangerous_attacks: {team_stats.get('dangerous_attacks', 'MISSING')}")
                            print(f"      attacks: {team_stats.get('attacks', 'MISSING')}")
                            print(f"      possession: {team_stats.get('ball_possession', 'MISSING')} (ball_possession)")
                            print(f"      possession: {team_stats.get('possession', 'MISSING')} (possession)")
                    else:
                        print(f"   ❌ Unexpected statistics format: {stats}")
        
        except ImportError:
            print("❌ Could not import dashboard data")
        
        # Method 3: Check live data collector
        print(f"\n🔧 METHOD 3: Live Data Collector")
        print("-" * 40)
        
        collected_matches = []  # LiveDataCollector doesn't have this method, skip for now
        if not collected_matches:
            print("❌ No matches from live data collector")
        else:
            print(f"✅ Collected {len(collected_matches)} matches")
            
            for i, match in enumerate(collected_matches[:1]):  # First match
                print(f"\n🔍 COLLECTED MATCH {i+1}:")
                print(f"   Match ID: {match.get('match_id', 'Unknown')}")
                print(f"   Teams: {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}")
                print(f"   Minute: {match.get('minute', 0)}")
                
                stats = match.get('statistics', {})
                if isinstance(stats, dict):
                    home_stats = stats.get('home', {})
                    away_stats = stats.get('away', {})
                    quality_score = stats.get('quality_score', 0)
                    
                    print(f"   📊 Quality score: {quality_score}")
                    print(f"   🏠 Home stats keys: {list(home_stats.keys())}")
                    print(f"   🏃 Away stats keys: {list(away_stats.keys())}")
                    
                    # Show actual values
                    for stat_name in ['shots_on_target', 'shots_off_target', 'dangerous_attacks', 'attacks', 'ball_possession']:
                        home_val = home_stats.get(stat_name, 'MISSING')
                        away_val = away_stats.get(stat_name, 'MISSING')
                        print(f"   {stat_name}: home={home_val}, away={away_val}")
        
    except Exception as e:
        print(f"❌ ERROR during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 DEBUGGING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_zero_momentum())