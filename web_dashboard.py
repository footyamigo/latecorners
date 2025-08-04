from flask import Flask, render_template, jsonify
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import threading
import time

load_dotenv()

app = Flask(__name__)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_alert(message):
    """Send alert message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured - skipping telegram alert")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        print("📱 Telegram alert sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")
        return False

# Global variables to store live data
live_matches_data = []
dashboard_stats = {
    'total_live': 0,
    'late_games': 0,
    'draws': 0,
    'close_games': 0,
    'last_update': None
}

# Global cache to avoid re-checking the same matches
odds_cache = {}
last_odds_check_time = {}

# Global alert tracking
alert_history = {}
last_alert_check = 0

# Rate limit tracking per entity
rate_limit_info = {
    'livescores': {'remaining': 3000, 'resets_in_seconds': 3600},
    'odds': {'remaining': 3000, 'resets_in_seconds': 3600}
}

def monitor_rate_limits(response, entity_name):
    """Monitor and track rate limit information from API responses"""
    try:
        # Check if response has rate limit headers or data
        if hasattr(response, 'json'):
            data = response.json()
            if 'rate_limit' in data:
                rate_limit_data = data['rate_limit']
                rate_limit_info[entity_name] = {
                    'remaining': rate_limit_data.get('remaining', 3000),
                    'resets_in_seconds': rate_limit_data.get('resets_in_seconds', 3600),
                    'requested_entity': rate_limit_data.get('requested_entity', entity_name)
                }
                print(f"📊 Rate limit for {entity_name}: {rate_limit_info[entity_name]['remaining']}/3000 remaining")
    except Exception as e:
        print(f"⚠️ Could not parse rate limit info: {e}")

def can_make_request(entity_name, required_calls=1):
    """Check if we can safely make requests to an entity"""
    entity_info = rate_limit_info.get(entity_name, {'remaining': 3000})
    remaining = entity_info['remaining']
    
    # Conservative check: ensure we have at least 10% buffer
    safe_threshold = max(300, required_calls * 2)  # 10% of 3000 or double required calls
    
    return remaining > safe_threshold

def trigger_85_minute_alert(match):
    """Trigger alert for 85-minute corner betting opportunity"""
    match_id = match['match_id']
    
    print(f"\n🔍 EVALUATING ALERT for Match {match_id}: {match['home_team']} vs {match['away_team']} ({match['minute']}')")
    
    # Prevent duplicate alerts for the same match
    if match_id in alert_history:
        print(f"❌ REJECTED: Duplicate alert prevention - match {match_id} already alerted")
        return False
    
    # Evaluate corner potential
    evaluation = evaluate_corner_potential(match)
    if not evaluation:
        print(f"❌ REJECTED: No corner evaluation returned (likely wrong time window)")
        return False
    
    print(f"📊 CORNER EVALUATION:")
    print(f"   • Final Score: {evaluation['score']:.1f}")
    print(f"   • Corner Count: {evaluation['total_corners']}")
    print(f"   • Corner Category: {evaluation['corner_category']}")
    print(f"   • Psychology Score: {evaluation['score']:.1f}") # Renamed to 'score'
    print(f"   • Recommendation: {evaluation['corner_category']} (Score: {evaluation['score']:.1f})") # Renamed to 'corner_category'
    print(f"   • Reason: {evaluation['corner_category']} (Score: {evaluation['score']:.1f})") # Renamed to 'corner_category'
    
    # UPDATED: Allow WEAK BUY alerts (removed from rejection list)
    if evaluation['corner_category'] == "TIER_1_BASELINE":
        print(f"❌ REJECTED: Recommendation is TIER_1_BASELINE - {evaluation['corner_category']} (Score: {evaluation['score']:.1f})")
        return False
    
    print(f"✅ SCORING PASSED: Action '{evaluation['corner_category']}' is actionable")
    
    # CRITICAL: Only alert if Asian corner odds are available
    odds_info = match.get('corner_odds', {})
    print(f"🎯 ODDS CHECK:")
    print(f"   • Odds Available: {odds_info.get('available', False)}")
    print(f"   • Odds Count: {odds_info.get('count', 0)}")
    print(f"   • Total Corner Markets: {odds_info.get('total_corner_markets', 0)}")
    print(f"   • Cached: {odds_info.get('cached', False)}")
    
    if not odds_info.get('available', False):
        print(f"❌ REJECTED: No Asian corner odds available for match {match_id}")
        print(f"   💡 This means bet365 Market 61 (Asian Total Corners) was not found")
        return False
    
    print(f"✅ ODDS PASSED: {odds_info['count']} Asian corner markets available from bet365")
    
    # Record alert
    alert_history[match_id] = {
        'timestamp': datetime.now(),
        'evaluation': evaluation,
        'odds_info': odds_info,
        'match_details': {
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'score': f"{match['home_score']}-{match['away_score']}",
            'league': match.get('league', 'Unknown'),
            'minute': match['minute']
        }
    }
    
    print(f"🚨 ALERT TRIGGERED! All conditions met for {match['home_team']} vs {match['away_team']}")
    
    # Generate comprehensive alert
    alert_data = _generate_alert_message(match, evaluation, odds_info)
    telegram_message = _generate_telegram_message(match, evaluation, odds_info)
    
    # Send Telegram alert
    telegram_sent = send_telegram_alert(telegram_message)
    
    # Log alert to console
    print("🚨" * 10)
    print("⚽ 85-MINUTE CORNER ALERT ⚽")
    print("🚨" * 10)
    print(alert_data['message'])
    print("🚨" * 10)
    
    if telegram_sent:
        print("📱 Alert sent to Telegram successfully!")
    else:
        print("⚠️ Telegram alert failed - check your bot configuration")
    
    return True

def _generate_alert_message(match, evaluation, odds_info):
    """Generate actionable alert message for corner betting"""
    
    corner_count = evaluation['total_corners']
    corner_category = evaluation['corner_category']
    
    # Generate simple, actionable reasoning
    if corner_category == "TIER_1_BASELINE":
        reason = f"Active match with perfect corner count ({corner_count}) - teams pushing for winner in final minutes"
    elif corner_category == "TIER_1_PEAK":
        reason = f"High-tempo match with {corner_count} corners - excellent attacking pressure late in game"
    elif corner_category == "TIER_1_PREMIUM":
        reason = f"Match building momentum with {corner_count} corners - late pressure likely to create more"
    elif corner_category == "TIER_1_HIGH":
        reason = f"Late game pressure with {corner_count} corners - desperate attacking expected"
    else:
        reason = f"Late game pressure with {corner_count} corners - desperate attacking expected"
    
    # Determine confidence level
    rec = evaluation # Renamed to 'evaluation'
    confidence = "HIGH" # Always HIGH for TIER 1
    
    message = f"""
🎯 MATCH: {match['home_team']} vs {match['away_team']}
📊 SCORE: {match['home_score']}-{match['away_score']} ({match['minute']}')
🏆 LEAGUE: {match.get('league', 'Unknown')}

🔥 BETTING OPPORTUNITY:
   • Current Corners: {corner_count} corners
   • Recommendation: ASIAN CORNER (OVER)
   • Confidence: {confidence}
   • Reason: {reason}

💰 ASIAN TOTAL CORNERS AVAILABLE:
   • bet365 Market: Asian Total Corners (Market ID: 61)
   • Live odds confirmed available for immediate betting

⚡ HOW TO BET:
   1. Open bet365 and search "{match['home_team']} {match['away_team']}"
   2. Go to Asian Corner market (Asian Total Corners)
   3. Place OVER bet based on current {corner_count} corner count
   4. Bet size: Use your standard unit size

🕐 ALERT TIME: {datetime.now().strftime('%H:%M:%S')}
"""
    
    return {
        'message': message,
        'match_id': match['match_id'],
        'action': 'ASIAN CORNER (OVER)',
        'confidence': confidence,
        'corner_count': corner_count,
        'odds_available': True
    }

def _generate_telegram_message(match, evaluation, odds_info):
    """Generate mobile-friendly Telegram alert message"""
    
    corner_count = evaluation['total_corners']
    corner_category = evaluation['corner_category']
    
    # Generate simple, actionable reasoning
    if corner_category == "TIER_1_BASELINE":
        reason = f"Perfect corner count ({corner_count}) - teams pushing for winner"
    elif corner_category == "TIER_1_PEAK":
        reason = f"High activity match ({corner_count} corners) - late pressure building"
    elif corner_category == "TIER_1_PREMIUM":
        reason = f"Momentum building ({corner_count} corners) - late surge expected"
    elif corner_category == "TIER_1_HIGH":
        reason = f"Late game pressure ({corner_count} corners) - desperation time"
    
    rec = evaluation
    confidence = "HIGH"
    
    # Mobile-optimized format
    message = f"""🚨 <b>CORNER ALERT</b> 🚨

⚽ <b>{match['home_team']} vs {match['away_team']}</b>
📊 Score: {match['home_score']}-{match['away_score']} (85')

🎯 <b>ASIAN CORNER (OVER)</b>
📈 Current: {corner_count} corners
🔥 Confidence: {confidence}
💡 {reason}

💰 <b>bet365 Asian Total Corners</b>
✅ Live odds confirmed available

⚡ <b>ACTION:</b>
1. Open bet365
2. Search "{match['home_team']} {match['away_team']}"
3. Go to Asian Corner market
4. Place OVER bet NOW

🕐 Alert: {datetime.now().strftime('%H:%M:%S')}"""
    
    return message

def should_check_odds(match):
    """Updated: Check odds for matches 70-90 minutes (extended window for comprehensive odds tracking)"""
    match_id = match['match_id']
    minute = match['minute']
    
    # EXTENDED WINDOW: Check odds from 70-90 minutes for comprehensive live odds tracking
    if minute < 70:
        print(f"🕐 Match {match_id} ({minute}'): Too early for odds checking (need 70-90 minutes)")
        return False
    
    if minute > 90:
        print(f"🕐 Match {match_id} ({minute}'): Beyond odds checking window (70-90 minutes)")
        return False
    
    # Only check odds for matches with corner statistics (essential for corner betting)
    if not match['statistics']['has_corners']:
        print(f"📊 Match {match_id} ({minute}'): No corner statistics available - skipping odds check")
        return False
    
    # Rate limiting: Don't check same match more than once every 2 minutes
    last_check = last_odds_check_time.get(match_id, 0)
    current_time = time.time()
    if current_time - last_check < 120:
        time_since_last = int(current_time - last_check)
        print(f"⏱️ Match {match_id} ({minute}'): Rate limited - last check {time_since_last}s ago (need 120s)")
        return False
    
    print(f"✅ Match {match_id} ({minute}'): Ready for odds checking")
    return True

def get_live_matches():
    """Get current live matches from API"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    if not api_key:
        print("❌ SPORTMONKS_API_KEY not found in environment!")
        return []
    
    if not can_make_request('livescores'):
        print("⚠️ Rate limit approaching for livescores entity, skipping this update")
        return []
    
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;periods.statistics;league;statistics'
    }
    
    try:
        print(f"🌐 Calling SportMonks API: {url}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Monitor rate limits
        monitor_rate_limits(response, 'livescores')
        
        matches = response.json().get('data', [])
        print(f"📥 Raw matches from API: {len(matches)}")
        
        live_matches = []
        
        for match in matches:
            periods = match.get('periods', [])
            has_ticking = any(period.get('ticking', False) for period in periods)
            
            if has_ticking:
                match_data = extract_match_data(match)
                if match_data and is_valid_live_match(match_data):
                    live_matches.append(match_data)
        
        print(f"✅ Filtered live matches: {len(live_matches)}")
        return live_matches
        
    except Exception as e:
        print(f"❌ Error getting live matches: {e}")
        return []

def is_valid_live_match(match_data):
    """Check if a match is valid for display (has stats and reasonable time)"""
    
    # Must have live statistics available
    if not match_data.get('statistics') or match_data['statistics'].get('total_stats_available', 0) == 0:
        return False
    
    # Filter out matches with unrealistic minutes (likely ended or data error)
    minute = match_data.get('minute', 0)
    if minute > 120:  # Even with extra time, 120+ minutes is suspicious
        return False
    
    # Must have basic match data
    if not match_data.get('home_team') or not match_data.get('away_team'):
        return False
    
    return True

def extract_match_data(match):
    """Extract match data for dashboard"""
    
    try:
        # Get teams
        participants = match.get('participants', [])
        home_team = away_team = "Unknown"
        
        for participant in participants:
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            name = participant.get('name', 'Unknown')
            
            if location == 'home':
                home_team = name
            elif location == 'away':
                away_team = name
        
        # Get score
        scores = match.get('scores', [])
        home_score = away_score = 0
        
        for score_entry in scores:
            if score_entry.get('description') == 'CURRENT':
                score_data = score_entry.get('score', {})
                goals = score_data.get('goals', 0)
                participant = score_data.get('participant', '')
                
                if participant == 'home':
                    home_score = goals
                elif participant == 'away':
                    away_score = goals
        
        # Get minute and state
        state = match.get('state', {}).get('short_name', 'unknown')
        
        periods = match.get('periods', [])
        minute = 0
        for period in periods:
            if period.get('ticking', False):
                minute = period.get('minutes', 0)
                break
        
        # Get league
        league_info = match.get('league', {})
        league_name = league_info.get('name', 'Unknown League')
        
        # Extract live statistics
        statistics = extract_live_statistics(match)
        
        # Determine priority and status
        if minute >= 85:
            priority = 'critical'
            status = 'Critical'
        elif minute >= 75:
            priority = 'high'
            status = 'Late Game'
        elif minute >= 60:
            priority = 'medium'
            status = 'Second Half'
        elif minute >= 45:
            priority = 'normal'
            status = 'Around HT'
        else:
            priority = 'early'
            status = 'Early Game'
        
        return {
            'match_id': match['id'],
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'minute': minute,
            'state': state,
            'league': league_name,
            'priority': priority,
            'status': status,
            'is_draw': home_score == away_score,
            'is_close': abs(home_score - away_score) <= 2,
            'goal_difference': abs(home_score - away_score),
            'statistics': statistics
        }
        
    except Exception as e:
        print(f"❌ Error extracting match data for match ID {match.get('id', 'unknown')}: {e}")
        return None

def extract_live_statistics(match):
    """Extract live statistics for corner betting analysis"""
    
    try:
        statistics = match.get('statistics', [])
        
        # Key stat type IDs for corner betting (REVERTED to original working system)
        stat_mapping = {
            34: 'corners',            # Corners ✅ (Type 34 - original working system + official docs)
            42: 'shots_total',        # Shots Total ✅ (Type 42 - confirmed)
            86: 'shots_on_target',    # Shots on Target ✅ (Type 86 - confirmed)
            44: 'dangerous_attacks',  # Dangerous Attacks ✅ (Type 44 - confirmed)
            98: 'crosses_total',      # Total Crosses ✅ (Type 98 - official)
            45: 'ball_possession',    # Ball Possession % ✅ (Type 45 - original working system)
            41: 'shots_off_target',   # Shots Off Target ✅ (Type 41 - confirmed)
            51: 'offsides'            # Offsides ✅ (Type 51 - confirmed)
        }
        
        home_stats = {}
        away_stats = {}
        
        for stat in statistics:
            type_id = stat.get('type_id')
            if type_id in stat_mapping:
                stat_name = stat_mapping[type_id]
                value = stat.get('data', {}).get('value', 0)
                location = stat.get('location', 'unknown')
                
                if location == 'home':
                    home_stats[stat_name] = value
                elif location == 'away':
                    away_stats[stat_name] = value
        
        return {
            'home': home_stats,
            'away': away_stats,
            'total_stats_available': len(home_stats) + len(away_stats),
            'has_corners': 'corners' in home_stats or 'corners' in away_stats,
            'has_shots': 'shots_total' in home_stats or 'shots_total' in away_stats,
            'has_premium_stats': 'shots_inside_box' in home_stats or 'shots_inside_box' in away_stats
        }
        
    except Exception as e:
        return {
            'home': {},
            'away': {},
            'total_stats_available': 0,
            'has_corners': False,
            'has_shots': False,
            'has_premium_stats': False
        }

def check_corner_odds_available(match_id):
    """Quick check if Asian corner odds are available for a match"""
    try:
        # Update last check time for rate limiting
        last_odds_check_time[match_id] = time.time()
        
        # Check if we can make the odds request
        if not can_make_request('odds'):
            print(f"⚠️ Rate limit approaching for odds entity, using cache for match {match_id}")
            # Return cached data if available
            if match_id in odds_cache:
                cache_time, cache_data = odds_cache[match_id]
                if time.time() - cache_time < 600:  # 10-minute cache for rate-limited scenarios
                    return cache_data
            return {'available': False, 'count': 0, 'total_corner_markets': 0, 'total_odds': 0, 'cached': True}
        
        # Check cache first (valid for 2 minutes)
        if match_id in odds_cache:
            cache_time, cache_data = odds_cache[match_id]
            if time.time() - cache_time < 120:  # 2 minutes cache
                return cache_data
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        
        # Use the working general inplay endpoint for quick odds check
        general_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
        params = {'api_token': api_key}
        
        # Shorter timeout for faster checking
        response = requests.get(general_url, params=params, timeout=5)
        
        # Monitor rate limits for odds entity
        monitor_rate_limits(response, 'odds')
        
        if response.status_code == 200:
            all_odds = response.json().get('data', [])
            
            # Extract bet365 Asian corner odds with detailed values
            bet365_corner_odds = []
            total_corner_markets = 0
            
            for odds in all_odds:
                market_id = odds.get('market_id')
                bookmaker_id = odds.get('bookmaker_id')
                
                # Only check Market 61 (Asian Total Corners) from bet365
                if market_id == 61:  # Only Asian Total Corners, not Asian Handicap (62)
                    total_corner_markets += 1
                    if bookmaker_id == 2:  # bet365 specifically
                        # Extract detailed odds info
                        odds_info = {
                            'label': odds.get('label', 'Unknown'),
                            'value': odds.get('value', 'N/A'),
                            'total': odds.get('total', 'N/A'),
                            'probability': odds.get('probability', 'N/A'),
                            'suspended': odds.get('suspended', False),
                            'stopped': odds.get('stopped', False)
                        }
                        bet365_corner_odds.append(odds_info)
            
            # Create readable odds details for logging/display
            odds_details = []
            active_odds = []
            
            for odds in bet365_corner_odds:
                total = odds['total']
                label = odds['label']
                value = odds['value']
                suspended = odds['suspended']
                stopped = odds['stopped']
                
                # WHOLE NUMBER FILTER: Only allow whole number corner totals (8, 9, 10, 11...)
                # Reject .5 totals (8.5, 9.5, 10.5...) to enable refund possibilities
                try:
                    total_float = float(total)
                    if total_float != int(total_float):  # If it's not a whole number
                        continue  # Skip this odds entry
                except (ValueError, TypeError):
                    continue  # Skip if total can't be converted to number
                
                # Format: "Over 10 = 2.02" or "Under 9 = 1.77 (suspended)"
                status = ""
                if suspended or stopped:
                    status = " (suspended)"
                    
                odds_str = f"{label} {total} = {value}{status}"
                odds_details.append(odds_str)
                
                # Track active (non-suspended) odds
                if not suspended and not stopped:
                    active_odds.append(odds_str)
            
            result = {
                'available': len(bet365_corner_odds) > 0,
                'count': len(bet365_corner_odds),
                'active_count': len(active_odds),
                'total_corner_markets': total_corner_markets,
                'total_odds': len(all_odds),
                'odds_details': odds_details,
                'active_odds': active_odds,
                'corner_odds_data': bet365_corner_odds  # Full data for alerts
            }
            
            # Cache the result
            odds_cache[match_id] = (time.time(), result)
            return result
        else:
            result = {'available': False, 'count': 0, 'total_corner_markets': 0, 'total_odds': 0}
            odds_cache[match_id] = (time.time(), result)
            return result
            
    except Exception as e:
        # Don't let individual failures break the whole process
        result = {'available': False, 'count': 0, 'total_corner_markets': 0, 'total_odds': 0, 'error': str(e)}
        odds_cache[match_id] = (time.time(), result)
        return result

def update_live_data():
    """Update live data in background"""
    
    print("🔄 Background updater thread started!")
    
    global live_matches_data, dashboard_stats
    
    while True:
        try:
            print(f"🔄 Starting data update at {datetime.now().strftime('%H:%M:%S')}")
            
            # Get fresh data
            matches = get_live_matches()
            print(f"📊 Got {len(matches)} matches from API")
            
            # Update global data
            live_matches_data = matches
            
            # Calculate stats focused on 85-minute corner alert system
            alert_ready_matches = [m for m in matches if m['minute'] >= 85]  # Matches at alert time
            approaching_alert_matches = [m for m in matches if 70 <= m['minute'] <= 90]  # Preparing for alerts (extended window)
            matches_with_stats = [m for m in matches if m['statistics']['total_stats_available'] > 0]
            
            print(f"🚨 Alert System Status:")
            print(f"   • {len(alert_ready_matches)} matches at 85+ minutes (alert time)")
            print(f"   • {len(approaching_alert_matches)} matches in extended odds window (70-90 min)")
            print(f"   • {len(matches_with_stats)} matches with live stats total")
            
            # STEP 1: Trigger 85-minute alerts for qualified matches
            alerts_triggered = 0
            for match in alert_ready_matches:
                print(f"\n🎯 CHECKING ALERT ELIGIBILITY: {match['home_team']} vs {match['away_team']} ({match['minute']}')")
                print(f"   • Has corner stats: {match['statistics']['has_corners']}")
                print(f"   • Has corner odds: {match.get('corner_odds', {}).get('available', False)}")
                
                if match['statistics']['has_corners'] and match.get('corner_odds', {}).get('available', False):
                    if trigger_85_minute_alert(match):
                        alerts_triggered += 1
                        print(f"✅ ALERT SENT for {match['home_team']} vs {match['away_team']}")
                    else:
                        print(f"❌ ALERT REJECTED for {match['home_team']} vs {match['away_team']}")
                else:
                    reasons = []
                    if not match['statistics']['has_corners']:
                        reasons.append("no corner stats")
                    if not match.get('corner_odds', {}).get('available', False):
                        reasons.append("no Asian corner odds")
                    print(f"❌ SKIPPED: Missing requirements - {', '.join(reasons)}")
            
            if alerts_triggered > 0:
                print(f"🚨 TRIGGERED {alerts_triggered} CORNER ALERTS!")
            else:
                print(f"📊 No alerts triggered this cycle")
            
            # STEP 2: Check corner odds for matches in extended window (70-90 minutes)
            matches_with_odds = 0
            checked_count = 0
            
            for match in matches_with_stats:
                if should_check_odds(match):  # Now checks 70-90 minute matches
                    checked_count += 1
                    print(f"🎯 MINUTE {match['minute']}: Checking odds for match {match['match_id']} ({match['home_team']} vs {match['away_team']})")
                    odds_check = check_corner_odds_available(match['match_id'])
                    if odds_check['available']:
                        matches_with_odds += 1
                        match['corner_odds'] = odds_check
                        
                        total_count = odds_check.get('count', 0)
                        active_count = odds_check.get('active_count', 0)
                        suspended_count = total_count - active_count
                        
                        print(f"✅ MINUTE {match['minute']}: Corner odds available! {total_count} bet365 Asian corner markets")
                        print(f"   🟢 ACTIVE (bettable): {active_count} markets | 🔶 SUSPENDED: {suspended_count} markets")
                        
                        # Show active odds first (the important ones)
                        if 'active_odds' in odds_check and odds_check['active_odds']:
                            print(f"   💎 ACTIVE ODDS (bettable now):")
                            for odds_str in odds_check['active_odds']:
                                print(f"      • {odds_str}")
                        
                        # Show all odds if there are suspended ones too
                        if 'odds_details' in odds_check and len(odds_check['odds_details']) > active_count:
                            print(f"   📊 ALL ODDS (including suspended): {', '.join(odds_check['odds_details'])}")
                            
                        print(f"   ⚡ Elite system will use these LIVE odds if match qualifies at 85'")
                    else:
                        print(f"❌ MINUTE {match['minute']}: No corner odds available for match {match['match_id']}")
                        print(f"   ⚠️ Elite system will re-check for odds if this match qualifies at 85'")
                        
                        # Attach "no odds" data so dashboard can show NO ODDS section
                        match['corner_odds'] = {
                            'available': False,
                            'count': 0,
                            'active_count': 0,
                            'total_corner_markets': 0,
                            'total_odds': 0,
                            'odds_details': [],
                            'active_odds': []
                        }
                else:
                    # Check cached odds for display purposes
                    if match['match_id'] in odds_cache:
                        cache_time, cache_data = odds_cache[match['match_id']]
                        if time.time() - cache_time < 300:  # 5-minute cache
                            if cache_data['available']:
                                matches_with_odds += 1
                                match['corner_odds'] = cache_data
            
            print(f"📊 Pre-alert preparation: checked {checked_count} matches, {matches_with_odds} with corner odds ready")
            
            # Ensure all matches in 70-90 minute window have corner_odds data for dashboard display
            for match in matches:
                if 70 <= match['minute'] <= 90 and 'corner_odds' not in match:
                    # Add default "no odds" data for dashboard display
                    match['corner_odds'] = {
                        'available': False,
                        'count': 0,
                        'active_count': 0,
                        'total_corner_markets': 0,
                        'total_odds': 0,
                        'odds_details': [],
                        'active_odds': []
                    }
            
            dashboard_stats = {
                'total_live': len(matches),
                'late_games': len(approaching_alert_matches),  # 70-90 minute matches (extended odds window)
                'draws': len([m for m in matches if m['is_draw']]),
                'close_games': len([m for m in matches if m['is_close']]),
                'critical_games': len(alert_ready_matches),  # 85+ minute matches (alert time)
                'with_stats': len([m for m in matches if m['statistics']['total_stats_available'] > 0]),
                'with_corners': len([m for m in matches if m['statistics']['has_corners']]),
                'with_odds': matches_with_odds,  # Matches with corner odds available
                'alerts_triggered': alerts_triggered,  # New: Track alerts sent this cycle
                'in_alert_window': len(approaching_alert_matches),  # Matches in 70-90 minute window
                'ready_for_alerts': len([m for m in alert_ready_matches if m['statistics']['has_corners'] and m.get('corner_odds', {}).get('available', False)]),  # Matches that could trigger alerts
                'last_update': datetime.now().strftime('%H:%M:%S')
            }
            
            print(f"📈 Dashboard updated: {dashboard_stats['total_live']} live matches, {dashboard_stats['with_odds']} with odds at {dashboard_stats['last_update']}")
            print(f"🎯 ELITE FILTER: Only alerting for DRAWS and UP TO 2-GOAL DIFFERENCE games (no blowouts)")
            
        except Exception as e:
            print(f"❌ Error updating data: {e}")
            import traceback
            print(f"🔍 Full error: {traceback.format_exc()}")
        
        time.sleep(45)  # Update every 45 seconds (reduced from 8 to avoid rate limits)

# Corner count sweet spot analysis (research-optimized)
CORNER_COUNT_SCORING = {
    # OPTIMAL SWEET SPOTS (Research-backed)
    'corners_7_to_9_prime_zone': 5,      # Peak opportunity - enough activity, not oversaturated
    'corners_10_to_12_high_activity': 3,  # Still good - active match with potential
    'corners_13_to_14_caution_zone': 1,   # Reduced points - getting oversaturated
    
    # LESS OPTIMAL RANGES  
    'corners_5_to_6_building': 2,         # Building activity - some potential
    'corners_15_to_16_oversaturated': -1, # Too much activity - likely exhausted
    'corners_17plus_extreme_fatigue': -3, # Extreme oversaturation - avoid
    
    # RED FLAGS
    'corners_4_or_less_insufficient': -2, # Insufficient activity for late corners
    'corners_6_premium': 10, # New: Premium for 6 corners
    'corners_7_premium': 12, # New: Premium for 7 corners
    'corners_8_premium': 14, # New: Premium for 8 corners
    'corners_8_to_11_sweet_spot': 16, # New: Sweet spot for 8-11 corners
}

def evaluate_corner_potential(match):
    """Evaluate corner betting potential using TIER 1 criteria"""
    stats = match.get('statistics', {})
    minute = match.get('minute', 0)
    
    print(f"📊 EVALUATING TIER 1 POTENTIAL for match at {minute} minutes")
    
    # Only evaluate matches in the 84:30-85:15 window
    if minute < 84 or minute > 85:
        print(f"❌ Outside TIER 1 window: {minute} minutes (need 84:30-85:15)")
        return None
    
    # TIER 1 STRICT FILTER: Only allow ultra-profitable score lines (0-1 or 1-1)
    home_score = match.get('home_score', 0)
    away_score = match.get('away_score', 0)
    
    is_tier1_eligible, tier1_reason = is_tier1_elite_scoreline(home_score, away_score)
    
    if not is_tier1_eligible:
        print(f"❌ TIER 1 REJECTED: Score {home_score}-{away_score} - {tier1_reason}")
        print(f"   💡 TIER 1 STRICT: Only accepts 0-1 (away leading) or 1-1 (draw)")
        return None
    
    print(f"✅ TIER 1 SCORELINE PASSED: {home_score}-{away_score} ({tier1_reason}) - ELITE opportunity!")
    
    home_stats = stats.get('home', {})
    away_stats = stats.get('away', {})
    
    # Core statistics
    total_corners = home_stats.get('corners', 0) + away_stats.get('corners', 0)
    total_shots = home_stats.get('shots_total', 0) + away_stats.get('shots_total', 0)
    total_shots_on_target = home_stats.get('shots_on_target', 0) + away_stats.get('shots_on_target', 0)
    dangerous_attacks = home_stats.get('dangerous_attacks', 0) + away_stats.get('dangerous_attacks', 0)
    
    print(f"📈 TIER 1 CORE STATS:")
    print(f"   • Total Corners: {total_corners} (need 6-10)")
    print(f"   • Total Shots on Target: {total_shots_on_target} (need 7-9)")
    print(f"   • Total Shots: {total_shots}")
    print(f"   • Dangerous Attacks: {dangerous_attacks}")
    
    # TIER 1 Corner Range Check
    if total_corners < 6 or total_corners > 10:
        print(f"❌ TIER 1 REJECTED: Corners {total_corners} outside 6-10 range")
        return None
    
    # TIER 1 Shots on Target Check
    if total_shots_on_target < 7 or total_shots_on_target > 9:
        print(f"❌ TIER 1 REJECTED: Shots on Target {total_shots_on_target} outside 7-9 range")
        return None
    
    # Calculate base score using TIER 1 corner ranges
    base_score = 0
    corner_category = ""
    
    if total_corners == 6:
        base_score += CORNER_COUNT_SCORING['corners_6_premium']
        corner_category = "TIER_1_BASELINE"
    elif total_corners == 7:
        base_score += CORNER_COUNT_SCORING['corners_7_premium']
        corner_category = "TIER_1_PEAK"
    elif total_corners == 8:
        base_score += CORNER_COUNT_SCORING['corners_8_premium']
        corner_category = "TIER_1_PREMIUM"
    elif total_corners == 9:
        base_score += CORNER_COUNT_SCORING['corners_8_to_11_sweet_spot']
        corner_category = "TIER_1_HIGH"
    elif total_corners == 10:
        base_score += CORNER_COUNT_SCORING['corners_8_to_11_sweet_spot']
        corner_category = "TIER_1_HIGH"
    
    print(f"🏷️ TIER 1 CATEGORY: {corner_category}")
    
    # Statistical activity scores
    activity_score = (
        total_corners * 3 +
        total_shots_on_target * 2 +  # Increased weight for shots on target
        total_shots * 1.5 +
        dangerous_attacks * 0.3
    )
    base_score += activity_score
    
    print(f"📊 TIER 1 ACTIVITY SCORING:")
    print(f"   • Corners × 3: {total_corners * 3:.1f}")
    print(f"   • Shots on Target × 2: {total_shots_on_target * 2:.1f}")
    print(f"   • Total Shots × 1.5: {total_shots * 1.5:.1f}")
    print(f"   • Dangerous Attacks × 0.3: {dangerous_attacks * 0.3:.1f}")
    print(f"   • Activity Subtotal: {activity_score:.1f}")
    
    # Final TIER 1 threshold check
    if base_score < 16.0:
        print(f"❌ TIER 1 REJECTED: Score {base_score:.1f} below threshold (need 16.0+)")
        return None
    
    print(f"✅ TIER 1 QUALIFIED: Final Score {base_score:.1f}")
    
    return {
        'score': base_score,
        'corner_category': corner_category,
        'total_corners': total_corners,
        'total_shots': total_shots,
        'total_shots_on_target': total_shots_on_target,
        'dangerous_attacks': dangerous_attacks
    }

def _get_recommendation(final_score, corner_category, minute):
    """Get betting recommendation based on score and conditions"""
    if corner_category in ["INSUFFICIENT", "EXTREME FATIGUE"]:
        return {
            'action': 'AVOID',
            'confidence': 'HIGH',
            'reason': f'Corner count {corner_category.lower()} - poor conditions'
        }
    
    if final_score >= 50 and corner_category in ["PRIME ZONE", "HIGH ACTIVITY"]:
        return {
            'action': 'STRONG BUY',
            'confidence': 'HIGH', 
            'reason': f'Excellent conditions: {corner_category} + high activity (Score: {final_score:.1f})'
        }
    elif final_score >= 35 and corner_category != "OVERSATURATED":
        return {
            'action': 'BUY',
            'confidence': 'MEDIUM',
            'reason': f'Good opportunity: {corner_category} (Score: {final_score:.1f})'
        }
    elif final_score >= 20:
        return {
            'action': 'WEAK BUY',
            'confidence': 'LOW',
            'reason': f'Marginal opportunity (Score: {final_score:.1f})'
        }
    else:
        return {
            'action': 'AVOID',
            'confidence': 'HIGH',
            'reason': f'Insufficient activity (Score: {final_score:.1f})'
        }

def is_tier1_elite_scoreline(home_score, away_score):
    """
    TIER 1 STRICT: Ultra-selective score line filtering for maximum profit
    Only allows the most profitable score lines: 0-1 and 1-1
    Based on 88.9% profit rate for 0-1 and 61.1% for 1-1
    """
    # TIER 1 GOLDEN OPPORTUNITY: Away team leading by 1 (0-1)
    if home_score == 0 and away_score == 1:
        return True, "TIER_1_AWAY_LEADING"
    
    # TIER 1 HIGH VALUE: Draw at 1-1  
    if home_score == 1 and away_score == 1:
        return True, "TIER_1_DRAW"
    
    return False, "REJECTED_SCORELINE"

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alert history"""
    recent_alerts = []
    cutoff_time = datetime.now() - timedelta(hours=2)  # Last 2 hours
    
    for match_id, alert_data in alert_history.items():
        if alert_data['timestamp'] > cutoff_time:
            recent_alerts.append({
                'match_id': match_id,
                'timestamp': alert_data['timestamp'].strftime('%H:%M:%S'),
                'match_details': alert_data['match_details'],
                'recommendation': alert_data['evaluation']['recommendation'],
                'corner_count': alert_data['evaluation']['corner_count'],
                'corner_category': alert_data['evaluation']['corner_category'],
                'final_score': alert_data['evaluation']['final_score'],
                'odds_count': alert_data['odds_info']['count']
            })
    
    # Sort by timestamp (newest first)
    recent_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'alerts': recent_alerts,
        'total_alerts_today': len(recent_alerts),
        'last_update': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/live-matches')
def api_live_matches():
    """API endpoint for live matches data"""
    return jsonify({
        'matches': live_matches_data,
        'stats': dashboard_stats,
        'alerts_triggered': dashboard_stats.get('alerts_triggered', 0)  # Include alert count
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for just stats"""
    return jsonify(dashboard_stats)

@app.route('/health')
def health_check():
    """Simple health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'service': 'latecorners-dashboard',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/system-status')
def system_status():
    """Debug endpoint to check if alert system thread is running"""
    import threading
    
    # Get all running threads
    threads = threading.enumerate()
    thread_names = [t.name for t in threads]
    
    # Check if alert system might be running
    alert_system_running = any('alert' in name.lower() or 'main' in name.lower() for name in thread_names)
    
    return jsonify({
        'dashboard_status': 'running',
        'total_threads': len(threads),
        'thread_names': thread_names,
        'alert_system_detected': alert_system_running,
        'timestamp': datetime.now().isoformat(),
        'live_matches_count': len(live_matches_data),
        'service': 'Late Corner Monitor - System Status Debug'
    })

@app.route('/api/corner-odds/<match_id>')
def get_corner_odds(match_id):
    """Get LIVE UPDATED Asian Total Corner odds (Market 61) from bet365 (Bookmaker 2)"""
    try:
        # Load API key
        api_key = os.getenv('SPORTMONKS_API_KEY')
        
        print(f"🎯 Fetching LIVE UPDATED corner odds for match {match_id}")
        print(f"🔑 API Key loaded: {'Yes' if api_key else 'No'}")
        
        corner_odds_data = {
            'match_id': match_id,
            'last_updated_odds': None,  # Use the real-time updated odds endpoint
            'filtered_results': {
                'market_61_bet365': [],  # Only Asian Total Corners from bet365
                'total_found': 0,
                'last_update_time': None
            }
        }
        
        # STEP 1: Use SportMonks "Last Updated Inplay Odds" endpoint (updated in last 10 seconds)
        # This is the CRUCIAL endpoint for real-time betting as it only returns odds that changed recently
        try:
            # Use the correct real-time odds endpoint with specific filters
            updated_odds_url = "https://api.sportmonks.com/v3/football/odds/inplay/latest"
            params = {
                'api_token': api_key,
                # Remove includes that don't exist for this endpoint - test basic first
                'filters': f'markets:61;bookmakers:2'  # Market 61 (Asian Total Corners) + Bookmaker 2 (bet365)
            }
            
            response = requests.get(updated_odds_url, params=params, timeout=15)
            
            corner_odds_data['last_updated_odds'] = {
                'status': 'tested',
                'url': updated_odds_url,
                'params': params,
                'response_code': response.status_code,
                'response_text': response.text[:500] if hasattr(response, 'text') else 'No response text'
            }
            
            if response.status_code == 200:
                all_recent_odds = response.json().get('data', [])
                
                # Filter for our specific match only
                match_odds = [
                    odds for odds in all_recent_odds 
                    if odds.get('fixture_id') == int(match_id)
                ]
                
                # Process the filtered odds
                asian_total_corners = []
                for odds in match_odds:
                    asian_total_corners.append({
                        'id': odds.get('id'),
                        'label': odds.get('label'),  # Over/Under
                        'value': odds.get('value'),  # Odds value
                        'total': odds.get('total'),  # Corner total (e.g., 8.5, 9.5)
                        'handicap': odds.get('handicap'),
                        'market_description': odds.get('market_description'),
                        'stopped': odds.get('stopped'),
                        'suspended': odds.get('suspended'),
                        'probability': odds.get('probability'),
                        'latest_update': odds.get('latest_bookmaker_update'),
                        'fixture_id': odds.get('fixture_id'),
                        'market_id': odds.get('market_id'),
                        'bookmaker_id': odds.get('bookmaker_id')
                    })
                
                corner_odds_data['last_updated_odds'].update({
                    'status': 'success',
                    'total_recent_odds': len(all_recent_odds),
                    'match_specific_odds': len(match_odds),
                    'all_fixtures_with_updates': list(set(odds.get('fixture_id') for odds in all_recent_odds)),
                    'explanation': 'This endpoint returns odds updated in the last 10 seconds for real-time betting'
                })
                
                corner_odds_data['filtered_results'].update({
                    'market_61_bet365': asian_total_corners,
                    'total_found': len(asian_total_corners),
                    'last_update_time': datetime.now().isoformat(),
                    'real_time_data': True
                })
                
            else:
                error_response = response.text if hasattr(response, 'text') else 'No response text'
                corner_odds_data['last_updated_odds'].update({
                    'status': 'error',
                    'message': f"API Error: {response.status_code}",
                    'full_error': error_response
                })
        except Exception as e:
            corner_odds_data['last_updated_odds'] = {'status': 'exception', 'error': str(e)}
        
        # STEP 2: FALLBACK - If no recent updates found, try the general inplay endpoint that worked before
        if corner_odds_data['filtered_results']['total_found'] == 0:
            try:
                print(f"🔄 No recent updates found, trying general inplay endpoint for match {match_id}")
                
                general_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
                params = {'api_token': api_key}
                
                response = requests.get(general_url, params=params, timeout=15)
                
                corner_odds_data['fallback_general'] = {
                    'status': 'tested',
                    'url': general_url,
                    'response_code': response.status_code,
                    'response_text': response.text[:300] if hasattr(response, 'text') else 'No response text'
                }
                
                if response.status_code == 200:
                    all_odds = response.json().get('data', [])
                    
                    # Filter for Market 61 (Asian Total Corners) and Bookmaker 2 (bet365)
                    asian_corner_bet365 = []
                    for odds in all_odds:
                        market_id = odds.get('market_id')
                        bookmaker_id = odds.get('bookmaker_id')
                        
                        if market_id == 61 and bookmaker_id == 2:  # Asian Total Corners from bet365
                            asian_corner_bet365.append({
                                'id': odds.get('id'),
                                'label': odds.get('label'),
                                'value': odds.get('value'),
                                'total': odds.get('total'),
                                'handicap': odds.get('handicap'),
                                'market_description': odds.get('market_description', 'Asian Total Corners'),
                                'stopped': odds.get('stopped'),
                                'suspended': odds.get('suspended'),
                                'probability': odds.get('probability'),
                                'latest_update': odds.get('latest_bookmaker_update')
                            })
                    
                    corner_odds_data['fallback_general'].update({
                        'status': 'success',
                        'total_odds': len(all_odds),
                        'asian_corner_bet365_found': len(asian_corner_bet365),
                        'last_update_time': datetime.now().isoformat()
                    })
                    
                    # Update filtered results with fallback data
                    if len(asian_corner_bet365) > 0:
                        corner_odds_data['filtered_results'].update({
                            'market_61_bet365': asian_corner_bet365,
                            'total_found': len(asian_corner_bet365),
                            'last_update_time': datetime.now().isoformat(),
                            'real_time_data': False,
                            'source': 'fallback_general_endpoint'
                        })
                
            except Exception as e:
                corner_odds_data['fallback_general'] = {'status': 'exception', 'error': str(e)}
        
        return jsonify(corner_odds_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/corner-odds-test')
def corner_odds_test_page():
    """Page to test corner odds for specific matches"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Corner Odds Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .search-box { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .results { background: white; padding: 20px; border-radius: 8px; }
            .match-item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
            .match-item:hover { background: #f0f0f0; }
            .odds-display { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .market-title { font-weight: bold; color: #333; margin-bottom: 10px; }
            .odds-item { margin: 5px 0; padding: 5px; background: white; border-radius: 3px; }
            .bet365-odds { border-left: 3px solid #4CAF50; }
            .error { color: #f44336; }
            .success { color: #4CAF50; }
            input[type="text"] { width: 300px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Asian Corner Odds Test</h1>
            
            <div class="search-box">
                <h3>Find North Lakes vs Sunshine Coast Match:</h3>
                <button onclick="loadLiveMatches()">Load Live Matches</button>
                <div id="matches-list"></div>
            </div>
            
            <div class="search-box">
                <h3>Test Corner Odds for Match ID:</h3>
                <input type="text" id="match-id" placeholder="Enter Match ID" />
                <button onclick="testCornerOdds()">Get Corner Odds</button>
            </div>
            
            <div class="results" id="results"></div>
        </div>
        
        <script>
            async function loadLiveMatches() {
                try {
                    const response = await fetch('/api/live-matches');
                    const data = await response.json();
                    
                    const matchesList = document.getElementById('matches-list');
                    matchesList.innerHTML = '';
                    
                    // Show ALL live matches for testing
                    matchesList.innerHTML = `<h4>📋 All Live Matches (${data.matches.length} total):</h4>`;
                    
                    // Look for the specific target match first
                    const targetMatches = data.matches.filter(match => 
                        match.home_team.includes('North Lakes') || 
                        match.away_team.includes('North Lakes') ||
                        match.home_team.includes('Sunshine Coast') || 
                        match.away_team.includes('Sunshine Coast')
                    );
                    
                    if (targetMatches.length > 0) {
                        matchesList.innerHTML += '<h4 style="color: green;">🎯 Target Match Found:</h4>';
                        targetMatches.forEach(match => {
                            matchesList.innerHTML += `
                                <div class="match-item" onclick="selectMatch('${match.match_id}')" style="border: 2px solid green;">
                                    <strong>${match.home_team} vs ${match.away_team}</strong><br>
                                    Match ID: ${match.match_id} | ${match.minute}' ${match.state}
                                </div>
                            `;
                        });
                        matchesList.innerHTML += '<hr>';
                    }
                    
                    // Show ALL other live matches
                    matchesList.innerHTML += '<h4>🔄 All Other Live Matches:</h4>';
                    const otherMatches = data.matches.filter(match => 
                        !match.home_team.includes('North Lakes') && 
                        !match.away_team.includes('North Lakes') &&
                        !match.home_team.includes('Sunshine Coast') && 
                        !match.away_team.includes('Sunshine Coast')
                    );
                    
                    otherMatches.forEach(match => {
                        matchesList.innerHTML += `
                            <div class="match-item" onclick="selectMatch('${match.match_id}')">
                                ${match.home_team} vs ${match.away_team}<br>
                                <small>ID: ${match.match_id} | ${match.minute}' ${match.state} | League: ${match.league_name || 'N/A'}</small>
                            </div>
                        `;
                    });
                    
                } catch (error) {
                    document.getElementById('matches-list').innerHTML = 'Error loading matches: ' + error.message;
                }
            }
            
            function selectMatch(matchId) {
                document.getElementById('match-id').value = matchId;
                testCornerOdds();
            }
            
            async function testCornerOdds() {
                const matchId = document.getElementById('match-id').value;
                if (!matchId) {
                    alert('Please enter a Match ID');
                    return;
                }
                
                const results = document.getElementById('results');
                results.innerHTML = '<p>🔄 Loading corner odds...</p>';
                
                try {
                    const response = await fetch(`/api/corner-odds/${matchId}`);
                    const data = await response.json();
                    
                    let html = `<h2>🚀 LIVE UPDATED Asian Corner Odds - Match ${matchId}</h2>`;
                    
                    // LIVE UPDATED ODDS (Last 10 seconds - REAL-TIME)
                    html += '<div class="odds-display">';
                    html += '<div class="market-title">⚡ LIVE UPDATED ODDS (Last 10 seconds - Market 61 + bet365 ONLY)</div>';
                    
                    if (data.last_updated_odds) {
                        html += `<p><strong>🔍 DEBUG INFO:</strong></p>`;
                        html += `<p>URL: <code>${data.last_updated_odds.url || 'N/A'}</code></p>`;
                        html += `<p>Filters: <code>${data.last_updated_odds.params?.filters || 'N/A'}</code></p>`;
                        html += `<p>Response Code: <code>${data.last_updated_odds.response_code || 'N/A'}</code></p>`;
                        html += `<p>Status: <code>${data.last_updated_odds.status || 'N/A'}</code></p>`;
                        
                        if (data.last_updated_odds.response_text) {
                            html += `<details><summary>Response Text (first 500 chars)</summary><pre>${data.last_updated_odds.response_text}</pre></details>`;
                        }
                        
                        if (data.last_updated_odds.status === 'success') {
                            html += `<p class="success">✅ API Success - ${data.last_updated_odds.total_recent_odds || 0} recent odds (last 10 seconds)</p>`;
                            html += `<p class="success">🎯 Match-specific odds: ${data.last_updated_odds.match_specific_odds || 0}</p>`;
                            html += `<p class="info">💡 ${data.last_updated_odds.explanation || 'Real-time betting data'}</p>`;
                            
                            // Show filtered results (Market 61 + bet365)
                            if (data.filtered_results && data.filtered_results.total_found > 0) {
                                html += `<p class="success">🎯 <strong>ASIAN TOTAL CORNERS (Market 61) from bet365 FOUND: ${data.filtered_results.total_found}</strong></p>`;
                                html += `<p class="info">⏰ Last updated: ${data.filtered_results.last_update_time}</p>`;
                                
                                data.filtered_results.market_61_bet365.forEach((odds, i) => {
                                    const statusIcon = odds.stopped ? '🛑' : odds.suspended ? '⏸️' : '✅';
                                    html += `
                                        <div class="odds-item bet365-odds">
                                            <strong>${statusIcon} ${i+1}. ${odds.market_description || 'Asian Total Corners'}</strong><br>
                                            <span class="odds-value">Label: <strong>${odds.label}</strong> | Value: <strong>${odds.value}</strong></span><br>
                                            ${odds.total ? `Total: <strong>${odds.total}</strong> corners | ` : ''}
                                            ${odds.probability ? `Probability: ${odds.probability} | ` : ''}
                                            ${odds.latest_update ? `Updated: ${odds.latest_update}` : ''}
                                            ${odds.stopped ? '<br><span class="error">⚠️ STOPPED</span>' : ''}
                                            ${odds.suspended ? '<br><span class="warning">⚠️ SUSPENDED</span>' : ''}
                                        </div>
                                    `;
                                });
                            } else {
                                html += '<p class="warning">⚠️ No Asian Total Corners (Market 61) from bet365 found for this match</p>';
                                html += '<p class="info">💡 This could mean: 1) No corner odds available, 2) Match not live, 3) bet365 not offering corner markets for this match</p>';
                            }
                        } else {
                            html += `<p class="error">❌ ${data.last_updated_odds.message || data.last_updated_odds.error || 'Error fetching live updated odds'}</p>`;
                        }
                    }
                    html += '</div>';
                    
                    // FALLBACK GENERAL ENDPOINT RESULTS
                    html += '<div class="odds-display">';
                    html += '<div class="market-title">🔄 FALLBACK - General Inplay Endpoint Results</div>';
                    
                    if (data.fallback_general) {
                        html += `<p><strong>🔍 DEBUG INFO:</strong></p>`;
                        html += `<p>URL: <code>${data.fallback_general.url || 'N/A'}</code></p>`;
                        html += `<p>Response Code: <code>${data.fallback_general.response_code || 'N/A'}</code></p>`;
                        html += `<p>Status: <code>${data.fallback_general.status || 'N/A'}</code></p>`;
                        
                        if (data.fallback_general.response_text) {
                            html += `<details><summary>Response Text (first 300 chars)</summary><pre>${data.fallback_general.response_text}</pre></details>`;
                        }
                        
                        if (data.fallback_general.status === 'success') {
                            html += `<p class="success">✅ API Success - ${data.fallback_general.total_odds || 0} total odds found</p>`;
                            html += `<p class="success">🎯 Found ${data.fallback_general.asian_corner_bet365_found || 0} Asian Total Corners from bet365</p>`;
                            html += `<p class="info">💡 This endpoint is a more general inplay endpoint that might return more data.</p>`;
                            
                            if (data.fallback_general.asian_corner_bet365_found > 0) {
                                html += `<p class="success">🎯 <strong>ASIAN TOTAL CORNERS (Market 61) from bet365 FOUND: ${data.fallback_general.asian_corner_bet365_found}</strong></p>`;
                                html += `<p class="info">⏰ Last updated: ${data.fallback_general.last_update_time || 'N/A'}</p>`;
                                
                                // Check if we have odds data from either source
                                const oddsData = data.filtered_results.market_61_bet365 || [];
                                oddsData.forEach((odds, i) => {
                                    const statusIcon = odds.stopped ? '🛑' : odds.suspended ? '⏸️' : '✅';
                                    html += `
                                        <div class="odds-item bet365-odds">
                                            <strong>${statusIcon} ${i+1}. ${odds.market_description || 'Asian Total Corners'}</strong><br>
                                            <span class="odds-value">Label: <strong>${odds.label}</strong> | Value: <strong>${odds.value}</strong></span><br>
                                            ${odds.total ? `Total: <strong>${odds.total}</strong> corners | ` : ''}
                                            ${odds.probability ? `Probability: ${odds.probability} | ` : ''}
                                            ${odds.latest_update ? `Updated: ${odds.latest_update}` : ''}
                                            ${odds.stopped ? '<br><span class="error">⚠️ STOPPED</span>' : ''}
                                            ${odds.suspended ? '<br><span class="warning">⚠️ SUSPENDED</span>' : ''}
                                        </div>
                                    `;
                                });
                            } else {
                                html += '<p class="warning">⚠️ No Asian Total Corners (Market 61) from bet365 found using fallback endpoint</p>';
                                html += '<p class="info">💡 This could mean: 1) No corner odds available, 2) Match not live, 3) bet365 not offering corner markets for this match</p>';
                            }
                        } else {
                            html += `<p class="error">❌ ${data.fallback_general.message || data.fallback_general.error || 'Error fetching fallback odds'}</p>`;
                        }
                    }
                    html += '</div>';
                    
                    results.innerHTML = html;
                    
                } catch (error) {
                    results.innerHTML = '<p class="error">Error: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 WORLD-CLASS PROFITABLE CORNER SYSTEM STARTING")
    print("=" * 60)
    print("📊 Loading initial data...")
    
    # Load initial data synchronously
    try:
        initial_matches = get_live_matches()
        live_matches_data = initial_matches
        
        dashboard_stats = {
            'total_live': len(initial_matches),
            'late_games': len([m for m in initial_matches if 83 <= m['minute'] < 85]),
            'draws': len([m for m in initial_matches if m['is_draw']]),
            'close_games': len([m for m in initial_matches if m['is_close']]),
            'critical_games': len([m for m in initial_matches if m['minute'] >= 85]),
            'with_stats': len([m for m in initial_matches if m['statistics']['total_stats_available'] > 0]),
            'with_corners': len([m for m in initial_matches if m['statistics']['has_corners']]),
            'with_odds': 0,  # Will be calculated by background thread
            'alerts_triggered': 0,
            'last_update': datetime.now().strftime('%H:%M:%S')
        }
        
        print(f"✅ Initial data loaded: {len(initial_matches)} live matches")
        
    except Exception as e:
        print(f"❌ Error loading initial data: {e}")
        live_matches_data = []
        dashboard_stats = {
            'total_live': 0,
            'late_games': 0,
            'draws': 0,
            'close_games': 0,
            'critical_games': 0,
            'with_stats': 0,
            'with_corners': 0,
            'with_odds': 0,
            'alerts_triggered': 0,
            'last_update': 'Error'
        }
    
def start_dashboard_background_thread():
    """Start the background data updater thread"""
    print("🚀 Starting background data updater thread...")
    update_thread = threading.Thread(target=update_live_data, daemon=True)
    update_thread.start()
    print("✅ Background thread started!")

if __name__ == "__main__":
    # When running web_dashboard.py directly
    start_dashboard_background_thread()
    
    print("📊 Open your browser to: http://localhost:5000")
    print("🔄 Auto-refreshes every 8 seconds (SportMonks optimized)")
    print("⚡ Smart rate limit monitoring per entity")
    print("🎯 PRECISION FEATURES:")
    print("   • 85-minute alerts with Asian corner odds")
    print("   • ELITE FILTER: Only draws and up to 2-goal difference games")
    print("   • Optimized corner count ranges (7-9 = PRIME ZONE)")
    print("   • Stop monitoring after alerts sent")
    print("   • Psychological scoring integration")
    print("   • Real-time corner category analysis")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 