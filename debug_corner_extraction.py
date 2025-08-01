#!/usr/bin/env python3
"""
Debug Corner Extraction
======================
Check what SportMonks actually returns for corner statistics.
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def debug_corner_statistics(fixture_id):
    """Debug what SportMonks returns for corner statistics"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    # Get fixture with statistics
    url = f'https://api.sportmonks.com/v3/football/fixtures/{fixture_id}'
    params = {
        'api_token': api_key,
        'include': 'statistics'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('data'):
            fixture = data['data']
            
            print(f"🔍 FIXTURE {fixture_id} DEBUG")
            print("="*50)
            
            # Check basic info
            print(f"📅 Starting at: {fixture.get('starting_at')}")
            print(f"📊 State: {fixture.get('state')}")
            
            # Debug statistics structure
            statistics = fixture.get('statistics', [])
            print(f"\n📊 STATISTICS ({len(statistics)} total):")
            
            if not statistics:
                print("   ❌ No statistics found")
                return
            
            # Show all statistics types
            print("\n📋 ALL STATISTIC TYPES:")
            for i, stat in enumerate(statistics):
                type_info = stat.get('type', {})
                type_id = type_info.get('id') if isinstance(type_info, dict) else stat.get('type_id')
                type_name = type_info.get('name') if isinstance(type_info, dict) else 'Unknown'
                
                print(f"   {i}: Type ID {type_id} - {type_name}")
                print(f"      Full stat: {json.dumps(stat, indent=6)}")
                print()
                
                # Look specifically for corner statistics
                if type_id == 34:
                    print(f"   🏆 CORNER STATISTIC FOUND!")
                    print(f"      Structure: {json.dumps(stat, indent=6)}")
                    
                    # Try different ways to extract value
                    value1 = stat.get('data', {}).get('value')
                    value2 = stat.get('value')
                    participant_id = stat.get('participant_id')
                    
                    print(f"      value via data.value: {value1}")
                    print(f"      value via direct: {value2}")
                    print(f"      participant_id: {participant_id}")
                    print()
            
            return statistics
                    
        else:
            print("❌ No fixture data found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test with one of the recently processed matches
    fixture_id = 19428967  # Independiente Medellín vs Jaguares
    debug_corner_statistics(fixture_id) 