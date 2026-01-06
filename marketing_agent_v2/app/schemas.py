"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models import ActionTypeEnum, ActionStatusEnum, ApprovalStatusEnum


# Campaign Schemas
class CampaignBase(BaseModel):
    name: str
    objective: Optional[str] = None
    start_date: datetime
    end_date: datetime
    status: str = "active"


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None


class CampaignResponse(CampaignBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Link Schemas
class LinkBase(BaseModel):
    campaign_id: int
    channel: str
    long_url: str


class LinkCreate(LinkBase):
    utm_json: Optional[Dict[str, str]] = None


class LinkResponse(LinkBase):
    id: int
    short_slug: str
    utm_json: Dict[str, str]
    created_at: datetime

    class Config:
        from_attributes = True


class LinkStatsResponse(BaseModel):
    link_id: int
    total_clicks: int
    total_bots: int
    unique_referrers: List[Dict[str, Any]]
    device_breakdown: Dict[str, int]
    country_breakdown: Dict[str, int]
    clicks_by_day: List[Dict[str, Any]]


# Click Event Schemas
class ClickEventCreate(BaseModel):
    referrer: Optional[str] = None
    device_type: Optional[str] = None
    user_agent: Optional[str] = None
    ip_hash: Optional[str] = None
    geo_country: Optional[str] = None


class ClickEventResponse(ClickEventCreate):
    id: int
    link_id: int
    timestamp: datetime
    is_bot: bool

    class Config:
        from_attributes = True


# Trend Schemas
class TrendItemResponse(BaseModel):
    id: int
    source: str
    title: str
    url: str
    published_at: Optional[datetime]
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TrendScoreResponse(BaseModel):
    id: int
    topic: str
    score: int
    explanation: Optional[str]
    window_start: datetime
    window_end: datetime

    class Config:
        from_attributes = True


class TrendDigestResponse(BaseModel):
    trends: List[TrendScoreResponse]
    last_ingest_time: Optional[datetime]
    total_items: int


# Action Schemas
class ActionPayload(BaseModel):
    """Base payload for actions."""
    pass


class EmailActionPayload(ActionPayload):
    recipient: str
    subject: str
    body: str
    html_body: Optional[str] = None


class SocialActionPayload(ActionPayload):
    platform: str  # twitter, facebook, linkedin, instagram
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None


class CMSActionPayload(ActionPayload):
    title: str
    content: str
    status: str = "draft"
    metadata: Optional[Dict[str, Any]] = None


class ActionCreate(BaseModel):
    type: ActionTypeEnum
    payload: Dict[str, Any]
    dry_run: bool = False
    scheduled_for: Optional[datetime] = None


class ActionResponse(BaseModel):
    id: int
    type: ActionTypeEnum
    status: ActionStatusEnum
    payload: Dict[str, Any]
    dry_run: bool
    scheduled_for: Optional[datetime]
    provider_message_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionListResponse(BaseModel):
    id: int
    type: ActionTypeEnum
    status: ActionStatusEnum
    scheduled_for: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Approval Schemas
class ApprovalCreate(BaseModel):
    status: ApprovalStatusEnum
    note: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    action_id: int
    status: ApprovalStatusEnum
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    actor: Optional[str]
    event_type: str
    entity_type: str
    entity_id: int
    details: Dict[str, Any]

    class Config:
        from_attributes = True


# Health Check
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "2.0.0"
