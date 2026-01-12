# Weekly Work Report System - Setup Guide

## Overview

The Weekly Work Report System generates comprehensive, honest weekly reports analyzing what worked, what didn't, why, future actions, and critical recommendations you might miss.

## Features

### Report Sections

1. **Executive Summary**
   - Revenue performance vs targets
   - Engagement metrics
   - Revenue by source

2. **What Worked**
   - Top performing content with metrics
   - Top performing campaigns
   - Platform performance analysis
   - Why they worked (root cause analysis)

3. **What Didn't Work**
   - Zero engagement content
   - Zero engagement campaigns
   - Underperforming platforms
   - Why they failed (root cause analysis)
   - Common failure patterns

4. **Future Actions**
   - Automatic improvements scheduled
   - Scheduled optimizations
   - Strategy adjustments
   - Platform focus shifts

5. **Honest Recommendations**
   - Critical issues you might miss
   - Missed opportunities
   - Blind spots
   - Quick wins
   - Strategic risks
   - Long-term strategy

## Configuration

Add to `.env`:

```bash
# Enable/disable weekly reports (default: true)
WEEKLY_REPORT_ENABLED=true

# Day of week to generate report (default: monday)
WEEKLY_REPORT_DAY=monday  # monday, tuesday, wednesday, etc.

# Time to generate report (24-hour format, default: 09:00)
WEEKLY_REPORT_TIME=09:00

# Number of days to analyze (default: 7)
WEEKLY_REPORT_DAYS=7

# Optional: Email to send report to
WEEKLY_REPORT_EMAIL=
```

## Report Generation

### Automatic

Reports are automatically generated:
- Every Monday at 9:00 AM (or configured day/time)
- Saved to `output/reports/weekly/`
- Both Markdown and JSON formats

### Manual

Generate a report manually:

```python
from cash_engine import CashEngine

engine = CashEngine()
engine.generate_weekly_report()
```

Or use the standalone generator:

```bash
python test_weekly_report.py
```

## Report Files

Reports are saved as:
- **Markdown**: `output/reports/weekly/weekly_report_YYYY-MM-DD.md`
- **JSON**: `output/reports/weekly/weekly_report_YYYY-MM-DD.json`

## Report Content

### What Worked Section

Identifies:
- Top 5 performing content pieces
- Top 5 performing campaigns
- Best performing platforms
- Success patterns and why they worked

### What Didn't Work Section

Identifies:
- Content with zero engagement
- Campaigns with zero clicks
- Underperforming platforms
- Common failure patterns and likely causes

### Future Actions Section

Shows:
- Automatic improvements from course correction
- Scheduled optimizations
- Strategy adjustments based on data
- Platform focus shifts

### Honest Recommendations Section

AI-powered (or rule-based) recommendations:
- **Critical Issues**: Things that will cause failure if not addressed
- **Missed Opportunities**: Revenue streams not being pursued
- **Blind Spots**: Issues you might not notice
- **Quick Wins**: Easy improvements with high impact
- **Strategic Risks**: Things that could fail
- **Long-term Strategy**: Big picture recommendations

## Integration

The weekly report system is automatically integrated:
- Runs on schedule (configurable day/time)
- Uses AI for recommendations (if OpenAI available)
- Falls back to rule-based recommendations if AI unavailable
- All reports logged to `logs/engine.log`

## Requirements

- Database must be accessible (`data/engine.db`)
- OpenAI API key (optional, for AI-powered recommendations)
- If OpenAI unavailable, uses rule-based recommendations

## Success Criteria

- ✅ Generates comprehensive weekly reports
- ✅ Identifies what worked and why
- ✅ Identifies what didn't work and why
- ✅ Provides future action plans
- ✅ Gives honest, actionable recommendations
- ✅ Highlights things you might miss
- ✅ Runs automatically on schedule
- ✅ Saves reports for historical analysis
