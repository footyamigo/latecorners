import asyncio
import logging
from typing import Dict, Optional
from telegram import Bot
from telegram.error import TelegramError

from config import get_config
from scoring_engine import ScoringResult

class TelegramNotifier:
    """Handles Telegram notifications for corner betting alerts"""
    
    def __init__(self):
        self.config = get_config()
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        self.chat_id = self.config.TELEGRAM_CHAT_ID
        self.logger = logging.getLogger(__name__)
        
        # Track sent alerts to avoid duplicates
        self.sent_alerts = set()
    
    async def send_corner_alert(self, scoring_result: ScoringResult, 
                               match_info: Dict, corner_odds: Optional[Dict] = None):
        """Send a corner betting alert via Telegram"""
        
        # Create unique alert ID to prevent duplicates
        alert_id = f"{scoring_result.fixture_id}_{scoring_result.minute}_{int(scoring_result.total_score)}"
        
        if alert_id in self.sent_alerts:
            self.logger.debug(f"Alert {alert_id} already sent, skipping")
            return
        
        try:
            message = self._format_alert_message(scoring_result, match_info, corner_odds)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            # Mark as sent
            self.sent_alerts.add(alert_id)
            
            self.logger.info(f"Corner alert sent for fixture {scoring_result.fixture_id}")
            
        except TelegramError as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error sending alert: {e}")
    
    def _format_alert_message(self, scoring_result: ScoringResult, 
                             match_info: Dict, corner_odds: Optional[Dict]) -> str:
        """Format the alert message for Telegram"""
        
        # Extract match details
        home_team = match_info.get('home_team', 'Home Team')
        away_team = match_info.get('away_team', 'Away Team')
        league = match_info.get('league', 'Unknown League')
        score = f"{match_info.get('home_score', 0)}-{match_info.get('away_score', 0)}"
        
        # Header with emoji
        message = f"🚨 <b>LATE CORNER ALERT</b> 🚨\n\n"
        
        # Match details
        message += f"<b>{home_team} vs {away_team}</b>\n"
        message += f"📊 Score: {score} | ⏱️ {scoring_result.minute}'\n"
        message += f"🏆 {league}\n\n"
        
        # Scoring details
        message += f"<b>🎯 ALERT SCORE: {scoring_result.total_score:.1f}</b>\n"
        message += f"(Threshold: {self.config.ALERT_THRESHOLD})\n\n"
        
        # Live match statistics
        message += f"<b>📊 Live Stats:</b>\n"
        message += f"🚩 Corners: {match_info.get('home_corners', 0)} - {match_info.get('away_corners', 0)}\n"
        message += f"⚽ Total Shots: {match_info.get('home_shots', 0)} - {match_info.get('away_shots', 0)}\n"
        message += f"🎯 Shots on Target: {match_info.get('home_shots_on_target', 0)} - {match_info.get('away_shots_on_target', 0)}\n"
        message += f"⚡ Total Attacks: {match_info.get('home_attacks', 0)} - {match_info.get('away_attacks', 0)}\n\n"
        
        # Key conditions (top 5)
        message += f"<b>🔥 Key Conditions:</b>\n"
        for i, condition in enumerate(scoring_result.triggered_conditions[:5], 1):
            message += f"{i}. {condition}\n"
        
        if len(scoring_result.triggered_conditions) > 5:
            remaining = len(scoring_result.triggered_conditions) - 5
            message += f"... +{remaining} more conditions\n"
        
        message += "\n"
        
        # Betting recommendation
        message += f"<b>💰 BETTING RECOMMENDATION:</b>\n"
        message += f"<i>Asian Over 1 Corner</i>\n"
        message += f"• Get money back if exactly 1 corner\n"
        message += f"• Win if 2+ corners\n"
        message += f"• Optimal entry: NOW (85th minute sweet spot)\n\n"
        
        # Live odds (if available) - Only Bet365
        if corner_odds:
            message += f"<b>📊 Live Corner Odds:</b>\n"
            
            # Filter for Bet365 odds only
            bet365_odds = {k: v for k, v in corner_odds.items() if 'bet365' in k.lower()}
            
            if bet365_odds:
                for odds_key, odds_data in bet365_odds.items():
                    selection = odds_data['selection']
                    odds = odds_data['odds']
                    message += f"• Bet365: {selection} @ {odds}\n"
            else:
                # Fallback to first available if no Bet365
                first_odds = list(corner_odds.items())[0]
                bookmaker = first_odds[0].split('_')[0]
                selection = first_odds[1]['selection']
                odds = first_odds[1]['odds']
                message += f"• {bookmaker}: {selection} @ {odds}\n"
            
            message += "\n"
        else:
            message += f"<i>⚠️ Live odds not available - check your bookmaker</i>\n\n"
        
        # Match context
        message += f"<b>📋 Context:</b> {scoring_result.match_context}\n\n"
        
        # Footer
        message += f"<i>🤖 Late Corner Bot | Time: {scoring_result.minute}'</i>"
        
        return message
    
    async def send_test_alert(self, match_info: Dict):
        """Send a test alert for 85th minute (for bot testing purposes)"""
        
        try:
            message = f"🧪 <b>TEST ALERT - 85TH MINUTE REACHED</b>\n\n"
            message += f"⚠️ <i>This is NOT a corner bet alert!</i>\n"
            message += f"📡 <i>Testing Telegram bot functionality</i>\n\n"
            
            message += f"<b>⚽ Match Details:</b>\n"
            message += f"🏠 <b>{match_info['home_team']}</b> vs <b>{match_info['away_team']}</b>\n"
            message += f"⏱️ <b>{match_info['minute']}'</b> | Score: <b>{match_info['home_score']}-{match_info['away_score']}</b>\n"
            message += f"🏆 League: {match_info['league']}\n\n"
            
            message += f"<b>📊 Current Stats:</b>\n"
            if match_info.get('corners'):
                message += f"🚩 Corners: {match_info['corners']['home']} - {match_info['corners']['away']}\n"
            if match_info.get('shots'):
                message += f"⚽ Shots: {match_info['shots']['home']} - {match_info['shots']['away']}\n"
            if match_info.get('attacks'):
                message += f"⚡ Attacks: {match_info['attacks']['home']} - {match_info['attacks']['away']}\n"
            
            message += f"\n<i>🤖 Telegram Bot Test | Time: {match_info['minute']}'</i>"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            self.logger.info(f"Test alert sent for match {match_info['home_team']} vs {match_info['away_team']}")
            
        except TelegramError as e:
            self.logger.error(f"Failed to send test alert: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error sending test alert: {e}")

    async def send_system_message(self, message: str, level: str = "INFO"):
        """Send a system status message"""
        try:
            if level == "ERROR":
                formatted_message = f"❌ <b>SYSTEM ERROR</b>\n\n{message}"
            elif level == "WARNING":
                formatted_message = f"⚠️ <b>SYSTEM WARNING</b>\n\n{message}"
            else:
                formatted_message = f"ℹ️ <b>SYSTEM INFO</b>\n\n{message}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=formatted_message,
                parse_mode='HTML'
            )
            
        except TelegramError as e:
            self.logger.error(f"Failed to send system message: {e}")
    
    async def send_startup_message(self):
        """Send a message when the bot starts up"""
        message = (
            "🚀 <b>Late Corner Bot Started</b>\n\n"
            "✅ Connected to Sportmonks API\n"
            "✅ Monitoring live matches\n"
            "🎯 Alert threshold: 6+ points\n"
            "⏱️ Monitoring from 85th minute\n"
            "🎲 Sweet spot: 8-11 total corners\n\n"
            "<i>Ready to find profitable late corner opportunities!</i>"
        )
        
        await self.send_system_message(message)
    
    async def test_connection(self) -> bool:
        """Test the Telegram bot connection"""
        try:
            # Send a simple test message
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="🧪 <b>Connection Test</b>\n\nTelegram bot is working correctly!",
                parse_mode='HTML'
            )
            return True
            
        except TelegramError as e:
            self.logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def clear_sent_alerts(self):
        """Clear the sent alerts cache (useful for testing)"""
        self.sent_alerts.clear()
        self.logger.info("Sent alerts cache cleared")

# Utility function for non-async usage
def send_alert_sync(scoring_result: ScoringResult, match_info: Dict, 
                   corner_odds: Optional[Dict] = None):
    """Synchronous wrapper for sending alerts"""
    notifier = TelegramNotifier()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(
        notifier.send_corner_alert(scoring_result, match_info, corner_odds)
    ) 