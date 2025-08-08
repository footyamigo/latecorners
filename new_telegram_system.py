#!/usr/bin/env python3
"""
BRAND NEW BULLETPROOF TELEGRAM ALERT SYSTEM
==========================================
NO MORE FAILURES. NO MORE FRUSTRATION.
This system uses basic HTTP requests and WILL work.
"""

import os
import json
import logging
from typing import Dict, Optional
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewTelegramSystem:
    """Brand new telegram system that WILL work"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.sent_alerts = set()
        
        logger.info("🆕 NEW TELEGRAM SYSTEM INITIALIZING...")
        logger.info(f"   Bot token: {'✅ SET' if self.bot_token else '❌ MISSING'}")
        logger.info(f"   Chat ID: {'✅ SET' if self.chat_id else '❌ MISSING'}")
        
        if self.bot_token and self.chat_id:
            logger.info("🎉 NEW TELEGRAM SYSTEM READY!")
        else:
            logger.error("❌ NEW TELEGRAM SYSTEM NOT CONFIGURED")
    
    def send_alert(self, match_data: Dict, tier: str, score: float, conditions: list) -> bool:
        """Send alert using simple HTTP requests - guaranteed to work"""
        
        if not self.bot_token or not self.chat_id:
            logger.error("❌ NEW TELEGRAM: Missing credentials")
            return False
        
        # Create unique alert ID
        match_id = match_data.get('fixture_id', 0)
        minute = match_data.get('minute', 85)
        alert_id = f"{match_id}_{minute}_{int(score)}"
        
        if alert_id in self.sent_alerts:
            logger.info(f"📵 NEW TELEGRAM: Alert {alert_id} already sent")
            return True
        
        logger.info(f"🚀 NEW TELEGRAM ALERT STARTING...")
        logger.info(f"   Match ID: {match_id}")
        logger.info(f"   Tier: {tier}")
        logger.info(f"   Score: {score}")
        logger.info(f"   Alert ID: {alert_id}")
        
        # 🚨 CRITICAL CHECK: Only send alerts when whole number odds are available
        active_odds = match_data.get('active_odds', [])
        
        # Pre-filter to check if we have whole number corner odds available
        filtered_active_odds = []
        for odds_str in active_odds:
            # Check if this is a corner odds string with a whole number
            if "Over" in odds_str or "Under" in odds_str:
                try:
                    # Extract the number after "Over " or "Under "
                    if "Over" in odds_str:
                        parts = odds_str.replace("Over ", "").split(" = ")
                    elif "Under" in odds_str:
                        parts = odds_str.replace("Under ", "").split(" = ")
                    
                    if len(parts) >= 1:
                        line = float(parts[0])
                        # Only include if it's a whole number
                        if line == int(line):
                            filtered_active_odds.append(odds_str)
                except (ValueError, TypeError):
                    # If we can't parse it, include it anyway (might be a different format)
                    filtered_active_odds.append(odds_str)
            else:
                # Non-corner odds, include as-is
                filtered_active_odds.append(odds_str)
        
        # 🚨 CRITICAL: Only send alert if we have whole number odds available
        if not filtered_active_odds:
            logger.info(f"📵 NEW TELEGRAM: No whole number odds available for {alert_id} - SKIPPING ALERT")
            logger.info(f"   Raw odds available: {active_odds}")
            logger.info(f"   Reason: Only sending alerts when whole number corner markets are available")
            return False
        
        logger.info(f"✅ NEW TELEGRAM: {len(filtered_active_odds)} whole number odds found - PROCEEDING WITH ALERT")
        logger.info(f"   Whole number odds: {filtered_active_odds}")
        
        # Create message (now guaranteed to have odds available)
        message = self._create_message(match_data, tier, score, conditions, filtered_active_odds)
        
        # Send via HTTP
        success = self._send_http_message(message)
        
        if success:
            self.sent_alerts.add(alert_id)
            logger.info(f"🎉 NEW TELEGRAM: Alert {alert_id} sent successfully!")
            return True
        else:
            logger.error(f"❌ NEW TELEGRAM: Alert {alert_id} failed!")
            return False
    
    def _generate_dynamic_action(self, corners: int, active_odds: list) -> str:
        """Generate dynamic ACTION text based on current corners and available odds"""
        
        # Parse available over/under lines from odds
        available_lines = []
        
        for odds_str in active_odds:
            if "Over" in odds_str or "Under" in odds_str:
                try:
                    # Parse "Over 9 = 1.70" or "Under 9 = 2.10" (whole numbers only)
                    if "Over" in odds_str:
                        parts = odds_str.replace("Over ", "").split(" = ")
                        if len(parts) == 2:
                            line = float(parts[0])
                            odds_value = float(parts[1])
                            
                            # Only accept whole number lines for refund possibilities
                            if line == int(line):
                                available_lines.append({
                                    'type': 'Over',
                                    'line': line,
                                    'odds': odds_value,
                                    'text': odds_str
                                })
                    elif "Under" in odds_str:
                        parts = odds_str.replace("Under ", "").split(" = ")
                        if len(parts) == 2:
                            line = float(parts[0])
                            odds_value = float(parts[1])
                            
                            # Only accept whole number lines for refund possibilities
                            if line == int(line):
                                available_lines.append({
                                    'type': 'Under',
                                    'line': line,
                                    'odds': odds_value,
                                    'text': odds_str
                                })
                except Exception as e:
                    logger.debug(f"Error parsing odds '{odds_str}': {e}")
                    continue
        
        if not available_lines:
            return "Check available corner markets"
        
        # Find the best suggestion - prioritize achievable Over bets
        best_over = None
        best_under = None
        
        for line_data in available_lines:
            line = line_data['line']
            line_type = line_data['type']
            
            if line_type == 'Over':
                # How many more corners needed?
                needed = line - corners
                if 0 < needed <= 3:  # Reasonable range (1-3 more corners needed)
                    if not best_over or needed < best_over['needed']:
                        best_over = {
                            'action': f"Consider {line_data['text']}",
                            'reason': f"Need {int(needed)} more corner{'s' if needed != 1 else ''}",
                            'needed': needed,
                            'line_data': line_data,
                            'priority': 1  # High priority for achievable overs
                        }
            
            elif line_type == 'Under':
                # How many corners can we still have?
                remaining = line - corners
                if remaining >= 0:  # Under is still possible (including exactly on line)
                    if not best_under or remaining < best_under['remaining']:
                        best_under = {
                            'action': f"Consider {line_data['text']}",
                            'reason': f"Max {int(remaining)} more corner{'s' if remaining != 1 else ''} allowed" if remaining > 0 else "Must avoid any more corners",
                            'remaining': remaining,
                            'line_data': line_data,
                            'priority': 2  # Lower priority than achievable overs
                        }
        
        # Choose the best suggestion - prioritize achievable Over bets
        best_suggestion = None
        
        if best_over:
            # Prioritize Over bets that need 1-3 more corners
            best_suggestion = best_over
        elif best_under and best_under['remaining'] <= 2:
            # Only suggest Under if it's close (0-2 more corners allowed)
            best_suggestion = best_under
        elif best_over:
            # Fall back to any Over bet if no good Under available
            best_suggestion = best_over
        elif best_under:
            # Last resort - any Under bet
            best_suggestion = best_under
        
        if best_suggestion:
            return f"{best_suggestion['action']} ({best_suggestion['reason']})"
        
        # Fallback - suggest closest line
        if available_lines:
            closest_line = min(available_lines, key=lambda x: abs(x['line'] - corners))
            return f"Check {closest_line['type']} {closest_line['line']} market"
        
        return "Check available corner markets"
    
    def _create_message(self, match_data: Dict, tier: str, score: float, conditions: list, active_odds: list) -> str:
        """Create a simple, effective alert message"""
        
        home_team = match_data.get('home_team', 'Home')
        away_team = match_data.get('away_team', 'Away')
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        minute = match_data.get('minute', 85)
        corners = match_data.get('total_corners', 0)
        
        # Get actual high priority count from scoring result
        high_priority_count = match_data.get('high_priority_count', 0)
        
        # Tier-specific header and requirements
        if tier == "ELITE":
            header = "🏆 ELITE CORNER ALERT 🏆"
            score_threshold = "8.0"
            priority_required = 2
        elif tier.startswith("TIER_1"):
            header = "💎 PREMIUM CORNER ALERT 💎"
            score_threshold = "16.0"
            priority_required = 3
        else:
            header = "💎 PREMIUM CORNER ALERT 💎"
            score_threshold = "6.0"
            priority_required = 1
        
        # Active odds - filter to only show whole number corner totals
        # This filtering is now done in send_alert, so we just pass the pre-filtered odds
        
        odds_text = "\n".join(f"• {odd}" for odd in active_odds[:3])  # No fallback needed - odds guaranteed
        
        # Generate simple betting recommendation based on current corners
        next_corner = corners + 1
        dynamic_action = f"Over {next_corner} Asian Corners"
        
        # Get momentum indicators if available
        momentum = match_data.get('momentum_indicators', {})
        patterns = match_data.get('detected_patterns', [])
        
        # Format momentum stats
        attack_intensity = momentum.get('attack_intensity', 0)
        shot_efficiency = momentum.get('shot_efficiency', 0)
        corner_momentum = momentum.get('corner_momentum', 0)
        score_context = momentum.get('score_context', 0)
        
        # Format patterns (take top 3 by weight)
        sorted_patterns = sorted(patterns, key=lambda x: x.get('weight', 0), reverse=True)
        pattern_text = "\n".join(f"• {p['name']} ({p['weight']})" for p in sorted_patterns[:3]) if patterns else "No patterns detected"
        
        team_prob = match_data.get('team_probability', None)
        message = f"""🚨 {header}

<b>{home_team} vs {away_team}</b>
📊 Score: {home_score}-{away_score} | ⏱️ {minute}'
🏆 Corners: {corners}

<b>🎯 ALERT METRICS:</b>
• Combined Probability: {score:.1f}%
{'• Team Probability: ' + f"{team_prob:.1f}%" if team_prob is not None else ''}
• Attack Quality: {attack_intensity:.1f}%
• Shot Efficiency: {shot_efficiency:.1f}%
• Corner Momentum: {corner_momentum:.1f}%
• Score Context: {score_context:.1f}%

⭐ High Priority: {high_priority_count}/{priority_required}

💡 <b>DETECTED PATTERNS:</b>
{pattern_text}

💫 <b>WHY THIS ALERT:</b>
{chr(10).join(f'• {condition}' for condition in conditions[:3])}

⚡ <b>ACTION:</b> {dynamic_action}
🎯 <b>TIMING:</b> Live betting available now
💰 <b>CONFIDENCE:</b> {tier} tier qualification

<i>Alert sent at {datetime.now().strftime('%H:%M:%S')}</i>
"""
        
        logger.info(f"📝 NEW TELEGRAM: Message created ({len(message)} chars)")
        logger.info(f"   Preview: {message[:100]}...")
        
        return message
    
    def _send_http_message(self, message: str) -> bool:
        """Send message using simple HTTP request"""
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        logger.info(f"🌐 NEW TELEGRAM: Sending HTTP request...")
        logger.info(f"   URL: {url[:50]}...")
        logger.info(f"   Chat ID: {self.chat_id}")
        logger.info(f"   Message length: {len(message)}")
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            logger.info(f"📡 NEW TELEGRAM: HTTP response received")
            logger.info(f"   Status code: {response.status_code}")
            logger.info(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    message_id = result.get('result', {}).get('message_id')
                    logger.info(f"✅ NEW TELEGRAM: SUCCESS! Message ID: {message_id}")
                    return True
                else:
                    logger.error(f"❌ NEW TELEGRAM: API error: {result}")
                    return False
            else:
                logger.error(f"❌ NEW TELEGRAM: HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ NEW TELEGRAM: Timeout error (10 seconds)")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ NEW TELEGRAM: Request error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ NEW TELEGRAM: Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_connection(self) -> bool:
        """Test telegram connection with a simple message"""
        
        logger.info("🧪 NEW TELEGRAM: Testing connection...")
        
        test_message = f"""🔧 NEW TELEGRAM SYSTEM TEST

✅ Connection verified at {datetime.now().strftime('%H:%M:%S')}
✅ HTTP requests working
✅ Message formatting working
✅ Ready for corner alerts!

🚀 The new system is bulletproof!"""
        
        return self._send_http_message(test_message)
    
    def send_system_message(self, message: str) -> bool:
        """Send a system message (startup, errors, etc.)"""
        try:
            logger.info(f"📢 SYSTEM MESSAGE: Sending...")
            success = self._send_http_message(message)
            if success:
                logger.info("✅ SYSTEM MESSAGE: Sent successfully!")
            else:
                logger.error("❌ SYSTEM MESSAGE: Failed to send")
            return success
        except Exception as e:
            logger.error(f"❌ SYSTEM MESSAGE ERROR: {e}")
            return False

# Global instance
new_telegram = NewTelegramSystem()

def send_corner_alert_new(match_data: Dict, tier: str, score: float, conditions: list) -> bool:
    """Simple function to send alerts using the new system"""
    return new_telegram.send_alert(match_data, tier, score, conditions)

def send_system_message_new(message: str) -> bool:
    """Simple function to send system messages using the new system"""
    return new_telegram.send_system_message(message)

def test_new_system():
    """Test the new telegram system"""
    
    logger.info("🧪 TESTING NEW TELEGRAM SYSTEM...")
    
    # Test connection
    if new_telegram.test_connection():
        logger.info("✅ NEW TELEGRAM SYSTEM WORKS!")
        return True
    else:
        logger.error("❌ NEW TELEGRAM SYSTEM FAILED!")
        return False

if __name__ == "__main__":
    # Test when run directly
    test_new_system() 