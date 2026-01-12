#!/usr/bin/env python3
"""Analyze 3-day performance metrics and determine if course correction is needed"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def analyze_performance():
    """Analyze performance metrics for the last 3 days"""
    db_path = Path("data/engine.db")
    if not db_path.exists():
        print("❌ Database not found")
        return None
    
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Calculate 3 days ago timestamp
    three_days_ago = datetime.now() - timedelta(days=3)
    
    metrics = {
        "period": "3 days",
        "start_date": three_days_ago.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # Revenue metrics
    c.execute('''
        SELECT COUNT(*), COALESCE(SUM(amount), 0), COALESCE(AVG(amount), 0)
        FROM revenue 
        WHERE timestamp >= ? AND status = 'completed'
    ''', (three_days_ago,))
    rev_count, rev_total, rev_avg = c.fetchone()
    metrics["revenue"] = {
        "entries": rev_count,
        "total": float(rev_total),
        "average_per_entry": float(rev_avg) if rev_count > 0 else 0.0,
        "daily_average": float(rev_total) / 3.0
    }
    
    # Content performance
    c.execute('''
        SELECT COUNT(*), COALESCE(SUM(clicks), 0), COALESCE(SUM(conversions), 0), 
               COALESCE(SUM(revenue), 0), COALESCE(AVG(clicks), 0)
        FROM content_performance 
        WHERE date >= ?
    ''', (three_days_ago,))
    perf = c.fetchone()
    metrics["content"] = {
        "entries": perf[0],
        "total_clicks": perf[1],
        "total_conversions": perf[2],
        "total_revenue": float(perf[3]),
        "avg_clicks_per_entry": float(perf[4]) if perf[0] > 0 else 0.0,
        "conversion_rate": (float(perf[2]) / perf[1] * 100) if perf[1] > 0 else 0.0
    }
    
    # Campaign performance
    c.execute('''
        SELECT COUNT(*), COALESCE(SUM(clicks), 0), COALESCE(SUM(conversions), 0), 
               COALESCE(SUM(commissions), 0)
        FROM campaign_performance 
        WHERE date >= ?
    ''', (three_days_ago,))
    camp = c.fetchone()
    metrics["campaigns"] = {
        "entries": camp[0],
        "total_clicks": camp[1],
        "total_conversions": camp[2],
        "total_commissions": float(camp[3]),
        "conversion_rate": (float(camp[2]) / camp[1] * 100) if camp[1] > 0 else 0.0
    }
    
    # Leads
    c.execute('SELECT COUNT(DISTINCT email) FROM leads')
    total_leads = c.fetchone()[0]
    c.execute('SELECT COUNT(DISTINCT email) FROM leads WHERE converted = 1')
    converted_leads = c.fetchone()[0]
    metrics["leads"] = {
        "total": total_leads,
        "converted": converted_leads,
        "conversion_rate": (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
    }
    
    # Products
    c.execute('''
        SELECT COUNT(*), COALESCE(SUM(sales_count), 0), COALESCE(SUM(total_revenue), 0)
        FROM products
    ''')
    prod = c.fetchone()
    metrics["products"] = {
        "total": prod[0],
        "total_sales": prod[1],
        "total_revenue": float(prod[2])
    }
    
    # Success thresholds
    target_monthly = 10000
    target_daily = target_monthly / 30
    target_3days = target_daily * 3
    
    metrics["targets"] = {
        "monthly": target_monthly,
        "daily": target_daily,
        "3_day": target_3days,
        "revenue_achievement_pct": (metrics["revenue"]["total"] / target_3days * 100) if target_3days > 0 else 0.0
    }
    
    # Determine if course correction is needed
    needs_correction = False
    issues = []
    
    if metrics["revenue"]["total"] < target_3days * 0.1:  # Less than 10% of target
        needs_correction = True
        issues.append(f"Revenue critically low: ${metrics['revenue']['total']:.2f} vs target ${target_3days:.2f}")
    
    if metrics["content"]["total_clicks"] == 0:
        needs_correction = True
        issues.append("Zero clicks on content - content not reaching audience")
    
    if metrics["campaigns"]["total_clicks"] == 0:
        needs_correction = True
        issues.append("Zero clicks on campaigns - affiliate links not working")
    
    if metrics["leads"]["total"] == 0:
        needs_correction = True
        issues.append("Zero leads generated - lead generation failing")
    
    if metrics["content"]["conversion_rate"] > 0 and metrics["content"]["conversion_rate"] < 1.0:
        needs_correction = True
        issues.append(f"Low conversion rate: {metrics['content']['conversion_rate']:.2f}%")
    
    metrics["needs_correction"] = needs_correction
    metrics["issues"] = issues
    
    conn.close()
    return metrics

if __name__ == "__main__":
    metrics = analyze_performance()
    if metrics:
        print("=" * 60)
        print("3-DAY PERFORMANCE ANALYSIS")
        print("=" * 60)
        print(f"\nPeriod: {metrics['start_date']} to {metrics['end_date']}")
        print(f"\n💰 REVENUE:")
        print(f"   Total: ${metrics['revenue']['total']:.2f}")
        print(f"   Target (3 days): ${metrics['targets']['3_day']:.2f}")
        print(f"   Achievement: {metrics['targets']['revenue_achievement_pct']:.1f}%")
        print(f"   Daily Average: ${metrics['revenue']['daily_average']:.2f}")
        print(f"\n📊 CONTENT PERFORMANCE:")
        print(f"   Entries: {metrics['content']['entries']}")
        print(f"   Total Clicks: {metrics['content']['total_clicks']}")
        print(f"   Conversions: {metrics['content']['total_conversions']}")
        print(f"   Conversion Rate: {metrics['content']['conversion_rate']:.2f}%")
        print(f"   Revenue: ${metrics['content']['total_revenue']:.2f}")
        print(f"\n🎯 CAMPAIGN PERFORMANCE:")
        print(f"   Entries: {metrics['campaigns']['entries']}")
        print(f"   Total Clicks: {metrics['campaigns']['total_clicks']}")
        print(f"   Conversions: {metrics['campaigns']['total_conversions']}")
        print(f"   Commissions: ${metrics['campaigns']['total_commissions']:.2f}")
        print(f"\n👥 LEADS:")
        print(f"   Total: {metrics['leads']['total']}")
        print(f"   Converted: {metrics['leads']['converted']}")
        print(f"\n📦 PRODUCTS:")
        print(f"   Total: {metrics['products']['total']}")
        print(f"   Sales: {metrics['products']['total_sales']}")
        print(f"   Revenue: ${metrics['products']['total_revenue']:.2f}")
        print(f"\n{'=' * 60}")
        if metrics["needs_correction"]:
            print("⚠️  COURSE CORRECTION NEEDED")
            print("=" * 60)
            for issue in metrics["issues"]:
                print(f"   • {issue}")
        else:
            print("✅ PERFORMANCE MEETS TARGETS")
        print("=" * 60)
