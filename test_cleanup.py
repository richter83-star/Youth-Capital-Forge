#!/usr/bin/env python3
"""Test the Smart Cleanup System"""

from ai_course_corrector import SmartCleanupSystem
import json

print("=" * 60)
print("Testing Smart Cleanup System")
print("=" * 60)

cs = SmartCleanupSystem()
results = cs.analyze_and_cleanup(grace_period_days=7, min_clicks_for_keep=1)

print(f"\n📊 Cleanup Results:")
print(f"   Content: Analyzed {results['content']['analyzed']}, Kept {results['content']['kept']}, Archived {results['content']['archived']}, Removed {results['content']['removed']}")
print(f"   Campaigns: Analyzed {results['campaigns']['analyzed']}, Kept {results['campaigns']['kept']}, Archived {results['campaigns']['archived']}, Removed {results['campaigns']['removed']}")
print(f"   Patterns Learned: {len(results['patterns_learned'])}")

if results['patterns_learned']:
    print(f"\n✅ Successful Patterns Identified:")
    for pattern in results['patterns_learned'][:5]:  # Top 5
        print(f"   • {pattern.get('pattern', 'Unknown')}: {pattern.get('reason', 'N/A')}")

# Get successful patterns
successful = cs.get_successful_patterns()
print(f"\n📚 Top Successful Patterns ({len(successful)} total):")
for pattern in successful[:5]:  # Top 5
    print(f"   • {pattern.get('type', 'unknown').upper()}: {pattern.get('content_file', pattern.get('campaign_id', 'Unknown'))}")
    print(f"     Score: {pattern.get('success_score', 0):.2f} | Clicks: {pattern.get('clicks', 0)} | Revenue: ${pattern.get('revenue', pattern.get('commissions', 0)):.2f}")

print("\n" + "=" * 60)
