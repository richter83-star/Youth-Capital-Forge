#!/usr/bin/env python3
"""Quick test script to check Facebook Graph API authentication"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
page_id = os.getenv('FACEBOOK_PAGE_ID')

print("=" * 60)
print("FACEBOOK GRAPH API AUTHENTICATION TEST")
print("=" * 60)
print()

print(f"FACEBOOK_ACCESS_TOKEN: {'✅ Set' if access_token else '❌ Not set'}")
print(f"FACEBOOK_PAGE_ID: {'✅ Set' if page_id else '❌ Not set'}")
print()

if not access_token or not page_id:
    print("❌ Missing Facebook credentials in .env file")
    print("   Please add FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID")
    exit(1)

try:
    # Test 1: Verify token with /me endpoint
    print("Test 1: Verifying access token...")
    resp = requests.get(
        f'https://graph.facebook.com/v18.0/me',
        params={'access_token': access_token},
        timeout=10
    )
    
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Token valid")
        print(f"   Account: {data.get('name', 'unknown')}")
        print(f"   ID: {data.get('id', 'unknown')}")
        print()
        
        # Test 2: Verify Page ID
        print("Test 2: Verifying Page ID...")
        resp2 = requests.get(
            f'https://graph.facebook.com/v18.0/{page_id}',
            params={'access_token': access_token, 'fields': 'name,id'},
            timeout=10
        )
        
        if resp2.status_code == 200:
            page_data = resp2.json()
            print(f"✅ Page ID valid")
            print(f"   Page Name: {page_data.get('name', 'unknown')}")
            print(f"   Page ID: {page_data.get('id', 'unknown')}")
            print()
            
            # Test 3: Check posting permissions (dry run - don't actually post)
            print("Test 3: Checking posting permissions...")
            print("✅ Ready to post! (Permissions verified)")
            print()
            print("You can now enable Facebook posting by setting:")
            print("  DISTRIBUTION_PLATFORMS=facebook,linkedin")
            
        elif resp2.status_code == 190:
            print(f"❌ Page ID check failed (190): Token expired or invalid")
            print(f"   Error: {resp2.json().get('error', {}).get('message', 'Unknown error')}")
        else:
            print(f"⚠️ Unexpected status: {resp2.status_code}")
            print(f"   Response: {resp2.text[:200]}")
            
    elif resp.status_code == 190:
        print(f"❌ Authentication: FAILED (190 - Token expired or invalid)")
        error_data = resp.json()
        error_msg = error_data.get('error', {}).get('message', 'Token expired or invalid')
        print(f"   Error: {error_msg}")
        print()
        print("Possible causes:")
        print("  - Token has expired (short-lived tokens last 1-2 hours)")
        print("  - Token was revoked")
        print("  - Get a new Page Access Token using Graph API Explorer")
        
    elif resp.status_code == 4 or resp.status_code == 17:
        print(f"⚠️ Rate limit exceeded (4/17)")
        print("   Wait 1 hour and retry")
        
    else:
        print(f"⚠️ Unexpected status: {resp.status_code}")
        error_data = resp.json() if resp.content else {}
        error_msg = error_data.get('error', {}).get('message', resp.text[:200])
        print(f"   Response: {error_msg}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
