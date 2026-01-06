"""
Celery application and worker configuration.
"""

from celery import Celery
from celery.schedules import crontab
import os

# Create Celery app
celery_app = Celery(
    'marketing_agent',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    'ingest-trends-daily': {
        'task': 'app.workers.tasks.ingest_trends',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'compute-trend-scores-daily': {
        'task': 'app.workers.tasks.compute_trend_scores',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'execute-pending-actions': {
        'task': 'app.workers.tasks.execute_pending_actions',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
