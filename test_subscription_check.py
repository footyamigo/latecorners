#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def check_subscription_message():
    """Check what message SportMonks returns about our subscription/permissions"""
    
    match_id = 19406130
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print(f"🔍 CHECKING SUBSCRIPTION MESSAGE for odds access")
    
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
    params = {"api_token": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📋 FULL RESPONSE:")
            print(json.dumps(data, indent=2))
            
            # Check subscription details
            if 'subscription' in data:
                sub_info = data['subscription']
                print(f"\n🎫 SUBSCRIPTION INFO:")
                for key, value in sub_info.items():
                    print(f"   {key}: {value}")
            
            # Check message
            if 'message' in data:
                message = data['message']
                print(f"\n💬 MESSAGE: {message}")
            
            # Check rate limit
            if 'rate_limit' in data:
                rate_info = data['rate_limit']
                print(f"\n⏱️ RATE LIMIT INFO:")
                for key, value in rate_info.items():
                    print(f"   {key}: {value}")
                    
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    check_subscription_message() 