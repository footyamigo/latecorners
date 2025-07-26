#!/usr/bin/env python3

"""
Simple run script for the Late Corner Betting Tool
This loads environment variables and starts the main application
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    
    # Look for .env file in the same directory as this script
    env_file = Path(__file__).parent / '.env'
    
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Loaded environment variables from .env file")
    else:
        print("⚠️ No .env file found. Make sure to set environment variables manually.")
        print("📄 Copy env_example.txt to .env and fill in your API keys")
        
except ImportError:
    print("⚠️ python-dotenv not installed. Installing...")
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main application
if __name__ == "__main__":
    try:
        from main import main
        import asyncio
        
        print("🚀 Starting Late Corner Betting Tool...")
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1) 