#!/usr/bin/env python3
"""Test the AI Course Correction System"""

from ai_course_corrector import AICourseCorrector

print("=" * 60)
print("Testing AI Course Correction System")
print("=" * 60)

cc = AICourseCorrector()
report = cc.run_course_correction(days=3)

print(f"\n✅ Course correction completed!")
print(f"   Issues identified: {len(report.get('issues', []))}")
print(f"   Needs correction: {report.get('needs_correction', False)}")
print(f"   Report saved to: output/reports/")

if report.get('needs_correction'):
    print("\n⚠️  Issues found:")
    for issue in report.get('issues', []):
        print(f"   • {issue.get('description', 'Unknown')}")
    
    fixes = report.get('fixes_implemented', {})
    if fixes.get('implemented'):
        print(f"\n✅ Implemented {len(fixes['implemented'])} fixes")
    if fixes.get('failed'):
        print(f"⚠️  {len(fixes['failed'])} fixes failed")

print("\n" + "=" * 60)
