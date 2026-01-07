#!/usr/bin/env python3
"""Quick test script to check Twitter API authentication"""

import os
from dotenv import load_dotenv
from requests_oauthlib import OAuth1
import requests

load_dotenv()

api_key = os.getenv('TWITTER_API_KEY')
api_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
live_posting = os.getenv('TWITTER_LIVE_POSTING', 'false').lower()

print("=" * 60)
print("TWITTER API AUTHENTICATION TEST")
print("=" * 60)
print()

print(f"TWITTER_LIVE_POSTING: {live_posting}")
print(f"Has all credentials: {bool(all([api_key, api_secret, access_token, access_secret]))}")
print()

if not all([api_key, api_secret, access_token, access_secret]):
    print("❌ Missing Twitter credentials in .env file")
    exit(1)

try:
    auth = OAuth1(api_key, api_secret, access_token, access_secret)
    
    # Test 1: Verify credentials with /users/me endpoint
    print("Test 1: Verifying credentials...")
    resp = requests.get('https://api.twitter.com/2/users/me', auth=auth, timeout=10)
    
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        username = data.get("data", {}).get("username", "unknown")
        user_id = data.get("data", {}).get("id", "unknown")
        print(f"✅ Authentication: SUCCESS")
        print(f"   Username: @{username}")
        print(f"   User ID: {user_id}")
        print()
        
        # Test 2: Try to post a test tweet (dry run - we'll just check permissions)
        print("Test 2: Checking posting permissions...")
        # We'll check by attempting to read recent tweets instead (safer)
        resp2 = requests.get(
            'https://api.twitter.com/2/tweets/search/recent?query=from:me&max_results=5',
            auth=auth,
            timeout=10
        )
        
        if resp2.status_code == 200:
            print(f"✅ Posting permissions: OK (can read tweets)")
        elif resp2.status_code in [401, 403]:
            print(f"⚠️ Posting permissions: May have issues (Status {resp2.status_code})")
            print(f"   Response: {resp2.text[:200]}")
        else:
            print(f"⚠️ Unexpected status: {resp2.status_code}")
            
    elif resp.status_code == 401:
        print(f"❌ Authentication: FAILED (401 Unauthorized)")
        print(f"   Error: {resp.text[:300]}")
        print()
        print("Possible causes:")
        print("  - API keys/access tokens are incorrect")
        print("  - Tokens have been revoked or expired")
        print("  - App permissions need to be set to 'Read and Write'")
        
    elif resp.status_code == 403:
        print(f"❌ Authentication: FAILED (403 Forbidden)")
        print(f"   Error: {resp.text[:300]}")
        print()
        print("Possible causes:")
        print("  - App doesn't have required permissions")
        print("  - Need to set permissions to 'Read and Write' in Twitter Developer Portal")
        
    else:
        print(f"⚠️ Unexpected status: {resp.status_code}")
        print(f"   Response: {resp.text[:300]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
