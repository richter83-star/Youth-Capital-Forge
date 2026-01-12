#!/usr/bin/env python3
"""Test script to verify Shopify API connection and configuration"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add cash_engine to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cash_engine import ShopifyManager
import sqlite3
from pathlib import Path

def test_shopify_connection():
    """Test Shopify API connection and configuration"""
    print("=" * 60)
    print("SHOPIFY INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("📋 Configuration Check:")
    print("-" * 60)
    
    store_domain = os.getenv('SHOPIFY_STORE_DOMAIN', '')
    api_key = os.getenv('SHOPIFY_API_KEY', '')
    api_secret = os.getenv('SHOPIFY_API_SECRET', '')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    webhook_secret = os.getenv('SHOPIFY_WEBHOOK_SECRET', '')
    enabled = os.getenv('SHOPIFY_ENABLED', 'false').lower() in ('true', '1', 'yes', 'on')
    
    print(f"SHOPIFY_STORE_DOMAIN: {'✅ Set' if store_domain else '❌ Not set'}")
    if store_domain:
        print(f"   Value: {store_domain}")
    
    print(f"SHOPIFY_API_KEY: {'✅ Set' if api_key else '⚠️ Optional (not set)'}")
    
    print(f"SHOPIFY_API_SECRET: {'✅ Set' if api_secret else '⚠️ Optional (not set)'}")
    
    print(f"SHOPIFY_ACCESS_TOKEN: {'✅ Set' if access_token else '❌ REQUIRED - Not set'}")
    if access_token:
        print(f"   Value: {access_token[:20]}...{access_token[-10:]}")
    
    print(f"SHOPIFY_WEBHOOK_SECRET: {'✅ Set' if webhook_secret else '⚠️ Optional (not set)'}")
    
    print(f"SHOPIFY_ENABLED: {'✅ Enabled' if enabled else '❌ Disabled'}")
    print()
    
    # Check if required variables are set
    if not store_domain:
        print("❌ SHOPIFY_STORE_DOMAIN is required!")
        print("   Set it in your .env file: SHOPIFY_STORE_DOMAIN=dracanus-ai.myshopify.com")
        return False
    
    if not access_token:
        print("❌ SHOPIFY_ACCESS_TOKEN is required!")
        print("   Get it from: Shopify Admin → Settings → Apps → Your App → API credentials")
        return False
    
    if not enabled:
        print("⚠️ SHOPIFY_ENABLED is false - integration will not work")
        print("   Set it in your .env file: SHOPIFY_ENABLED=true")
    
    print()
    print("=" * 60)
    print("API Connection Test")
    print("=" * 60)
    print()
    
    # Test API connection
    try:
        # Initialize database connection
        db_path = Path("./data/engine.db")
        db_conn = None
        if db_path.exists():
            db_conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Create ShopifyManager
        shopify_manager = ShopifyManager(db_conn)
        
        if not shopify_manager.enabled:
            print("❌ Shopify integration is disabled")
            print("   Set SHOPIFY_ENABLED=true in your .env file")
            if db_conn:
                db_conn.close()
            return False
        
        # Test 1: Fetch products
        print("Test 1: Fetching products from Shopify...")
        products = shopify_manager.fetch_products()
        
        if products:
            print(f"✅ Successfully fetched {len(products)} products")
            print()
            print("Sample products:")
            for i, product in enumerate(products[:5], 1):  # Show first 5
                title = product.get("title", "Unknown")
                handle = product.get("handle", "unknown")
                variants = product.get("variants", [])
                price = variants[0].get("price", "0") if variants else "0"
                print(f"   {i}. {title} (${price}) - Handle: {handle}")
            
            if len(products) > 5:
                print(f"   ... and {len(products) - 5} more products")
            print()
            
            # Test 2: Generate product URL
            print("Test 2: Generating product URLs...")
            if products:
                sample_product = products[0]
                handle = sample_product.get("handle", "")
                if handle:
                    url = shopify_manager.get_product_url(handle, utm_source="test")
                    print(f"✅ Generated URL: {url}")
                else:
                    print("⚠️ Product handle not found")
            print()
            
            # Test 3: Product matching
            print("Test 3: Testing product matching...")
            test_content = "Check out our Ghost Launch Bundle for autonomous store experiments"
            match = shopify_manager.find_matching_product(test_content)
            if match:
                print(f"✅ Found matching product: {match.get('title', 'Unknown')}")
            else:
                print("⚠️ No product match found for test content")
            print()
            
            # Test 4: Database sync (optional)
            if db_conn:
                print("Test 4: Syncing products to database...")
                synced = shopify_manager.sync_products_to_db()
                print(f"✅ Synced {synced} products to database")
                print()
            
            print("=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("1. Ensure webhook is configured in Shopify Admin")
            print("2. Set SHOPIFY_WEBHOOK_SECRET if using webhook signature verification")
            print("3. Restart Cash Engine to enable automatic product sync")
            
            if db_conn:
                db_conn.close()
            return True
        else:
            print("⚠️ No products found (this may be normal if store has no products)")
            print("   Or there may be an authentication issue")
            
            # Try to get more details
            print()
            print("Checking API access...")
            try:
                url = shopify_manager._get_api_url("/products.json")
                headers = shopify_manager._get_headers()
                import requests
                resp = requests.get(url, headers=headers, params={"limit": 1}, timeout=10)
                print(f"   Status Code: {resp.status_code}")
                if resp.status_code == 401:
                    print("   ❌ Authentication failed - check SHOPIFY_ACCESS_TOKEN")
                elif resp.status_code == 403:
                    print("   ❌ Access denied - check app permissions/scopes")
                elif resp.status_code == 404:
                    print("   ❌ Store not found - check SHOPIFY_STORE_DOMAIN")
                elif resp.status_code == 200:
                    data = resp.json()
                    count = len(data.get("products", []))
                    print(f"   ✅ API accessible - found {count} products")
                else:
                    print(f"   ⚠️ Unexpected status: {resp.status_code}")
                    print(f"   Response: {resp.text[:200]}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            if db_conn:
                db_conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error testing Shopify connection: {e}")
        import traceback
        traceback.print_exc()
        if db_conn:
            db_conn.close()
        return False

if __name__ == "__main__":
    success = test_shopify_connection()
    sys.exit(0 if success else 1)
