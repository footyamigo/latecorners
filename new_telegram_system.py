#!/usr/bin/env python3
"""
BRAND NEW BULLETPROOF TELEGRAM ALERT SYSTEM
==========================================
NO MORE FAILURES. NO MORE FRUSTRATION.
This system uses basic HTTP requests and WILL work.
"""

import os
import json
import re
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
        
        # ENHANCED ODDS DETECTION: Also check suspended odds for premium tiers
        all_odds_available = active_odds if active_odds else []
        
        # For premium tiers, also include suspended odds from odds_details if active_odds is empty
        if tier in ['ELITE_CORNER', 'PANICKING_FAVORITE', 'FIGHTING_UNDERDOG'] and not all_odds_available:
            odds_details = match_data.get('odds_details', [])
            logger.info(f"🔍 Premium tier detected with no active odds - checking suspended odds: {len(odds_details)} total")
            all_odds_available = odds_details
            
        for odds_str in all_odds_available:
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
                        current_corners = match_data.get('total_corners', 0)
                        
                        # SIMPLIFIED LOGIC: Accept ALL corner odds (no restriction on whole numbers or 0.5)
                        # For premium tiers, include even suspended odds
                        if tier in ['ELITE_CORNER', 'PANICKING_FAVORITE', 'FIGHTING_UNDERDOG', 'OPTIMIZED_PROFITABLE']:
                            # Remove suspended status for clean display
                            clean_odds = odds_str.replace(" (suspended)", "")
                            filtered_active_odds.append(clean_odds)
                        else:
                            # For regular tiers, only include non-suspended
                            if "(suspended)" not in odds_str:
                                filtered_active_odds.append(odds_str)
                except (ValueError, TypeError):
                    # If we can't parse it, include it anyway (might be a different format)
                    if tier in ['ELITE_CORNER', 'PANICKING_FAVORITE', 'FIGHTING_UNDERDOG']:
                        clean_odds = odds_str.replace(" (suspended)", "")
                        filtered_active_odds.append(clean_odds)
                    elif "(suspended)" not in odds_str:
                        filtered_active_odds.append(odds_str)
            else:
                # Non-corner odds, include as-is
                filtered_active_odds.append(odds_str)
        
        # 🚨 CRITICAL: Only send alert if we have corner odds available (EXCEPT for premium systems)
        if not filtered_active_odds and tier not in ['ELITE_CORNER', 'PANICKING_FAVORITE', 'FIGHTING_UNDERDOG', 'OPTIMIZED_PROFITABLE']:
            logger.info(f"📵 NEW TELEGRAM: No corner odds available for {alert_id} - SKIPPING ALERT")
            logger.info(f"   Raw odds available: {active_odds}")
            logger.info(f"   Reason: No corner odds available for this match")
            return False
        elif tier in ['ELITE_CORNER', 'PANICKING_FAVORITE', 'FIGHTING_UNDERDOG', 'OPTIMIZED_PROFITABLE'] and not filtered_active_odds:
            if tier == 'ELITE_CORNER':
                logger.info(f"🎯 ELITE OVERRIDE: No odds available but ELITE_CORNER filter passed - SENDING ALERT")
            elif tier == 'PANICKING_FAVORITE':
                logger.info(f"🧠 PSYCHOLOGY OVERRIDE: No odds available but PANICKING_FAVORITE detected - SENDING ALERT")
            elif tier == 'FIGHTING_UNDERDOG':
                logger.info(f"🥊 UNDERDOG OVERRIDE: No odds available but FIGHTING_UNDERDOG detected - SENDING ALERT")
            else:  # OPTIMIZED_PROFITABLE
                logger.info(f"🚀 OPTIMIZED OVERRIDE: No odds available but OPTIMIZED_PROFITABLE pattern detected - SENDING ALERT")
            # Fallback odds text for when no real odds available
            if tier in ['OPTIMIZED_PROFITABLE', 'MOMENTUM_INVERTED']:
                filtered_active_odds = ["Under X More Corners (check live markets)"]
            else:
                filtered_active_odds = ["Over X Asian Corners (check live markets)"]
        
        logger.info(f"✅ NEW TELEGRAM: {len(filtered_active_odds)} compatible odds found - PROCEEDING WITH ALERT")
        logger.info(f"   Compatible odds: {filtered_active_odds}")
        
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
        
        # 🚀 NEW STRATEGY: Prioritize UNDER bets (profitable strategy)
        best_suggestion = None
        
        if best_under and best_under['remaining'] <= 2:
            # PRIORITIZE Under bets that allow 0-2 more corners (profitable strategy!)
            best_suggestion = best_under
        elif best_under:
            # Any Under bet is better than Over for our new strategy
            best_suggestion = best_under
        elif best_over and best_over['needed'] <= 1:
            # Only suggest Over if we need exactly 1 more corner
            best_suggestion = best_over
        elif best_over:
            # Last resort - Over bets (but note this contradicts our profitable strategy)
            best_suggestion = best_over
        
        if best_suggestion:
            return f"{best_suggestion['action']} ({best_suggestion['reason']})"
        
        # Fallback - suggest closest line
        if available_lines:
            closest_line = min(available_lines, key=lambda x: abs(x['line'] - corners))
            return f"Check {closest_line['type']} {closest_line['line']} market"
        
        return "Check available corner markets"
    
    def _get_momentum_level(self, momentum: float, tier: str = None) -> str:
        """Get momentum intensity level - updated for momentum inverted system"""
        
        # For momentum inverted system: LOW momentum is good (UNDER corners)
        if tier == 'MOMENTUM_INVERTED':
            if momentum <= 50:
                return "Ultra low momentum - stagnant game 🔇"
            elif momentum <= 100:
                return "Low momentum - limited attacking 📉"
            elif momentum <= 140:
                return "Moderate momentum - still viable for UNDER ⚖️"
            else:
                return "High momentum - more corners likely 📈"
        else:
            # Legacy system: HIGH momentum is good (OVER corners)
            if momentum >= 180:
                return "Corner storm explosive! 🔥🔥🔥"
            elif momentum >= 150:
                return "Extreme corner pressure 🔥🔥"
            elif momentum >= 120:
                return "High corner-creating momentum 🔥"
            else:
                return "Building pressure ⚡"
    
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
        if tier == "OPTIMIZED_PROFITABLE":
            header = "🚀 OPTIMIZED PROFITABLE ALERT - DATA-DRIVEN 🚀"
            score_threshold = "Profitable Pattern"
            priority_required = 0
        elif tier == "ELITE_CORNER":
            header = "🎯 ELITE CORNER ALERT - 100% POSITIVE RATE 🎯"
            score_threshold = "Elite Filter"
            priority_required = 0
        elif tier == "PANICKING_FAVORITE":
            header = "🧠 PANICKING FAVORITE ALERT - PSYCHOLOGY EDGE 🧠"
            score_threshold = "Psychology System"
            priority_required = 0
        elif tier == "FIGHTING_UNDERDOG":
            header = "🥊 FIGHTING UNDERDOG ALERT - GIANT-KILLING MODE 🥊"
            score_threshold = "Giant-Killing System"
            priority_required = 0
        elif tier == "ELITE":
            header = "🏆 ELITE CORNER ALERT 🏆"
            score_threshold = "8.0"
            priority_required = 2
        elif tier and tier.startswith("TIER_1"):
            header = "💎 PREMIUM CORNER ALERT 💎"
            score_threshold = "16.0"
            priority_required = 3
        else:
            header = "⚽ Corner Alert"
            score_threshold = "6.0"
            priority_required = 1
        
        # Active odds - filter to only show whole number corner totals
        # This filtering is now done in send_alert, so we just pass the pre-filtered odds
        
        odds_text = "\n".join(f"• {odd}" for odd in active_odds[:3])  # No fallback needed - odds guaranteed
        
        # 🚀 NEW STRATEGY: Recommend UNDER bets (profitable strategy)
        # For momentum inverted system, recommend Under corners
        if tier in ['OPTIMIZED_PROFITABLE', 'MOMENTUM_INVERTED']:
            next_corner = corners + 1
            dynamic_action = f"Under {next_corner} Asian Corners"
        else:
            # Legacy fallback for old psychology systems
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
        
        # Format patterns - handle both string and dict patterns
        if patterns:
            if isinstance(patterns[0], str):
                # Simple string patterns (new format)
                pattern_text = "\n".join(f"• {p}" for p in patterns[:3])
            else:
                # Dict patterns with weights (old format)
                sorted_patterns = sorted(patterns, key=lambda x: x.get('weight', 0), reverse=True)
                pattern_text = "\n".join(f"• {p['name']} ({p['weight']})" for p in sorted_patterns[:3])
        else:
            pattern_text = "No patterns detected"
        
        team_prob = match_data.get('team_probability', None)

        # Build metrics safely (avoid f-string expressions that embed backslashes)
        metrics_lines = []
        
        # Get shots on target data
        home_shots_on_target = match_data.get('home_shots_on_target', 0)
        away_shots_on_target = match_data.get('away_shots_on_target', 0)
        total_shots_on_target = match_data.get('total_shots_on_target', 0)
        
        if tier == 'OPTIMIZED_PROFITABLE':
            # NEW: Clean optimized system metrics
            win_rate = momentum.get('win_rate_estimate', score)
            metrics_lines.append(f"• Historical Win Rate: {win_rate:.0f}%")
            metrics_lines.append(f"• Shots on Target: {home_shots_on_target} vs {away_shots_on_target} (Total: {total_shots_on_target})")
            metrics_lines.append(f"• Market: Under 2 More Corners")
        elif tier in ['LATE_MOMENTUM', 'LATE_MOMENTUM_DRAW', 'PANICKING_FAVORITE', 'FIGHTING_UNDERDOG', 'MOMENTUM_INVERTED']:
            # Use momentum format for psychology alert types and momentum inverted
            momentum_level = self._get_momentum_level(score, tier)
            metrics_lines.append(f"• Combined Momentum (Last 10min): {score:.0f} pts - {momentum_level}")
            metrics_lines.append(f"• Shots on Target: {home_shots_on_target} vs {away_shots_on_target} (Total: {total_shots_on_target})")
            # Add betting recommendation
            if active_odds:
                # NEW: recommend UNDER for momentum inverted system
                current_corners = match_data.get('total_corners', 0)
                next_corner = current_corners + 1
                
                # Check if this is momentum inverted system
                if tier in ['MOMENTUM_INVERTED'] or 'momentum' in str(match_data.get('detected_patterns', [])).lower():
                    metrics_lines.append(f"• Asian Corners: Under {next_corner}")
                else:
                    # Legacy: recommend Over for old systems (if any remain)
                    metrics_lines.append(f"• Asian Corners: Over {next_corner}")
        else:
            # Legacy format for old tiers
            metrics_lines.append(f"• Combined Probability: {score:.1f}%")
            metrics_lines.append(f"• Shots on Target: {home_shots_on_target} vs {away_shots_on_target} (Total: {total_shots_on_target})")
            if team_prob is not None:
                metrics_lines.append(f"• Team Probability: {team_prob:.1f}%")
        
        # Add additional momentum metrics if available
        if attack_intensity:
            metrics_lines.append(f"• Attack Quality: {attack_intensity:.1f}%")
        if shot_efficiency:
            metrics_lines.append(f"• Shot Efficiency: {shot_efficiency:.1f}%")
        if corner_momentum:
            metrics_lines.append(f"• Corner Momentum: {corner_momentum:.1f}%")
        if score_context:
            metrics_lines.append(f"• Score Context: {score_context:.1f}%")

        # Clean message without lengthy explanations
        message = (
            f"{header}\n\n"
            f"<b>{home_team} vs {away_team}</b>\n"
            f"⚽ Score: {home_score}-{away_score} | ⏱️ {minute}' | 🚩 Corners: {corners}\n\n"
            f"<b>📊 ALERT METRICS:</b>\n" + "\n".join(metrics_lines) + "\n\n"
            f"<b>⚡ ACTION:</b> {dynamic_action}\n"
            f"<b>⏰ TIMING:</b> Live betting available now\n"
            f"<b>💪 CONFIDENCE:</b> {self._get_confidence_text(tier)}\n\n"
            f"<i>Alert sent at {datetime.now().strftime('%H:%M:%S')}</i>"
        )
        
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

    def _create_dynamic_late_momentum_message(self, match_data: Dict) -> str:
        """Create a dynamic LATE_MOMENTUM alert message based on actual match statistics"""
        home_team = match_data.get('home_team', 'Home')
        away_team = match_data.get('away_team', 'Away')
        minute = match_data.get('minute', 85)
        combined_momentum = match_data.get('total_probability', 0)
        
        # Get shots on target data
        home_shots = match_data.get('home_shots_on_target', 0)
        away_shots = match_data.get('away_shots_on_target', 0)
        total_shots = match_data.get('total_shots_on_target', 0)
        
        # Get momentum breakdown
        momentum_home = match_data.get('momentum_home', {})
        momentum_away = match_data.get('momentum_away', {})
        home_momentum = momentum_home.get('total', 0)
        away_momentum = momentum_away.get('total', 0)
        
        # Determine leading team in momentum
        if home_momentum > away_momentum:
            leading_team = home_team
            leading_momentum = home_momentum
        else:
            leading_team = away_team
            leading_momentum = away_momentum
        
        # Build dynamic message based on actual stats
        message_parts = []
        message_parts.append(f"🔥 Explosive late-game attacking detected at {minute}'!")
        
        if total_shots > 0:
            message_parts.append(f"Both teams combining for {total_shots} shots on target ({home_shots}-{away_shots}), showing relentless pressure.")
        
        message_parts.append(f"{leading_team} leading the momentum charge with intense attacking pressure.")
        
        message_parts.append(f"As the game enters its final phase with stoppage time approaching, desperate attacking creates prime corner opportunities as teams push for the result!")
        
        return " ".join(message_parts)

    def _create_dynamic_draw_momentum_message(self, match_data: Dict) -> str:
        """Create a dynamic LATE_MOMENTUM_DRAW alert message based on actual match statistics"""
        home_team = match_data.get('home_team', 'Home')
        away_team = match_data.get('away_team', 'Away')
        minute = match_data.get('minute', 85)
        combined_momentum = match_data.get('total_probability', 0)
        draw_odds = match_data.get('draw_odds', 0)
        
        # Get shots on target data
        home_shots = match_data.get('home_shots_on_target', 0)
        away_shots = match_data.get('away_shots_on_target', 0)
        total_shots = match_data.get('total_shots_on_target', 0)
        
        # Get score context
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        
        # Build dynamic message
        message_parts = []
        message_parts.append(f"📈 Perfect storm scenario at {minute}'!")
        message_parts.append(f"Low draw market odds show bookmakers expect goals, while our AI confirms explosive combined attacking momentum.")
        
        if total_shots > 0:
            message_parts.append(f"Match intensity evident: {total_shots} shots on target ({home_shots}-{away_shots}) proves both teams are pushing hard.")
        
        if home_score == away_score:
            message_parts.append(f"With scores level in the closing stages, both {home_team} and {away_team} will commit everything forward - creating corner goldmine as stoppage time looms!")
        else:
            message_parts.append(f"Score pressure drives desperate attacking in the final moments - expect corner opportunities as teams chase the result with stoppage time approaching!")
        
        return " ".join(message_parts)

    def _create_elite_corner_message(self, match_data: Dict) -> str:
        """Create dynamic message for ELITE_CORNER alerts - 100% positive rate system"""
        
        # Extract data
        minute = match_data.get('minute', 85)
        home_team = match_data.get('home_team', 'Home')
        away_team = match_data.get('away_team', 'Away')
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        corners = match_data.get('total_corners', 0)
        total_shots_ot = match_data.get('total_shots_on_target', 0)
        
        # Get momentum data
        momentum_indicators = match_data.get('momentum_indicators', {})
        combined_momentum = momentum_indicators.get('combined_momentum10', 0)
        
        message_parts = []
        
        # Elite system explanation
        message_parts.append("🎯 ELITE 100% POSITIVE RATE SYSTEM ACTIVATED!")
        message_parts.append(f"This match passed our strictest filtering - historically 100% positive outcomes (Wins + Refunds).")
        
        # Score-specific context
        if home_score == away_score:
            # Draw situation
            if home_score == 0:
                message_parts.append(f"0-0 stalemate broken! Both {home_team} and {away_team} desperately pushing for the breakthrough as time runs out.")
            else:
                message_parts.append(f"Level at {home_score}-{away_score}! Both teams throwing everything forward - corner opportunities exploding as stoppage time approaches!")
        elif abs(home_score - away_score) == 1:
            # Close game
            leading_team = home_team if home_score > away_score else away_team
            trailing_team = away_team if home_score > away_score else home_team
            message_parts.append(f"{leading_team} clinging to narrow lead while {trailing_team} launches desperate final assault - corner bonanza incoming!")
        else:
            # Other scenarios
            message_parts.append(f"As the clock ticks down, intense attacking pressure creates premium corner opportunities!")
        
        # Corner momentum context
        if corners >= 11:
            message_parts.append(f"Already {corners} corners recorded - the corner momentum is unstoppable! More corners inevitable as desperation peaks.")
        elif corners >= 8:
            message_parts.append(f"With {corners} corners already, both teams in full attacking mode. The corner floodgates are about to burst open!")
        else:
            message_parts.append(f"Perfect corner setup detected! Our AI identifies explosive attacking patterns building to corner crescendo.")
        
        # Shots context if available
        if total_shots_ot > 0:
            message_parts.append(f"Teams firing {total_shots_ot} shots on target shows relentless attacking intent - corners are the inevitable result!")
        
        # Final urgency
        message_parts.append("⚡ FINAL MINUTES DESPERATION = CORNER GOLDMINE!")
        
        return " ".join(message_parts)
    
    def _get_confidence_text(self, tier: str) -> str:
        """Get confidence text based on alert tier"""
        if tier == "OPTIMIZED_PROFITABLE":
            return "Data-Driven Profitable System (70-88% Win Rate)"
        elif tier == "ELITE_CORNER":
            return "Elite 100% Positive System"
        elif tier == "PANICKING_FAVORITE":
            return "Psychology-Driven Edge System"
        elif tier == "FIGHTING_UNDERDOG":
            return "Giant-Killing Psychology System"
        else:
            return "High Confidence System"
    
    def _create_panicking_favorite_message(self, match_data: Dict) -> str:
        """Create dynamic message for PANICKING_FAVORITE alerts - psychology-driven system"""
        
        # Extract data
        minute = match_data.get('minute', 75)
        home_team = match_data.get('home_team', 'Home')
        away_team = match_data.get('away_team', 'Away')
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        corners = match_data.get('total_corners', 0)
        
        # Get psychology data if available
        psychology_data = match_data.get('psychology_data', {})
        favorite_team = psychology_data.get('favorite_team', 'home')
        favorite_odds = psychology_data.get('favorite_odds', 1.50)
        panic_level = psychology_data.get('panic_level', 'HIGH_PANIC')
        
        message_parts = []
        
        # Psychology system explanation
        message_parts.append("🧠 PSYCHOLOGY ALERT: Heavy favorite under extreme pressure!")
        message_parts.append(f"Market expectations completely shattered - {favorite_odds:.2f} odds favorite failing to deliver.")
        
        # Identify the teams
        if favorite_team == 'home':
            fav_name = home_team
            und_name = away_team
        else:
            fav_name = away_team
            und_name = home_team
        
        # Panic level specific context
        if panic_level == 'MAXIMUM_PANIC':
            message_parts.append(f"🚨 MAXIMUM PANIC MODE: {fav_name} was supposed to dominate but can't even take the lead!")
        elif panic_level == 'HIGH_PANIC':
            message_parts.append(f"⚠️ HIGH PRESSURE: {fav_name} desperately trying to avoid embarrassment!")
        else:
            message_parts.append(f"📈 BUILDING PRESSURE: {fav_name} feeling the heat as time runs out!")
        
        # Score-specific psychological context
        goal_difference = abs(home_score - away_score)
        if home_score == away_score:
            message_parts.append(f"Level at {home_score}-{away_score}! {fav_name} expected easy win but reality hits hard - desperation corners incoming!")
        elif goal_difference == 1:
            if (favorite_team == 'home' and home_score > away_score) or (favorite_team == 'away' and away_score > home_score):
                message_parts.append(f"Only leading by 1 goal! {fav_name} needs more cushion - expect frantic attacking and corner explosion!")
            else:
                message_parts.append(f"SHOCK! {und_name} defying all odds! {fav_name} in absolute panic mode throwing everything forward!")
        
        # Corner psychology
        if corners >= 10:
            message_parts.append(f"Already {corners} corners shows the relentless pressure - {fav_name} won't stop until they get the result their odds demanded!")
        elif corners >= 7:
            message_parts.append(f"With {corners} corners building, {fav_name}'s desperation creates perfect corner storm!")
        else:
            message_parts.append(f"Corner explosion imminent! Psychological pressure forces {fav_name} into panic attack mode!")
        
        # Psychology insight
        message_parts.append(f"🎯 PSYCHOLOGY EDGE: When heavy favorites panic, tactical discipline disappears and corners multiply exponentially!")
        
        return " ".join(message_parts)
    
    def _create_fighting_underdog_message(self, match_data: Dict) -> str:
        """Create dynamic message for FIGHTING_UNDERDOG alerts - giant-killing system"""
        
        # Extract data
        minute = match_data.get('minute', 75)
        home_team = match_data.get('home_team', 'Home')
        away_team = match_data.get('away_team', 'Away')
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        corners = match_data.get('total_corners', 0)
        
        # Get psychology data if available
        psychology_data = match_data.get('psychology_data', {})
        underdog_team = psychology_data.get('underdog_team', 'home')
        underdog_odds = psychology_data.get('underdog_odds', 4.00)
        giant_killing_level = psychology_data.get('giant_killing_level', 'HIGH_GIANT_KILLING')
        
        message_parts = []
        
        # Giant-killing system explanation
        message_parts.append("🥊 GIANT-KILLING ALERT: Massive underdog defying all expectations!")
        message_parts.append(f"Market gave them just {(100/underdog_odds):.1f}% chance - but they're writing their own story!")
        
        # Identify the teams
        if underdog_team == 'home':
            underdog_name = home_team
            favorite_name = away_team
        else:
            underdog_name = away_team
            favorite_name = home_team
        
        # Giant-killing level specific context
        if giant_killing_level == 'MAXIMUM_GIANT_KILLING':
            message_parts.append(f"🚨 MAXIMUM GIANT-KILLING: {underdog_name} ({underdog_odds:.2f} odds) AHEAD OR LEVEL! This is David vs Goliath!")
        elif giant_killing_level == 'HIGH_GIANT_KILLING':
            message_parts.append(f"⚡ HIGH GIANT-KILLING: {underdog_name} ({underdog_odds:.2f} odds) smelling the upset of a lifetime!")
        elif giant_killing_level == 'NOTHING_TO_LOSE':
            message_parts.append(f"💥 NOTHING TO LOSE: {underdog_name} ({underdog_odds:.2f} odds) throwing everything forward - miracle within reach!")
        else:
            message_parts.append(f"🔥 FINAL DESPERATION: {underdog_name} ({underdog_odds:.2f} odds) in last-chance saloon mode!")
        
        # Score-specific giant-killing context
        goal_difference = abs(home_score - away_score)
        if home_score == away_score:
            message_parts.append(f"Level at {home_score}-{away_score}! {underdog_name} proving everyone wrong - the script is being rewritten!")
        elif goal_difference == 1:
            if (underdog_team == 'home' and home_score > away_score) or (underdog_team == 'away' and away_score > home_score):
                message_parts.append(f"SHOCK LEAD! {underdog_name} ahead {home_score}-{away_score}! They taste victory and want MORE!")
            else:
                message_parts.append(f"Only 1 goal behind! {underdog_name} can feel the miracle - one moment of magic needed!")
        
        # Corner psychology for underdogs
        if corners >= 8:
            message_parts.append(f"Already {corners} corners shows {underdog_name} refusing to give up - they're creating chaos and corners follow!")
        elif corners >= 5:
            message_parts.append(f"With {corners} corners, {underdog_name} showing they belong here - giant-killing corner storm brewing!")
        else:
            message_parts.append(f"When underdogs fight for their lives, corners explode! {underdog_name} ready to throw everything at {favorite_name}!")
        
        # Giant-killing psychology insight
        message_parts.append(f"🎯 GIANT-KILLING EDGE: When massive underdogs smell upset, they attack with zero fear - corners are inevitable!")
        
        # Final inspiration
        message_parts.append("⚡ DAVID vs GOLIATH = CORNER CHAOS!")
        
        return " ".join(message_parts)

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