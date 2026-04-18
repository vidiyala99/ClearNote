import uuid

from sqlalchemy.dialects.postgresql import insert

from app.db.models.summary import Summary
from app.db.models.transcript import Transcript
from app.db.session import SessionLocal
from app.services.ai import AIService
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.summarize")
def summarize_visit(visit_id: str):
    """
    1. Read transcript text from previous task output.
    2. Prompt LLM to generate SOAP Notes.
    3. Save structures back to summary tables.
    """
    if isinstance(visit_id, str):
        visit_uuid = uuid.UUID(visit_id)
    else:
        visit_uuid = visit_id

    db = SessionLocal()
    try:
        # 1. Fetch transcript
        transcript = db.query(Transcript).filter(Transcript.visit_id == visit_uuid).first()
        if not transcript:
            raise ValueError(f"No transcript found for visit {visit_id} to summarize.")

        # 2. Trigger AI Summarization
        ai_service = AIService()
        summary_data = ai_service.summarize_notes(transcript.raw_text)

        # 3. Upsert summary into database
        stmt = insert(Summary).values(
            id=uuid.uuid4(),
            visit_id=visit_uuid,
            overview=summary_data.get("overview"),
            medications=summary_data.get("medications", []),
            diagnoses=summary_data.get("diagnoses", []),
            action_items=summary_data.get("action_items", []),
            urgency_tag=summary_data.get("urgency_tag", "normal")
        ).on_conflict_do_update(
            index_elements=[Summary.visit_id],
            set_={
                "overview": summary_data.get("overview"),
                "medications": summary_data.get("medications", []),
                "diagnoses": summary_data.get("diagnoses", []),
                "action_items": summary_data.get("action_items", []),
                "urgency_tag": summary_data.get("urgency_tag", "normal")
            }
        )
        db.execute(stmt)
        db.commit()

    finally:
         db.close()

    return str(visit_uuid)
