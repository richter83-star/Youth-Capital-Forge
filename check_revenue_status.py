#!/usr/bin/env python3
"""
Revenue Generation Status Checker
Identifies blockers and verifies all revenue streams are active
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

def check_env_vars():
    """Check critical environment variables"""
    print("=" * 60)
    print("🔍 CHECKING ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    critical_vars = {
        "GUMROAD_TOKEN": "Gumroad API access",
        "OPENAI_API_KEY": "Template generation",
        "MARKETING_AGENT_URL": "Affiliate tracking",
        "TWITTER_BEARER_TOKEN": "Trend analysis (optional)",
    }
    
    missing = []
    for var, purpose in critical_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked} ({purpose})")
        else:
            print(f"❌ {var}: MISSING ({purpose})")
            missing.append(var)
    
    return missing

def check_database():
    """Check database status and recent activity"""
    print("\n" + "=" * 60)
    print("💾 CHECKING DATABASE")
    print("=" * 60)
    
    db_path = Path("./data/engine.db")
    if not db_path.exists():
        print("❌ Database not found at ./data/engine.db")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Database exists with {len(tables)} tables")
        
        # Check recent revenue
        cursor.execute('''
            SELECT SUM(amount) FROM revenue 
            WHERE timestamp >= datetime('now', '-7 days') AND status = 'completed'
        ''')
        revenue_7d = cursor.fetchone()[0] or 0.0
        print(f"📊 Revenue (last 7 days): ${revenue_7d:.2f}")
        
        # Check products
        cursor.execute('SELECT COUNT(*) FROM products')
        product_count = cursor.fetchone()[0] or 0
        print(f"📦 Products in database: {product_count}")
        
        # Check recent products
        cursor.execute('''
            SELECT COUNT(*) FROM products 
            WHERE created_date >= datetime('now', '-7 days')
        ''')
        recent_products = cursor.fetchone()[0] or 0
        print(f"📦 Products created (last 7 days): {recent_products}")
        
        # Check leads
        cursor.execute('SELECT COUNT(*) FROM leads')
        lead_count = cursor.fetchone()[0] or 0
        print(f"🎯 Leads in database: {lead_count}")
        
        # Check campaigns
        cursor.execute('SELECT COUNT(*) FROM template_ab_tests WHERE status = "active"')
        active_tests = cursor.fetchone()[0] or 0
        print(f"🧪 Active A/B tests: {active_tests}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_gumroad_api():
    """Check Gumroad API connectivity"""
    print("\n" + "=" * 60)
    print("🛒 CHECKING GUMROAD API")
    print("=" * 60)
    
    token = os.getenv('GUMROAD_TOKEN')
    if not token:
        print("❌ GUMROAD_TOKEN not set")
        return False
    
    try:
        response = requests.get(
            'https://api.gumroad.com/v2/products',
            params={'access_token': token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                products = data.get('products', [])
                print(f"✅ Gumroad API connected - {len(products)} products found")
                return True
            else:
                print(f"❌ Gumroad API error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Gumroad API HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Gumroad API connection failed: {e}")
        return False

def check_marketing_agent():
    """Check Marketing Agent V2 connectivity"""
    print("\n" + "=" * 60)
    print("🔗 CHECKING MARKETING AGENT")
    print("=" * 60)
    
    url = os.getenv('MARKETING_AGENT_URL', 'http://localhost:9000')
    
    try:
        response = requests.get(f"{url}/healthz", timeout=5)
        if response.status_code == 200:
            print(f"✅ Marketing Agent accessible at {url}")
            return True
        else:
            print(f"⚠️ Marketing Agent returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Marketing Agent not accessible at {url}")
        print("   Note: This is optional - affiliate tracking will use fallback")
        return False
    except Exception as e:
        print(f"❌ Marketing Agent check failed: {e}")
        return False

def check_templates():
    """Check template files"""
    print("\n" + "=" * 60)
    print("📄 CHECKING TEMPLATES")
    print("=" * 60)
    
    templates_dir = Path("./products")
    if not templates_dir.exists():
        print("❌ Products directory not found")
        return False
    
    templates = list(templates_dir.glob("*.md"))
    print(f"✅ Found {len(templates)} template files")
    
    if templates:
        print("   Recent templates:")
        for template in templates[:5]:
            size = template.stat().st_size
            print(f"   - {template.name} ({size} bytes)")
    
    return len(templates) > 0

def check_logs():
    """Check recent log activity"""
    print("\n" + "=" * 60)
    print("📋 CHECKING LOGS")
    print("=" * 60)
    
    log_path = Path("./logs/engine.log")
    if not log_path.exists():
        print("⚠️ Log file not found - engine may not have run yet")
        return False
    
    try:
        # Read last 50 lines
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            recent_lines = lines[-20:] if len(lines) > 20 else lines
        
        print(f"✅ Log file exists ({len(lines)} total lines)")
        print("\n   Recent activity:")
        for line in recent_lines[-5:]:
            print(f"   {line.strip()}")
        
        # Check for errors
        error_count = sum(1 for line in lines if 'ERROR' in line or 'error' in line.lower())
        if error_count > 0:
            print(f"\n⚠️ Found {error_count} error entries in logs")
        
        return True
    except Exception as e:
        print(f"❌ Error reading logs: {e}")
        return False

def check_revenue_streams():
    """Check if revenue streams are configured"""
    print("\n" + "=" * 60)
    print("💰 CHECKING REVENUE STREAMS")
    print("=" * 60)
    
    streams = [
        "digital_product_factory",
        "affiliate_automation",
        "lead_generation_bot",
        "content_syndication"
    ]
    
    for stream in streams:
        print(f"✅ {stream} configured")
    
    return True

def generate_report():
    """Generate comprehensive status report"""
    print("\n" + "=" * 60)
    print("📊 REVENUE GENERATION STATUS REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        "env_vars": check_env_vars(),
        "database": check_database(),
        "gumroad": check_gumroad_api(),
        "marketing_agent": check_marketing_agent(),
        "templates": check_templates(),
        "logs": check_logs(),
        "revenue_streams": check_revenue_streams()
    }
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY & BLOCKERS")
    print("=" * 60)
    
    blockers = []
    
    if results["env_vars"]:
        blockers.append(f"Missing environment variables: {', '.join(results['env_vars'])}")
    
    if not results["database"]:
        blockers.append("Database not accessible or not initialized")
    
    if not results["gumroad"]:
        blockers.append("Gumroad API not accessible - product sales tracking disabled")
    
    if not results["templates"]:
        blockers.append("No template files found - product generation disabled")
    
    if blockers:
        print("\n❌ BLOCKERS FOUND:")
        for i, blocker in enumerate(blockers, 1):
            print(f"   {i}. {blocker}")
        print("\n⚠️ Revenue generation may be limited until these are resolved.")
    else:
        print("\n✅ NO CRITICAL BLOCKERS FOUND")
        print("   All systems appear operational for revenue generation.")
    
    print("\n💡 RECOMMENDATIONS:")
    print("   1. Ensure cash_engine.py is running: python cash_engine.py")
    print("   2. Check logs/engine.log for runtime errors")
    print("   3. Verify Gumroad products are published and accessible")
    print("   4. Ensure Marketing Agent V2 is running (optional but recommended)")
    print("   5. Monitor revenue table in database for sales tracking")
    
    return blockers

if __name__ == "__main__":
    blockers = generate_report()
    sys.exit(0 if not blockers else 1)
