import datetime
import uuid

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.job import Job, JobStatus
from app.db.models.user import User
from app.db.models.visit import Visit

TEST_JWT_SECRET = "test-secret-key-with-32-characters"
UTC = datetime.timezone.utc


def _create_mock_token(payload: dict) -> str:
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def test_transcribe_unauthorized(client: TestClient):
    """Wait for unauthorized returned when token is missing."""
    response = client.post("/api/v1/jobs/transcribe", json={"visit_id": str(uuid.uuid4())})
    assert response.status_code == 401


def test_transcribe_success(client: TestClient, db: Session, mocker):
    """Test successful transcribe response with presigned url generation."""
    user = User(
        id=uuid.uuid4(),
        email="doctor@example.com",
        clerk_user_id="clerk_doc_456",
        preferred_language="en"
    )
    db.add(user)
    db.commit()

    visit = Visit(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Consultation",
        visit_date=datetime.date.today(),
        consent_at=datetime.datetime.now(UTC)
    )
    db.add(visit)
    db.commit()

    # Mock Boto3 S3 Client
    mock_s3 = mocker.patch("app.api.v1.jobs._get_s3_client")
    mock_s3.return_value.generate_presigned_post.return_value = {
        "url": "https://s3.amazonaws.com/upload",
        "fields": {"key": "visits/123/audio", "AWSAccessKeyId": "test"}
    }

    token = _create_mock_token({"sub": "clerk_doc_456", "email": "doctor@example.com"})

    response = client.post(
        "/api/v1/jobs/transcribe",
        json={"visit_id": str(visit.id)},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "upload_fields" in data

    # Verify job created in DB
    job = db.query(Job).filter(Job.visit_id == visit.id).first()
    assert job is not None
    assert job.status == JobStatus.queued


def test_confirm_upload_magic_bytes_invalid(client: TestClient, db: Session, mocker):
    """Confirm fails with 422 for invalid magic bytes."""
    # Setup visit & job
    user = User(id=uuid.uuid4(), email="u@e.com", clerk_user_id="c_1")
    db.add(user)
    db.commit()

    visit = Visit(
        id=uuid.uuid4(), user_id=user.id, title="Test",
        visit_date=datetime.date.today(), consent_at=datetime.datetime.now(UTC)
    )
    db.add(visit)
    db.commit()

    job = Job(id=uuid.uuid4(), visit_id=visit.id, s3_key="test/key", status=JobStatus.queued)
    db.add(job)
    db.commit()

    # Mock S3 Client response invalid bytes
    mock_s3 = mocker.patch("app.api.v1.jobs._get_s3_client")
    mock_body = mocker.MagicMock()
    mock_body.read.return_value = b"NOT_AUDIO_FILE" # invalid
    mock_s3.return_value.get_object.return_value = {"Body": mock_body}
    token = _create_mock_token({"sub": "c_1", "email": "u@e.com"})

    response = client.post(
        f"/api/v1/jobs/{job.id}/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_confirm_upload_success(client: TestClient, db: Session, mocker):
    """Confirm succeeds with WebM magic bytes and enqueues Celery chain."""
    user = User(id=uuid.uuid4(), email="u2@e.com", clerk_user_id="c_2")
    db.add(user)
    db.commit()

    visit = Visit(
        id=uuid.uuid4(), user_id=user.id, title="Test",
        visit_date=datetime.date.today(), consent_at=datetime.datetime.now(UTC)
    )
    db.add(visit)
    db.commit()

    job = Job(id=uuid.uuid4(), visit_id=visit.id, s3_key="test/key2", status=JobStatus.queued)
    db.add(job)
    db.commit()

    # Mock S3 Client response WebM bytes: 1A 45 DF A3
    mock_s3 = mocker.patch("app.api.v1.jobs._get_s3_client")
    mock_body = mocker.MagicMock()
    mock_body.read.return_value = bytes.fromhex("1A45DFA3FFFFFFFF")
    mock_s3.return_value.get_object.return_value = {"Body": mock_body}

    # Mock Celery chain.apply_async
    mock_chain = mocker.patch("celery.chain")
    mock_async = mocker.MagicMock()
    mock_async.id = "task_id_123"
    mock_chain.return_value.apply_async.return_value = mock_async
    token = _create_mock_token({"sub": "c_2", "email": "u2@e.com"})

    response = client.post(
        f"/api/v1/jobs/{job.id}/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "queued"}

    # Verify updates in DB
    db.refresh(job)
    db.refresh(visit)
    assert job.celery_task_id == "task_id_123"
    assert visit.audio_s3_key == "test/key2"
