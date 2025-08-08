import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# Test with a specific match that we know has statistics
test_match_id = 19380117  # Malmö FF W vs Vittsjo W - we know this has good stats
print(f"📊 Testing enhanced statistics for match ID: {test_match_id}")

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
            # CORNER & ATTACKING STATS (from docs)
            34: "Corners",                    # corners (CORNERS) ⭐ CONFIRMED
            42: "Shots Total",               # shots-total (SHOTS_TOTAL) ⭐ CONFIRMED
            41: "Shots Off Target",          # shots-off-target (SHOTS_OFF_TARGET) ⭐ CONFIRMED
            49: "Shots Inside Box",          # shots-insidebox (SHOTS_INSIDEBOX) ⭐ KEY FOR CORNERS
            50: "Shots Outside Box",         # shots-outsidebox (SHOTS_OUTSIDEBOX) ⭐ KEY FOR CORNERS
            43: "Attacks",                   # attacks (ATTACKS) ⭐ CONFIRMED
            44: "Dangerous Attacks",         # dangerous-attacks (DANGEROUS_ATTACKS) ⭐ CONFIRMED
            
            # PRESSURE & TEMPO STATS (from docs)
            45: "Ball Possession %",         # ball-possession (BALL_POSSESSION) ⭐ KEY FOR PRESSURE
            51: "Offsides",                  # offsides (OFFSIDES) ⭐ KEY FOR ATTACKING INTENSITY
            47: "Penalties",                 # penalties (PENALTIES) ⭐ HIGH PRESSURE SITUATIONS
            46: "Ball Safe",                 # ball-safe (BALL_SAFE)
            
            # ADDITIONAL STATS FROM DOCS
            52: "Fouls",                     # May correlate with corners
            53: "Yellow Cards",              # Pressure indicator
            54: "Red Cards",                 # Game state indicator
            55: "Throw Ins",                 # Often lead to corners
            56: "Free Kicks",                # Can lead to corner situations
            57: "Goal Kicks",                # Defensive clearances
            58: "Crosses",                   # Directly related to corners
            59: "Dribbles",                  # Attacking actions
            60: "Interceptions",             # Defensive actions
            
            # WHAT WE'VE DISCOVERED SO FAR
            84: "Big Chances Missed",        # Confirmed from our testing
            86: "Saves (Likely)",           # Pattern analysis suggests this
        }
        
        print(f"\n🎯 ENHANCED STATISTICS ANALYSIS:")
        print("=" * 90)
        
        all_type_ids = set(home_stats.keys()) | set(away_stats.keys())
        
        # First show what we have available
        print(f"📍 ALL AVAILABLE STATISTICS:")
        print("   " + "-" * 70)
        for type_id in sorted(all_type_ids):
            home_val = home_stats.get(type_id, 0)
            away_val = away_stats.get(type_id, 0)
            total_val = home_val + away_val
            stat_name = official_stat_mapping.get(type_id, f"Unknown Type {type_id}")
            print(f"   📊 {stat_name:<25} | Type {type_id:<3} | Home: {home_val:<3} | Away: {away_val:<3} | Total: {total_val}")
        
        # Categorize stats for corner prediction
        corner_indicators = [34, 49, 50, 58]  # Direct corner predictors
        pressure_indicators = [45, 51, 47, 43, 44, 59]  # Attacking pressure
        tempo_indicators = [42, 41, 55, 56, 57]  # Game tempo & set pieces
        
        print(f"\n📍 DIRECT CORNER PREDICTION INDICATORS:")
        print("   " + "-" * 70)
        corner_score = 0
        corners_available = 0
        
        for type_id in corner_indicators:
            if type_id in all_type_ids:
                home_val = home_stats.get(type_id, 0)
                away_val = away_stats.get(type_id, 0)
                total_val = home_val + away_val
                stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                print(f"   ✅ {stat_name:<25} | Home: {home_val:<3} | Away: {away_val:<3} | Total: {total_val}")
                corners_available += 1
                
                # Scoring system for corner prediction
                if type_id == 34:  # Corners
                    corner_score += total_val * 3  # Weight corners heavily
                elif type_id == 49:  # Shots inside box
                    corner_score += total_val * 2  # High correlation with corners
                elif type_id == 50:  # Shots outside box  
                    corner_score += total_val * 0.5  # Lower correlation
                elif type_id == 58:  # Shots blocked
                    corner_score += total_val * 1.5  # Direct correlation
            else:
                stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                print(f"   ❌ {stat_name:<25} | NOT AVAILABLE")
        
        print(f"\n🔥 ATTACKING PRESSURE INDICATORS:")
        print("   " + "-" * 70)
        pressure_score = 0
        pressure_available = 0
        
        for type_id in pressure_indicators:
            if type_id in all_type_ids:
                home_val = home_stats.get(type_id, 0)
                away_val = away_stats.get(type_id, 0)
                total_val = home_val + away_val
                stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                print(f"   ✅ {stat_name:<25} | Home: {home_val:<3} | Away: {away_val:<3} | Total: {total_val}")
                pressure_available += 1
                
                # Scoring system for pressure
                if type_id == 51:  # Offsides
                    pressure_score += total_val * 2  # High attacking intensity
                elif type_id == 45:  # Possession
                    pressure_score += abs(home_val - away_val) * 0.3  # Possession imbalance creates pressure
                elif type_id in [43, 44]:  # Attacks
                    pressure_score += total_val * 0.1  # Scale down large numbers
                elif type_id == 59:  # Dribbles
                    pressure_score += total_val * 0.8
            else:
                stat_name = official_stat_mapping.get(type_id, f"Type {type_id}")
                print(f"   ❌ {stat_name:<25} | NOT AVAILABLE")
        
        # ENHANCED CORNER PREDICTION ALGORITHM
        print(f"\n🎯 ENHANCED LATE CORNER PREDICTION:")
        print("=" * 90)
        
        # Calculate stats availability
        total_key_stats = len(corner_indicators) + len(pressure_indicators)
        available_key_stats = corners_available + pressure_available
        data_quality = (available_key_stats / total_key_stats) * 100
        
        print(f"   📊 Data Quality: {data_quality:.1f}% ({available_key_stats}/{total_key_stats} key stats available)")
        print(f"   📊 Corner Score: {corner_score:.1f}")
        print(f"   🔥 Pressure Score: {pressure_score:.1f}")
        
        # Calculate weighted score with data quality factor
        base_score = corner_score + (pressure_score * 0.4)
        quality_adjusted_score = base_score * (data_quality / 100)
        
        print(f"   🎯 BASE SCORE: {base_score:.1f}")
        print(f"   🎯 QUALITY-ADJUSTED SCORE: {quality_adjusted_score:.1f}")
        
        if minute >= 70:
            if quality_adjusted_score >= 20:
                print(f"   🟢 EXCELLENT corner opportunity! (Score: {quality_adjusted_score:.1f})")
                print(f"   💰 STRONG BUY recommendation for corner bets")
            elif quality_adjusted_score >= 12:
                print(f"   🟡 GOOD corner opportunity (Score: {quality_adjusted_score:.1f})")
                print(f"   💡 MODERATE BUY recommendation")
            elif quality_adjusted_score >= 6:
                print(f"   🟠 FAIR corner opportunity (Score: {quality_adjusted_score:.1f})")
                print(f"   ⚠️ WEAK BUY - proceed with caution")
            else:
                print(f"   🔴 POOR corner opportunity (Score: {quality_adjusted_score:.1f})")
                print(f"   ❌ AVOID - low corner potential")
        else:
            print(f"   ⏰ Match at {minute}' - wait until 70+ minutes")
            print(f"   📈 Current trajectory score: {quality_adjusted_score:.1f}")
    
    else:
        print("❌ No statistics found")

else:
    print("❌ No fixture data returned") 