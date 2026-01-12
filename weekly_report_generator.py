#!/usr/bin/env python3
"""
Weekly Work Report Generator
Comprehensive weekly analysis: what worked, what didn't, why, future actions, and honest recommendations
"""

import os
import json
import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logger
logger = logging.getLogger('WeeklyReportGenerator')

# OpenAI client (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None


class DataAggregator:
    """Aggregates 7-day performance data"""
    
    def __init__(self, db_path: Path = Path("./data/engine.db")):
        self.db_path = db_path
    
    def aggregate_week(self, days: int = 7) -> Dict[str, Any]:
        """Aggregate performance data for the week"""
        if not self.db_path.exists():
            return {"error": "Database not found"}
        
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        week_start = datetime.now() - timedelta(days=days)
        
        data = {
            "period_days": days,
            "start_date": week_start.isoformat(),
            "end_date": datetime.now().isoformat(),
        }
        
        # Revenue
        c.execute('''
            SELECT COUNT(*), COALESCE(SUM(amount), 0), COALESCE(AVG(amount), 0),
                   MIN(timestamp), MAX(timestamp)
            FROM revenue 
            WHERE timestamp >= ? AND status = 'completed'
        ''', (week_start,))
        rev = c.fetchone()
        data["revenue"] = {
            "entries": rev[0],
            "total": float(rev[1]),
            "average": float(rev[2]) if rev[0] > 0 else 0.0,
            "first_transaction": rev[3],
            "last_transaction": rev[4]
        }
        
        # Revenue by source
        c.execute('''
            SELECT source, COUNT(*), COALESCE(SUM(amount), 0)
            FROM revenue 
            WHERE timestamp >= ? AND status = 'completed'
            GROUP BY source
            ORDER BY SUM(amount) DESC
        ''', (week_start,))
        data["revenue_by_source"] = {
            row[0]: {"count": row[1], "total": float(row[2])}
            for row in c.fetchall()
        }
        
        # Content performance
        c.execute('''
            SELECT content_file, platform, SUM(clicks) as total_clicks,
                   SUM(conversions) as total_conversions, SUM(revenue) as total_revenue,
                   COUNT(*) as entry_count, MAX(date) as last_date
            FROM content_performance
            WHERE date >= ?
            GROUP BY content_file, platform
        ''', (week_start,))
        data["content_entries"] = [
            {
                "content_file": row[0],
                "platform": row[1],
                "clicks": row[2],
                "conversions": row[3],
                "revenue": float(row[4]),
                "entry_count": row[5],
                "last_date": row[6]
            }
            for row in c.fetchall()
        ]
        
        # Campaign performance
        c.execute('''
            SELECT campaign_id, SUM(clicks) as total_clicks,
                   SUM(conversions) as total_conversions, SUM(commissions) as total_commissions,
                   COUNT(*) as entry_count, MAX(date) as last_date
            FROM campaign_performance
            WHERE date >= ?
            GROUP BY campaign_id
        ''', (week_start,))
        data["campaign_entries"] = [
            {
                "campaign_id": row[0],
                "clicks": row[1],
                "conversions": row[2],
                "commissions": float(row[3]),
                "entry_count": row[4],
                "last_date": row[5]
            }
            for row in c.fetchall()
        ]
        
        # Leads
        c.execute('SELECT COUNT(DISTINCT email) FROM leads')
        total_leads = c.fetchone()[0]
        c.execute('SELECT COUNT(DISTINCT email) FROM leads WHERE converted = 1')
        converted_leads = c.fetchone()[0]
        data["leads"] = {
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
        data["products"] = {
            "total": prod[0],
            "total_sales": prod[1],
            "total_revenue": float(prod[2])
        }
        
        # Calculate targets
        target_monthly = float(os.getenv('TARGET_MONTHLY', '10000'))
        target_daily = target_monthly / 30
        target_week = target_daily * days
        
        data["targets"] = {
            "monthly": target_monthly,
            "daily": target_daily,
            "weekly": target_week,
            "achievement_pct": (data["revenue"]["total"] / target_week * 100) if target_week > 0 else 0.0
        }
        
        conn.close()
        return data


class SuccessAnalyzer:
    """Analyzes what worked and why"""
    
    def analyze_successes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify successful content, campaigns, and strategies"""
        successes = {
            "top_content": [],
            "top_campaigns": [],
            "top_platforms": {},
            "top_products": [],
            "success_patterns": []
        }
        
        # Top performing content
        content_sorted = sorted(
            data.get("content_entries", []),
            key=lambda x: x.get("revenue", 0) + (x.get("clicks", 0) * 0.1) + (x.get("conversions", 0) * 5),
            reverse=True
        )
        successes["top_content"] = content_sorted[:10]
        
        # Top performing campaigns
        campaign_sorted = sorted(
            data.get("campaign_entries", []),
            key=lambda x: x.get("commissions", 0) + (x.get("clicks", 0) * 0.1) + (x.get("conversions", 0) * 5),
            reverse=True
        )
        successes["top_campaigns"] = campaign_sorted[:10]
        
        # Platform performance
        platform_stats = {}
        for entry in data.get("content_entries", []):
            platform = entry.get("platform", "unknown")
            if platform not in platform_stats:
                platform_stats[platform] = {"clicks": 0, "conversions": 0, "revenue": 0.0, "count": 0}
            platform_stats[platform]["clicks"] += entry.get("clicks", 0)
            platform_stats[platform]["conversions"] += entry.get("conversions", 0)
            platform_stats[platform]["revenue"] += entry.get("revenue", 0.0)
            platform_stats[platform]["count"] += 1
        
        successes["top_platforms"] = dict(sorted(
            platform_stats.items(),
            key=lambda x: x[1]["revenue"] + (x[1]["clicks"] * 0.1),
            reverse=True
        ))
        
        # Extract success patterns
        if successes["top_content"]:
            for content in successes["top_content"][:3]:
                if content.get("clicks", 0) > 0 or content.get("revenue", 0) > 0:
                    successes["success_patterns"].append({
                        "type": "content",
                        "pattern": f"{content.get('content_file')} on {content.get('platform')}",
                        "metrics": {
                            "clicks": content.get("clicks", 0),
                            "conversions": content.get("conversions", 0),
                            "revenue": content.get("revenue", 0.0)
                        },
                        "why_it_worked": self._analyze_why_content_worked(content)
                    })
        
        if successes["top_campaigns"]:
            for campaign in successes["top_campaigns"][:3]:
                if campaign.get("clicks", 0) > 0 or campaign.get("commissions", 0) > 0:
                    successes["success_patterns"].append({
                        "type": "campaign",
                        "pattern": f"Campaign {campaign.get('campaign_id')}",
                        "metrics": {
                            "clicks": campaign.get("clicks", 0),
                            "conversions": campaign.get("conversions", 0),
                            "commissions": campaign.get("commissions", 0.0)
                        },
                        "why_it_worked": self._analyze_why_campaign_worked(campaign)
                    })
        
        return successes
    
    def _analyze_why_content_worked(self, content: Dict[str, Any]) -> str:
        """Analyze why content performed well"""
        reasons = []
        
        if content.get("clicks", 0) > 0:
            reasons.append(f"Generated {content.get('clicks')} clicks")
        if content.get("conversions", 0) > 0:
            reasons.append(f"Achieved {content.get('conversions')} conversions")
        if content.get("revenue", 0) > 0:
            reasons.append(f"Generated ${content.get('revenue'):.2f} revenue")
        
        platform = content.get("platform", "unknown")
        if platform != "unknown":
            reasons.append(f"Platform: {platform}")
        
        return "; ".join(reasons) if reasons else "Limited data available"
    
    def _analyze_why_campaign_worked(self, campaign: Dict[str, Any]) -> str:
        """Analyze why campaign performed well"""
        reasons = []
        
        if campaign.get("clicks", 0) > 0:
            reasons.append(f"Generated {campaign.get('clicks')} clicks")
        if campaign.get("conversions", 0) > 0:
            reasons.append(f"Achieved {campaign.get('conversions')} conversions")
        if campaign.get("commissions", 0) > 0:
            reasons.append(f"Earned ${campaign.get('commissions'):.2f} commissions")
        
        return "; ".join(reasons) if reasons else "Limited data available"


class FailureAnalyzer:
    """Analyzes what didn't work and why"""
    
    def analyze_failures(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify failed content, campaigns, and strategies"""
        failures = {
            "zero_engagement_content": [],
            "zero_engagement_campaigns": [],
            "underperforming_platforms": {},
            "zero_sales_products": [],
            "failure_patterns": []
        }
        
        # Zero engagement content
        for entry in data.get("content_entries", []):
            if entry.get("clicks", 0) == 0 and entry.get("conversions", 0) == 0 and entry.get("revenue", 0) == 0:
                failures["zero_engagement_content"].append({
                    "content_file": entry.get("content_file"),
                    "platform": entry.get("platform"),
                    "entry_count": entry.get("entry_count", 0),
                    "last_date": entry.get("last_date"),
                    "why_it_failed": self._analyze_why_content_failed(entry)
                })
        
        # Zero engagement campaigns
        for entry in data.get("campaign_entries", []):
            if entry.get("clicks", 0) == 0 and entry.get("conversions", 0) == 0 and entry.get("commissions", 0) == 0:
                failures["zero_engagement_campaigns"].append({
                    "campaign_id": entry.get("campaign_id"),
                    "entry_count": entry.get("entry_count", 0),
                    "last_date": entry.get("last_date"),
                    "why_it_failed": self._analyze_why_campaign_failed(entry)
                })
        
        # Underperforming platforms (zero engagement)
        platform_failures = {}
        for entry in failures["zero_engagement_content"]:
            platform = entry.get("platform", "unknown")
            if platform not in platform_failures:
                platform_failures[platform] = 0
            platform_failures[platform] += 1
        
        failures["underperforming_platforms"] = platform_failures
        
        # Extract failure patterns
        if failures["zero_engagement_content"]:
            failures["failure_patterns"].append({
                "type": "content_engagement",
                "count": len(failures["zero_engagement_content"]),
                "common_issue": "Content not reaching audience or tracking broken",
                "likely_causes": [
                    "Posts not actually being published",
                    "Platform API issues",
                    "Tracking system not recording clicks",
                    "Content not visible to audience"
                ]
            })
        
        if failures["zero_engagement_campaigns"]:
            failures["failure_patterns"].append({
                "type": "campaign_engagement",
                "count": len(failures["zero_engagement_campaigns"]),
                "common_issue": "Affiliate links not working or not being clicked",
                "likely_causes": [
                    "Marketing Agent V2 not tracking",
                    "Links not properly embedded",
                    "Links pointing to wrong URLs",
                    "Tracking system down"
                ]
            })
        
        return failures
    
    def _analyze_why_content_failed(self, content: Dict[str, Any]) -> str:
        """Analyze why content failed"""
        reasons = []
        
        if content.get("entry_count", 0) > 0:
            reasons.append(f"Tracked {content.get('entry_count')} times with zero engagement")
        
        platform = content.get("platform", "unknown")
        if platform != "unknown":
            reasons.append(f"Platform: {platform}")
        
        last_date = content.get("last_date")
        if last_date:
            try:
                last_date_obj = datetime.fromisoformat(last_date) if isinstance(last_date, str) else last_date
                days_ago = (datetime.now() - last_date_obj).days
                if days_ago > 7:
                    reasons.append(f"Last activity {days_ago} days ago")
            except:
                pass
        
        return "; ".join(reasons) if reasons else "No engagement data"
    
    def _analyze_why_campaign_failed(self, campaign: Dict[str, Any]) -> str:
        """Analyze why campaign failed"""
        reasons = []
        
        if campaign.get("entry_count", 0) > 0:
            reasons.append(f"Tracked {campaign.get('entry_count')} times with zero engagement")
        
        last_date = campaign.get("last_date")
        if last_date:
            try:
                last_date_obj = datetime.fromisoformat(last_date) if isinstance(last_date, str) else last_date
                days_ago = (datetime.now() - last_date_obj).days
                if days_ago > 7:
                    reasons.append(f"Last activity {days_ago} days ago")
            except:
                pass
        
        return "; ".join(reasons) if reasons else "No engagement data"


class FuturePlanner:
    """Plans future actions based on current state"""
    
    def __init__(self, cash_engine=None):
        self.cash_engine = cash_engine
    
    def plan_future_actions(self, data: Dict[str, Any], successes: Dict[str, Any], 
                           failures: Dict[str, Any]) -> Dict[str, Any]:
        """Plan what the system will do in the future"""
        actions = {
            "automatic_improvements": [],
            "scheduled_optimizations": [],
            "strategy_adjustments": [],
            "platform_focus_shifts": []
        }
        
        # Automatic improvements from course correction
        if self.cash_engine and hasattr(self.cash_engine, 'course_corrector'):
            actions["automatic_improvements"].append({
                "action": "AI Course Correction runs every 6 hours",
                "purpose": "Automatically diagnose and fix performance issues",
                "expected_impact": "Maintain optimal performance"
            })
            actions["automatic_improvements"].append({
                "action": "Smart Cleanup System runs with course correction",
                "purpose": "Remove dead entries, keep what works",
                "expected_impact": "Clean database, learn from success"
            })
        
        # Scheduled optimizations
        actions["scheduled_optimizations"].append({
            "action": "Content syndication every 1 hour",
            "purpose": "Distribute content to platforms",
            "frequency": "Hourly"
        })
        actions["scheduled_optimizations"].append({
            "action": "Lead generation every 3 hours",
            "purpose": "Extract and qualify leads",
            "frequency": "Every 3 hours"
        })
        actions["scheduled_optimizations"].append({
            "action": "Product sync every 6 hours",
            "purpose": "Sync Shopify products to database",
            "frequency": "Every 6 hours"
        })
        
        # Strategy adjustments based on data
        if failures.get("zero_engagement_content"):
            actions["strategy_adjustments"].append({
                "action": "Focus on platforms with engagement",
                "reason": f"{len(failures['zero_engagement_content'])} content entries with zero engagement",
                "adjustment": "Prioritize platforms showing results"
            })
        
        if successes.get("top_platforms"):
            top_platform = list(successes["top_platforms"].keys())[0] if successes["top_platforms"] else None
            if top_platform:
                actions["platform_focus_shifts"].append({
                    "action": f"Increase focus on {top_platform}",
                    "reason": f"Top performing platform this week",
                    "adjustment": "Allocate more resources to this platform"
                })
        
        # Product optimization
        if data.get("products", {}).get("total_sales", 0) == 0:
            actions["strategy_adjustments"].append({
                "action": "Review product strategy",
                "reason": "Zero product sales this week",
                "adjustment": "Consider pricing, promotion, or product changes"
            })
        
        return actions


class RecommendationEngine:
    """AI-powered recommendation engine for honest, actionable advice"""
    
    def __init__(self):
        self.openai_client = openai_client
    
    def generate_recommendations(self, data: Dict[str, Any], successes: Dict[str, Any],
                                 failures: Dict[str, Any], actions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate honest recommendations the user might miss"""
        
        if not self.openai_client:
            return self._rule_based_recommendations(data, successes, failures, actions)
        
        try:
            context = f"""
Week Performance Summary:
- Revenue: ${data['revenue']['total']:.2f} (Target: ${data['targets']['weekly']:.2f}, Achievement: {data['targets']['achievement_pct']:.1f}%)
- Content: {len(data.get('content_entries', []))} entries, {sum(c.get('clicks', 0) for c in data.get('content_entries', []))} total clicks
- Campaigns: {len(data.get('campaign_entries', []))} entries, {sum(c.get('clicks', 0) for c in data.get('campaign_entries', []))} total clicks
- Leads: {data.get('leads', {}).get('total', 0)} total, {data.get('leads', {}).get('converted', 0)} converted
- Products: {data.get('products', {}).get('total', 0)} total, {data.get('products', {}).get('total_sales', 0)} sales

What Worked:
{json.dumps(successes.get('success_patterns', [])[:5], indent=2)}

What Didn't Work:
- Zero engagement content: {len(failures.get('zero_engagement_content', []))}
- Zero engagement campaigns: {len(failures.get('zero_engagement_campaigns', []))}
- Failure patterns: {json.dumps(failures.get('failure_patterns', []), indent=2)}
"""
            
            prompt = f"""You are analyzing a revenue generation system's weekly performance. Provide HONEST, ACTIONABLE recommendations that the user might miss.

Focus on:
1. **Critical Issues**: Things that will cause failure if not addressed
2. **Missed Opportunities**: Revenue streams or strategies not being pursued
3. **Blind Spots**: Issues the user might not notice
4. **Quick Wins**: Easy improvements with high impact
5. **Strategic Risks**: Things that could fail
6. **Long-term Strategy**: Big picture recommendations

Be direct and honest. Don't sugarcoat. The user needs actionable advice.

Format as JSON with keys: critical_issues (array), missed_opportunities (array), blind_spots (array), quick_wins (array), strategic_risks (array), long_term_strategy (array).

Each item should have: title, description, impact (high/medium/low), action_required.
"""
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are an expert business analyst. Provide direct, honest, actionable recommendations. Be specific and data-driven."},
                    {"role": "user", "content": prompt + "\n\nContext:\n" + context}
                ],
                temperature=0.4,
                max_tokens=2500
            )
            
            result_text = response.choices[0].message.content
            
            # Try to parse JSON
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                recommendations = json.loads(result_text)
                recommendations["method"] = "ai"
                return recommendations
            except json.JSONDecodeError:
                # Fallback to rule-based
                return self._rule_based_recommendations(data, successes, failures, actions)
        
        except Exception as e:
            logger.error(f"AI recommendations failed: {e}, falling back to rule-based")
            return self._rule_based_recommendations(data, successes, failures, actions)
    
    def _rule_based_recommendations(self, data: Dict[str, Any], successes: Dict[str, Any],
                                    failures: Dict[str, Any], actions: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based recommendations"""
        recommendations = {
            "method": "rule_based",
            "critical_issues": [],
            "missed_opportunities": [],
            "blind_spots": [],
            "quick_wins": [],
            "strategic_risks": [],
            "long_term_strategy": []
        }
        
        # Critical issues
        if data.get("revenue", {}).get("total", 0) == 0:
            recommendations["critical_issues"].append({
                "title": "Zero Revenue Generated",
                "description": "No revenue this week despite active systems. This indicates a fundamental problem with content distribution, tracking, or conversion.",
                "impact": "high",
                "action_required": "Immediate investigation: Verify posts are actually being published, check tracking systems, test affiliate links"
            })
        
        if len(failures.get("zero_engagement_content", [])) > 100:
            recommendations["critical_issues"].append({
                "title": "Massive Content Engagement Failure",
                "description": f"{len(failures['zero_engagement_content'])} content entries with zero engagement. Content is not reaching audience.",
                "impact": "high",
                "action_required": "Verify platform API connections, check if posts are actually published, test tracking systems"
            })
        
        # Missed opportunities
        if data.get("products", {}).get("total", 0) > 0 and data.get("products", {}).get("total_sales", 0) == 0:
            recommendations["missed_opportunities"].append({
                "title": "Products Not Being Promoted",
                "description": f"You have {data['products']['total']} products but zero sales. Products exist but aren't being effectively promoted.",
                "impact": "medium",
                "action_required": "Review product promotion strategy, ensure products are linked in content, consider pricing adjustments"
            })
        
        # Blind spots
        if len(failures.get("zero_engagement_campaigns", [])) > 50:
            recommendations["blind_spots"].append({
                "title": "Affiliate Links May Not Be Working",
                "description": f"{len(failures['zero_engagement_campaigns'])} campaigns with zero clicks. Affiliate links might not be functional or visible.",
                "impact": "high",
                "action_required": "Test affiliate link generation, verify Marketing Agent V2 is tracking, check link embedding in content"
            })
        
        # Quick wins
        if successes.get("top_platforms"):
            top_platform = list(successes["top_platforms"].keys())[0]
            recommendations["quick_wins"].append({
                "title": f"Double Down on {top_platform}",
                "description": f"{top_platform} is your top performing platform. Increase posting frequency there.",
                "impact": "medium",
                "action_required": f"Increase {top_platform} content distribution frequency"
            })
        
        # Strategic risks
        if data.get("revenue", {}).get("total", 0) < data.get("targets", {}).get("weekly", 0) * 0.1:
            recommendations["strategic_risks"].append({
                "title": "Revenue Target Not Being Met",
                "description": f"Only {data['targets']['achievement_pct']:.1f}% of weekly target achieved. Current trajectory will not meet monthly goal.",
                "impact": "high",
                "action_required": "Review entire revenue strategy, consider additional revenue streams, optimize conversion funnels"
            })
        
        # Long-term strategy
        recommendations["long_term_strategy"].append({
            "title": "Build on What Works",
            "description": "Identify successful patterns and replicate them. Stop investing in strategies that show zero engagement.",
            "impact": "high",
            "action_required": "Use Smart Cleanup System to identify successful patterns, replicate top performers, remove dead strategies"
        })
        
        return recommendations


class ReportFormatter:
    """Formats the weekly report"""
    
    def format_markdown(self, report_data: Dict[str, Any]) -> str:
        """Format report as markdown"""
        week_start = datetime.fromisoformat(report_data["data"]["start_date"])
        week_end = datetime.fromisoformat(report_data["data"]["end_date"])
        
        md = f"""# Weekly Work Report
**Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}**

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Executive Summary

### Revenue Performance
- **Total Revenue**: ${report_data['data']['revenue']['total']:.2f}
- **Weekly Target**: ${report_data['data']['targets']['weekly']:.2f}
- **Achievement**: {report_data['data']['targets']['achievement_pct']:.1f}%
- **Daily Average**: ${report_data['data']['revenue']['total'] / 7:.2f}

### Engagement Metrics
- **Content Entries**: {len(report_data['data'].get('content_entries', []))}
- **Total Content Clicks**: {sum(c.get('clicks', 0) for c in report_data['data'].get('content_entries', []))}
- **Campaign Entries**: {len(report_data['data'].get('campaign_entries', []))}
- **Total Campaign Clicks**: {sum(c.get('clicks', 0) for c in report_data['data'].get('campaign_entries', []))}
- **Leads Generated**: {report_data['data'].get('leads', {}).get('total', 0)}
- **Leads Converted**: {report_data['data'].get('leads', {}).get('converted', 0)}

### Revenue by Source
"""
        
        for source, stats in report_data['data'].get('revenue_by_source', {}).items():
            md += f"- **{source}**: ${stats['total']:.2f} ({stats['count']} transactions)\n"
        
        md += "\n---\n\n## ✅ What Worked\n\n"
        
        # Top content
        if report_data['successes'].get('top_content'):
            md += "### Top Performing Content\n\n"
            for i, content in enumerate(report_data['successes']['top_content'][:5], 1):
                md += f"{i}. **{content.get('content_file', 'Unknown')}** on {content.get('platform', 'unknown')}\n"
                md += f"   - Clicks: {content.get('clicks', 0)} | Conversions: {content.get('conversions', 0)} | Revenue: ${content.get('revenue', 0):.2f}\n"
                md += f"   - Why it worked: {self._get_why_worked(content, report_data['successes'].get('success_patterns', []))}\n\n"
        
        # Top campaigns
        if report_data['successes'].get('top_campaigns'):
            md += "### Top Performing Campaigns\n\n"
            for i, campaign in enumerate(report_data['successes']['top_campaigns'][:5], 1):
                md += f"{i}. **Campaign {campaign.get('campaign_id', 'Unknown')}**\n"
                md += f"   - Clicks: {campaign.get('clicks', 0)} | Conversions: {campaign.get('conversions', 0)} | Commissions: ${campaign.get('commissions', 0):.2f}\n"
                md += f"   - Why it worked: {self._get_why_worked(campaign, report_data['successes'].get('success_patterns', []))}\n\n"
        
        # Top platforms
        if report_data['successes'].get('top_platforms'):
            md += "### Platform Performance\n\n"
            for platform, stats in list(report_data['successes']['top_platforms'].items())[:5]:
                md += f"- **{platform}**: {stats['clicks']} clicks, {stats['conversions']} conversions, ${stats['revenue']:.2f} revenue\n"
        
        md += "\n---\n\n## ❌ What Didn't Work\n\n"
        
        # Zero engagement content
        zero_content = report_data['failures'].get('zero_engagement_content', [])
        if zero_content:
            md += f"### Zero Engagement Content ({len(zero_content)} entries)\n\n"
            md += "**Sample failures:**\n"
            for entry in zero_content[:5]:
                md += f"- {entry.get('content_file', 'Unknown')} on {entry.get('platform', 'unknown')}\n"
                md += f"  - Why it failed: {entry.get('why_it_failed', 'Unknown')}\n"
            if len(zero_content) > 5:
                md += f"- ... and {len(zero_content) - 5} more\n"
            md += "\n"
        
        # Zero engagement campaigns
        zero_campaigns = report_data['failures'].get('zero_engagement_campaigns', [])
        if zero_campaigns:
            md += f"### Zero Engagement Campaigns ({len(zero_campaigns)} entries)\n\n"
            md += "**Sample failures:**\n"
            for entry in zero_campaigns[:5]:
                md += f"- Campaign {entry.get('campaign_id', 'Unknown')}\n"
                md += f"  - Why it failed: {entry.get('why_it_failed', 'Unknown')}\n"
            if len(zero_campaigns) > 5:
                md += f"- ... and {len(zero_campaigns) - 5} more\n"
            md += "\n"
        
        # Failure patterns
        if report_data['failures'].get('failure_patterns'):
            md += "### Common Failure Patterns\n\n"
            for pattern in report_data['failures']['failure_patterns']:
                md += f"- **{pattern.get('type', 'Unknown')}**: {pattern.get('common_issue', 'Unknown')}\n"
                md += f"  - Count: {pattern.get('count', 0)}\n"
                md += f"  - Likely causes: {', '.join(pattern.get('likely_causes', []))}\n\n"
        
        md += "\n---\n\n## 🔮 Future Actions\n\n"
        
        # Automatic improvements
        if report_data['actions'].get('automatic_improvements'):
            md += "### Automatic Improvements\n\n"
            for action in report_data['actions']['automatic_improvements']:
                md += f"- **{action.get('action', 'Unknown')}**\n"
                md += f"  - Purpose: {action.get('purpose', 'N/A')}\n"
                md += f"  - Expected impact: {action.get('expected_impact', 'N/A')}\n\n"
        
        # Scheduled optimizations
        if report_data['actions'].get('scheduled_optimizations'):
            md += "### Scheduled Optimizations\n\n"
            for opt in report_data['actions']['scheduled_optimizations']:
                md += f"- **{opt.get('action', 'Unknown')}** ({opt.get('frequency', 'N/A')})\n"
                md += f"  - Purpose: {opt.get('purpose', 'N/A')}\n\n"
        
        # Strategy adjustments
        if report_data['actions'].get('strategy_adjustments'):
            md += "### Strategy Adjustments\n\n"
            for adj in report_data['actions']['strategy_adjustments']:
                md += f"- **{adj.get('action', 'Unknown')}**\n"
                md += f"  - Reason: {adj.get('reason', 'N/A')}\n"
                md += f"  - Adjustment: {adj.get('adjustment', 'N/A')}\n\n"
        
        md += "\n---\n\n## 💡 Honest Recommendations\n\n"
        md += "*These are things you might miss - direct, actionable advice*\n\n"
        
        recs = report_data.get('recommendations', {})
        
        if recs.get('critical_issues'):
            md += "### 🚨 Critical Issues\n\n"
            for issue in recs['critical_issues']:
                md += f"- **{issue.get('title', 'Unknown')}**\n"
                md += f"  - {issue.get('description', 'N/A')}\n"
                md += f"  - Impact: {issue.get('impact', 'unknown').upper()}\n"
                md += f"  - Action Required: {issue.get('action_required', 'N/A')}\n\n"
        
        if recs.get('missed_opportunities'):
            md += "### 🎯 Missed Opportunities\n\n"
            for opp in recs['missed_opportunities']:
                md += f"- **{opp.get('title', 'Unknown')}**\n"
                md += f"  - {opp.get('description', 'N/A')}\n"
                md += f"  - Impact: {opp.get('impact', 'unknown').upper()}\n"
                md += f"  - Action Required: {opp.get('action_required', 'N/A')}\n\n"
        
        if recs.get('blind_spots'):
            md += "### 👁️ Blind Spots (Things You Might Miss)\n\n"
            for spot in recs['blind_spots']:
                md += f"- **{spot.get('title', 'Unknown')}**\n"
                md += f"  - {spot.get('description', 'N/A')}\n"
                md += f"  - Impact: {spot.get('impact', 'unknown').upper()}\n"
                md += f"  - Action Required: {spot.get('action_required', 'N/A')}\n\n"
        
        if recs.get('quick_wins'):
            md += "### ⚡ Quick Wins\n\n"
            for win in recs['quick_wins']:
                md += f"- **{win.get('title', 'Unknown')}**\n"
                md += f"  - {win.get('description', 'N/A')}\n"
                md += f"  - Impact: {win.get('impact', 'unknown').upper()}\n"
                md += f"  - Action Required: {win.get('action_required', 'N/A')}\n\n"
        
        if recs.get('strategic_risks'):
            md += "### ⚠️ Strategic Risks\n\n"
            for risk in recs['strategic_risks']:
                md += f"- **{risk.get('title', 'Unknown')}**\n"
                md += f"  - {risk.get('description', 'N/A')}\n"
                md += f"  - Impact: {risk.get('impact', 'unknown').upper()}\n"
                md += f"  - Action Required: {risk.get('action_required', 'N/A')}\n\n"
        
        if recs.get('long_term_strategy'):
            md += "### 🎯 Long-term Strategy\n\n"
            for strategy in recs['long_term_strategy']:
                md += f"- **{strategy.get('title', 'Unknown')}**\n"
                md += f"  - {strategy.get('description', 'N/A')}\n"
                md += f"  - Impact: {strategy.get('impact', 'unknown').upper()}\n"
                md += f"  - Action Required: {strategy.get('action_required', 'N/A')}\n\n"
        
        md += "\n---\n\n"
        md += f"*Report generated by Cash Engine v2.0 - AI Course Correction System*\n"
        md += f"*For questions or issues, check logs/engine.log*\n"
        
        return md
    
    def _get_why_worked(self, item: Dict[str, Any], patterns: List[Dict[str, Any]]) -> str:
        """Get why something worked from patterns"""
        for pattern in patterns:
            if pattern.get("type") == "content" and item.get("content_file"):
                if pattern.get("pattern", "").startswith(item.get("content_file", "")):
                    return pattern.get("why_it_worked", "Performed well")
            elif pattern.get("type") == "campaign" and item.get("campaign_id"):
                if str(item.get("campaign_id")) in pattern.get("pattern", ""):
                    return pattern.get("why_it_worked", "Performed well")
        return "Limited analysis data available"


class WeeklyReportGenerator:
    """Main weekly report generator"""
    
    def __init__(self, db_path: Path = Path("./data/engine.db"), cash_engine=None):
        self.data_aggregator = DataAggregator(db_path)
        self.success_analyzer = SuccessAnalyzer()
        self.failure_analyzer = FailureAnalyzer()
        self.future_planner = FuturePlanner(cash_engine)
        self.recommendation_engine = RecommendationEngine()
        self.report_formatter = ReportFormatter()
        self.db_path = db_path
    
    def generate_weekly_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive weekly report"""
        logger.info("📊 Generating Weekly Work Report...")
        
        # Step 1: Aggregate data
        data = self.data_aggregator.aggregate_week(days)
        if "error" in data:
            return {"error": data["error"]}
        
        logger.info(f"📈 Aggregated {days}-day data: ${data['revenue']['total']:.2f} revenue")
        
        # Step 2: Analyze successes
        successes = self.success_analyzer.analyze_successes(data)
        logger.info(f"✅ Identified {len(successes['success_patterns'])} success patterns")
        
        # Step 3: Analyze failures
        failures = self.failure_analyzer.analyze_failures(data)
        logger.info(f"❌ Identified {len(failures['zero_engagement_content'])} failed content, {len(failures['zero_engagement_campaigns'])} failed campaigns")
        
        # Step 4: Plan future actions
        actions = self.future_planner.plan_future_actions(data, successes, failures)
        logger.info(f"🔮 Planned {len(actions['automatic_improvements']) + len(actions['strategy_adjustments'])} future actions")
        
        # Step 5: Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(
            data, successes, failures, actions
        )
        logger.info(f"💡 Generated recommendations (method: {recommendations.get('method', 'unknown')})")
        
        # Step 6: Compile report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "data": data,
            "successes": successes,
            "failures": failures,
            "actions": actions,
            "recommendations": recommendations
        }
        
        # Step 7: Format and save
        markdown_report = self.report_formatter.format_markdown(report_data)
        
        # Save reports
        report_dir = Path("./output/reports/weekly")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        md_file = report_dir / f"weekly_report_{date_str}.md"
        json_file = report_dir / f"weekly_report_{date_str}.json"
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Weekly report saved: {md_file}")
        logger.info(f"📄 Weekly report data saved: {json_file}")
        
        return {
            "success": True,
            "markdown_file": str(md_file),
            "json_file": str(json_file),
            "report_data": report_data
        }
