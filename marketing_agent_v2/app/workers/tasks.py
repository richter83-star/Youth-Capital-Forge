"""
Celery tasks for background job execution.
"""

import logging
from datetime import datetime
from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.services import ActionService, TrendEngine, SettingsService
from app.models import ActionStatusEnum
from app.workers.connectors import get_connector

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def ingest_trends(self):
    """Ingest trends from configured RSS feeds."""
    db = SessionLocal()
    try:
        # Load feeds configuration
        feeds = [
            {'name': 'HackerNews', 'url': 'https://news.ycombinator.com/rss'},
            {'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/'},
            {'name': 'ProductHunt', 'url': 'https://www.producthunt.com/feed'},
        ]
        
        engine = TrendEngine(db)
        count = engine.ingest_feeds(feeds)
        
        logger.info(f"Ingested {count} trend items")
        return {'status': 'success', 'items_ingested': count}
    
    except Exception as exc:
        logger.error(f"Error ingesting trends: {exc}")
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def compute_trend_scores(self):
    """Compute trend scores from ingested items."""
    db = SessionLocal()
    try:
        engine = TrendEngine(db)
        scores = engine.compute_trend_scores()
        
        logger.info(f"Computed {len(scores)} trend scores")
        return {'status': 'success', 'scores_computed': len(scores)}
    
    except Exception as exc:
        logger.error(f"Error computing trend scores: {exc}")
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def execute_pending_actions(self):
    """Execute all pending approved actions."""
    db = SessionLocal()
    try:
        action_service = ActionService(db)
        settings_service = SettingsService(db)
        
        # Check kill switch
        if settings_service.is_kill_switch_enabled():
            logger.warning("Kill switch is enabled, skipping action execution")
            return {'status': 'skipped', 'reason': 'kill_switch_enabled'}
        
        # Get executable actions
        actions = action_service.get_executable_actions()
        logger.info(f"Found {len(actions)} executable actions")
        
        results = []
        for action in actions:
            try:
                result = execute_action.delay(action.id)
                results.append({'action_id': action.id, 'task_id': result.id})
            except Exception as e:
                logger.error(f"Error queuing action {action.id}: {e}")
        
        return {'status': 'success', 'actions_queued': len(results)}
    
    except Exception as exc:
        logger.error(f"Error executing pending actions: {exc}")
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def execute_action(self, action_id: int):
    """Execute a single action."""
    db = SessionLocal()
    try:
        action_service = ActionService(db)
        settings_service = SettingsService(db)
        
        # Check kill switch
        if settings_service.is_kill_switch_enabled():
            logger.warning(f"Kill switch enabled, canceling action {action_id}")
            action_service.mark_failed(action_id, "Kill switch enabled")
            return {'status': 'failed', 'reason': 'kill_switch_enabled'}
        
        # Get action
        action = action_service.get_action(action_id)
        if not action:
            logger.error(f"Action {action_id} not found")
            return {'status': 'failed', 'reason': 'action_not_found'}
        
        # Check approval
        approvals = db.query(db.query(type(action)).approvals).filter(
            db.query(type(action)).approvals.status == 'approved'
        ).all()
        
        if not approvals:
            logger.warning(f"Action {action_id} has no approval, canceling")
            action_service.mark_failed(action_id, "No approval found")
            return {'status': 'failed', 'reason': 'no_approval'}
        
        # Mark as executing
        action_service.mark_executing(action_id)
        
        # Get connector
        connector = get_connector(action.type)
        
        # Execute
        logger.info(f"Executing action {action_id} of type {action.type}")
        
        try:
            result = connector.execute(
                payload=action.payload,
                dry_run=action.dry_run
            )
            
            # Mark as succeeded
            action_service.mark_succeeded(
                action_id,
                provider_message_id=result.get('provider_message_id')
            )
            
            logger.info(f"Action {action_id} executed successfully")
            return {'status': 'success', 'result': result}
        
        except Exception as e:
            logger.error(f"Error executing action {action_id}: {e}")
            action_service.mark_failed(action_id, str(e))
            raise
    
    except Exception as exc:
        logger.error(f"Error in execute_action task: {exc}")
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        db.close()
