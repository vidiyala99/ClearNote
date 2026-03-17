import uuid
import os
import tempfile
import boto3
from sqlalchemy.dialects.postgresql import insert

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.visit import Visit, VisitStatus
from app.db.models.transcript import Transcript
from app.services.ai import AIService
from app.config import settings

@celery_app.task(name="app.workers.tasks.transcribe")
def transcribe_audio(visit_id: str):
    """
    1. Fetch visit and download audio from S3
    2. Transcribe via AIService (OpenAI Whisper)
    3. Save transcript text to DB
    """
    if isinstance(visit_id, str):
        visit_uuid = uuid.UUID(visit_id)
    else:
        visit_uuid = visit_id

    db = SessionLocal()
    tmp_path = None
    try:
        visit = db.query(Visit).filter(Visit.id == visit_uuid).first()
        if not visit or not visit.audio_s3_key:
             return str(visit_uuid)

        visit.status = VisitStatus.processing
        db.commit()

        # 1. Download file from S3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        
        # Create full temp file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp_path = tmp.name
            s3.download_file(settings.s3_bucket_name, visit.audio_s3_key, tmp_path)

        # 2. Transcribe Audio
        ai_service = AIService()
        transcript_text = ai_service.transcribe_audio(tmp_path)

        # 3. Upsert transcript into database
        stmt = insert(Transcript).values(
            id=uuid.uuid4(),
            visit_id=visit_uuid,
            raw_text=transcript_text,
            chunks=[], # Optional: populate later if requiring sub-segment timing
            language_detected="en"
        ).on_conflict_do_update(
            index_elements=[Transcript.visit_id],
            set_={
                "raw_text": transcript_text
            }
        )
        db.execute(stmt)
        db.commit()

    except Exception as e:
        # If any AI step triggers a fail, set status to failed
        if 'visit' in locals() and visit:
            visit.status = VisitStatus.failed
            db.commit()
        raise e
    finally:
        # Cleanup file layout
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        db.close()

    return str(visit_uuid)
