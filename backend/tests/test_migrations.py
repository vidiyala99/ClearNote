"""
Tests that all 5 tables and 3 ENUMs are created correctly by the schema setup.
Uses the db_engine fixture (session-scoped) which runs create_all().
"""
import uuid
from datetime import datetime, date

import pytest
from sqlalchemy import inspect, text


def test_all_tables_created(db_engine):
    inspector = inspect(db_engine)
    tables = set(inspector.get_table_names())
    assert {"users", "visits", "jobs", "transcripts", "summaries"}.issubset(tables)


def test_all_enums_created(db_engine):
    with db_engine.connect() as conn:
        result = conn.execute(
            text("SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname")
        )
        enums = {row[0] for row in result}
    assert {"visit_status", "job_status", "urgency_tag"}.issubset(enums)


def test_users_table_columns(db_engine):
    inspector = inspect(db_engine)
    cols = {c["name"] for c in inspector.get_columns("users")}
    assert cols == {"id", "email", "clerk_user_id", "preferred_language", "created_at", "deleted_at"}


def test_visits_table_columns(db_engine):
    inspector = inspect(db_engine)
    cols = {c["name"] for c in inspector.get_columns("visits")}
    assert {"id", "user_id", "title", "visit_date", "consent_at", "status", "audio_s3_key",
            "tags", "created_at", "updated_at"}.issubset(cols)


def test_jobs_table_columns(db_engine):
    inspector = inspect(db_engine)
    cols = {c["name"] for c in inspector.get_columns("jobs")}
    assert {"id", "visit_id", "s3_key", "status", "celery_task_id", "created_at"}.issubset(cols)


def test_s3_key_not_nullable(db_engine):
    inspector = inspect(db_engine)
    cols = {c["name"]: c for c in inspector.get_columns("jobs")}
    assert cols["s3_key"]["nullable"] is False


def test_create_user(db):
    from app.db.models.user import User
    user = User(
        id=uuid.uuid4(),
        email="alice@example.com",
        clerk_user_id="user_alice",
    )
    db.add(user)
    db.flush()
    fetched = db.query(User).filter_by(email="alice@example.com").one()
    assert fetched.clerk_user_id == "user_alice"
    assert fetched.preferred_language == "en"


def test_create_visit(db, test_user):
    from app.db.models.visit import Visit, VisitStatus
    visit = Visit(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Cardiology Checkup",
        visit_date=date(2026, 3, 14),
        consent_at=datetime.utcnow(),
    )
    db.add(visit)
    db.flush()
    fetched = db.query(Visit).filter_by(title="Cardiology Checkup").one()
    assert fetched.status == VisitStatus.pending
    assert fetched.tags == []


def test_create_job_requires_s3_key(db, test_user):
    from app.db.models.visit import Visit
    from app.db.models.job import Job, JobStatus
    import uuid as _uuid
    visit_id = _uuid.uuid4()
    visit = Visit(
        id=visit_id,
        user_id=test_user.id,
        title="Test Visit",
        visit_date=date(2026, 3, 14),
        consent_at=datetime.utcnow(),
    )
    db.add(visit)
    db.flush()

    job = Job(
        id=_uuid.uuid4(),
        visit_id=visit_id,
        s3_key=f"visits/{visit_id}/audio",
    )
    db.add(job)
    db.flush()
    fetched = db.query(Job).filter_by(visit_id=visit_id).one()
    assert fetched.status == JobStatus.queued
    assert fetched.s3_key == f"visits/{visit_id}/audio"


def test_visit_fk_cascade(db, test_user):
    from app.db.models.visit import Visit
    from app.db.models.job import Job
    import uuid as _uuid
    visit_id = _uuid.uuid4()
    visit = Visit(
        id=visit_id,
        user_id=test_user.id,
        title="Cascade Test",
        visit_date=date(2026, 3, 14),
        consent_at=datetime.utcnow(),
    )
    db.add(visit)
    db.flush()
    job = Job(id=_uuid.uuid4(), visit_id=visit_id, s3_key=f"visits/{visit_id}/audio")
    db.add(job)
    db.flush()

    db.delete(visit)
    db.flush()
    assert db.query(Job).filter_by(visit_id=visit_id).count() == 0
