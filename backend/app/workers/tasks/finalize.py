import uuid

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.visit import Visit, VisitStatus
from app.db.models.job import Job, JobStatus


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
    finally:
        db.close()

    return str(visit_uuid)

