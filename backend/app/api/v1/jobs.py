import uuid
import boto3
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError

from app.config import settings
from app.db.models.job import Job, JobStatus
from app.db.models.visit import Visit, VisitStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.job import TranscribeRequest, TranscribeResponse

router = APIRouter()


def _get_s3_client():
    """Build S3 client."""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


@router.post("/jobs/transcribe", response_model=TranscribeResponse)
def transcribe_audio(request: Request, body: TranscribeRequest, db: Session = Depends(get_db)):
    """
    1. Creates/updates Job row with status='queued'.
    2. Generates S3 presigned POST.
    """
    clerk_id = getattr(request.state, "clerk_user_id", None)
    if not clerk_id:
        raise HTTPException(
            status_code=401, detail={"error": {"code": "UNAUTHORIZED"}}
        )

    user = db.query(User).filter(User.clerk_user_id == clerk_id).first()
    if not user:
         raise HTTPException(
             status_code=401, detail={"error": {"code": "UNAUTHORIZED"}}
         )

    visit = db.query(Visit).filter(Visit.id == body.visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # verify user owns the visit
    if visit.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    s3_key = f"visits/{body.visit_id}/audio"

    # 1. Row management
    job = db.query(Job).filter(Job.visit_id == body.visit_id).first()
    if not job:
        job = Job(
            id=uuid.uuid4(),
            visit_id=body.visit_id,
            s3_key=s3_key,
            status=JobStatus.queued
        )
        db.add(job)
    else:
        job.s3_key = s3_key
        job.status = JobStatus.queued

    db.commit()
    db.refresh(job)

    # 2. AWS S3 Presigned POST
    s3_client = _get_s3_client()
    try:
        presigned = s3_client.generate_presigned_post(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
            Fields={}, # empty, conditions govern it
            Conditions=[
                ["starts-with", "$Content-Type", "audio/"],
                ["content-length-range", 1, 524288000],
            ],
            ExpiresIn=3600,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"S3 Error: {exc}")

    return {
        "job_id": job.id,
        "upload_url": presigned["url"],
        "upload_fields": presigned["fields"]
    }


@router.post("/jobs/{job_id}/confirm", response_model=dict)
def confirm_upload(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Validates uploaded content via presigned post then triggers Celery pipeline.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    visit = db.query(Visit).filter(Visit.id == job.visit_id).first()
    if not visit:
         raise HTTPException(status_code=404, detail="Visit not found")

    # 1. Key mismatch
    if visit.audio_s3_key and visit.audio_s3_key != job.s3_key:
        raise HTTPException(
            status_code=409, detail={"error": {"code": "JOB_ALREADY_CONFIRMED"}}
        )

    # 2. Idempotency Check
    if visit.status in [VisitStatus.processing, VisitStatus.ready]:
         return {"status": "queued"}

    # 3. Magic Bytes Check
    s3_client = _get_s3_client()
    try:
         # GET first 12 bytes from S3
         response = s3_client.get_object(
             Bucket=settings.s3_bucket_name,
             Key=job.s3_key,
             Range="bytes=0-11"
         )
         magic_bytes = response['Body'].read()
    except ClientError as exc:
         if exc.response['Error']['Code'] == 'NoSuchKey':
              raise HTTPException(status_code=404, detail="S3 file not uploaded yet")
         raise HTTPException(status_code=503, detail="S3 service unreachable")
    except Exception:
         raise HTTPException(status_code=503, detail="S3 service unreachable")

    # Map magic signatures for WebM, MP3, M4A, WAV, etc.
    # Just checking first 4 as placeholder or standard
    is_valid_audio = False
    signature_hex = magic_bytes.hex().upper()

    # E.g. RIFF (WAV), ftyp (M4A), 1A45DFA3 (WebM cluster), ID3 (MP3)
    if signature_hex.startswith("1A45DFA3"): # WebM
        is_valid_audio = True
    elif signature_hex.startswith("52494646"): # RIFF / WAV
        is_valid_audio = True
    elif signature_hex.startswith("494433") or signature_hex.startswith("FFF"): # ID3
        is_valid_audio = True
    elif "46545950" in signature_hex:  # ftyp - mp4/m4a
        is_valid_audio = True

    if not is_valid_audio:
         raise HTTPException(status_code=422, detail="Invalid audio format")

    # 4. Success -> trigger chain
    from celery import chain
    from app.workers.tasks.transcribe import transcribe_audio
    from app.workers.tasks.finalize import finalize_visit

    visit.audio_s3_key = job.s3_key
    visit.status = VisitStatus.pending # to trigger Celery process, or processing?
    # Spec says: On success: update visits.audio_s3_key=s3_key, enqueue Celery, update jobs.celery_task_id
    
    # Trigger Celery chain async
    # chain(transcribe_audio.s(visit_id), finalize_visit.s())
    res = chain(transcribe_audio.s(visit.id), finalize_visit.s()).apply_async()

    job.celery_task_id = res.id
    db.commit()

    return {"status": "queued"}
