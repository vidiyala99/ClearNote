import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import app.db.models  # noqa: F401 — registers all models
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app


def _make_db_url(p) -> str:
    return f"postgresql+psycopg2://{p.user}:{p.password}@{p.host}:{p.port}/{p.dbname}"


@pytest.fixture(scope="session")
def db_engine(postgresql_noproc):
    """Create engine + schema once per test session against the CI postgres service."""
    url = _make_db_url(postgresql_noproc)
    engine = create_engine(url, pool_pre_ping=True)

    # Create all ENUMs and tables
    with engine.begin() as conn:
        conn.execute(
            text(
                "DO $$ BEGIN "
                "CREATE TYPE visit_status AS ENUM ('pending','processing','ready','failed');"
                "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "CREATE TYPE job_status AS ENUM ('queued','processing','done','failed');"
                "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "CREATE TYPE urgency_tag AS ENUM "
                "('normal','follow-up','referral','prescription','urgent');"
                "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
            )
        )
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(db_engine) -> Session:
    """Transactional test fixture — rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db) -> TestClient:
    """TestClient with get_db overridden to use the transactional test session."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    from app.db.models.user import User

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        clerk_user_id="user_test123",
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
