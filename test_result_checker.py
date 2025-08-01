#!/usr/bin/env python3
"""
Test Result Checker
==================
Test the hourly result checking functionality.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set database URL for local testing
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_result_checker():
    """Test the result checker functionality"""
    
    print("🔍 TESTING RESULT CHECKER")
    print("="*40)
    
    try:
        from result_checker import check_pending_results
        
        logger.info("🧪 Running result checker test...")
        await check_pending_results()
        logger.info("✅ Result checker test completed")
        
    except Exception as e:
        logger.error(f"❌ Result checker test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_result_checker()) 