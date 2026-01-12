#!/usr/bin/env python3
"""Quick system health check"""

import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

print("=" * 60)
print("CASH ENGINE SYSTEM STATUS CHECK")
print("=" * 60)
print()

# Check database
db_path = Path("data/engine.db")
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Products
    c.execute("SELECT COUNT(*) FROM products")
    product_count = c.fetchone()[0]
    print(f"✅ Products in database: {product_count}")
    
    # Revenue (last 7 days)
    c.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM revenue WHERE date >= date('now', '-7 days')")
    rev_count, rev_total = c.fetchone()
    print(f"✅ Revenue entries (7d): {rev_count} | Total: ${rev_total:.2f}")
    
    # Last revenue date
    c.execute("SELECT MAX(date) FROM revenue")
    last_rev = c.fetchone()[0]
    print(f"✅ Last revenue entry: {last_rev or 'None'}")
    
    # Content performance (last 7 days)
    c.execute("SELECT COUNT(*), COALESCE(SUM(clicks), 0) FROM content_performance WHERE date >= date('now', '-7 days')")
    perf_count, total_clicks = c.fetchone()
    print(f"✅ Content performance entries (7d): {perf_count} | Total clicks: {total_clicks}")
    
    # Campaigns
    c.execute("SELECT COUNT(*) FROM campaigns WHERE status = 'active'")
    active_campaigns = c.fetchone()[0]
    print(f"✅ Active campaigns: {active_campaigns}")
    
    # Shopify products
    c.execute("SELECT COUNT(*) FROM products WHERE source = 'shopify'")
    shopify_products = c.fetchone()[0]
    print(f"✅ Shopify products: {shopify_products}")
    
    conn.close()
else:
    print("❌ Database not found")

print()

# Check log file
log_path = Path("logs/engine.log")
if log_path.exists():
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        if lines:
            last_line = lines[-1].strip()
            print(f"✅ Last log entry: {last_line[:100]}...")
            print(f"✅ Total log lines: {len(lines)}")
        else:
            print("⚠️  Log file is empty")
else:
    print("❌ Log file not found")

print()

# Check for errors in last 100 lines
if log_path.exists():
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        recent_lines = f.readlines()[-100:]
        errors = [l for l in recent_lines if 'ERROR' in l or 'CRITICAL' in l or 'Exception' in l]
        if errors:
            print(f"⚠️  Found {len(errors)} errors in last 100 log lines:")
            for err in errors[-5:]:  # Show last 5 errors
                print(f"   {err.strip()[:120]}")
        else:
            print("✅ No recent errors in logs")

print()
print("=" * 60)
