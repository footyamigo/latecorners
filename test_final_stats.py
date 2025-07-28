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
    # Fallback to any live match
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
            
            # Updated stat type mapping based on discoveries
            discovered_stat_mapping = {
                34: "Corners (Likely)",      # max=7, avg=3.1, very consistent
                41: "Shots on Goal (Likely)", # max=13, avg=5.5 
                42: "Shots Total (Likely)",   # max=16, avg=7.8
                43: "Possession/Passes",      # max=242, avg=60+
                44: "Attacks",                # max=127, confirmed
                45: "Dangerous Attacks",      # max=72, confirmed  
                46: "Unknown 46",
                51: "Red Cards (Likely)",     # max=1, avg=0.5
                52: "Yellow Cards (Likely)",  # max=1, avg=0.8
                55: "Unknown 55",
                56: "Fouls (Likely)",         # max=10, avg=4.2
                59: "Unknown 59", 
                64: "Unknown 64",
                82: "Unknown 82",
                84: "Big Chances Missed",     # max=5, confirmed
                86: "Saves (Likely)",         # max=3, avg=2.2
                98: "Unknown 98",
                117: "Unknown 117"
            }
            
            print(f"\n🎯 LIVE MATCH STATISTICS:")
            print("=" * 80)
            
            all_type_ids = set(home_stats.keys()) | set(away_stats.keys())
            for type_id in sorted(all_type_ids):
                home_val = home_stats.get(type_id, 'N/A')
                away_val = away_stats.get(type_id, 'N/A')
                stat_name = discovered_stat_mapping.get(type_id, f"Unknown Type {type_id}")
                print(f"   {stat_name:<25} | Type {type_id:<3} | Home: {home_val:<3} | Away: {away_val}")
            
            # Focus on key stats for corner system
            print(f"\n🏆 KEY STATS FOR LATE CORNER SYSTEM:")
            print("=" * 80)
            
            key_stats = [
                (34, "Corners"),
                (42, "Total Shots"), 
                (41, "Shots on Goal"),
                (44, "Attacks"),
                (45, "Dangerous Attacks"),
                (84, "Big Chances Missed"),
                (86, "Saves"),
                (52, "Yellow Cards"),
                (51, "Red Cards")
            ]
            
            corner_total = 0
            shot_total = 0
            
            print(f"   {'Stat':<18} | {'Home':<4} | {'Away':<4} | {'Total':<5} | Status")
            print("   " + "-" * 60)
            
            for type_id, stat_name in key_stats:
                home_val = home_stats.get(type_id, 0) if home_stats.get(type_id) != 'N/A' else 0
                away_val = away_stats.get(type_id, 0) if away_stats.get(type_id) != 'N/A' else 0
                total_val = home_val + away_val
                
                status = "✅ Available" if type_id in all_type_ids else "❌ Missing"
                print(f"   {stat_name:<18} | {home_val:<4} | {away_val:<4} | {total_val:<5} | {status}")
                
                if type_id == 34:  # Corners
                    corner_total = total_val
                elif type_id in [41, 42]:  # Shots
                    shot_total = max(shot_total, total_val)  # Use the higher of the two
            
            # Corner system evaluation
            print(f"\n🎯 LATE CORNER SYSTEM EVALUATION:")
            print("=" * 80)
            
            if minute >= 70:
                if corner_total >= 8:
                    print(f"   🟢 HIGH CORNER ACTIVITY: {corner_total} total corners (≥8)")
                elif corner_total >= 5:
                    print(f"   🟡 MEDIUM CORNER ACTIVITY: {corner_total} total corners (5-7)")
                else:
                    print(f"   🔴 LOW CORNER ACTIVITY: {corner_total} total corners (<5)")
                
                if shot_total >= 15:
                    print(f"   🟢 HIGH SHOT ACTIVITY: {shot_total} total shots (≥15)")
                elif shot_total >= 10:
                    print(f"   🟡 MEDIUM SHOT ACTIVITY: {shot_total} total shots (10-14)")
                else:
                    print(f"   🔴 LOW SHOT ACTIVITY: {shot_total} total shots (<10)")
                
                # Overall recommendation
                if corner_total >= 8 and shot_total >= 15:
                    print(f"   🎯 RECOMMENDATION: EXCELLENT candidate for late corner betting!")
                elif corner_total >= 5 and shot_total >= 10:
                    print(f"   ⚡ RECOMMENDATION: GOOD candidate for late corner betting!")
                else:
                    print(f"   ⚠️  RECOMMENDATION: POOR candidate - low activity")
            else:
                print(f"   ⏰ Match at {minute}' - wait until 70+ minutes for late corner system")
        
        else:
            print("❌ No statistics found")
    
    else:
        print("❌ No fixture data returned")

else:
    print("❌ No live matches found") 