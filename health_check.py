#!/usr/bin/env python3
"""
Railway Health Check Script
Quick diagnostic for deployment issues
"""

import os
import requests
from dotenv import load_dotenv

def main():
    print("🔍 RAILWAY DEPLOYMENT HEALTH CHECK")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    print("1. 📝 Environment Variables:")
    api_key = os.getenv('SPORTMONKS_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN') 
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
    port = os.getenv('PORT', '5000')
    
    print(f"   ✅ PORT: {port}")
    print(f"   {'✅' if api_key else '❌'} SPORTMONKS_API_KEY: {'Set' if api_key else 'MISSING'}")
    print(f"   {'✅' if telegram_token else '❌'} TELEGRAM_BOT_TOKEN: {'Set' if telegram_token else 'MISSING'}")
    print(f"   {'✅' if telegram_chat else '❌'} TELEGRAM_CHAT_ID: {'Set' if telegram_chat else 'MISSING'}")
    
    if not api_key:
        print("\n❌ CRITICAL: SportMonks API key is missing!")
        print("🔧 Add SPORTMONKS_API_KEY to Railway environment variables")
        return False
    
    # Test SportMonks API
    print("\n2. 🔗 Testing SportMonks API:")
    try:
        url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {'api_token': api_key, 'include': 'scores'}
        
        print(f"   🌐 Calling: {url}")
        response = requests.get(url, params=params, timeout=15)
        
        print(f"   📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('data', [])
            print(f"   ✅ API Working! Found {len(matches)} live matches")
            return True
        elif response.status_code == 401:
            print("   ❌ INVALID API KEY!")
            print("   🔧 Check your SportMonks API key in Railway variables")
            return False
        elif response.status_code == 429:
            print("   ⚠️ RATE LIMIT EXCEEDED!")
            print("   🔧 API key over quota - check your SportMonks dashboard")
            return False
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ API Connection Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Health check PASSED!")
        print("💡 Your app should work correctly on Railway")
    else:
        print("\n💥 Health check FAILED!")
        print("🔧 Fix the issues above before deploying") 