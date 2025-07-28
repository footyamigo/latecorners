#!/usr/bin/env python3
"""
Railway-optimized startup script for Late Corner Monitor
"""

import os
import sys
import asyncio

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'SPORTMONKS_API_KEY',
        'TELEGRAM_BOT_TOKEN', 
        'TELEGRAM_CHAT_ID'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Set these in Railway Variables tab")
        sys.exit(1)
    
    print("✅ All environment variables configured")

def main():
    """Main startup function"""
    print("🚂 Starting Late Corner Monitor on Railway...")
    
    # Check environment
    check_environment()
    
    # Import and run main application
    try:
        from main import main as run_main
        asyncio.run(run_main())
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 