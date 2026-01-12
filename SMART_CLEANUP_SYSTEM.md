# Smart Cleanup System - Documentation

## Overview

The Smart Cleanup System is integrated into the AI Course Correction System. It automatically manages content and campaign entries by:

- **Keeping** what works (has engagement)
- **Improving** what's partial (recent entries in grace period)
- **Removing** what doesn't work (old entries with zero engagement)

## How It Works

### 1. Analysis Phase

The system analyzes all entries in:
- `content_performance` table
- `campaign_performance` table

For each entry, it checks:
- Total clicks, conversions, revenue
- Last activity date
- Age of entry

### 2. Decision Logic

**KEEP** if:
- Has engagement (clicks ≥ threshold OR conversions > 0 OR revenue > 0)
- Still in grace period (recent, might perform)

**ARCHIVE & REMOVE** if:
- Old (beyond grace period)
- Zero engagement (no clicks, conversions, or revenue)

### 3. Archiving

Before removal, entries are archived to:
```
data/archived/content_<filename>_<platform>_<date>.json
data/archived/campaign_<campaign_id>_<date>.json
```

Archive files contain:
- Original entry data
- Performance metrics
- Reason for archiving
- Archive timestamp

### 4. Pattern Learning

The system identifies successful patterns:
- Top performing content (by revenue, clicks, conversions)
- Top performing campaigns (by commissions, clicks, conversions)
- Calculates success scores for ranking

These patterns are saved in reports for replication.

## Configuration

Add to `.env`:

```bash
# Grace period before removing non-performing entries (days, default: 7)
CLEANUP_GRACE_PERIOD_DAYS=7

# Minimum clicks to keep an entry (default: 1)
# Set to 0 to remove entries with zero engagement immediately after grace period
CLEANUP_MIN_CLICKS_FOR_KEEP=1
```

## When Cleanup Runs

- Automatically as part of course correction (every 6 hours)
- Can be run manually via `SmartCleanupSystem.analyze_and_cleanup()`

## Example Results

```
📊 Cleanup Results:
   Content: Analyzed 3825, Kept 3, Archived 3822, Removed 3822
   Campaigns: Analyzed 11167, Kept 179, Archived 10988, Removed 10988
   Patterns Learned: 0
```

## Success Criteria

The cleanup system ensures:
- ✅ Database stays clean (removes dead entries)
- ✅ Successful patterns are identified and preserved
- ✅ Nothing valuable is lost (archived before removal)
- ✅ System learns from what works
- ✅ Only active, potentially valuable entries remain

## Manual Execution

```python
from ai_course_corrector import SmartCleanupSystem

cs = SmartCleanupSystem()
results = cs.analyze_and_cleanup(
    grace_period_days=7,
    min_clicks_for_keep=1
)

# Get successful patterns
patterns = cs.get_successful_patterns()
```

## Integration

The cleanup system is automatically integrated:
- Runs as part of course correction
- Results included in course correction reports
- Successful patterns saved for replication
- All actions logged to `logs/engine.log`
