import platform
import subprocess
import uuid

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
        '{executable} start -D "{datadir}" '
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


postgresql_proc = factories.postgresql_proc(
    executable="pg_ctl",
    port=None,
    dbname="clearnote_test",
)


def _make_db_url(p) -> str:
    return f"postgresql+psycopg2://{p.user}:{p.password}@{p.host}:{p.port}/{p.dbname}"


@pytest.fixture(scope="session")
def db_engine(postgresql_proc):
    """Create engine + schema once per test session against a temporary postgres process."""
    url = _make_db_url(postgresql_proc)
    janitor = DatabaseJanitor(
        user=postgresql_proc.user,
        host=postgresql_proc.host,
        port=postgresql_proc.port,
        dbname=postgresql_proc.dbname,
        template_dbname=postgresql_proc.template_dbname,
        version=postgresql_proc.version,
        password=postgresql_proc.password,
    )

    with janitor:
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
