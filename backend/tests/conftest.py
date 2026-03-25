import os
import platform
import shutil
import subprocess
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pytest_postgresql import factories
from pytest_postgresql.executor import PostgreSQLExecutor
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

import app.db.models  # noqa: F401 — registers all models
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app

if platform.system() == "Windows":
    PostgreSQLExecutor.BASE_PROC_START_COMMAND = (
        '"{executable}" start -D "{datadir}" '
        '-o "-F -p {port} -c logging_collector=off {postgres_options}" '
        '-l "{logfile}" {startparams}'
    )

    def _windows_stop(self, sig=None, exp_sig=None):
        subprocess.check_output(
            f'{self.executable} stop -D "{self.datadir}" -m f',
            shell=True,
        )
        self._clear_process()
        return self

    PostgreSQLExecutor.stop = _windows_stop

PG_CTL_PATH = shutil.which("pg_ctl")
USE_EXTERNAL_POSTGRES = PG_CTL_PATH is None

if not USE_EXTERNAL_POSTGRES:
    postgresql_proc = factories.postgresql_proc(
        executable="pg_ctl",
        port=None,
        dbname="clearnote_test",
    )


def _make_db_url(p) -> str:
    return f"postgresql+psycopg2://{p.user}:{p.password}@{p.host}:{p.port}/{p.dbname}"


@pytest.fixture(scope="session")
def postgres_runtime(request):
    if not USE_EXTERNAL_POSTGRES:
        return request.getfixturevalue("postgresql_proc")

    return SimpleNamespace(
        user=os.getenv("POSTGRES_USER", "clearnote"),
        password=os.getenv("POSTGRES_PASSWORD", "clearnote"),
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "clearnote_test"),
        template_dbname=os.getenv("POSTGRES_TEMPLATE_DB", "template1"),
        version=16,
    )


@pytest.fixture(scope="session")
def db_engine(postgres_runtime):
    """Create engine + schema once per test session against a postgres runtime."""
    url = _make_db_url(postgres_runtime)

    def _prepare_engine():
        engine = create_engine(url, pool_pre_ping=True)
        with engine.begin() as conn:
            if USE_EXTERNAL_POSTGRES:
                conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
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
        return engine

    if USE_EXTERNAL_POSTGRES:
        engine = _prepare_engine()
        yield engine
        Base.metadata.drop_all(engine)
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
        engine.dispose()
        return

    janitor = DatabaseJanitor(
        user=postgres_runtime.user,
        host=postgres_runtime.host,
        port=postgres_runtime.port,
        dbname=postgres_runtime.dbname,
        template_dbname=postgres_runtime.template_dbname,
        version=postgres_runtime.version,
        password=postgres_runtime.password,
    )

    with janitor:
        engine = _prepare_engine()
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
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not nested.is_active:
            nested = connection.begin_nested()

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


class _SessionProxy:
    def __init__(self, session: Session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        # Worker tasks close their own sessions; keep the shared test session open.
        pass


@pytest.fixture
def worker_sessionlocal(db: Session, mocker):
    proxy = _SessionProxy(db)
    mocker.patch("app.workers.tasks.transcribe.SessionLocal", return_value=proxy)
    mocker.patch("app.workers.tasks.finalize.SessionLocal", return_value=proxy)
    mocker.patch("app.workers.tasks.cleanup.SessionLocal", return_value=proxy)
    return proxy
