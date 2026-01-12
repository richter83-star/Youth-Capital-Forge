#!/usr/bin/env python3
"""Test the Weekly Report Generator"""

from weekly_report_generator import WeeklyReportGenerator

print("=" * 60)
print("Testing Weekly Report Generator")
print("=" * 60)

generator = WeeklyReportGenerator()
result = generator.generate_weekly_report(days=7)

if result.get("success"):
    print(f"\n✅ Weekly report generated successfully!")
    print(f"   Markdown: {result.get('markdown_file', 'N/A')}")
    print(f"   JSON: {result.get('json_file', 'N/A')}")
    
    report_data = result.get('report_data', {})
    data = report_data.get('data', {})
    successes = report_data.get('successes', {})
    failures = report_data.get('failures', {})
    recommendations = report_data.get('recommendations', {})
    
    print(f"\n📊 Report Summary:")
    print(f"   Revenue: ${data.get('revenue', {}).get('total', 0):.2f}")
    print(f"   Achievement: {data.get('targets', {}).get('achievement_pct', 0):.1f}%")
    print(f"   Success patterns: {len(successes.get('success_patterns', []))}")
    print(f"   Failed content: {len(failures.get('zero_engagement_content', []))}")
    print(f"   Failed campaigns: {len(failures.get('zero_engagement_campaigns', []))}")
    print(f"   Recommendations: {len(recommendations.get('critical_issues', []))} critical, {len(recommendations.get('quick_wins', []))} quick wins")
    
    print(f"\n💡 Sample Recommendations:")
    if recommendations.get('critical_issues'):
        for issue in recommendations['critical_issues'][:2]:
            print(f"   🚨 {issue.get('title', 'Unknown')}")
    if recommendations.get('quick_wins'):
        for win in recommendations['quick_wins'][:2]:
            print(f"   ⚡ {win.get('title', 'Unknown')}")
else:
    print(f"\n❌ Report generation failed: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 60)
