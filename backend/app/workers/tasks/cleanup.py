import datetime
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models.visit import Visit, VisitStatus
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.delete_s3_key")
def delete_s3_key(s3_key: str):
    """Deletes an S3 object on background to clean up orphans."""
    import boto3
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )
    try:
        s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    except ClientError as exc:
        # Log and ignore — orphan cleanup is best-effort
        pass


@celery_app.task(name="app.workers.tasks.cleanup_orphans")
def cleanup_orphans():
    """
    Finds pending visits older than 30 minutes, fails them and schedules S3 deletion.
    """
    db: Session = SessionLocal()
    try:
        threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        orphans = db.query(Visit).filter(
            Visit.status == VisitStatus.pending,
            Visit.created_at < threshold
        ).all()

        for visit in orphans:
            visit.status = VisitStatus.failed
            if visit.audio_s3_key:
                delete_s3_key.delay(visit.audio_s3_key)

        db.commit()
    finally:
        db.close()
