#!/usr/bin/env python3
"""
FIRST HALF TELEGRAM ALERT SYSTEM
================================
Telegram alerts for first half Asian corner system targeting Market ID 63.

Sends alerts at 30-35 minutes for:
- Halftime Panic Favorites (heavy favorites under pressure)
- Halftime Giant Killers (massive underdogs defying odds)

Market: 63 "1st Half Asian Corners"
Same high standards and quality as late corner system!
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

class FirstHalfTelegramSystem:
    """First half telegram system for Market ID 63 alerts"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.sent_alerts = set()
        
        logger.info("🏁 FIRST HALF TELEGRAM SYSTEM INITIALIZING...")
        logger.info(f"   Bot token: {'✅ SET' if self.bot_token else '❌ MISSING'}")
        logger.info(f"   Chat ID: {'✅ SET' if self.chat_id else '❌ MISSING'}")
        logger.info(f"   Target Market: 63 '1st Half Asian Corners'")
        
        if self.bot_token and self.chat_id:
            logger.info("🎉 FIRST HALF TELEGRAM SYSTEM READY!")
        else:
            logger.error("❌ FIRST HALF TELEGRAM SYSTEM NOT CONFIGURED")
    
    def send_first_half_alert(self, match_data: Dict, alert_data: Dict) -> bool:
        """Send first half alert for Market ID 63"""
        
        if not self.bot_token or not self.chat_id:
            logger.error("❌ FIRST HALF TELEGRAM: Missing credentials")
            return False
        
        # Create unique alert ID
        match_id = match_data.get('fixture_id', 0)
        minute = match_data.get('minute', 30)
        tier = alert_data.get('alert_type', 'FIRST_HALF')
        alert_id = f"FH_{match_id}_{minute}_{tier}"
        
        if alert_id in self.sent_alerts:
            logger.info(f"📵 FIRST HALF TELEGRAM: Alert {alert_id} already sent")
            return True
        
        logger.info(f"🏁 FIRST HALF TELEGRAM ALERT STARTING...")
        logger.info(f"   Match ID: {match_id}")
        logger.info(f"   Tier: {tier}")
        logger.info(f"   Minute: {minute}")
        logger.info(f"   Alert ID: {alert_id}")
        
        # Get first half corner odds (Market ID 63)
        first_half_odds = self._get_first_half_corner_odds(match_data)
        
        if not first_half_odds:
            logger.info(f"🎯 FIRST HALF: No 1st half corner odds available - proceeding with psychology alert")
            first_half_odds = [f"1st Half Asian Corners: Over {match_data.get('total_corners', 0) + 1}.5"]
        
        logger.info(f"✅ FIRST HALF TELEGRAM: {len(first_half_odds)} odds found - PROCEEDING WITH ALERT")
        logger.info(f"   First half odds: {first_half_odds}")
        
        # Create first half message
        message = self._create_first_half_message(match_data, alert_data, first_half_odds)
        
        # Send via HTTP
        success = self._send_http_message(message)
        
        if success:
            self.sent_alerts.add(alert_id)
            logger.info(f"🎉 FIRST HALF TELEGRAM: Alert {alert_id} sent successfully!")
            return True
        else:
            logger.error(f"❌ FIRST HALF TELEGRAM: Alert {alert_id} failed!")
            return False
    
    def _get_first_half_corner_odds(self, match_data: Dict) -> list:
        """Extract first half corner odds (Market ID 63) from match data"""
        
        # Look for first half corner odds in odds data
        odds_data = match_data.get('odds_details', [])
        first_half_odds = []
        current_corners = match_data.get('total_corners', 0)
        
        for odds_str in odds_data:
            # Look for first half corner markets
            if any(keyword in odds_str.lower() for keyword in ['1st half', 'first half', 'half corner']):
                # Extract and validate
                try:
                    if "Over" in odds_str or "Under" in odds_str:
                        # Parse line value
                        if "Over" in odds_str:
                            parts = odds_str.replace("Over ", "").split(" = ")
                        else:
                            parts = odds_str.replace("Under ", "").split(" = ")
                        
                        if len(parts) >= 1:
                            line = float(parts[0])
                            
                            # Include whole numbers or .5 matching current corners
                            is_whole_number = line == int(line)
                            is_current_half = line == current_corners + 0.5
                            
                            if is_whole_number or is_current_half:
                                clean_odds = odds_str.replace(" (suspended)", "")
                                first_half_odds.append(clean_odds)
                                
                except (ValueError, TypeError):
                    # Include anyway if we can't parse
                    first_half_odds.append(odds_str)
        
        # If no specific first half odds found, generate recommendations
        if not first_half_odds:
            # Generate first half recommendations based on current corners
            next_corner = current_corners + 1
            first_half_odds = [
                f"1st Half Over {current_corners + 0.5} Asian Corners",
                f"1st Half Over {next_corner} Asian Corners" 
            ]
        
        return first_half_odds[:3]  # Max 3 odds
    
    def _create_first_half_message(self, match_data: Dict, alert_data: Dict, first_half_odds: list) -> str:
        """Create first half alert message"""
        
        # Extract match data
        home_team = match_data.get('home_team', 'Team A')
        away_team = match_data.get('away_team', 'Team B')
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        minute = match_data.get('minute', 30)
        corners = match_data.get('total_corners', 0)
        
        # Extract alert data
        alert_type = alert_data.get('alert_type', 'FIRST_HALF')
        combined_momentum = alert_data.get('combined_momentum', 0)
        tier = alert_data.get('tier', alert_type)
        
        # Determine header based on alert type
        if 'PANIC' in alert_type.upper():
            header = "🏁 HALFTIME PANIC FAVORITE ALERT 🏁"
            emoji = "🚨"
        elif 'UNDERDOG' in alert_type.upper() or 'GIANT' in alert_type.upper():
            header = "🥊 HALFTIME GIANT KILLER ALERT 🥊"
            emoji = "⚡"
        else:
            header = "🏁 FIRST HALF CORNER ALERT 🏁"
            emoji = "🎯"
        
        # Format first half odds
        odds_text = "\n".join(f"• {odd}" for odd in first_half_odds[:3])
        
        # Build momentum metrics (same format as late system)
        metrics_lines = []
        momentum_level = self._get_momentum_level(combined_momentum)
        metrics_lines.append(f"• Combined Momentum (Last 10min): {combined_momentum:.0f} pts - {momentum_level}")
        
        # Add first half betting recommendation
        next_corner = corners + 1
        metrics_lines.append(f"• 1st Half Asian Corners: Over {next_corner}")
        
        # Create psychology explanation
        why_text = self._create_first_half_psychology_message(alert_data, match_data)
        
        # Generate first half action recommendation
        action_text = f"1st Half Over {next_corner} Asian Corners"
        
        message = (
            f"{header}\n\n"
            f"<b>{home_team} vs {away_team}</b>\n"
            f"⚽ Score: {home_score}-{away_score} | ⏱️ {minute}' | 🚩 Corners: {corners}\n\n"
            f"<b>📊 FIRST HALF METRICS:</b>\n" + "\n".join(metrics_lines) + "\n\n"
            f"<b>🎯 WHY THIS FIRST HALF ALERT:</b>\n{why_text}\n\n"
            f"<b>⚡ ACTION:</b> {action_text}\n"
            f"<b>⏰ TIMING:</b> First half live betting available now\n"
            f"<b>💪 CONFIDENCE:</b> {self._get_first_half_confidence_text(tier)}\n\n"
            f"<i>First half alert sent at {datetime.now().strftime('%H:%M:%S')}</i>"
        )
        
        logger.info(f"📝 FIRST HALF TELEGRAM: Message created ({len(message)} chars)")
        logger.info(f"   Preview: {message[:100]}...")
        
        return message
    
    def _create_first_half_psychology_message(self, alert_data: Dict, match_data: Dict) -> str:
        """Create psychology explanation for first half alerts"""
        
        alert_type = alert_data.get('alert_type', '').upper()
        
        if 'PANIC' in alert_type:
            # Halftime panic favorite
            favorite_odds = alert_data.get('favorite_odds', 1.30)
            panic_description = alert_data.get('panic_description', 'Heavy favorite under pressure')
            home_score = match_data.get('home_score', 0)
            away_score = match_data.get('away_score', 0)
            minute = match_data.get('minute', 30)
            corners = match_data.get('total_corners', 0)
            
            return (
                f"🚨 HALFTIME PANIC: Heavy favorite ({favorite_odds:.2f}) in desperation mode! "
                f"{panic_description} 🎯 HALFTIME PSYCHOLOGY: Teams push hardest in final 15 minutes before break - "
                f"corners guaranteed when favorites panic! With {corners} corners already, the pressure cooker "
                f"is building for explosive halftime finish! ⚡ PANIC = CORNER STORM!"
            )
            
        elif 'UNDERDOG' in alert_type or 'GIANT' in alert_type:
            # Halftime giant killer
            underdog_odds = alert_data.get('underdog_odds', 4.00)
            giant_killing_description = alert_data.get('giant_killing_description', 'Massive underdog defying odds')
            home_score = match_data.get('home_score', 0)
            away_score = match_data.get('away_score', 0)
            minute = match_data.get('minute', 30)
            corners = match_data.get('total_corners', 0)
            
            return (
                f"🥊 HALFTIME GIANT-KILLING: Massive underdog ({underdog_odds:.2f}) writing their own story! "
                f"{giant_killing_description} 🎯 HALFTIME UPRISING: When underdogs smell upset, they attack "
                f"with zero fear before halftime - corners flow like water! With {corners} corners, the "
                f"giant-killing momentum is unstoppable! ⚡ DAVID vs GOLIATH = CORNER CHAOS!"
            )
        
        else:
            # Generic first half
            momentum = alert_data.get('combined_momentum', 0)
            return (
                f"🏁 FIRST HALF PRESSURE: Explosive {momentum:.0f} momentum points building toward halftime! "
                f"Teams know the break is coming - last chance to make their mark in first 45 minutes! "
                f"Halftime desperation creates corner opportunities! ⚡ FIRST HALF FINALE!"
            )
    
    def _get_momentum_level(self, momentum: float) -> str:
        """Get momentum intensity level for first half (same standards as late system)"""
        if momentum >= 180:
            return "Halftime corner storm explosive! 🔥🔥🔥"
        elif momentum >= 150:
            return "Extreme halftime pressure 🔥🔥"
        elif momentum >= 120:
            return "High halftime momentum 🔥"
        else:
            return "Building halftime pressure ⚡"
    
    def _get_first_half_confidence_text(self, tier: str) -> str:
        """Get confidence text for first half alerts"""
        if 'PANIC' in tier.upper():
            return "Halftime Panic Psychology System"
        elif 'UNDERDOG' in tier.upper() or 'GIANT' in tier.upper():
            return "Halftime Giant-Killing Psychology System"
        else:
            return "First Half Momentum System"
    
    def _send_http_message(self, message: str) -> bool:
        """Send message using simple HTTP request (same as late system)"""
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        try:
            logger.info(f"🌐 FIRST HALF HTTP: Sending to {url}")
            logger.info(f"   Payload size: {len(str(payload))} chars")
            
            response = requests.post(url, json=payload, timeout=10)
            
            logger.info(f"📡 FIRST HALF HTTP: Status {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"✅ FIRST HALF HTTP: Message sent successfully!")
                    logger.info(f"   Message ID: {result.get('result', {}).get('message_id', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ FIRST HALF HTTP: Telegram API error: {result}")
                    return False
            else:
                logger.error(f"❌ FIRST HALF HTTP: HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ FIRST HALF HTTP: Request timeout")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ FIRST HALF HTTP: Request error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ FIRST HALF HTTP: Unexpected error: {e}")
            return False