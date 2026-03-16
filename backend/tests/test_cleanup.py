import uuid
from datetime import date, datetime, timezone, timedelta
from app.db.models import Visit, VisitStatus


def test_orphan_cleanup_marks_old_pending_visits_failed(db, test_user):
    from app.workers.tasks.cleanup import cleanup_orphaned_visits

    # Create a visit backdated 31 minutes
    old_visit = Visit(
        user_id=test_user.id,
        title="Old Visit",
        visit_date=date.today(),
        consent_at=datetime.now(timezone.utc),
        status=VisitStatus.pending,
    )
    db.add(old_visit)
    db.commit()

    # Backdate created_at in the DB
    db.execute(
        __import__("sqlalchemy").text(
            "UPDATE visits SET created_at = :ts WHERE id = :id"
        ),
        {"ts": datetime.now(timezone.utc) - timedelta(minutes=31), "id": old_visit.id},
    )
    db.commit()

    cleanup_orphaned_visits()
    db.refresh(old_visit)
    assert old_visit.status == VisitStatus.failed


def test_orphan_cleanup_leaves_recent_visits_alone(db, test_user):
    from app.workers.tasks.cleanup import cleanup_orphaned_visits

    recent_visit = Visit(
        user_id=test_user.id,
        title="Recent Visit",
        visit_date=date.today(),
        consent_at=datetime.now(timezone.utc),
        status=VisitStatus.pending,
    )
    db.add(recent_visit)
    db.commit()

    cleanup_orphaned_visits()
    db.refresh(recent_visit)
    assert recent_visit.status == VisitStatus.pending
