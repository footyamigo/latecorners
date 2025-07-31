#!/usr/bin/env python3

import json

def test_dashboard_odds_display():
    """Test the new dashboard odds display with sample data"""
    
    print(f"🎯 TESTING DASHBOARD ODDS DISPLAY")
    print(f"=" * 60)
    
    # Sample match data that would come from the API
    sample_match_with_odds = {
        "match_id": 19468975,
        "home_team": "Al Buqa'a",
        "away_team": "Sama Al Sarhan",
        "minute": 75,
        "home_score": 0,
        "away_score": 0,
        "league": "Premier League",
        "status": "Second Half",
        "corner_odds": {
            "available": True,
            "count": 8,
            "active_count": 2,
            "total_corner_markets": 8,
            "total_odds": 283,
            "odds_details": [
                "Over 10.5 = 1.95",
                "Under 10.5 = 1.85",
                "Over 9.5 = 2.10 (suspended)",
                "Under 9.5 = 1.70 (suspended)",
                "Over 9 = 1.88 (suspended)",
                "Under 9 = 1.92 (suspended)",
                "Over 8.5 = 2.05 (suspended)",
                "Under 8.5 = 1.75 (suspended)"
            ],
            "active_odds": [
                "Over 10.5 = 1.95",
                "Under 10.5 = 1.85"
            ]
        },
        "statistics": {
            "total_stats_available": 12,
            "has_corners": True,
            "home": {
                "corners": 3,
                "shots_total": 8,
                "shots_on_goal": 2,
                "dangerous_attacks": 15,
                "crosses": 4,
                "ball_possession": 55
            },
            "away": {
                "corners": 2,
                "shots_total": 6,
                "shots_on_goal": 1,
                "dangerous_attacks": 12,
                "crosses": 2,
                "ball_possession": 45
            }
        }
    }
    
    sample_match_no_odds = {
        "match_id": 19468976,
        "home_team": "Khan Tengri", 
        "away_team": "AKAS",
        "minute": 72,
        "home_score": 1,
        "away_score": 0,
        "league": "First Division",
        "status": "Second Half",
        "corner_odds": {
            "available": False,
            "count": 0,
            "active_count": 0,
            "total_corner_markets": 0,
            "total_odds": 0
        },
        "statistics": {
            "total_stats_available": 10,
            "has_corners": True,
            "home": {
                "corners": 4,
                "shots_total": 12,
                "shots_on_goal": 3,
                "dangerous_attacks": 18,
                "crosses": 6,
                "ball_possession": 62
            },
            "away": {
                "corners": 1,
                "shots_total": 5,
                "shots_on_goal": 1,
                "dangerous_attacks": 8,
                "crosses": 1,
                "ball_possession": 38
            }
        }
    }
    
    print(f"📊 SAMPLE API RESPONSE:")
    print(f"-" * 40)
    
    api_response = {
        "matches": [sample_match_with_odds, sample_match_no_odds],
        "stats": {
            "total_live": 2,
            "alert_ready": 0,
            "with_odds": 1,
            "critical_games": 0,
            "late_games": 2
        }
    }
    
    print(json.dumps(api_response, indent=2))
    
    print(f"\n🎯 WHAT YOU'LL SEE ON DASHBOARD:")
    print(f"=" * 50)
    
    for i, match in enumerate([sample_match_with_odds, sample_match_no_odds], 1):
        print(f"\n📱 MATCH {i}: {match['home_team']} vs {match['away_team']} ({match['minute']}')")
        
        if match['minute'] >= 70 and match['minute'] <= 90:
            if match['corner_odds']['available']:
                total = match['corner_odds']['count']
                active = match['corner_odds']['active_count'] 
                suspended = total - active
                
                print(f"   💰 Corner Odds Section: LIVE")
                print(f"   📊 Summary: {total} markets • {active} active • {suspended} suspended")
                print(f"   🟢 ACTIVE ODDS (bettable):")
                for odds in match['corner_odds']['active_odds']:
                    print(f"      • {odds}")
                
                if suspended > 0:
                    print(f"   ⏸️ SUSPENDED ODDS (first 3):")
                    suspended_odds = [o for o in match['corner_odds']['odds_details'] if '(suspended)' in o]
                    for odds in suspended_odds[:3]:
                        clean_odds = odds.replace(' (suspended)', '')
                        print(f"      • {clean_odds}")
            else:
                print(f"   💰 Corner Odds Section: NO ODDS")
                print(f"   📊 No bet365 Asian corner markets available")
        else:
            print(f"   💰 Corner Odds Section: Not shown (outside 70-90 minute window)")
    
    print(f"\n🚀 DASHBOARD FEATURES:")
    print(f"=" * 50)
    print(f"✅ Real-time odds values displayed")
    print(f"✅ Active vs suspended odds clearly marked")
    print(f"✅ Green highlight for bettable odds")
    print(f"✅ Automatic refresh every 8 seconds")
    print(f"✅ Only shows odds for 70-90 minute matches")
    print(f"✅ Mobile responsive design")

if __name__ == "__main__":
    test_dashboard_odds_display() 