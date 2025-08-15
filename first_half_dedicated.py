#!/usr/bin/env python3
"""
DEDICATED FIRST HALF CORNER ALERT SYSTEM
========================================
Simple, standalone system for first half alerts (30-35 minutes).
NO shared data dependencies - direct API calls only.
"""

import asyncio
import logging
import time
from datetime import datetime
import sys
import os

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from database_postgres import get_database
from sportmonks_client import SportmonksClient

class DedicatedFirstHalfSystem:
    """Dedicated First Half monitoring system - independent and simple"""
    
    def __init__(self):
        self.config = get_config()
        self.api_client = SportmonksClient()
        self.database = get_database()
        self.alerted_matches = set()
        
        # Setup logging
        self.logger = logging.getLogger('first_half_dedicated')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - FIRST_HALF_DEDICATED - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("🚀 DEDICATED FIRST HALF SYSTEM INITIALIZED")
        self.logger.info("   Target: 30-35 minutes")
        self.logger.info("   Market: 1st Half Asian Corners")
        self.logger.info("   Mode: Direct API calls (no shared data)")
    
    def get_live_matches(self):
        """Get live matches directly from API"""
        try:
            matches = self.api_client.get_live_matches(filter_by_minute=False)
            return matches or []
        except Exception as e:
            self.logger.error(f"Error fetching live matches: {e}")
            return []
    
    def is_first_half_match(self, match):
        """Check if match is in first half and 30-35 minute window"""
        try:
            minute = match.get('minute', 0)
            state = match.get('state', {}).get('short_name', '')
            
            # Must be 30-35 minutes and in first half
            if not (30 <= minute <= 35):
                return False
            
            # Must be first half state
            if state not in ['1H', 'LIVE']:  # Accept both 1H and general LIVE
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking first half match: {e}")
            return False
    
    def extract_basic_stats(self, match):
        """Extract basic match stats for momentum"""
        try:
            fixture_id = match.get('id')
            minute = match.get('minute', 0)
            home_team = match.get('localteam', {}).get('name', 'Home')
            away_team = match.get('visitorteam', {}).get('name', 'Away')
            
            # Get scores
            home_score = 0
            away_score = 0
            if 'scores' in match:
                for score in match['scores']:
                    if score.get('score') == 'localteam':
                        home_score = score.get('goal', 0)
                    elif score.get('score') == 'visitorteam':
                        away_score = score.get('goal', 0)
            
            # Count corners
            corners = 0
            if 'events' in match:
                for event in match['events']:
                    if event.get('type', {}).get('name') == 'corner':
                        corners += 1
            
            return {
                'fixture_id': fixture_id,
                'minute': minute,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'corners': corners
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting stats: {e}")
            return None
    
    def should_alert(self, stats):
        """Simple alert criteria for first half"""
        try:
            # Basic criteria for first half alerts
            minute = stats['minute']
            corners = stats['corners']
            
            # Must be in timing window
            if not (30 <= minute <= 35):
                return False, "Outside timing window"
            
            # Must have some corner activity
            if corners < 2:
                return False, "Insufficient corners"
            
            # Simple momentum check - if we're at 30+ minutes with 2+ corners, it's promising
            return True, f"First half opportunity: {corners} corners at {minute}'"
            
        except Exception as e:
            self.logger.error(f"Error checking alert criteria: {e}")
            return False, "Error in criteria check"
    
    def send_first_half_alert(self, stats, reason):
        """Send simple first half alert"""
        try:
            # Simple alert info for database
            alert_info = {
                'fixture_id': stats['fixture_id'],
                'home_team': stats['home_team'],
                'away_team': stats['away_team'],
                'home_score': stats['home_score'],
                'away_score': stats['away_score'],
                'minute': stats['minute'],
                'total_corners': stats['corners'],
                'tier': 'FIRST_HALF_OPPORTUNITY',
                'alert_type': 'FIRST_HALF_ASIAN_CORNERS',
                'total_probability': 75.0,
                'team_probability': None,
                'conditions': reason,
                'active_odds': ['1st Half Asian Corners - Check Live Markets'],
                'odds_details': ['1st Half Over X.5 Corners'],
                'market_type': '1st_half_asian_corners',
                'market_id': 63
            }
            
            # Save to database
            success = self.database.save_alert(alert_info)
            
            if success:
                self.logger.info(f"✅ FIRST HALF ALERT SAVED: {stats['home_team']} vs {stats['away_team']}")
                self.logger.info(f"   Minute: {stats['minute']}', Corners: {stats['corners']}")
                self.logger.info(f"   Reason: {reason}")
                return True
            else:
                self.logger.error("❌ Failed to save first half alert")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False
    
    async def monitor_cycle(self):
        """Single monitoring cycle"""
        try:
            # Get live matches
            matches = self.get_live_matches()
            
            if not matches:
                self.logger.debug("No live matches found")
                return
            
            self.logger.info(f"🔍 FIRST HALF: Processing {len(matches)} live matches")
            
            # Filter for first half matches
            first_half_matches = [m for m in matches if self.is_first_half_match(m)]
            
            if not first_half_matches:
                self.logger.info(f"   No matches in 30-35 minute first half window (total: {len(matches)})")
                return
            
            self.logger.info(f"🎯 FIRST HALF: Found {len(first_half_matches)} matches in 30-35 minute window!")
            
            # Process each match
            for match in first_half_matches:
                try:
                    stats = self.extract_basic_stats(match)
                    if not stats:
                        continue
                    
                    fixture_id = stats['fixture_id']
                    
                    # Skip if already alerted
                    if fixture_id in self.alerted_matches:
                        continue
                    
                    self.logger.info(f"📊 ANALYZING: {stats['home_team']} vs {stats['away_team']} ({stats['minute']}')")
                    self.logger.info(f"   Score: {stats['home_score']}-{stats['away_score']}, Corners: {stats['corners']}")
                    
                    # Check if should alert
                    should_alert, reason = self.should_alert(stats)
                    
                    if should_alert:
                        # Send alert
                        if self.send_first_half_alert(stats, reason):
                            self.alerted_matches.add(fixture_id)
                            self.logger.info(f"🚨 FIRST HALF ALERT SENT!")
                        else:
                            self.logger.error(f"❌ Failed to send alert")
                    else:
                        self.logger.info(f"   ⏭️ No alert: {reason}")
                
                except Exception as e:
                    self.logger.error(f"Error processing match: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error in monitor cycle: {e}")
    
    async def run(self):
        """Main monitoring loop"""
        self.logger.info("🚀 DEDICATED FIRST HALF MONITOR STARTING")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 First Half Cycle {cycle_count}")
                
                await self.monitor_cycle()
                
                # Wait 30 seconds
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 First Half monitor stopped")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in main loop: {e}")
                await asyncio.sleep(60)

async def main():
    """Entry point"""
    system = DedicatedFirstHalfSystem()
    await system.run()

if __name__ == "__main__":
    asyncio.run(main())