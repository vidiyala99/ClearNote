import uuid
import time
from sqlalchemy.dialects.postgresql import insert

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.visit import Visit, VisitStatus
from app.db.models.transcript import Transcript


@celery_app.task(name="app.workers.tasks.transcribe")
def transcribe_audio(visit_id: str):
    """
    1. Set visit.status = 'processing'
    2. Sleep 3 seconds (mock processing time)
    3. Idempotent upsert transcript
    """
    # Convert back to UUID if passed as string back from chain
    if isinstance(visit_id, str):
        visit_uuid = uuid.UUID(visit_id)
    else:
        visit_uuid = visit_id

    db = SessionLocal()
    try:
        visit = db.query(Visit).filter(Visit.id == visit_uuid).first()
        if not visit:
             return str(visit_uuid)

        visit.status = VisitStatus.processing
        db.commit()

        # Mock time
        time.sleep(3)

        # Upsert transcript
        stmt = insert(Transcript).values(
            id=uuid.uuid4(),
            visit_id=visit_uuid,
            raw_text="This is a mock transcript of the visit.",
            chunks=[{"start": 0, "end": 3, "text": "This is a mock transcript"}],
            language_detected="en"
        ).on_conflict_do_update(
            index_elements=[Transcript.visit_id],
            set_={
                "raw_text": "This is a mock transcript of the visit.",
                "chunks": [{"start": 0, "end": 3, "text": "This is a mock transcript"}]
            }
        )
        db.execute(stmt)
        db.commit()
    finally:
        db.close()

    return str(visit_uuid)

