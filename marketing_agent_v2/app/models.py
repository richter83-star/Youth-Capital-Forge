"""
SQLAlchemy models for the marketing agent database.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON,
    Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(50), default="viewer", nullable=False)  # admin, editor, viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    approvals = relationship("Approval", back_populates="approved_by_user")
    actions = relationship("Action", back_populates="created_by_user")


class Settings(Base):
    """System settings (key-value store)."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Campaign(Base):
    """Campaign model for organizing marketing efforts."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    objective = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assets = relationship("Asset", back_populates="campaign")
    links = relationship("Link", back_populates="campaign")


class Asset(Base):
    """Asset model for storing content (images, text, etc.)."""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    channel = Column(String(50), nullable=False)  # email, social, cms
    content = Column(Text, nullable=False)
    asset_metadata = Column(JSON, default={})  # Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="assets")


class Link(Base):
    """Link model for tracking URLs with UTM parameters."""
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    channel = Column(String(50), nullable=False)
    long_url = Column(Text, nullable=False)
    short_slug = Column(String(50), unique=True, index=True, nullable=False)
    utm_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="links")
    click_events = relationship("ClickEvent", back_populates="link")

    __table_args__ = (
        Index("idx_campaign_channel", "campaign_id", "channel"),
    )


class ClickEvent(Base):
    """Click event model for tracking link clicks."""
    __tablename__ = "click_events"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    referrer = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    user_agent = Column(Text, nullable=True)
    ip_hash = Column(String(64), nullable=True)
    is_bot = Column(Boolean, default=False)
    geo_country = Column(String(2), nullable=True)

    # Relationships
    link = relationship("Link", back_populates="click_events")

    __table_args__ = (
        Index("idx_link_timestamp", "link_id", "timestamp"),
    )


class TrendItem(Base):
    """Trend item model for storing RSS feed items."""
    __tablename__ = "trend_items"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    raw_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_source_published", "source", "published_at"),
    )


class TrendScore(Base):
    """Trend score model for storing computed trend scores."""
    __tablename__ = "trend_scores"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    score = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_topic_window", "topic", "window_start", "window_end"),
    )


class ActionStatusEnum(str, Enum):
    """Enum for action status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class ActionTypeEnum(str, Enum):
    """Enum for action type."""
    EMAIL = "email"
    SOCIAL = "social"
    CMS = "cms"


class Action(Base):
    """Action model for outbound marketing actions."""
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(ActionTypeEnum), nullable=False)
    status = Column(SQLEnum(ActionStatusEnum), default=ActionStatusEnum.DRAFT, nullable=False)
    payload = Column(JSON, nullable=False)
    dry_run = Column(Boolean, default=False)
    scheduled_for = Column(DateTime, nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    approvals = relationship("Approval", back_populates="action")
    audit_logs = relationship("AuditLog", back_populates="action")
    created_by_user = relationship("User", back_populates="actions")

    __table_args__ = (
        Index("idx_status_scheduled", "status", "scheduled_for"),
    )


class ApprovalStatusEnum(str, Enum):
    """Enum for approval status."""
    APPROVED = "approved"
    DENIED = "denied"


class Approval(Base):
    """Approval model for action approvals."""
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    status = Column(SQLEnum(ApprovalStatusEnum), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    action = relationship("Action", back_populates="approvals")
    approved_by_user = relationship("User", back_populates="approvals")


class AuditLogEventEnum(str, Enum):
    """Enum for audit log event types."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTED = "executed"
    FAILED = "failed"


class AuditLog(Base):
    """Audit log model for tracking system events."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    actor = Column(String(255), nullable=True)
    event_type = Column(SQLEnum(AuditLogEventEnum), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=True)
    details = Column(JSON, default={})

    # Relationships
    action = relationship("Action", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_timestamp_event", "timestamp", "event_type"),
        Index("idx_entity", "entity_type", "entity_id"),
    )
