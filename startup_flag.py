#!/usr/bin/env python3
"""
Simple utility to track first startup and prevent spam messages
"""

import os
from datetime import datetime

STARTUP_FLAG_FILE = '/tmp/latecorners_started' if os.name != 'nt' else 'latecorners_started.txt'

def is_first_startup() -> bool:
    """Check if this is the first startup since deployment"""
    if os.path.exists(STARTUP_FLAG_FILE):
        return False
    
    # Create the flag file
    try:
        with open(STARTUP_FLAG_FILE, 'w') as f:
            f.write(f"Started at: {datetime.now().isoformat()}\n")
        return True
    except Exception:
        # If we can't create the file, assume it's first startup
        return True

def mark_startup():
    """Mark that the app has started up"""
    try:
        with open(STARTUP_FLAG_FILE, 'w') as f:
            f.write(f"Started at: {datetime.now().isoformat()}\n")
    except Exception:
        pass  # Ignore errors 