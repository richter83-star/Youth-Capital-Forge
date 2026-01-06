"""
FastAPI main application.
"""

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db, init_db
from app.schemas import (
    HealthCheckResponse, CampaignCreate, CampaignResponse, CampaignUpdate,
    LinkCreate, LinkResponse, LinkStatsResponse, ActionCreate, ActionResponse,
    ActionListResponse, ApprovalCreate, ApprovalResponse, TrendDigestResponse
)
from app.models import ActionTypeEnum, ActionStatusEnum
from app.services import LinkService, TrendEngine, ActionService, SettingsService

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Marketing Agent V2",
    description="Production-ready marketing automation platform",
    version="2.0.0"
)


# Health check endpoint
@app.get("/healthz", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="2.0.0"
    )


# Campaign endpoints
@app.post("/api/campaigns", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign."""
    from app.models import Campaign
    
    db_campaign = Campaign(**campaign.model_dump())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return CampaignResponse.model_validate(db_campaign)


@app.get("/api/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List campaigns."""
    from app.models import Campaign
    
    campaigns = db.query(Campaign).offset(skip).limit(limit).all()
    return [CampaignResponse.model_validate(c) for c in campaigns]


@app.get("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get a campaign by ID."""
    from app.models import Campaign
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignResponse.model_validate(campaign)


@app.put("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: int, campaign: CampaignUpdate, db: Session = Depends(get_db)):
    """Update a campaign."""
    from app.models import Campaign
    
    db_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    update_data = campaign.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_campaign, field, value)
    
    db.commit()
    db.refresh(db_campaign)
    return CampaignResponse.model_validate(db_campaign)


# Link endpoints
@app.post("/api/links", response_model=LinkResponse)
async def create_link(link: LinkCreate, db: Session = Depends(get_db)):
    """Create a new tracked link."""
    service = LinkService(db)
    return service.create_link(
        campaign_id=link.campaign_id,
        channel=link.channel,
        long_url=link.long_url,
        utm_params=link.utm_json
    )


@app.get("/api/links", response_model=list[LinkResponse])
async def list_links(
    campaign_id: int = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List tracked links."""
    service = LinkService(db)
    return service.list_links(campaign_id=campaign_id, skip=skip, limit=limit)


@app.get("/api/links/{link_id}", response_model=LinkResponse)
async def get_link(link_id: int, db: Session = Depends(get_db)):
    """Get a link by ID."""
    service = LinkService(db)
    link = service.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@app.get("/api/links/{link_id}/stats", response_model=LinkStatsResponse)
async def get_link_stats(link_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get statistics for a link."""
    service = LinkService(db)
    try:
        return service.get_link_stats(link_id, days=days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Short link redirect
@app.get("/r/{slug}")
async def redirect_short_link(slug: str, db: Session = Depends(get_db)):
    """Redirect short link and record click."""
    service = LinkService(db)
    link = service.get_link_by_slug(slug)
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Record click (in production, would extract from request headers)
    service.record_click(
        link_id=link.id,
        referrer=None,  # Would come from request.headers.get('referer')
        user_agent=None,  # Would come from request.headers.get('user-agent')
        ip_address=None  # Would come from request.client.host
    )
    
    return RedirectResponse(url=link.long_url, status_code=301)


# Trend endpoints
@app.post("/api/trends/ingest")
async def ingest_trends(db: Session = Depends(get_db)):
    """Manually trigger trend ingestion."""
    from app.workers.tasks import ingest_trends as ingest_task
    
    # Queue the task
    task = ingest_task.delay()
    return {"status": "queued", "task_id": task.id}


@app.get("/api/trends/digest", response_model=TrendDigestResponse)
async def get_trend_digest(hours: int = 24, limit: int = 10, db: Session = Depends(get_db)):
    """Get trend digest."""
    engine = TrendEngine(db)
    digest = engine.get_trend_digest(limit=limit, hours=hours)
    
    return TrendDigestResponse(
        trends=digest['trends'],
        last_ingest_time=digest['last_ingest_time'],
        total_items=digest['total_items']
    )


# Action endpoints
@app.post("/api/actions", response_model=ActionResponse)
async def create_action(action: ActionCreate, db: Session = Depends(get_db)):
    """Create a new action."""
    service = ActionService(db)
    return service.create_action(
        action_type=action.type,
        payload=action.payload,
        dry_run=action.dry_run,
        scheduled_for=action.scheduled_for
    )


@app.get("/api/actions", response_model=list[ActionListResponse])
async def list_actions(
    status: ActionStatusEnum = Query(None),
    action_type: ActionTypeEnum = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List actions."""
    service = ActionService(db)
    actions = service.list_actions(status=status, action_type=action_type, skip=skip, limit=limit)
    return [ActionListResponse.model_validate(a) for a in actions]


@app.get("/api/actions/{action_id}", response_model=ActionResponse)
async def get_action(action_id: int, db: Session = Depends(get_db)):
    """Get an action by ID."""
    service = ActionService(db)
    action = service.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@app.post("/api/actions/{action_id}/submit", response_model=ActionResponse)
async def submit_action(action_id: int, db: Session = Depends(get_db)):
    """Submit an action for approval."""
    service = ActionService(db)
    try:
        return service.submit_action_for_approval(action_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/actions/{action_id}/approve", response_model=ApprovalResponse)
async def approve_action(action_id: int, approval: ApprovalCreate, db: Session = Depends(get_db)):
    """Approve an action."""
    service = ActionService(db)
    try:
        return service.approve_action(action_id, approved_by=1, note=approval.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/actions/{action_id}/deny", response_model=ApprovalResponse)
async def deny_action(action_id: int, approval: ApprovalCreate, db: Session = Depends(get_db)):
    """Deny an action."""
    service = ActionService(db)
    try:
        return service.deny_action(action_id, approved_by=1, note=approval.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Admin UI
@app.get("/admin")
async def admin_home():
    """Admin dashboard home."""
    return FileResponse("app/templates/admin/index.html")


@app.get("/admin/approvals")
async def admin_approvals():
    """Admin approvals page."""
    return FileResponse("app/templates/admin/approvals.html")


@app.get("/admin/trends")
async def admin_trends():
    """Admin trends page."""
    return FileResponse("app/templates/admin/trends.html")


@app.get("/admin/links")
async def admin_links():
    """Admin links page."""
    return FileResponse("app/templates/admin/links.html")


@app.get("/admin/campaigns")
async def admin_campaigns():
    """Admin campaigns page."""
    return FileResponse("app/templates/admin/campaigns.html")


# Mount static files
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except:
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
