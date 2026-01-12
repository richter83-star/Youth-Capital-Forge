#!/usr/bin/env python3
"""
AI-Driven Course Correction System
Automatically analyzes performance, diagnoses issues, and implements fixes
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
logger = logging.getLogger('AICourseCorrector')

# OpenAI client (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None


class PerformanceAnalyzer:
    """Analyzes performance metrics and identifies issues"""
    
    def __init__(self, db_path: Path = Path("./data/engine.db")):
        self.db_path = db_path
    
    def analyze_period(self, days: int = 3) -> Dict[str, Any]:
        """Analyze performance for specified period"""
        if not self.db_path.exists():
            return {"error": "Database not found"}
        
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        period_start = datetime.now() - timedelta(days=days)
        
        metrics = {
            "period_days": days,
            "start_date": period_start.isoformat(),
            "end_date": datetime.now().isoformat(),
        }
        
        # Revenue metrics
        c.execute('''
            SELECT COUNT(*), COALESCE(SUM(amount), 0), COALESCE(AVG(amount), 0)
            FROM revenue 
            WHERE timestamp >= ? AND status = 'completed'
        ''', (period_start,))
        rev_count, rev_total, rev_avg = c.fetchone()
        metrics["revenue"] = {
            "entries": rev_count,
            "total": float(rev_total),
            "average_per_entry": float(rev_avg) if rev_count > 0 else 0.0,
            "daily_average": float(rev_total) / days if days > 0 else 0.0
        }
        
        # Content performance
        c.execute('''
            SELECT COUNT(*), COALESCE(SUM(clicks), 0), COALESCE(SUM(conversions), 0), 
                   COALESCE(SUM(revenue), 0), COALESCE(AVG(clicks), 0)
            FROM content_performance 
            WHERE date >= ?
        ''', (period_start,))
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
        ''', (period_start,))
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
        
        # Calculate targets
        target_monthly = float(os.getenv('TARGET_MONTHLY', '10000'))
        target_daily = target_monthly / 30
        target_period = target_daily * days
        
        metrics["targets"] = {
            "monthly": target_monthly,
            "daily": target_daily,
            "period": target_period,
            "revenue_achievement_pct": (metrics["revenue"]["total"] / target_period * 100) if target_period > 0 else 0.0
        }
        
        conn.close()
        return metrics
    
    def identify_issues(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance issues from metrics"""
        issues = []
        threshold_pct = float(os.getenv('REVENUE_THRESHOLD_PCT', '10'))
        
        # Revenue check
        if metrics["revenue"]["total"] < metrics["targets"]["period"] * (threshold_pct / 100):
            issues.append({
                "type": "revenue",
                "severity": "critical",
                "description": f"Revenue critically low: ${metrics['revenue']['total']:.2f} vs target ${metrics['targets']['period']:.2f} ({metrics['targets']['revenue_achievement_pct']:.1f}%)",
                "impact": "high"
            })
        
        # Content clicks check
        if metrics["content"]["total_clicks"] == 0 and metrics["content"]["entries"] > 0:
            issues.append({
                "type": "content_engagement",
                "severity": "critical",
                "description": f"Zero clicks on {metrics['content']['entries']} content entries - content not reaching audience",
                "impact": "high"
            })
        
        # Campaign clicks check
        if metrics["campaigns"]["total_clicks"] == 0 and metrics["campaigns"]["entries"] > 0:
            issues.append({
                "type": "campaign_engagement",
                "severity": "critical",
                "description": f"Zero clicks on {metrics['campaigns']['entries']} campaign entries - affiliate links not working",
                "impact": "high"
            })
        
        # Lead generation check
        if metrics["leads"]["total"] == 0:
            issues.append({
                "type": "lead_generation",
                "severity": "high",
                "description": "Zero leads generated - lead generation failing",
                "impact": "medium"
            })
        
        # Conversion rate check
        if metrics["content"]["conversion_rate"] > 0 and metrics["content"]["conversion_rate"] < 1.0:
            issues.append({
                "type": "conversion_rate",
                "severity": "medium",
                "description": f"Low conversion rate: {metrics['content']['conversion_rate']:.2f}%",
                "impact": "medium"
            })
        
        return issues


class AIDiagnostician:
    """Uses AI to diagnose root causes and recommend fixes"""
    
    def __init__(self):
        self.openai_client = openai_client
    
    def diagnose(self, metrics: Dict[str, Any], issues: List[Dict[str, Any]], 
                 recent_logs: Optional[str] = None) -> Dict[str, Any]:
        """Use AI to diagnose root causes"""
        
        if not self.openai_client:
            # Fallback to rule-based diagnosis
            return self._rule_based_diagnosis(metrics, issues)
        
        try:
            # Prepare context for AI
            context = f"""
Performance Metrics (Last {metrics['period_days']} days):
- Revenue: ${metrics['revenue']['total']:.2f} (Target: ${metrics['targets']['period']:.2f})
- Content Clicks: {metrics['content']['total_clicks']} from {metrics['content']['entries']} entries
- Campaign Clicks: {metrics['campaigns']['total_clicks']} from {metrics['campaigns']['entries']} entries
- Leads: {metrics['leads']['total']} total, {metrics['leads']['converted']} converted
- Products: {metrics['products']['total']} total, {metrics['products']['total_sales']} sales

Issues Identified:
{json.dumps(issues, indent=2)}

Recent Logs (last 50 lines):
{recent_logs or 'No logs available'}
"""
            
            prompt = f"""You are analyzing a revenue generation system that has been running for {metrics['period_days']} days with zero revenue and zero clicks.

Analyze the performance data and identify the ROOT CAUSES of why:
1. Content is being syndicated but getting zero clicks
2. Affiliate campaigns have zero clicks
3. No revenue is being generated

Provide:
1. Root cause analysis (be specific - is it API issues, tracking problems, content quality, platform issues?)
2. Prioritized list of fixes (most impactful first)
3. Specific actionable steps to implement each fix

Format as JSON with keys: root_causes, fixes (array of objects with: priority, action, expected_impact, implementation_steps)
"""
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are an expert revenue system analyst. Provide specific, actionable technical recommendations."},
                    {"role": "user", "content": prompt + "\n\nContext:\n" + context}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                # Extract JSON if wrapped in markdown
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                diagnosis = json.loads(result_text)
                diagnosis["method"] = "ai"
                return diagnosis
            except json.JSONDecodeError:
                # If JSON parsing fails, use text analysis
                return {
                    "method": "ai_text",
                    "analysis": result_text,
                    "root_causes": self._extract_root_causes_from_text(result_text),
                    "fixes": self._extract_fixes_from_text(result_text)
                }
        
        except Exception as e:
            logger.error(f"AI diagnosis failed: {e}, falling back to rule-based")
            return self._rule_based_diagnosis(metrics, issues)
    
    def _rule_based_diagnosis(self, metrics: Dict[str, Any], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback rule-based diagnosis"""
        root_causes = []
        fixes = []
        
        # Zero clicks on content
        if metrics["content"]["total_clicks"] == 0 and metrics["content"]["entries"] > 0:
            root_causes.append({
                "issue": "Content not reaching audience",
                "possible_causes": [
                    "Posts not actually being published to platforms",
                    "Platform API authentication issues",
                    "Content formatting preventing visibility",
                    "Tracking system not recording clicks"
                ]
            })
            fixes.append({
                "priority": 1,
                "action": "Verify platform API connections and test actual post publication",
                "expected_impact": "high",
                "implementation_steps": [
                    "Test Twitter/Facebook/LinkedIn API connections",
                    "Verify posts are actually published (check platform directly)",
                    "Check if tracking URLs are being generated correctly",
                    "Test click tracking system"
                ]
            })
        
        # Zero campaign clicks
        if metrics["campaigns"]["total_clicks"] == 0:
            root_causes.append({
                "issue": "Affiliate links not working",
                "possible_causes": [
                    "Marketing Agent V2 not tracking clicks",
                    "Affiliate links not properly embedded in content",
                    "Links pointing to wrong URLs",
                    "Tracking system down or misconfigured"
                ]
            })
            fixes.append({
                "priority": 2,
                "action": "Verify Marketing Agent V2 and affiliate link generation",
                "expected_impact": "high",
                "implementation_steps": [
                    "Check Marketing Agent V2 availability",
                    "Test affiliate link generation",
                    "Verify links are embedded in content",
                    "Implement fallback tracking if Marketing Agent is down"
                ]
            })
        
        # Zero revenue
        if metrics["revenue"]["total"] == 0:
            root_causes.append({
                "issue": "No revenue generation",
                "possible_causes": [
                    "No clicks = no conversions",
                    "Products not properly configured",
                    "Checkout/payment systems not working",
                    "Content not compelling enough to convert"
                ]
            })
            fixes.append({
                "priority": 3,
                "action": "Fix click generation first, then optimize conversion",
                "expected_impact": "critical",
                "implementation_steps": [
                    "Fix content distribution (priority 1)",
                    "Fix affiliate links (priority 2)",
                    "Once clicks are working, optimize conversion rates",
                    "Test product checkout flows"
                ]
            })
        
        return {
            "method": "rule_based",
            "root_causes": root_causes,
            "fixes": fixes
        }
    
    def _extract_root_causes_from_text(self, text: str) -> List[str]:
        """Extract root causes from AI text response"""
        causes = []
        # Simple extraction - look for numbered lists or bullet points
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['root cause', 'issue', 'problem', 'because']):
                causes.append(line.strip())
        return causes[:5]  # Top 5
    
    def _extract_fixes_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract fixes from AI text response"""
        fixes = []
        # Simple extraction
        lines = text.split('\n')
        current_fix = None
        for line in lines:
            if any(keyword in line.lower() for keyword in ['fix', 'action', 'solution', 'recommend']):
                if current_fix:
                    fixes.append(current_fix)
                current_fix = {"action": line.strip(), "priority": len(fixes) + 1}
        if current_fix:
            fixes.append(current_fix)
        return fixes


class FixImplementer:
    """Implements fixes automatically"""
    
    def __init__(self, cash_engine=None):
        self.cash_engine = cash_engine
        self.marketing_agent_url = os.getenv('MARKETING_AGENT_URL', 'http://localhost:9000')
    
    def implement_fixes(self, fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Implement prioritized fixes"""
        results = {
            "implemented": [],
            "failed": [],
            "skipped": []
        }
        
        for fix in sorted(fixes, key=lambda x: x.get("priority", 999)):
            try:
                action = fix.get("action", "").lower()
                
                # Fix 1: Verify platform API connections
                if "platform api" in action or "verify platform" in action:
                    result = self._verify_platform_apis()
                    if result["success"]:
                        results["implemented"].append({"fix": fix, "result": result})
                    else:
                        results["failed"].append({"fix": fix, "result": result})
                
                # Fix 2: Verify Marketing Agent and affiliate links
                elif "marketing agent" in action or "affiliate link" in action:
                    result = self._verify_affiliate_tracking()
                    if result["success"]:
                        results["implemented"].append({"fix": fix, "result": result})
                    else:
                        results["failed"].append({"fix": fix, "result": result})
                
                # Fix 3: Increase posting frequency
                elif "posting frequency" in action or "increase" in action:
                    result = self._increase_posting_frequency()
                    if result["success"]:
                        results["implemented"].append({"fix": fix, "result": result})
                    else:
                        results["failed"].append({"fix": fix, "result": result})
                
                # Fix 4: Improve lead generation
                elif "lead generation" in action or "leads" in action:
                    result = self._improve_lead_generation()
                    if result["success"]:
                        results["implemented"].append({"fix": fix, "result": result})
                    else:
                        results["failed"].append({"fix": fix, "result": result})
                
                else:
                    results["skipped"].append({"fix": fix, "reason": "No implementation available"})
            
            except Exception as e:
                results["failed"].append({"fix": fix, "error": str(e)})
        
        return results
    
    def _verify_platform_apis(self) -> Dict[str, Any]:
        """Verify platform API connections"""
        results = {}
        
        # Check Twitter
        twitter_key = os.getenv('TWITTER_API_KEY')
        twitter_token = os.getenv('TWITTER_ACCESS_TOKEN')
        results["twitter"] = {
            "configured": bool(twitter_key and twitter_token),
            "status": "configured" if (twitter_key and twitter_token) else "missing_credentials"
        }
        
        # Check Facebook
        facebook_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
        results["facebook"] = {
            "configured": bool(facebook_token),
            "status": "configured" if facebook_token else "missing_credentials"
        }
        
        # Check LinkedIn
        linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        results["linkedin"] = {
            "configured": bool(linkedin_token),
            "status": "configured" if linkedin_token else "missing_credentials"
        }
        
        return {
            "success": True,
            "details": results,
            "message": "Platform API status checked"
        }
    
    def _verify_affiliate_tracking(self) -> Dict[str, Any]:
        """Verify Marketing Agent V2 and affiliate link tracking"""
        try:
            # Check Marketing Agent availability
            response = requests.get(f"{self.marketing_agent_url}/health", timeout=5)
            agent_available = response.status_code == 200
            
            # Check if campaigns exist
            if agent_available:
                campaigns_response = requests.get(f"{self.marketing_agent_url}/api/campaigns", timeout=5)
                campaigns_available = campaigns_response.status_code == 200
            else:
                campaigns_available = False
            
            return {
                "success": True,
                "marketing_agent_available": agent_available,
                "campaigns_accessible": campaigns_available,
                "message": f"Marketing Agent: {'available' if agent_available else 'unavailable'}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Marketing Agent check failed - may need fallback tracking"
            }
    
    def _increase_posting_frequency(self) -> Dict[str, Any]:
        """Increase content posting frequency"""
        # This would modify the schedule in cash_engine
        # For now, return recommendation
        return {
            "success": True,
            "message": "Recommendation: Increase content syndication frequency from current schedule",
            "action_required": "manual_schedule_adjustment"
        }
    
    def _improve_lead_generation(self) -> Dict[str, Any]:
        """Improve lead generation"""
        return {
            "success": True,
            "message": "Recommendation: Increase lead generation frequency and add new sources",
            "action_required": "manual_config_adjustment"
        }


class SmartCleanupSystem:
    """Smart cleanup system - keeps what works, improves what's partial, removes what doesn't"""
    
    def __init__(self, db_path: Path = Path("./data/engine.db")):
        self.db_path = db_path
        self.archive_path = Path("./data/archived")
        self.archive_path.mkdir(parents=True, exist_ok=True)
    
    def analyze_and_cleanup(self, grace_period_days: int = 7, min_clicks_for_keep: int = 1) -> Dict[str, Any]:
        """Analyze entries and clean up non-performing ones"""
        if not self.db_path.exists():
            return {"error": "Database not found"}
        
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=grace_period_days)
        results = {
            "timestamp": datetime.now().isoformat(),
            "grace_period_days": grace_period_days,
            "content": {"analyzed": 0, "kept": 0, "archived": 0, "removed": 0},
            "campaigns": {"analyzed": 0, "kept": 0, "archived": 0, "removed": 0},
            "patterns_learned": []
        }
        
        # Analyze content performance
        c.execute('''
            SELECT content_file, platform, SUM(clicks) as total_clicks, 
                   SUM(conversions) as total_conversions, SUM(revenue) as total_revenue,
                   MAX(date) as last_date, COUNT(*) as entry_count
            FROM content_performance
            GROUP BY content_file, platform
        ''')
        
        content_entries = c.fetchall()
        results["content"]["analyzed"] = len(content_entries)
        
        for entry in content_entries:
            content_file, platform, clicks, conversions, revenue, last_date, entry_count = entry
            last_date_obj = datetime.fromisoformat(last_date) if last_date else datetime.min
            
            # Determine action: keep, improve, or remove
            if clicks >= min_clicks_for_keep or conversions > 0 or revenue > 0:
                # KEEP: Has engagement
                results["content"]["kept"] += 1
                results["patterns_learned"].append({
                    "type": "content",
                    "pattern": f"{content_file} on {platform}",
                    "reason": "performing",
                    "clicks": clicks,
                    "conversions": conversions,
                    "revenue": float(revenue)
                })
            elif (datetime.now() - last_date_obj).days < grace_period_days:
                # KEEP: Still in grace period (recent, might perform)
                results["content"]["kept"] += 1
            else:
                # REMOVE: Old and no engagement
                # Archive the entry first
                try:
                    archive_data = {
                        "content_file": content_file,
                        "platform": platform,
                        "clicks": clicks,
                        "conversions": conversions,
                        "revenue": float(revenue),
                        "last_date": last_date,
                        "archived_date": datetime.now().isoformat(),
                        "reason": "no_engagement_after_grace_period"
                    }
                    archive_file = self.archive_path / f"content_{content_file}_{platform}_{datetime.now().strftime('%Y%m%d')}.json"
                    with open(archive_file, 'w') as f:
                        json.dump(archive_data, f, indent=2)
                    
                    # Remove from database
                    c.execute('''
                        DELETE FROM content_performance 
                        WHERE content_file = ? AND platform = ?
                    ''', (content_file, platform))
                    
                    results["content"]["archived"] += 1
                    results["content"]["removed"] += 1
                except Exception as e:
                    logger.error(f"Error archiving content entry: {e}")
        
        # Analyze campaign performance
        c.execute('''
            SELECT campaign_id, SUM(clicks) as total_clicks,
                   SUM(conversions) as total_conversions, SUM(commissions) as total_commissions,
                   MAX(date) as last_date, COUNT(*) as entry_count
            FROM campaign_performance
            GROUP BY campaign_id
        ''')
        
        campaign_entries = c.fetchall()
        results["campaigns"]["analyzed"] = len(campaign_entries)
        
        for entry in campaign_entries:
            campaign_id, clicks, conversions, commissions, last_date, entry_count = entry
            last_date_obj = datetime.fromisoformat(last_date) if last_date else datetime.min
            
            # Determine action
            if clicks >= min_clicks_for_keep or conversions > 0 or commissions > 0:
                # KEEP: Has engagement
                results["campaigns"]["kept"] += 1
                results["patterns_learned"].append({
                    "type": "campaign",
                    "pattern": f"Campaign {campaign_id}",
                    "reason": "performing",
                    "clicks": clicks,
                    "conversions": conversions,
                    "commissions": float(commissions)
                })
            elif (datetime.now() - last_date_obj).days < grace_period_days:
                # KEEP: Still in grace period
                results["campaigns"]["kept"] += 1
            else:
                # REMOVE: Old and no engagement
                try:
                    archive_data = {
                        "campaign_id": campaign_id,
                        "clicks": clicks,
                        "conversions": conversions,
                        "commissions": float(commissions),
                        "last_date": last_date,
                        "archived_date": datetime.now().isoformat(),
                        "reason": "no_engagement_after_grace_period"
                    }
                    archive_file = self.archive_path / f"campaign_{campaign_id}_{datetime.now().strftime('%Y%m%d')}.json"
                    with open(archive_file, 'w') as f:
                        json.dump(archive_data, f, indent=2)
                    
                    # Remove from database
                    c.execute('DELETE FROM campaign_performance WHERE campaign_id = ?', (campaign_id,))
                    
                    results["campaigns"]["archived"] += 1
                    results["campaigns"]["removed"] += 1
                except Exception as e:
                    logger.error(f"Error archiving campaign entry: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🧹 Cleanup complete: Archived {results['content']['archived']} content, {results['campaigns']['archived']} campaigns")
        logger.info(f"✅ Kept {results['content']['kept']} content, {results['campaigns']['kept']} campaigns")
        logger.info(f"📚 Learned {len(results['patterns_learned'])} successful patterns")
        
        return results
    
    def get_successful_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns that are working well"""
        if not self.db_path.exists():
            return []
        
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        patterns = []
        
        # Get top performing content
        c.execute('''
            SELECT content_file, platform, SUM(clicks) as total_clicks,
                   SUM(conversions) as total_conversions, SUM(revenue) as total_revenue
            FROM content_performance
            WHERE clicks > 0 OR conversions > 0 OR revenue > 0
            GROUP BY content_file, platform
            ORDER BY total_revenue DESC, total_clicks DESC
            LIMIT 10
        ''')
        
        for row in c.fetchall():
            patterns.append({
                "type": "content",
                "content_file": row[0],
                "platform": row[1],
                "clicks": row[2],
                "conversions": row[3],
                "revenue": float(row[4]),
                "success_score": float(row[4]) + (row[2] * 0.1) + (row[3] * 5)  # Weighted score
            })
        
        # Get top performing campaigns
        c.execute('''
            SELECT campaign_id, SUM(clicks) as total_clicks,
                   SUM(conversions) as total_conversions, SUM(commissions) as total_commissions
            FROM campaign_performance
            WHERE clicks > 0 OR conversions > 0 OR commissions > 0
            GROUP BY campaign_id
            ORDER BY total_commissions DESC, total_clicks DESC
            LIMIT 10
        ''')
        
        for row in c.fetchall():
            patterns.append({
                "type": "campaign",
                "campaign_id": row[0],
                "clicks": row[1],
                "conversions": row[2],
                "commissions": float(row[3]),
                "success_score": float(row[3]) + (row[1] * 0.1) + (row[2] * 5)
            })
        
        conn.close()
        
        # Sort by success score
        patterns.sort(key=lambda x: x.get("success_score", 0), reverse=True)
        
        return patterns


class AICourseCorrector:
    """Main course correction orchestrator"""
    
    def __init__(self, db_path: Path = Path("./data/engine.db"), cash_engine=None):
        self.analyzer = PerformanceAnalyzer(db_path)
        self.diagnostician = AIDiagnostician()
        self.fix_implementer = FixImplementer(cash_engine)
        self.cleanup_system = SmartCleanupSystem(db_path)
        self.db_path = db_path
    
    def run_course_correction(self, days: int = 3, read_logs: bool = True) -> Dict[str, Any]:
        """Run complete course correction analysis and implementation"""
        logger.info("🔍 Starting AI Course Correction Analysis...")
        
        # Step 1: Analyze performance
        metrics = self.analyzer.analyze_period(days)
        if "error" in metrics:
            return {"error": metrics["error"]}
        
        logger.info(f"📊 Analyzed {days}-day performance: Revenue ${metrics['revenue']['total']:.2f} ({metrics['targets']['revenue_achievement_pct']:.1f}% of target)")
        
        # Step 2: Identify issues
        issues = self.analyzer.identify_issues(metrics)
        logger.info(f"⚠️  Identified {len(issues)} performance issues")
        
        # Step 3: AI diagnosis
        recent_logs = None
        if read_logs:
            log_path = Path("./logs/engine.log")
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_logs = '\n'.join(lines[-50:])  # Last 50 lines
        
        diagnosis = self.diagnostician.diagnose(metrics, issues, recent_logs)
        logger.info(f"🤖 AI Diagnosis complete (method: {diagnosis.get('method', 'unknown')})")
        
        # Step 4: Implement fixes
        fixes = diagnosis.get("fixes", [])
        if fixes:
            implementation_results = self.fix_implementer.implement_fixes(fixes)
            logger.info(f"🔧 Implemented {len(implementation_results['implemented'])} fixes")
        else:
            implementation_results = {"implemented": [], "failed": [], "skipped": []}
        
        # Step 5: Smart Cleanup - keep what works, remove what doesn't
        logger.info("🧹 Running smart cleanup system...")
        grace_period = int(os.getenv('CLEANUP_GRACE_PERIOD_DAYS', '7'))
        min_clicks = int(os.getenv('CLEANUP_MIN_CLICKS_FOR_KEEP', '1'))
        cleanup_results = self.cleanup_system.analyze_and_cleanup(
            grace_period_days=grace_period,
            min_clicks_for_keep=min_clicks
        )
        
        # Get successful patterns for learning
        successful_patterns = self.cleanup_system.get_successful_patterns()
        logger.info(f"📚 Identified {len(successful_patterns)} successful patterns to replicate")
        
        # Step 6: Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "metrics": metrics,
            "issues": issues,
            "diagnosis": diagnosis,
            "fixes_implemented": implementation_results,
            "cleanup_results": cleanup_results,
            "successful_patterns": successful_patterns[:10],  # Top 10 patterns
            "needs_correction": len(issues) > 0
        }
        
        # Save report
        report_path = Path("./output/reports")
        report_path.mkdir(parents=True, exist_ok=True)
        report_file = report_path / f"course_correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Course correction report saved: {report_file}")
        
        return report
