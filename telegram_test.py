#!/usr/bin/env python3
"""
Telegram Bot Test Script
Test your Telegram bot configuration before running the main system
"""

import os
import requests
from dotenv import load_dotenv

def test_telegram_setup():
    """Test Telegram bot configuration"""
    
    # Load environment variables
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print("🔍 Testing Telegram Configuration...")
    print("=" * 50)
    
    # Check if credentials are set
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        print("🔧 Please add: TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return False
    
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not found in .env file")
        print("🔧 Please add: TELEGRAM_CHAT_ID=your_chat_id_here")
        return False
    
    print(f"✅ Bot Token: {bot_token[:10]}...{bot_token[-5:]}")
    print(f"✅ Chat ID: {chat_id}")
    
    # Test bot API connection
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        bot_info = response.json()
        if bot_info.get('ok'):
            bot_name = bot_info['result']['first_name']
            bot_username = bot_info['result']['username']
            print(f"✅ Bot Connected: @{bot_username} ({bot_name})")
        else:
            print("❌ Invalid bot token")
            return False
            
    except Exception as e:
        print(f"❌ Bot API Error: {e}")
        return False
    
    # Send test message
    try:
        test_message = """🧪 <b>Corner System Test</b> 🧪

✅ Telegram integration working!
🚨 You'll receive corner alerts here when:
• Match reaches 85 minutes
• Good corner betting conditions
• Asian corner odds available

Ready for live alerts! ⚽"""

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        print("✅ Test message sent successfully!")
        print("📱 Check your Telegram for the test message")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test message: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions for Telegram bot"""
    
    print("\n" + "🤖 TELEGRAM BOT SETUP INSTRUCTIONS" + "\n")
    print("=" * 50)
    print("""
1. 📱 Create a Telegram Bot:
   • Open Telegram and search for @BotFather
   • Send /newbot
   • Choose a name and username for your bot
   • Copy the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)

2. 💬 Get Your Chat ID:
   • Start a chat with your new bot
   • Send any message to your bot
   • Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   • Find "chat":{"id":123456789} in the response
   • Copy the chat ID number

3. 📝 Add to .env file:
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here

4. 🧪 Run this test again to verify setup
""")

if __name__ == "__main__":
    print("🤖 Telegram Corner Alert System Setup")
    print("=" * 50)
    
    success = test_telegram_setup()
    
    if not success:
        print_setup_instructions()
    else:
        print("\n🎉 Telegram setup complete!")
        print("💡 Your corner system will now send alerts to Telegram!") 