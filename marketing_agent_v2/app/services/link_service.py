"""
Link tracking service with bot filtering and analytics.
"""

import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import Link, ClickEvent, Campaign
from app.schemas import LinkCreate, LinkResponse, LinkStatsResponse, ClickEventCreate


class BotDetector:
    """Detects bot traffic based on user agent and referrer."""
    
    BOT_TOKENS = [
        'bot', 'spider', 'crawl', 'slurp', 'curl', 'wget', 'python',
        'java', 'ruby', 'perl', 'php', 'node', 'go', 'rust',
        'googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider',
        'yandexbot', 'facebookexternalhit', 'twitterbot', 'linkedinbot'
    ]
    
    @classmethod
    def is_bot(cls, user_agent: Optional[str], referrer: Optional[str]) -> bool:
        """
        Detect if a request is from a bot.
        
        Args:
            user_agent: HTTP user agent string
            referrer: HTTP referrer string
        
        Returns:
            True if likely a bot, False otherwise
        """
        # Missing user agent and referrer is suspicious
        if not user_agent and not referrer:
            return True
        
        # Check user agent for bot tokens
        if user_agent:
            ua_lower = user_agent.lower()
            for token in cls.BOT_TOKENS:
                if token in ua_lower:
                    return True
        
        return False


class LinkService:
    """Service for managing tracked links."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_link(
        self,
        campaign_id: int,
        channel: str,
        long_url: str,
        utm_params: Optional[Dict[str, str]] = None
    ) -> LinkResponse:
        """
        Create a new tracked link.
        
        Args:
            campaign_id: Campaign ID
            channel: Channel name (email, social, cms)
            long_url: Long URL to track
            utm_params: Optional UTM parameters
        
        Returns:
            LinkResponse
        """
        # Verify campaign exists
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Generate short slug
        short_slug = self._generate_short_slug()
        
        # Build UTM JSON
        utm_json = utm_params or {}
        if not utm_json.get('utm_source'):
            utm_json['utm_source'] = channel
        if not utm_json.get('utm_medium'):
            utm_json['utm_medium'] = 'marketing'
        if not utm_json.get('utm_campaign'):
            utm_json['utm_campaign'] = f"campaign_{campaign_id}"
        
        # Create link
        link = Link(
            campaign_id=campaign_id,
            channel=channel,
            long_url=long_url,
            short_slug=short_slug,
            utm_json=utm_json
        )
        
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        
        return LinkResponse.model_validate(link)
    
    def get_link(self, link_id: int) -> Optional[LinkResponse]:
        """Get a link by ID."""
        link = self.db.query(Link).filter(Link.id == link_id).first()
        if link:
            return LinkResponse.model_validate(link)
        return None
    
    def get_link_by_slug(self, slug: str) -> Optional[Link]:
        """Get a link by short slug."""
        return self.db.query(Link).filter(Link.short_slug == slug).first()
    
    def list_links(self, campaign_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[LinkResponse]:
        """List links with optional campaign filter."""
        query = self.db.query(Link)
        if campaign_id:
            query = query.filter(Link.campaign_id == campaign_id)
        
        links = query.offset(skip).limit(limit).all()
        return [LinkResponse.model_validate(link) for link in links]
    
    def record_click(
        self,
        link_id: int,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        geo_country: Optional[str] = None
    ) -> int:
        """
        Record a click event for a link.
        
        Args:
            link_id: Link ID
            referrer: HTTP referrer
            user_agent: HTTP user agent
            ip_address: IP address
            geo_country: Country code
        
        Returns:
            Click event ID
        """
        # Detect bot
        is_bot = BotDetector.is_bot(user_agent, referrer)
        
        # Hash IP for privacy
        ip_hash = None
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
        
        # Detect device type
        device_type = self._detect_device_type(user_agent)
        
        # Create click event
        click = ClickEvent(
            link_id=link_id,
            referrer=referrer,
            user_agent=user_agent,
            ip_hash=ip_hash,
            is_bot=is_bot,
            device_type=device_type,
            geo_country=geo_country
        )
        
        self.db.add(click)
        self.db.commit()
        self.db.refresh(click)
        
        return click.id
    
    def get_link_stats(self, link_id: int, days: int = 30) -> LinkStatsResponse:
        """
        Get statistics for a link.
        
        Args:
            link_id: Link ID
            days: Number of days to look back
        
        Returns:
            LinkStatsResponse with detailed statistics
        """
        link = self.db.query(Link).filter(Link.id == link_id).first()
        if not link:
            raise ValueError(f"Link {link_id} not found")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all clicks
        clicks = self.db.query(ClickEvent).filter(
            and_(
                ClickEvent.link_id == link_id,
                ClickEvent.timestamp >= cutoff_date
            )
        ).all()
        
        # Calculate statistics
        total_clicks = len(clicks)
        total_bots = sum(1 for c in clicks if c.is_bot)
        
        # Top referrers
        referrer_counts = {}
        for click in clicks:
            if click.referrer:
                referrer_counts[click.referrer] = referrer_counts.get(click.referrer, 0) + 1
        
        top_referrers = [
            {"referrer": ref, "count": count}
            for ref, count in sorted(referrer_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Device breakdown
        device_breakdown = {}
        for click in clicks:
            device = click.device_type or "unknown"
            device_breakdown[device] = device_breakdown.get(device, 0) + 1
        
        # Country breakdown
        country_breakdown = {}
        for click in clicks:
            country = click.geo_country or "unknown"
            country_breakdown[country] = country_breakdown.get(country, 0) + 1
        
        # Clicks by day
        clicks_by_day = {}
        for click in clicks:
            day = click.timestamp.date().isoformat()
            clicks_by_day[day] = clicks_by_day.get(day, 0) + 1
        
        clicks_by_day_list = [
            {"date": date, "clicks": count}
            for date, count in sorted(clicks_by_day.items())
        ]
        
        return LinkStatsResponse(
            link_id=link_id,
            total_clicks=total_clicks,
            total_bots=total_bots,
            unique_referrers=top_referrers,
            device_breakdown=device_breakdown,
            country_breakdown=country_breakdown,
            clicks_by_day=clicks_by_day_list
        )
    
    def _generate_short_slug(self, length: int = 8) -> str:
        """Generate a unique short slug."""
        while True:
            slug = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))
            # Check uniqueness
            existing = self.db.query(Link).filter(Link.short_slug == slug).first()
            if not existing:
                return slug
    
    def _detect_device_type(self, user_agent: Optional[str]) -> Optional[str]:
        """Detect device type from user agent."""
        if not user_agent:
            return None
        
        ua_lower = user_agent.lower()
        
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            return 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            return 'tablet'
        elif 'windows' in ua_lower or 'macintosh' in ua_lower or 'linux' in ua_lower:
            return 'desktop'
        
        return None
