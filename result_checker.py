#!/usr/bin/env python3
"""
Result Checker - Check Final Corner Results
==========================================
Hourly check of finished matches to determine bet outcomes.
"""

import asyncio
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List
from database import get_database

logger = logging.getLogger(__name__)

class ResultChecker:
    """Check final results of elite alert matches"""
    
    def __init__(self):
        self.db = get_database()
        self.api_token = os.getenv('SPORTMONKS_API_KEY')
        self.base_url = "https://api.sportmonks.com/v3/football"
    
    async def check_all_pending_results(self):
        """Check results for all unfinished alerts"""
        
        logger.info("🔍 RESULT CHECKER: Starting hourly check...")
        
        if not self.api_token:
            logger.error("❌ SportMonks API token not found")
            return
        
        unfinished_alerts = self.db.get_unfinished_alerts()
        
        if not unfinished_alerts:
            logger.info("✅ No pending alerts to check")
            return
        
        logger.info(f"🔍 Checking {len(unfinished_alerts)} pending alerts...")
        
        for alert in unfinished_alerts:
            try:
                await self._check_single_alert(alert)
                # Small delay between API calls to respect rate limits
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Error checking alert {alert['id']}: {e}")
        
        # Show summary after checking
        self._log_performance_summary()
    
    async def _check_single_alert(self, alert: Dict):
        """Check result for a single alert"""
        
        fixture_id = alert['fixture_id']
        logger.info(f"🔍 Checking fixture {fixture_id}: {alert['teams']}")
        
        try:
            # Get fixture with final statistics
            match_data = await self._get_fixture_final_stats(fixture_id)
            
            if not match_data:
                logger.warning(f"⚠️ No data for fixture {fixture_id}")
                return
            
            # Check if match is finished (empty response means not finished)
            if not match_data:
                logger.info(f"⏳ Match {fixture_id} not finished yet")
                return
            
            # Double-check state if available
            state = match_data.get('state', {})
            match_state = state.get('state') if isinstance(state, dict) else state
            
            if match_state and match_state != 'FT':
                logger.info(f"⏳ Match {fixture_id} not finished yet (Status: {match_state})")
                return
            
            # Get final corner count
            final_corners = self._extract_corner_count(match_data)
            
            if final_corners is None:
                logger.warning(f"⚠️ Could not extract final corners for fixture {fixture_id}")
                return
            
            # Calculate result
            result = self._calculate_over_result(alert['over_line'], final_corners)
            
            # Update database
            success = self.db.update_alert_result(alert['id'], final_corners, result)
            
            if success:
                logger.info(f"✅ RESULT UPDATED: {alert['teams']}")
                logger.info(f"   Alert: {alert['corners_at_alert']} corners @ 85' → Over {alert['over_line']}")
                logger.info(f"   Final: {final_corners} corners → {result}")
            
        except Exception as e:
            logger.error(f"❌ Error checking fixture {fixture_id}: {e}")
    
    async def _get_fixture_final_stats(self, fixture_id: int) -> Dict:
        """Get fixture final statistics using correct SportMonks API approach"""
        
        # Method 1: Check if fixture is in finished fixtures list (fixtureStates:5)
        finished_url = f"{self.base_url}/fixtures"
        finished_params = {
            'api_token': self.api_token,
            'filters': f'fixtureStates:5;fixtures:{fixture_id}',  # State 5 = finished
            'include': 'statistics'
        }
        
        try:
            logger.info(f"🔍 Checking if fixture {fixture_id} is in finished fixtures list...")
            response = requests.get(finished_url, params=finished_params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                logger.info("✅ Match found in finished fixtures list!")
                # Don't return finished fixtures data - get individual fixture for accurate stats
                logger.info("🔄 Getting individual fixture for accurate statistics...")
                
                individual_url = f"{self.base_url}/fixtures/{fixture_id}"
                individual_params = {
                    'api_token': self.api_token,
                    'include': 'statistics'
                }
                
                response = requests.get(individual_url, params=individual_params, timeout=10)
                response.raise_for_status()
                
                individual_data = response.json()
                
                if individual_data.get('data'):
                    logger.info("✅ Individual fixture data retrieved for accurate corner count")
                    return individual_data['data']
                else:
                    logger.warning("⚠️ Individual fixture data not found, using finished fixtures data")
                    return data['data'][0]
            
            # Method 2: Check individual fixture with statistics
            logger.info(f"📊 Checking individual fixture {fixture_id}...")
            individual_url = f"{self.base_url}/fixtures/{fixture_id}"
            individual_params = {
                'api_token': self.api_token,
                'include': 'statistics'
            }
            
            response = requests.get(individual_url, params=individual_params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data'):
                fixture_data = data['data']
                
                # Check if match is finished using state
                state = fixture_data.get('state', {})
                match_state = state.get('state')
                
                logger.info(f"📊 Match state: {match_state}")
                
                if match_state == 'FT':  # Full Time
                    logger.info("✅ Match confirmed as finished (FT state)")
                    return fixture_data
                else:
                    logger.info(f"⏳ Match not finished yet (Status: {match_state})")
                    return {}
            else:
                logger.warning(f"⚠️ No data returned for fixture {fixture_id}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed for fixture {fixture_id}: {e}")
            return {}
    
    def _extract_corner_count(self, match_data: Dict) -> int:
        """Extract total corner count from match statistics"""
        
        try:
            statistics = match_data.get('statistics', [])
            
            home_corners = 0
            away_corners = 0
            
            logger.info(f"🔍 Analyzing {len(statistics)} statistics for corner data...")
            
            for i, stat in enumerate(statistics):
                if stat.get('type_id') == 34:  # Corner statistic (reverted to correct Type 34)
                    location = stat.get('location')
                    value = stat.get('data', {}).get('value', 0)
                    participant_id = stat.get('participant_id')
                    
                    logger.info(f"   📊 Corner stat {i}: location='{location}', value={value}, participant={participant_id}")
                    
                    if location == 'home':
                        home_corners = int(value)
                        logger.info(f"   ✅ Home corners updated to: {home_corners}")
                    elif location == 'away':
                        away_corners = int(value)
                        logger.info(f"   ✅ Away corners updated to: {away_corners}")
                    else:
                        logger.warning(f"   ⚠️ Unknown location: '{location}'")
            
            total_corners = home_corners + away_corners
            logger.info(f"📊 FINAL EXTRACTION: {home_corners} (home) + {away_corners} (away) = {total_corners} total")
            
            if total_corners == 0:
                logger.warning("⚠️ Zero corners detected - possible data extraction issue")
                # Log first few non-corner stats for debugging
                logger.info("🔍 Sample of other statistics:")
                for i, stat in enumerate(statistics[:5]):
                    logger.info(f"   Stat {i}: type_id={stat.get('type_id')}, location={stat.get('location')}")
            
            return total_corners
            
        except Exception as e:
            logger.error(f"❌ Error extracting corner count: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_over_result(self, over_line: str, final_corners: int) -> str:
        """Calculate if over bet won, lost, or refunded"""
        
        try:
            line = float(over_line)
            
            if final_corners > line:
                return "WIN"
            elif final_corners == line:
                # This rarely happens with .5 lines, but possible with whole numbers
                return "REFUND"
            else:
                return "LOSS"
                
        except ValueError:
            logger.error(f"❌ Invalid over line: {over_line}")
            return "UNKNOWN"
    
    def _log_performance_summary(self):
        """Log current performance statistics"""
        
        stats = self.db.get_performance_stats()
        
        if stats:
            logger.info("📈 CURRENT PERFORMANCE:")
            logger.info(f"   📊 Total: {stats['total_alerts']} alerts")
            logger.info(f"   ✅ Wins: {stats['wins']}")
            logger.info(f"   ❌ Losses: {stats['losses']}")  
            logger.info(f"   🔄 Refunds: {stats['refunds']}")
            logger.info(f"   ⏳ Pending: {stats['pending']}")
            logger.info(f"   🎯 Win Rate: {stats['win_rate']}%")

# Global checker instance
result_checker = ResultChecker()

async def check_pending_results():
    """Global function to check pending results"""
    await result_checker.check_all_pending_results()

if __name__ == "__main__":
    # For testing
    asyncio.run(check_pending_results()) 