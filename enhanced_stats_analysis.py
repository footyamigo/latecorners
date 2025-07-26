import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# Get a live match in 2nd half
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods'
}

print("🔍 Getting live matches...")
response = requests.get(url, params=params)
data = response.json()
matches = data.get('data', [])

# Find a match in 2nd half with good stats
test_match = None
for match in matches:
    state = match.get('state', {})
    if isinstance(state, dict):
        state_name = state.get('developer_name', '')
        if state_name == 'INPLAY_2ND_HALF':
            test_match = match
            break

if not test_match:
    test_match = matches[0] if matches else None

if test_match:
    test_match_id = test_match['id']
    print(f"📊 Testing statistics for match ID: {test_match_id}")
    
    # Get detailed fixture stats
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{test_match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'statistics;events;scores;participants;state;periods'
    }
    
    print("📈 Fetching detailed fixture statistics...")
    fixture_response = requests.get(fixture_url, params=fixture_params)
    fixture_data = fixture_response.json()
    
    if 'data' in fixture_data:
        fixture = fixture_data['data']
        
        # Show match info
        participants = fixture.get('participants', [])
        home_team = "Unknown"
        away_team = "Unknown"
        if participants:
            for participant in participants:
                name = participant.get('name', 'Unknown')
                meta = participant.get('meta', {})
                location = meta.get('location', 'unknown')
                if location == 'home':
                    home_team = name
                elif location == 'away':
                    away_team = name
        
        # Show current state and minute
        state = fixture.get('state', {})
        periods = fixture.get('periods', [])
        minute = 0
        for period in periods:
            if period.get('ticking', False):
                minute = period.get('minutes', 0)
                if '2nd' in period.get('description', '').lower():
                    minute += 45
                break
        
        print(f"\n⚽ MATCH: {home_team} vs {away_team}")
        print(f"   State: {state.get('developer_name', 'Unknown')} | Minute: {minute}'")
        
        # Analyze statistics
        statistics = fixture.get('statistics', [])
        print(f"\n📊 Found {len(statistics)} statistics entries")
        
        if statistics:
            # Group by location
            home_stats = {}
            away_stats = {}
            
            for stat in statistics:
                location = stat.get('location', 'unknown')
                type_id = stat.get('type_id', 'Unknown')
                value = stat.get('data', {}).get('value', 0)
                
                if location == 'home':
                    home_stats[type_id] = value
                elif location == 'away':
                    away_stats[type_id] = value
            
            # Official SportMonks stat type mapping from documentation
            official_stat_mapping = {
                # CORNER & ATTACKING STATS
                34: "Corners",                    # corners (CORNERS)
                42: "Shots Total",               # shots-total (SHOTS_TOTAL)  
                41: "Shots Off Target",          # shots-off-target (SHOTS_OFF_TARGET)
                49: "Shots Inside Box",          # shots-insidebox (SHOTS_INSIDEBOX) ⭐ KEY FOR CORNERS
                50: "Shots Outside Box",         # shots-outsidebox (SHOTS_OUTSIDEBOX) ⭐ KEY FOR CORNERS
                43: "Attacks",                   # attacks (ATTACKS)
                44: "Dangerous Attacks",         # dangerous-attacks (DANGEROUS_ATTACKS)
                
                # PRESSURE & TEMPO STATS  
                45: "Ball Possession %",         # ball-possession (BALL_POSSESSION) ⭐ KEY FOR PRESSURE
                51: "Offsides",                  # offsides (OFFSIDES) ⭐ KEY FOR ATTACKING INTENSITY
                47: "Penalties",                 # penalties (PENALTIES) ⭐ HIGH PRESSURE SITUATIONS
                46: "Ball Safe",                 # ball-safe (BALL_SAFE)
                
                # DEFENSIVE ACTIONS (correlate with corners)
                52: "Saves",                     # Need to verify this
                53: "Blocks",                    # Need to verify this
                
                # CARDS & FOULS
                54: "Yellow Cards",              # Need to verify
                55: "Red Cards",                 # Need to verify  
                56: "Fouls",                     # Need to verify
                
                # ADDITIONAL CORNER-RELEVANT STATS
                57: "Throw Ins",                 # throw-ins often lead to corners
                58: "Free Kicks",                # can lead to corner situations
                59: "Goal Kicks",                # defensive clearances
                60: "Crosses",                   # directly related to corners
            }
            
            print(f"\n🎯 COMPREHENSIVE STATISTICS ANALYSIS:")
            print("=" * 90)
            
            all_type_ids = set(home_stats.keys()) | set(away_stats.keys())
            
            # Categorize stats for better analysis
            corner_indicators = [34, 49, 50, 60]  # Direct corner predictors
            pressure_indicators = [45, 51, 47, 43, 44]  # Attacking pressure
            tempo_indicators = [42, 41, 57, 58]  # Game tempo
            
            print(f"📍 DIRECT CORNER INDICATORS:")
            print("   " + "-" * 70)
            corner_score = 0
            for type_id in corner_indicators:
                if type_id in all_type_ids:
                    home_val = home_stats.get(type_id, 0)
                    away_val = away_stats.get(type_id, 0)
                    total_val = home_val + away_val
                    stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                    print(f"   ✅ {stat_name:<20} | Home: {home_val:<3} | Away: {away_val:<3} | Total: {total_val}")
                    
                    # Scoring system for corner prediction
                    if type_id == 34:  # Corners
                        corner_score += total_val * 2  # Weight corners heavily
                    elif type_id == 49:  # Shots inside box
                        corner_score += total_val * 1.5  # High correlation with corners
                    elif type_id == 50:  # Shots outside box  
                        corner_score += total_val * 0.5  # Lower correlation
                    elif type_id == 60:  # Crosses
                        corner_score += total_val * 1.2  # Direct correlation
                else:
                    stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                    print(f"   ❌ {stat_name:<20} | NOT AVAILABLE")
            
            print(f"\n🔥 ATTACKING PRESSURE INDICATORS:")
            print("   " + "-" * 70)
            pressure_score = 0
            for type_id in pressure_indicators:
                if type_id in all_type_ids:
                    home_val = home_stats.get(type_id, 0)
                    away_val = away_stats.get(type_id, 0)
                    total_val = home_val + away_val
                    stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                    print(f"   ✅ {stat_name:<20} | Home: {home_val:<3} | Away: {away_val:<3} | Total: {total_val}")
                    
                    # Scoring system for pressure
                    if type_id == 51:  # Offsides
                        pressure_score += total_val * 2  # High attacking intensity
                    elif type_id == 45:  # Possession
                        pressure_score += max(home_val, away_val) * 0.5  # Dominant possession
                    elif type_id in [43, 44]:  # Attacks
                        pressure_score += total_val * 0.8
                else:
                    stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                    print(f"   ❌ {stat_name:<20} | NOT AVAILABLE")
            
            print(f"\n⚡ GAME TEMPO INDICATORS:")
            print("   " + "-" * 70)
            tempo_score = 0
            for type_id in tempo_indicators:
                if type_id in all_type_ids:
                    home_val = home_stats.get(type_id, 0)
                    away_val = away_stats.get(type_id, 0)
                    total_val = home_val + away_val
                    stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                    print(f"   ✅ {stat_name:<20} | Home: {home_val:<3} | Away: {away_val:<3} | Total: {total_val}")
                    
                    # Scoring system for tempo
                    if type_id == 42:  # Total shots
                        tempo_score += total_val * 1.0
                    elif type_id in [57, 58]:  # Throw ins, free kicks
                        tempo_score += total_val * 0.3
                else:
                    stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                    print(f"   ❌ {stat_name:<20} | NOT AVAILABLE")
            
            # Show any additional stats we found
            print(f"\n📋 ALL OTHER AVAILABLE STATS:")
            print("   " + "-" * 70)
            other_stats = all_type_ids - set(corner_indicators + pressure_indicators + tempo_indicators)
            for type_id in sorted(other_stats):
                home_val = home_stats.get(type_id, 0)
                away_val = away_stats.get(type_id, 0)
                total_val = home_val + away_val
                stat_name = official_stat_mapping.get(type_id, f"Unknown Type {type_id}")
                print(f"   📊 {stat_name:<20} | Home: {home_val:<3} | Away: {away_val:<3} | Total: {total_val}")
            
            # ENHANCED CORNER PREDICTION ALGORITHM
            print(f"\n🎯 ENHANCED LATE CORNER PREDICTION:")
            print("=" * 90)
            
            # Calculate weighted score
            total_score = corner_score + (pressure_score * 0.3) + (tempo_score * 0.2)
            
            print(f"   📊 Corner Score: {corner_score:.1f}")
            print(f"   🔥 Pressure Score: {pressure_score:.1f}")  
            print(f"   ⚡ Tempo Score: {tempo_score:.1f}")
            print(f"   🎯 TOTAL WEIGHTED SCORE: {total_score:.1f}")
            
            if minute >= 70:
                if total_score >= 25:
                    print(f"   🟢 EXCELLENT corner opportunity! (Score: {total_score:.1f})")
                    print(f"   💰 STRONG BUY recommendation for corner bets")
                elif total_score >= 15:
                    print(f"   🟡 GOOD corner opportunity (Score: {total_score:.1f})")
                    print(f"   💡 MODERATE BUY recommendation")
                elif total_score >= 8:
                    print(f"   🟠 FAIR corner opportunity (Score: {total_score:.1f})")
                    print(f"   ⚠️ WEAK BUY - proceed with caution")
                else:
                    print(f"   🔴 POOR corner opportunity (Score: {total_score:.1f})")
                    print(f"   ❌ AVOID - low corner potential")
            else:
                print(f"   ⏰ Match at {minute}' - wait until 70+ minutes")
                print(f"   📈 Current trajectory score: {total_score:.1f}")
        
        else:
            print("❌ No statistics found")
    
    else:
        print("❌ No fixture data returned")

else:
    print("❌ No live matches found") 