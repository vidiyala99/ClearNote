import uuid
import datetime
from sqlalchemy.orm import Session

from app.db.models.job import Job, JobStatus
from app.db.models.user import User
from app.db.models.visit import Visit, VisitStatus
from app.db.models.transcript import Transcript

from app.workers.tasks.transcribe import transcribe_audio
from app.workers.tasks.finalize import finalize_visit
from app.workers.tasks.cleanup import cleanup_orphans


def test_transcribe_audio_updates_status(db: Session):
    """Test transcribe_audio sets status to processing and upserts transcript."""
    # Setup
    user = User(id=uuid.uuid4(), email="w@e.com", clerk_user_id="cw_1")
    db.add(user)
    db.commit()

    visit = Visit(
        id=uuid.uuid4(), user_id=user.id, title="Test",
        visit_date=datetime.date.today(), consent_at=datetime.datetime.utcnow(),
        status=VisitStatus.pending
    )
    db.add(visit)
    db.commit()

    # Call task synchronously
    result_id = transcribe_audio(str(visit.id))
    assert result_id == str(visit.id)

    # Verify mutations
    db.refresh(visit)
    assert visit.status == VisitStatus.processing

    transcript = db.query(Transcript).filter(Transcript.visit_id == visit.id).first()
    assert transcript is not None
    assert transcript.raw_text == "This is a mock transcript of the visit."


def test_finalize_visit_updates_status(db: Session):
    """Test finalize_visit sets statuses to ready and done."""
    # Setup
    user = User(id=uuid.uuid4(), email="w2@e.com", clerk_user_id="cw_2")
    db.add(user)
    db.commit()

    visit = Visit(
        id=uuid.uuid4(), user_id=user.id, title="Test",
        visit_date=datetime.date.today(), consent_at=datetime.datetime.utcnow(),
        status=VisitStatus.processing
    )
    db.add(visit)

    job = Job(id=uuid.uuid4(), visit_id=visit.id, s3_key="test", status=JobStatus.processing)
    db.add(job)
    db.commit()

    # Call task synchronously
    finalize_visit(str(visit.id))

    # Verify mutations
    db.refresh(visit)
    db.refresh(job)
    assert visit.status == VisitStatus.ready
    assert job.status == JobStatus.done


def test_cleanup_orphans_fails_backdated_visits(db: Session):
    """Test cleanup_orphans marks old pending visits as failed."""
    # Setup
    user = User(id=uuid.uuid4(), email="w3@e.com", clerk_user_id="cw_3")
    db.add(user)
    db.commit()

    # Backdated visit (31 mins ago)
    old_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=31)
    old_visit = Visit(
        id=uuid.uuid4(), user_id=user.id, title="Old Visit",
        visit_date=datetime.date.today(), consent_at=datetime.datetime.utcnow(),
        status=VisitStatus.pending, created_at=old_time
    )
    db.add(old_visit)

    # Fresh visit (5 mins ago)
    new_visit = Visit(
        id=uuid.uuid4(), user_id=user.id, title="New Visit",
        visit_date=datetime.date.today(), consent_at=datetime.datetime.utcnow(),
        status=VisitStatus.pending, created_at=datetime.datetime.utcnow()
    )
    db.add(new_visit)
    db.commit()

    # Call task synchronously
    cleanup_orphans()

    # Verify mutations
    db.refresh(old_visit)
    db.refresh(new_visit)

    assert old_visit.status == VisitStatus.failed
    assert new_visit.status == VisitStatus.pending # stays pending
