#!/usr/bin/env python3

"""
Test script for Sportmonks API connection
Run this to verify your Sportmonks API setup is working
"""

import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Loaded .env file")
    else:
        print("❌ No .env file found!")
        sys.exit(1)
except ImportError:
    print("Installing python-dotenv...")
    import os
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

def test_sportmonks():
    try:
        from sportmonks_client import SportmonksClient
        
        print("🧪 Testing Sportmonks API connection...")
        
        client = SportmonksClient()
        
        # Test 1: Get ALL live matches first
        print("📡 Testing live matches endpoint (ALL matches)...")
        all_live_matches = client.get_live_matches(filter_by_minute=False)
        
        if all_live_matches is not None:
            print(f"✅ Live matches API working - found {len(all_live_matches)} total live matches")
            
            # Test 2: Get filtered matches
            print("🔍 Testing filtered matches (70+ minutes)...")
            filtered_matches = client.get_live_matches(filter_by_minute=True)
            print(f"📊 Found {len(filtered_matches)} matches past 70 minutes")
            
            if len(all_live_matches) > 0:
                print("\n📋 Sample live matches:")
                for i, match in enumerate(all_live_matches[:5]):  # Show first 5
                    fixture_id = match.get('id', 'Unknown')
                    
                    # Use proper extraction methods 
                    minute = client._extract_minute(match)
                    state = client._extract_state(match)
                    home_team, away_team = client._extract_teams(match)
                    home_score, away_score = client._extract_score(match)
                    
                    print(f"   {i+1}. {home_team} vs {away_team}")
                    print(f"       Score: {home_score}-{away_score} | Minute: {minute}' | State: {state}")
                    print(f"       ID: {fixture_id}")
                    
                    if minute >= 80:  # Highlight late matches
                        print(f"       🎯 ← LATE MATCH FOR CORNER SYSTEM!")
                    print()
                
                # Test 3: Get detailed stats for first match if available
                if len(all_live_matches) > 0:
                    test_fixture_id = all_live_matches[0]['id']
                    print(f"\n📈 Testing fixture stats for match {test_fixture_id}...")
                    
                    match_stats = client.get_fixture_stats(test_fixture_id)
                    if match_stats:
                        print("✅ Fixture stats API working")
                        print(f"   Score: {match_stats.home_score}-{match_stats.away_score}")
                        print(f"   Minute: {match_stats.minute}")
                        print(f"   Total corners: {match_stats.total_corners}")
                        print(f"   Shots on target: {match_stats.shots_on_target}")
                    else:
                        print("⚠️ Fixture stats returned no data (this may be normal)")
                
                # Test 4: Try to get odds (may not be available for all matches)
                print(f"\n💰 Testing odds API for match {test_fixture_id}...")
                odds = client.get_live_corner_odds(test_fixture_id)
                if odds:
                    print("✅ Live odds API working")
                    print(f"   Found {len(odds)} corner betting markets")
                else:
                    print("⚠️ No live corner odds available (this is normal if no corner markets)")
                
            else:
                print("⚠️ No live matches found at the moment")
                print("   This is normal if no matches are currently live")
            
            return True
        else:
            print("❌ Failed to get live matches")
            return False
            
    except Exception as e:
        print(f"❌ Sportmonks API test error: {e}")
        
        # Check common issues
        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n💡 This looks like an API key issue:")
            print("   - Check your SPORTMONKS_API_KEY in .env file")
            print("   - Make sure your API key is active")
            print("   - Verify you have the right subscription plan")
        elif "403" in str(e) or "Forbidden" in str(e):
            print("\n💡 This looks like a subscription issue:")
            print("   - Check that your plan includes Live Scores API")
            print("   - Verify your API key has access to football data")
        elif "429" in str(e) or "rate limit" in str(e).lower():
            print("\n💡 This looks like a rate limiting issue:")
            print("   - You may be making too many requests")
            print("   - Try again in a few minutes")
        
        return False

if __name__ == "__main__":
    result = test_sportmonks()
    
    if result:
        print("\n🎉 Sportmonks API setup is working!")
        print("✅ Ready to monitor live matches")
    else:
        print("\n❌ Sportmonks API setup failed.")
        print("Check your API key and subscription plan.")
        sys.exit(1) 