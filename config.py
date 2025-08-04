import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    # API Configuration
    SPORTMONKS_API_KEY: str = os.getenv('SPORTMONKS_API_KEY', '')
    SPORTMONKS_BASE_URL: str = 'https://api.sportmonks.com/v3/football'
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Scoring System Configuration
    ALERT_THRESHOLD: int = 6  # Minimum score to trigger alert
    # Timing Configuration
    MIN_MINUTE_FOR_ALERT: int = 85  # Don't alert before 85th minute
    MAX_MINUTE_FOR_ALERT: int = 87  # Don't alert after 87th minute

    # TIER 1 STRICT ELITE SYSTEM PARAMETERS
    ELITE_SCORE_THRESHOLD: float = 16.0     # TIER 1: Minimum elite score (was 8.0)
    ELITE_HIGH_PRIORITY_THRESHOLD: int = 3  # TIER 1: Minimum high priority count (was 2)
    ELITE_MIN_CORNERS: int = 6              # TIER 1: Minimum corners
    ELITE_MAX_CORNERS: int = 10             # TIER 1: Maximum corners (expanded from 8 for flexibility)
    ELITE_MIN_SHOTS_ON_TARGET: int = 7      # TIER 1: Minimum total shots on target
    ELITE_MAX_SHOTS_ON_TARGET: int = 9      # TIER 1: Maximum total shots on target
    ELITE_MIN_HIGH_PRIORITY: int = 3        # TIER 1: Minimum high priority indicators

    # Alert timing (extended window for better opportunity capture)
    TARGET_ALERT_MINUTE_MIN: int = 85  # Start of alert window
    TARGET_ALERT_MINUTE_MAX: int = 87  # End of alert window
    
    # Corner Count Sweet Spot (at 85th minute)
    CORNER_SWEET_SPOT_MIN: int = 8
    CORNER_SWEET_SPOT_MAX: int = 11
    
    # Monitoring Configuration
    LIVE_POLL_INTERVAL: int = 30  # Poll every 30 seconds (reduced from 15 to avoid rate limits)
    MATCH_DISCOVERY_INTERVAL: int = 300  # Check for new matches every 5 minutes
    MIN_MINUTE_TO_START_MONITORING: int = 60   # Start monitoring from 60th minute
    
    # Precise 85th Minute Alert Configuration
    TARGET_ALERT_MINUTE: int = 85  # Exact minute for alerts
    ALERT_WINDOW_START: int = 84  # Start checking from 84:50
    ALERT_WINDOW_END: int = 85   # Stop checking at 85:15
    
    # Rate Limiting
    API_RATE_LIMIT_DELAY: float = 1.0  # Increased delay between API calls (seconds)
    MAX_REQUESTS_PER_MINUTE: int = 100  # Conservative limit
    
    # Logging
    LOG_LEVEL: str = 'INFO'
    LOG_FILE: str = 'latecorners.log'

# TIER 1 STRICT ELITE CORNER ALERT CONFIGURATION
# ELITE_MIN_CORNERS = 6  # Tier 1: Minimum corners for elite alerts
# ELITE_MAX_CORNERS = 8  # Tier 1: Maximum corners for elite alerts (was 14)

# TIER 1 ELITE SCORE THRESHOLDS
# ELITE_SCORE_THRESHOLD = 16  # Tier 1: Minimum elite score (was 10)

# TIER 1 SHOTS ON TARGET RANGE  
# ELITE_MIN_SHOTS_ON_TARGET = 7  # Tier 1: Minimum total shots on target
# ELITE_MAX_SHOTS_ON_TARGET = 9  # Tier 1: Maximum total shots on target

# TIER 1 HIGH PRIORITY REQUIREMENTS
# ELITE_MIN_HIGH_PRIORITY = 3  # Tier 1: Minimum high priority indicators (was 1)

# Scoring Matrix Configuration
SCORING_MATRIX = {
    # Corner count scoring - focused on 6-8 range
    'corners_6_premium': 2.0,   # Premium scoring for 6 corners
    'corners_7_premium': 2.5,   # Peak scoring for 7 corners  
    'corners_8_premium': 2.0,   # Premium scoring for 8 corners
    
    # High Priority Indicators (4-5 points) - Prioritizing game state + reliable data
    'team_trailing_by_1_after_75min': 5,    # Enhanced: Prime corner scenario
    'draw_situation_after_75min': 4,        # New: Both teams pushing for goals
    'shots_on_target_last_15min_5plus': 5,  # Enhanced: More reliable data
    'shots_on_target_total_8plus': 4,       # Alternative threshold for total game
    'dangerous_attacks_2nd_half_30plus': 4, # Updated: Realistic threshold based on live data analysis
    'shots_blocked_total_6plus': 4,         # Reduced: Less reliable data
    'big_chances_created_last_15min_3plus': 4,
    
    # Medium Priority Indicators (2-4 points)
    'shots_total_second_half_10plus': 3,
    'shots_on_target_8plus_but_less_than_2_goals': 4,
    'shots_inside_box_last_20min_5plus': 4,  # Enhanced: Very high corner correlation
    'hit_woodwork_3plus': 4,  # Enhanced: Near misses create pressure
    'crosses_last_15min_8plus': 3,  # Enhanced: Failed crosses → corners
    'counter_attacks_last_15min_2plus': 2,
    'key_passes_last_10min_4plus': 2,  # Missing key added
    'throwins_last_20min_6plus': 2,   # Missing key added
    'offsides_last_15min_2plus': 2,   # Missing key added
    
    # Tactical Indicators (1-3 points) - Enhanced corner-focused
    'attacking_sub_after_70min': 2,
    'offsides_last_15min_3plus': 2,  # Enhanced: Shows attacking urgency
    'throwins_last_20min_8plus': 2,  # Enhanced: Territory pressure indicator
    
    # Corner Count Context - TIER 1 focused (6-8 only)
    'corners_6_low': 0.5,                # Baseline
    'corners_7_baseline': 1,             # Good potential
    'corners_8_to_11_sweet_spot': 3,     # Peak range
    'corners_12_maximum': 1,             # High but acceptable
    'corners_13_14_high': 0,             # Remove high corner scoring for TIER 1
    
    # REMOVED ALL NEGATIVE INDICATORS - ONLY POSITIVE SCORING
    'red_card_issued': 0,        # No penalty
    'leading_by_2_goals': 0,     # No penalty for TIER 1
    'gk_making_8plus_saves': 0,  # No penalty
}

# Historical multipliers
HISTORICAL_MULTIPLIERS = {
    'team_averages_6plus_corners_per_game': 1.3,
    'head_to_head_avg_10plus_corners': 1.2,
    'home_team_losing_at_home': 1.4,
    'derby_rivalry_match': 1.2,
}



def get_config() -> Config:
    """Get configuration instance with validation."""
    config = Config()
    
    # Validate required API keys
    if not config.SPORTMONKS_API_KEY:
        raise ValueError("SPORTMONKS_API_KEY environment variable is required")
    
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
    if not config.TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID environment variable is required")
    
    return config 