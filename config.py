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
    MIN_MINUTE_FOR_ALERT: int = 85  # Don't alert before 85th minute
    
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

# Scoring Matrix Configuration
SCORING_MATRIX = {
    # High Priority Indicators (4-5 points) - Prioritizing game state + reliable data
    'team_trailing_by_1_after_75min': 5,    # Enhanced: Prime corner scenario
    'draw_situation_after_75min': 4,        # New: Both teams pushing for goals
    'shots_on_target_last_15min_5plus': 5,  # Enhanced: More reliable data
    'shots_on_target_total_8plus': 4,       # Alternative threshold for total game
    'dangerous_attacks_last_10min_6plus': 4,
    'shots_blocked_total_6plus': 4,         # Reduced: Less reliable data
    'big_chances_created_last_15min_3plus': 4,
    
    # Medium Priority Indicators (2-4 points)
    'shots_total_second_half_10plus': 3,
    'shots_on_target_8plus_but_less_than_2_goals': 4,
    'shots_inside_box_last_20min_5plus': 4,  # Enhanced: Very high corner correlation
    'hit_woodwork_3plus': 4,  # Enhanced: Near misses create pressure
    'crosses_last_15min_8plus': 3,  # Enhanced: Failed crosses → corners
    'counter_attacks_last_15min_2plus': 2,
    
    # Tactical Indicators (1-3 points) - Enhanced corner-focused
    'attacking_sub_after_70min': 2,
    'offsides_last_15min_3plus': 2,  # Enhanced: Shows attacking urgency
    'throwins_last_20min_8plus': 2,  # Enhanced: Territory pressure indicator
    
    # Corner Count Context (7-12 corners now MANDATORY for elite alerts)
    'corners_8_to_11_sweet_spot': 3,     # Peak corner generation range
    'corners_7_baseline': 1,             # Minimum acceptable
    'corners_12_maximum': 1,             # Still acceptable but getting high
    
    # Negative Indicators
    'red_card_issued': -3,
    'leading_by_2_goals': -3,    # New: Comfortable lead reduces corner urgency
    'gk_making_8plus_saves': -1,
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