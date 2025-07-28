import os
import requests
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

def test_available_live_stats():
    """Test what live statistics are actually available in current matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 TESTING AVAILABLE LIVE STATISTICS")
    print("=" * 60)
    
    # Get live matches with statistics
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;statistics'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        matches = response.json().get('data', [])
        print(f"📊 Retrieved {len(matches)} inplay matches")
        
        # Filter for truly live matches with ticking
        live_matches = []
        for match in matches:
            periods = match.get('periods', [])
            has_ticking = any(period.get('ticking', False) for period in periods)
            if has_ticking:
                live_matches.append(match)
        
        print(f"⚽ Found {len(live_matches)} truly live matches")
        
        # Analyze all available stat types
        stat_type_counts = defaultdict(int)
        stat_examples = defaultdict(list)
        
        for match in live_matches:
            statistics = match.get('statistics', [])
            
            for stat in statistics:
                type_id = stat.get('type_id')
                value = stat.get('data', {}).get('value', 0)
                location = stat.get('location', 'unknown')
                
                if type_id and value > 0:  # Only count non-zero stats
                    stat_type_counts[type_id] += 1
                    
                    if len(stat_examples[type_id]) < 3:  # Keep first 3 examples
                        # Get team names for context
                        participants = match.get('participants', [])
                        home_team = away_team = "Unknown"
                        
                        for participant in participants:
                            meta = participant.get('meta', {})
                            p_location = meta.get('location', 'unknown')
                            name = participant.get('name', 'Unknown')
                            
                            if p_location == 'home':
                                home_team = name.split(' ')[0]  # First word only
                            elif p_location == 'away':
                                away_team = name.split(' ')[0]
                        
                        stat_examples[type_id].append({
                            'teams': f"{home_team} vs {away_team}",
                            'location': location,
                            'value': value
                        })
        
        print(f"\n📈 LIVE STATISTICS ANALYSIS:")
        print(f"Found {len(stat_type_counts)} different stat types with non-zero values")
        
        # Known stat mapping
        known_stats = {
            34: 'Corners',
            42: 'Shots Total',  
            41: 'Shots on Goal',
            44: 'Dangerous Attacks',
            49: 'Shots Inside Box',
            60: 'Crosses',
            45: 'Ball Possession',
            46: 'Shots Blocked',
            47: 'Fouls',
            52: 'Throw Ins',
            53: 'Free Kicks',
            54: 'Offsides',
            55: 'Corner Kicks',
            56: 'Goal Kicks'
        }
        
        # Sort by frequency (most common first)
        sorted_stats = sorted(stat_type_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n📊 STAT TYPES BY FREQUENCY:")
        for type_id, count in sorted_stats:
            name = known_stats.get(type_id, f"Unknown Type {type_id}")
            examples = stat_examples[type_id]
            
            print(f"\n🔸 Type {type_id}: {name}")
            print(f"   📈 Found in {count} match instances")
            print(f"   📋 Examples:")
            
            for example in examples:
                print(f"      {example['teams']} | {example['location']}: {example['value']}")
        
        # Check for unknown stat types
        unknown_types = [type_id for type_id in stat_type_counts.keys() if type_id not in known_stats]
        
        if unknown_types:
            print(f"\n🔍 UNKNOWN STAT TYPES TO INVESTIGATE:")
            for type_id in sorted(unknown_types):
                count = stat_type_counts[type_id]
                examples = stat_examples[type_id][:2]  # Show first 2
                print(f"   Type {type_id}: {count} instances")
                for example in examples:
                    print(f"      {example['teams']} | {example['location']}: {example['value']}")
        
        # Summary for corner betting
        corner_relevant = [34, 42, 41, 44, 49, 60, 47, 54]  # Most relevant for corners
        available_relevant = [t for t in corner_relevant if t in stat_type_counts]
        
        print(f"\n🎯 CORNER BETTING RELEVANT STATS:")
        print(f"   Available: {len(available_relevant)}/{len(corner_relevant)} types")
        
        for type_id in available_relevant:
            name = known_stats[type_id]
            count = stat_type_counts[type_id]
            print(f"   ✅ {name} (Type {type_id}): {count} instances")
        
        missing_relevant = [t for t in corner_relevant if t not in stat_type_counts]
        if missing_relevant:
            print(f"\n❌ MISSING RELEVANT STATS:")
            for type_id in missing_relevant:
                name = known_stats[type_id]
                print(f"   ❌ {name} (Type {type_id}): Not available")
        
        return stat_type_counts
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

if __name__ == "__main__":
    test_available_live_stats() 