"""
Trend engine service for RSS ingestion and trend scoring.
"""

import feedparser
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models import TrendItem, TrendScore


class TrendEngine:
    """Engine for ingesting trends and computing scores."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def ingest_feeds(self, feeds: List[Dict[str, str]]) -> int:
        """
        Ingest RSS feeds and store items.
        
        Args:
            feeds: List of feed dicts with 'name' and 'url' keys
        
        Returns:
            Number of items ingested
        """
        count = 0
        
        for feed_config in feeds:
            source = feed_config.get('name', feed_config.get('url'))
            url = feed_config.get('url')
            
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:20]:  # Limit to 20 items per feed
                    # Check if item already exists
                    existing = self.db.query(TrendItem).filter(
                        and_(
                            TrendItem.source == source,
                            TrendItem.title == entry.get('title', '')
                        )
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Parse published date
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    
                    # Create trend item
                    item = TrendItem(
                        source=source,
                        title=entry.get('title', ''),
                        url=entry.get('link', ''),
                        published_at=published_at,
                        summary=entry.get('summary', ''),
                        raw_json={
                            'title': entry.get('title', ''),
                            'link': entry.get('link', ''),
                            'summary': entry.get('summary', ''),
                            'author': entry.get('author', '')
                        }
                    )
                    
                    self.db.add(item)
                    count += 1
                
                self.db.commit()
            
            except Exception as e:
                print(f"Error ingesting feed {url}: {e}")
                continue
        
        return count
    
    def compute_trend_scores(self, window_hours: int = 24) -> List[TrendScore]:
        """
        Compute trend scores based on velocity.
        
        Velocity = mentions in last 24h / mentions in previous 24-72h
        
        Args:
            window_hours: Hours to look back for current window
        
        Returns:
            List of TrendScore objects
        """
        now = datetime.utcnow()
        current_window_start = now - timedelta(hours=window_hours)
        previous_window_start = now - timedelta(hours=window_hours * 3)
        previous_window_end = current_window_start
        
        # Get items from current window
        current_items = self.db.query(TrendItem).filter(
            TrendItem.published_at >= current_window_start
        ).all()
        
        # Extract keywords/topics
        topics = Counter()
        
        for item in current_items:
            keywords = self._extract_keywords(item.title)
            for keyword in keywords:
                topics[keyword] += 1
        
        # Compute velocity for top topics
        scores = []
        
        for topic, current_count in topics.most_common(20):
            # Count in previous window
            previous_count = self.db.query(func.count(TrendItem.id)).filter(
                and_(
                    TrendItem.published_at >= previous_window_start,
                    TrendItem.published_at < previous_window_end,
                    TrendItem.title.ilike(f"%{topic}%")
                )
            ).scalar() or 0
            
            # Calculate velocity score
            if previous_count > 0:
                velocity = current_count / max(previous_count, 1)
            else:
                velocity = current_count * 2  # Boost new topics
            
            score = int(velocity * 100)
            
            # Generate explanation
            explanation = self._generate_explanation(topic, current_count, velocity)
            
            # Check if score already exists for this window
            existing = self.db.query(TrendScore).filter(
                and_(
                    TrendScore.topic == topic,
                    TrendScore.window_start == current_window_start,
                    TrendScore.window_end == now
                )
            ).first()
            
            if not existing:
                trend_score = TrendScore(
                    topic=topic,
                    window_start=current_window_start,
                    window_end=now,
                    score=score,
                    explanation=explanation
                )
                self.db.add(trend_score)
                scores.append(trend_score)
        
        self.db.commit()
        return scores
    
    def get_trend_digest(self, limit: int = 10, hours: int = 24) -> Dict[str, Any]:
        """
        Get a digest of top trends.
        
        Args:
            limit: Number of top trends to return
            hours: Hours to look back
        
        Returns:
            Dictionary with trends and metadata
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get top trend scores
        trend_scores = self.db.query(TrendScore).filter(
            TrendScore.window_end >= cutoff_time
        ).order_by(TrendScore.score.desc()).limit(limit).all()
        
        # Get last ingest time
        last_item = self.db.query(TrendItem).order_by(TrendItem.created_at.desc()).first()
        last_ingest_time = last_item.created_at if last_item else None
        
        # Count total items
        total_items = self.db.query(func.count(TrendItem.id)).filter(
            TrendItem.created_at >= cutoff_time
        ).scalar() or 0
        
        return {
            'trends': trend_scores,
            'last_ingest_time': last_ingest_time,
            'total_items': total_items
        }
    
    def _extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract keywords from text using simple tokenization.
        
        Args:
            text: Text to extract keywords from
            min_length: Minimum keyword length
        
        Returns:
            List of keywords
        """
        # Convert to lowercase and split
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        keywords = [
            word for word in words
            if len(word) >= min_length and word not in stop_words
        ]
        
        return keywords
    
    def _generate_explanation(self, topic: str, count: int, velocity: float) -> str:
        """Generate a human-readable explanation for a trend."""
        if velocity > 3:
            trend_type = "rapidly trending"
        elif velocity > 1.5:
            trend_type = "trending"
        else:
            trend_type = "emerging"
        
        return f"'{topic}' is {trend_type} with {count} recent mentions (velocity: {velocity:.1f}x)"
