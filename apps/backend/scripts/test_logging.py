#!/usr/bin/env python3
"""Test script to verify API logging is working"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test various endpoints to see if logging works"""
    
    print("Testing API endpoints to verify logging...")
    print("-" * 50)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    time.sleep(1)
    
    # Test docs endpoint
    print("\n2. Testing docs endpoint...")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"   Status: {response.status_code}")
    
    time.sleep(1)
    
    # Test login endpoint (will fail without credentials)
    print("\n3. Testing login endpoint (expected to fail)...")
    try:
        response = requests.post(f"{BASE_URL}/login")
        print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "-" * 50)
    print("Check your backend logs to see the request logging!")

if __name__ == "__main__":
    test_endpoints()