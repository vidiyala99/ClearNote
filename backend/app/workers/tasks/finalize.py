import uuid

from app.db.models.job import Job, JobStatus
from app.db.models.visit import Visit, VisitStatus
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.finalize")
def finalize_visit(visit_id: str):
    """
    1. Set visit.status = 'ready'
    2. Set job.status = 'done'
    """
    if isinstance(visit_id, str):
        visit_uuid = uuid.UUID(visit_id)
    else:
        visit_uuid = visit_id

    db = SessionLocal()
    try:
        visit = db.query(Visit).filter(Visit.id == visit_uuid).first()
        if not visit:
            return str(visit_uuid)

        visit.status = VisitStatus.ready

        job = db.query(Job).filter(Job.visit_id == visit_uuid).first()
        if job:
            job.status = JobStatus.done

        db.commit()

        # Publish notification via Redis for WebSockets
        import json

        import redis

        from app.config import settings
        try:
            r = redis.from_url(settings.redis_url)
            r.publish("notifications", json.dumps({
                "type": "visit_ready",
                "visit_id": str(visit_uuid),
                "user_id": str(visit.user_id),
                "status": "ready"
            }))
        except Exception:
            pass # Non-blocking layout fail safeties
    finally:
        db.close()

    return str(visit_uuid)

