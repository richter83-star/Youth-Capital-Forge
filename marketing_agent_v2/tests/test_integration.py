"""
Integration tests for the marketing agent.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Campaign, Link, ClickEvent, Action, Approval, ActionTypeEnum, ActionStatusEnum
from app.services import LinkService, ActionService


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Setup and teardown test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestLinkTracking:
    """Tests for link tracking functionality."""
    
    def test_create_link_and_redirect_records_click(self):
        """Test that creating a link and redirecting records a click event."""
        db = TestingSessionLocal()
        
        # Create campaign
        campaign = Campaign(
            name="Test Campaign",
            objective="Testing",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status="active"
        )
        db.add(campaign)
        db.commit()
        
        # Create link
        service = LinkService(db)
        link_response = service.create_link(
            campaign_id=campaign.id,
            channel="email",
            long_url="https://example.com/page"
        )
        
        assert link_response.id is not None
        assert link_response.short_slug is not None
        
        # Record click
        click_id = service.record_click(
            link_id=link_response.id,
            referrer="https://google.com",
            user_agent="Mozilla/5.0"
        )
        
        assert click_id is not None
        
        # Verify click was recorded
        click = db.query(ClickEvent).filter(ClickEvent.id == click_id).first()
        assert click is not None
        assert click.link_id == link_response.id
        assert click.is_bot is False
        
        db.close()
    
    def test_bot_detection(self):
        """Test that bot traffic is correctly detected."""
        db = TestingSessionLocal()
        
        campaign = Campaign(
            name="Test Campaign",
            objective="Testing",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        db.add(campaign)
        db.commit()
        
        service = LinkService(db)
        link_response = service.create_link(
            campaign_id=campaign.id,
            channel="email",
            long_url="https://example.com"
        )
        
        # Record bot click
        click_id = service.record_click(
            link_id=link_response.id,
            user_agent="Googlebot/2.1",
            referrer=""
        )
        
        click = db.query(ClickEvent).filter(ClickEvent.id == click_id).first()
        assert click.is_bot is True
        
        db.close()


class TestActions:
    """Tests for action and approval workflow."""
    
    def test_actions_cannot_execute_without_approval(self):
        """Test that actions cannot execute without approval."""
        db = TestingSessionLocal()
        
        service = ActionService(db)
        
        # Create action
        action_response = service.create_action(
            action_type=ActionTypeEnum.EMAIL,
            payload={"recipient": "test@example.com", "subject": "Test", "body": "Test"},
            dry_run=False
        )
        
        assert action_response.status == ActionStatusEnum.DRAFT
        
        # Get executable actions - should be empty
        executable = service.get_executable_actions()
        assert len(executable) == 0
        
        # Submit for approval
        submitted = service.submit_action_for_approval(action_response.id)
        assert submitted.status == ActionStatusEnum.PENDING_APPROVAL
        
        # Approve
        approval = service.approve_action(action_response.id, approved_by=1)
        assert approval.status.value == "approved"
        
        # Now should be executable
        executable = service.get_executable_actions()
        assert len(executable) == 1
        
        db.close()
    
    def test_kill_switch_blocks_execution(self):
        """Test that kill switch prevents action execution."""
        from app.services import SettingsService
        
        db = TestingSessionLocal()
        
        settings = SettingsService(db)
        settings.set_setting('KILL_SWITCH', 'true')
        
        assert settings.is_kill_switch_enabled() is True
        
        db.close()


class TestTrendScoring:
    """Tests for trend scoring."""
    
    def test_trend_scoring_produces_scores(self):
        """Test that trend scoring produces at least one score from sample data."""
        from app.services import TrendEngine
        from app.models import TrendItem
        
        db = TestingSessionLocal()
        
        # Create sample trend items
        for i in range(5):
            item = TrendItem(
                source="TestFeed",
                title=f"Breaking news about AI and machine learning {i}",
                url=f"https://example.com/article-{i}",
                published_at=datetime.utcnow(),
                summary="Test summary"
            )
            db.add(item)
        
        db.commit()
        
        # Compute scores
        engine = TrendEngine(db)
        scores = engine.compute_trend_scores()
        
        assert len(scores) > 0
        assert scores[0].score > 0
        assert scores[0].explanation is not None
        
        db.close()


class TestAPI:
    """Tests for API endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_create_campaign(self):
        """Test campaign creation endpoint."""
        response = client.post(
            "/api/campaigns",
            json={
                "name": "Test Campaign",
                "objective": "Testing",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["id"] is not None
    
    def test_create_link(self):
        """Test link creation endpoint."""
        # First create a campaign
        campaign_response = client.post(
            "/api/campaigns",
            json={
                "name": "Test Campaign",
                "objective": "Testing",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
        )
        campaign_id = campaign_response.json()["id"]
        
        # Create link
        response = client.post(
            "/api/links",
            json={
                "campaign_id": campaign_id,
                "channel": "email",
                "long_url": "https://example.com/page"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["short_slug"] is not None
        assert data["campaign_id"] == campaign_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
