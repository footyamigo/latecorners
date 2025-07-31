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
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🤖 INITIALIZING TELEGRAM BOT...")
        
        try:
            self.config = get_config()
            
            # Check bot token
            bot_token = self.config.TELEGRAM_BOT_TOKEN
            if not bot_token:
                self.logger.error(f"❌ TELEGRAM_BOT_TOKEN not configured!")
                self.bot = None
            else:
                self.logger.info(f"✅ Bot token configured (ending: ...{bot_token[-10:]})")
                self.bot = Bot(token=bot_token)
                self.logger.info(f"✅ Telegram Bot object created")
            
            # Check chat ID
            chat_id = self.config.TELEGRAM_CHAT_ID
            if not chat_id:
                self.logger.error(f"❌ TELEGRAM_CHAT_ID not configured!")
                self.chat_id = None
            else:
                self.logger.info(f"✅ Chat ID configured: {chat_id}")
                self.chat_id = chat_id
            
            # Track sent alerts to avoid duplicates
            self.sent_alerts = set()
            
            if self.bot and self.chat_id:
                self.logger.info(f"🎉 TELEGRAM BOT READY FOR ALERTS!")
            else:
                self.logger.warning(f"⚠️ TELEGRAM BOT NOT FULLY CONFIGURED")
                
        except Exception as e:
            self.logger.error(f"❌ TELEGRAM BOT INITIALIZATION FAILED:")
            self.logger.error(f"   Error: {type(e).__name__}: {str(e)}")
            self.bot = None
            self.chat_id = None
            self.sent_alerts = set()
    
    async def send_corner_alert(self, scoring_result: ScoringResult, 
                               match_info: Dict, corner_odds: Optional[Dict] = None):
        """Send a corner betting alert via Telegram"""
        
        # Create unique alert ID to prevent duplicates
        alert_id = f"{scoring_result.fixture_id}_{scoring_result.minute}_{int(scoring_result.total_score)}"
        
        self.logger.info(f"🚀 TELEGRAM ALERT ATTEMPT: {alert_id}")
        self.logger.info(f"   Match: {match_info.get('home_team')} vs {match_info.get('away_team')}")
        self.logger.info(f"   Tier: {match_info.get('tier', 'UNKNOWN')}")
        self.logger.info(f"   Score: {scoring_result.total_score}")
        
        if alert_id in self.sent_alerts:
            self.logger.warning(f"📵 ALERT DUPLICATE: {alert_id} already sent, skipping")
            return True  # Already sent successfully
        
        # Configuration verification
        if not self.bot:
            self.logger.error(f"❌ TELEGRAM BOT NOT INITIALIZED")
            return False
            
        if not self.chat_id:
            self.logger.error(f"❌ TELEGRAM CHAT_ID NOT SET")
            return False
        
        self.logger.info(f"📱 TELEGRAM CONFIG: Bot initialized, Chat ID: {self.chat_id}")
        
        try:
            # Format message with detailed logging
            self.logger.info(f"📝 FORMATTING MESSAGE...")
            message = self._format_alert_message(scoring_result, match_info, corner_odds)
            
            # Log message preview (first 200 chars)
            preview = message[:200] + "..." if len(message) > 200 else message
            self.logger.info(f"📄 MESSAGE PREVIEW: {preview}")
            self.logger.info(f"📊 MESSAGE LENGTH: {len(message)} characters")
            
            # Attempt to send
            self.logger.info(f"📤 SENDING TO TELEGRAM...")
            self.logger.info(f"   Chat ID: {self.chat_id}")
            self.logger.info(f"   Parse mode: HTML")
            
            response = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            # Log successful response
            self.logger.info(f"✅ TELEGRAM SUCCESS!")
            self.logger.info(f"   Message ID: {response.message_id}")
            self.logger.info(f"   Date: {response.date}")
            
            # Mark as sent
            self.sent_alerts.add(alert_id)
            
            self.logger.info(f"🎉 CORNER ALERT SENT SUCCESSFULLY for fixture {scoring_result.fixture_id}")
            return True  # Success
            
        except TelegramError as e:
            self.logger.error(f"❌ TELEGRAM API ERROR:")
            self.logger.error(f"   Error type: {type(e).__name__}")
            self.logger.error(f"   Error message: {str(e)}")
            self.logger.error(f"   Error code: {getattr(e, 'error_code', 'N/A')}")
            self.logger.error(f"   Description: {getattr(e, 'description', 'N/A')}")
            return False  # Failed
        except Exception as e:
            self.logger.error(f"❌ UNEXPECTED ERROR SENDING ALERT:")
            self.logger.error(f"   Error type: {type(e).__name__}")
            self.logger.error(f"   Error message: {str(e)}")
            import traceback
            self.logger.error(f"   Traceback: {traceback.format_exc()}")
            return False  # Failed
    
    def _format_alert_message(self, scoring_result: ScoringResult, 
                             match_info: Dict, corner_odds: Optional[Dict]) -> str:
        """Format the alert message for Telegram"""
        
        # Extract match details
        home_team = match_info.get('home_team', 'Home Team')
        away_team = match_info.get('away_team', 'Away Team')
        league = match_info.get('league', 'Unknown League')
        score = f"{match_info.get('home_score', 0)}-{match_info.get('away_score', 0)}"
        tier = match_info.get('tier', 'ELITE')
        
        # Header with tier-specific emoji and title
        if tier == "ELITE":
            message = f"🏆 <b>ELITE CORNER ALERT</b> 🏆\n\n"
        else:
            message = f"💎 <b>PREMIUM CORNER ALERT</b> 💎\n\n"
        
        # Match details
        message += f"<b>{home_team} vs {away_team}</b>\n"
        message += f"📊 Score: {score} | ⏱️ {scoring_result.minute}'\n"
        message += f"🏆 {league}\n\n"
        
        # Scoring details with tier-specific thresholds
        if tier == "ELITE":
            message += f"<b>🎯 ELITE SCORE: {scoring_result.total_score:.1f}/8.0</b>\n"
            message += f"⭐ High Priority: {match_info.get('high_priority_count', 0)}/2\n"
            message += f"(Ultra-selective: 8+ score, 2+ priority, 84-85')\n\n"
        else:
            message += f"<b>🎯 PREMIUM SCORE: {scoring_result.total_score:.1f}/6.0</b>\n"
            message += f"⭐ High Priority: {match_info.get('high_priority_count', 0)}/1\n"
            message += f"(Accessible: 6+ score, 1+ priority, 82-87')\n\n"
        
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