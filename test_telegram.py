#!/usr/bin/env python3

"""
Test script for Telegram bot connection
Run this to verify your Telegram setup is working
"""

import asyncio
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Loaded .env file")
    else:
        print("❌ No .env file found!")
        sys.exit(1)
except ImportError:
    print("Installing python-dotenv...")
    import os
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

# Test the Telegram bot
async def test_telegram():
    try:
        from telegram_bot import TelegramNotifier
        
        print("🧪 Testing Telegram bot connection...")
        
        notifier = TelegramNotifier()
        
        # Test basic connection
        success = await notifier.test_connection()
        
        if success:
            print("✅ Telegram bot test PASSED!")
            
            # Send a more detailed test message
            await notifier.send_system_message(
                "🎉 Late Corner Bot Setup Complete!\n\n"
                "✅ Bot is connected and working\n"
                "✅ Ready to receive corner alerts\n\n"
                "Next step: Test with live matches!", 
                "INFO"
            )
            
            return True
        else:
            print("❌ Telegram bot test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Telegram test error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_telegram())
    
    if result:
        print("\n🎉 Telegram setup is working perfectly!")
        print("You should have received 2 test messages in your Telegram")
    else:
        print("\n❌ Telegram setup failed. Check your bot token and chat ID.")
        sys.exit(1) 