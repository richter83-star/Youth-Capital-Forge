# AI Course Correction System - Setup Guide

## Overview

The AI Course Correction System automatically analyzes performance metrics, diagnoses issues, and implements fixes when revenue targets are not being met.

## Environment Variables

Add these to your `.env` file:

```bash
# Enable/disable course correction (default: true)
COURSE_CORRECTION_ENABLED=true

# How often to check performance (in hours, default: 6)
PERFORMANCE_CHECK_INTERVAL_HOURS=6

# Period to analyze for course correction (in days, default: 3)
COURSE_CORRECTION_PERIOD_DAYS=3

# Revenue threshold percentage - triggers correction if below this % of target (default: 10)
REVENUE_THRESHOLD_PCT=10

# Monthly revenue target (default: 10000)
TARGET_MONTHLY=10000

# Smart Cleanup System settings
CLEANUP_GRACE_PERIOD_DAYS=7  # Days to wait before removing non-performing entries
CLEANUP_MIN_CLICKS_FOR_KEEP=1  # Minimum clicks to keep an entry (0 = remove if no engagement)
```

## How It Works

1. **Performance Analysis**: Every 6 hours (configurable), the system analyzes:
   - Revenue vs targets
   - Content clicks and engagement
   - Campaign performance
   - Lead generation
   - Product sales

2. **AI Diagnosis**: Uses OpenAI (if available) or rule-based analysis to:
   - Identify root causes of performance issues
   - Prioritize fixes by impact
   - Generate actionable recommendations

3. **Automatic Fixes**: Implements fixes such as:
   - Verifying platform API connections
   - Checking Marketing Agent V2 availability
   - Testing affiliate link generation
   - Adjusting posting frequencies

4. **Smart Cleanup System**: Automatically:
   - **Keeps** entries with engagement (clicks, conversions, revenue)
   - **Archives** old entries with zero engagement after grace period
   - **Removes** dead entries from active tracking
   - **Learns** from successful patterns to replicate what works

## Reports

Course correction reports are saved to:
```
output/reports/course_correction_YYYYMMDD_HHMMSS.json
```

Each report contains:
- Performance metrics for the analyzed period
- Identified issues with severity levels
- AI diagnosis and root causes
- Implemented fixes and results
- Cleanup results (what was kept, archived, removed)
- Successful patterns identified for replication

## Manual Execution

You can manually trigger course correction:

```python
from cash_engine import CashEngine

engine = CashEngine()
engine.run_course_correction()
```

Or use the standalone analyzer:

```bash
python analyze_performance.py
```

## Success Criteria

The system triggers course correction when:
- Revenue is below 10% of target (configurable)
- Zero clicks on content despite syndication
- Zero clicks on campaigns
- Zero leads generated
- Low conversion rates (< 1%)

## Integration

The course correction system is automatically integrated into the Cash Engine:
- Runs every 6 hours (configurable)
- First check runs 5 minutes after engine start
- All corrections are logged to `logs/engine.log`

## Requirements

- OpenAI API key (optional, for AI-powered diagnosis)
- If OpenAI is not available, falls back to rule-based diagnosis
- Database must be accessible (`data/engine.db`)
- Logs must be accessible (`logs/engine.log`)
