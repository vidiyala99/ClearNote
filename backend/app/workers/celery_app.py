from celery import Celery
from app.config import settings

celery_app = Celery(
    "clearnote",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Discover tasks
celery_app.autodiscover_tasks(["app.workers"])

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "cleanup-orphans-15min": {
        "task": "app.workers.tasks.cleanup_orphans",
        "schedule": crontab(minute="*/15"),
    },
}

