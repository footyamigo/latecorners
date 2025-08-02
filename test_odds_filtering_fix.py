#!/usr/bin/env python3
"""
Test the critical fix for odds filtering - ensuring we ONLY send alerts
when whole number corner odds are available (no .5 odds).
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_telegram_system import NewTelegramSystem

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_odds_filtering():
    print("🧪 TESTING ODDS FILTERING FIX")
    print("="*60)
    
    # Mock telegram credentials for testing
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_12345'
    os.environ['TELEGRAM_CHAT_ID'] = 'test_chat_id'
    
    telegram = NewTelegramSystem()
    
    # Override the _send_http_message to just return True for testing
    original_send = telegram._send_http_message
    telegram._send_http_message = lambda message: True
    
    # Test 1: Match with NO whole number odds (should NOT send alert)
    print("\n📋 TEST 1: Match with ONLY .5 odds (should SKIP alert)")
    match_data_no_whole_odds = {
        'fixture_id': 123456,
        'minute': 85,
        'home_team': 'Test Team A',
        'away_team': 'Test Team B', 
        'home_score': 1,
        'away_score': 0,
        'corners': 9,
        'active_odds': [
            'Over 9.5 = 1.85',  # .5 odds
            'Under 9.5 = 1.95', # .5 odds
            'Over 10.5 = 2.25', # .5 odds
            'Under 10.5 = 1.62' # .5 odds
        ]
    }
    
    result1 = telegram.send_alert(match_data_no_whole_odds, "ELITE", 15.0, [])
    print(f"🎯 RESULT 1: Alert sent = {result1} (should be False)")
    print(f"   Expected: False (no whole number odds)")
    print(f"   Actual: {result1}")
    
    # Test 2: Match with whole number odds (should send alert)
    print("\n📋 TEST 2: Match with whole number odds (should SEND alert)")
    match_data_with_whole_odds = {
        'fixture_id': 123457,
        'minute': 85,
        'home_team': 'Test Team C',
        'away_team': 'Test Team D',
        'home_score': 2,
        'away_score': 1,
        'corners': 8,
        'active_odds': [
            'Over 9 = 1.85',    # Whole number!
            'Under 9 = 1.95',   # Whole number!
            'Over 10 = 2.25',   # Whole number!
            'Under 10 = 1.62'   # Whole number!
        ]
    }
    
    result2 = telegram.send_alert(match_data_with_whole_odds, "ELITE", 15.0, [])
    print(f"🎯 RESULT 2: Alert sent = {result2} (should be True)")
    print(f"   Expected: True (whole number odds available)")
    print(f"   Actual: {result2}")
    
    # Test 3: Match with MIX of .5 and whole number odds (should send alert)
    print("\n📋 TEST 3: Match with MIX of .5 and whole number odds (should SEND alert)")
    match_data_mixed_odds = {
        'fixture_id': 123458,
        'minute': 85,
        'home_team': 'Test Team E',
        'away_team': 'Test Team F',
        'home_score': 0,
        'away_score': 0,
        'corners': 7,
        'active_odds': [
            'Over 8.5 = 1.85',  # .5 odds (filtered out)
            'Over 9 = 1.75',    # Whole number! (included)
            'Under 9 = 2.05',   # Whole number! (included)
            'Over 10.5 = 2.25'  # .5 odds (filtered out)
        ]
    }
    
    result3 = telegram.send_alert(match_data_mixed_odds, "ELITE", 15.0, [])
    print(f"🎯 RESULT 3: Alert sent = {result3} (should be True)")
    print(f"   Expected: True (some whole number odds available)")
    print(f"   Actual: {result3}")
    
    # Test 4: Match with NO odds at all (should NOT send alert)
    print("\n📋 TEST 4: Match with NO odds at all (should SKIP alert)")
    match_data_no_odds = {
        'fixture_id': 123459,
        'minute': 85,
        'home_team': 'Test Team G',
        'away_team': 'Test Team H',
        'home_score': 1,
        'away_score': 2,
        'corners': 12,
        'active_odds': []  # No odds
    }
    
    result4 = telegram.send_alert(match_data_no_odds, "ELITE", 15.0, [])
    print(f"🎯 RESULT 4: Alert sent = {result4} (should be False)")
    print(f"   Expected: False (no odds available)")
    print(f"   Actual: {result4}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY:")
    print(f"   Test 1 (only .5 odds): {'✅ PASS' if result1 == False else '❌ FAIL'}")
    print(f"   Test 2 (whole odds): {'✅ PASS' if result2 == True else '❌ FAIL'}")
    print(f"   Test 3 (mixed odds): {'✅ PASS' if result3 == True else '❌ FAIL'}")
    print(f"   Test 4 (no odds): {'✅ PASS' if result4 == False else '❌ FAIL'}")
    
    all_passed = (result1 == False and result2 == True and result3 == True and result4 == False)
    print(f"\n🎯 OVERALL: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("🎉 The fix works! We now only send alerts when whole number odds are available!")
    else:
        print("🚨 Something is still wrong with the odds filtering logic!")
    
    # Clean up environment
    if 'TELEGRAM_BOT_TOKEN' in os.environ:
        del os.environ['TELEGRAM_BOT_TOKEN']
    if 'TELEGRAM_CHAT_ID' in os.environ:
        del os.environ['TELEGRAM_CHAT_ID']

if __name__ == "__main__":
    test_odds_filtering() 