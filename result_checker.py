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
        self.api_token = os.getenv('SPORTMONKS_API_TOKEN')
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
            
            # Check if match is finished
            if match_data.get('state') != 'FT':
                logger.info(f"⏳ Match {fixture_id} not finished yet (Status: {match_data.get('state')})")
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
        """Get fixture final statistics from SportMonks"""
        
        url = f"{self.base_url}/fixtures/{fixture_id}"
        params = {
            'api_token': self.api_token,
            'include': 'scores;statistics',
            'filters': 'fixtureStatisticTypes:34'  # 34 = corner statistics
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data'):
                return data['data']
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
            
            for stat in statistics:
                if stat.get('type_id') == 34:  # Corner statistic
                    location = stat.get('location')
                    value = stat.get('data', {}).get('value', 0)
                    
                    if location == 'home':
                        home_corners = int(value)
                    elif location == 'away':
                        away_corners = int(value)
            
            total_corners = home_corners + away_corners
            logger.info(f"📊 Final corners: {home_corners} + {away_corners} = {total_corners}")
            
            return total_corners
            
        except Exception as e:
            logger.error(f"❌ Error extracting corners: {e}")
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