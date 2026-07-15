#!/usr/bin/env python3
"""
Test script to verify the API endpoints work correctly
before running the Telegram bot.
"""

import requests
import json
from typing import Dict, Any, Optional

API_BASE_URL = "http://localhost:8000"


def test_health_check() -> bool:
    """Test if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_get_camera_result(sscc: str) -> Optional[Dict[str, Any]]:
    """Test getcamerares endpoint."""
    try:
        payload = {"SSCC": sscc}
        response = requests.post(
            f"{API_BASE_URL}/api/getcamerares",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ getcamerares failed for SSCC {sscc}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ getcamerares error for SSCC {sscc}: {e}")
        return None


def test_get_analyzed(limit: int = 500, offset: int = 0) -> Optional[Dict[str, Any]]:
    """Test getanalyzed endpoint."""
    try:
        url = f"{API_BASE_URL}/api/getanalyzed?limit={limit}&offset={offset}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ getanalyzed failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ getanalyzed error: {e}")
        return None


def main():
    """Run all tests."""
    print("🧪 Testing API endpoints...\n")
    
    # Test health check
    print("1. Testing health check...")
    if test_health_check():
        print("   ✅ API is running\n")
    else:
        print("   ❌ API is not running. Start the server first:\n")
        print("   uvicorn main:app --reload --port 8000 --host 0.0.0.0\n")
        return
    
    # Test getcamerares with test values
    print("2. Testing getcamerares endpoint...")
    test_ssccs = ["111", "666", "777", "999", "148102689000000010"]
    for sscc in test_ssccs:
        result = test_get_camera_result(sscc)
        if result:
            print(f"   ✅ SSCC {sscc}: {json.dumps(result, indent=2)[:100]}...")
        else:
            print(f"   ❌ SSCC {sscc}: Failed")
    print()
    
    # Test getanalyzed
    print("3. Testing getanalyzed endpoint...")
    result = test_get_analyzed(limit=500, offset=0)
    if result:
        if isinstance(result, dict):
            count = result.get("Count", 0)
            records = result.get("Records", [])
            print(f"   ✅ Total count: {count}, Records returned: {len(records)}")
            if records:
                print(f"   First 3 records:")
                for i, record in enumerate(records[:3], 1):
                    sscc = record.get("SSCC", "N/A")
                    msg = record.get("Msg", "N/A")
                    print(f"      {i}. SSCC: {sscc}, Msg: {msg}")
        else:
            print(f"   ✅ Response: {json.dumps(result, indent=2)[:200]}...")
    else:
        print("   ❌ Failed to fetch analyzed records")
    print()
    
    # Test with different limits and offsets
    print("4. Testing pagination...")
    for limit, offset in [(20, 0), (50, 100), (100, 0)]:
        result = test_get_analyzed(limit=limit, offset=offset)
        if result:
            if isinstance(result, dict):
                count = result.get("Count", 0)
                records = result.get("Records", [])
                print(f"   ✅ limit={limit}, offset={offset}: {len(records)} records (total: {count})")
            else:
                print(f"   ✅ limit={limit}, offset={offset}: Success")
        else:
            print(f"   ❌ limit={limit}, offset={offset}: Failed")
    print()
    
    print("✅ All tests completed!")
    print("\n🤖 You can now run the Telegram bot:")
    print("   export TELEGRAM_BOT_TOKEN='your-bot-token'")
    print("   python telegram_bot.py")


if __name__ == "__main__":
    main()
