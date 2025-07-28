#!/usr/bin/env python3
"""
Simple test script to verify Telegram bot configuration
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_telegram_bot():
    """Test the Telegram bot configuration"""
    
    print("🧪 TESTING: Telegram Bot Configuration...")
    print("=" * 50)
    
    try:
        from telegram_bot import TelegramNotifier
        
        # Initialize Telegram notifier
        telegram = TelegramNotifier()
        
        print("✅ SUCCESS: TelegramNotifier initialized")
        
        # Test basic connection
        print("📡 TESTING: Sending test message...")
        await telegram.send_system_message("🧪 TEST: Telegram bot configuration test - ignore this message")
        
        print("✅ SUCCESS: Test message sent!")
        print("📱 CHECK: Please check your Telegram to confirm message received")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Telegram test failed: {e}")
        import traceback
        print(f"📋 TRACEBACK: {traceback.format_exc()}")
        return False

async def test_environment_variables():
    """Test if environment variables are properly loaded"""
    
    print("🔧 TESTING: Environment Variables...")
    print("=" * 30)
    
    # Check required variables
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'SPORTMONKS_API_KEY']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * (len(value) - 4)}{value[-4:]}")  # Show last 4 chars
        else:
            print(f"❌ {var}: NOT SET")
            return False
    
    return True

async def main():
    """Main test function"""
    
    print("🧪 TELEGRAM BOT TEST UTILITY")
    print("=" * 50)
    
    # Test environment variables first
    if not await test_environment_variables():
        print("❌ FAILED: Environment variables not properly configured")
        return
    
    # Test Telegram bot
    if await test_telegram_bot():
        print("🎉 SUCCESS: Telegram bot is working correctly!")
    else:
        print("💥 FAILED: Telegram bot test failed")

if __name__ == "__main__":
    asyncio.run(main()) 