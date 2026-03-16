# ClearNote Phase 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the full ClearNote monorepo — FastAPI backend, React/TypeScript frontend, PostgreSQL schema, Celery worker stub, S3 upload flow, Docker Compose, and GitHub Actions CI.

**Architecture:** Monorepo with `backend/` (FastAPI, sync SQLAlchemy/psycopg2, Celery) and `frontend/` (React 18, Vite, TypeScript, Tailwind, shadcn/ui). Auth via Clerk (JWKS-validated JWT on backend, Clerk SDK on frontend). Audio uploads use S3 presigned POST with a two-task Celery chain stub.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy (sync), Alembic, Celery 5, Redis 7, PostgreSQL 16, React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, react-router-dom v6, Clerk, boto3, pytest, pytest-postgresql, vitest

**Spec:** `docs/superpowers/specs/2026-03-14-phase1-foundation-design.md`

---

## File Map

### Backend — Created

| File | Responsibility |
|---|---|
| `backend/pyproject.toml` | Dependencies, ruff/mypy/pytest config |
| `backend/Dockerfile` | Single image for api + worker + beat |
| `backend/alembic.ini` | Alembic config |
| `backend/alembic/env.py` | Migration env with model imports |
| `backend/alembic/versions/001_initial.py` | Creates all 5 tables + 3 ENUMs |
| `backend/app/main.py` | FastAPI app factory, CORS, router mount |
| `backend/app/config.py` | pydantic-settings Settings class |
| `backend/app/db/base.py` | SQLAlchemy declarative base |
| `backend/app/db/session.py` | Engine + SessionLocal + get_db dependency |
| `backend/app/db/models/user.py` | User model |
| `backend/app/db/models/visit.py` | Visit model + VisitStatus enum |
| `backend/app/db/models/job.py` | Job model + JobStatus enum |
| `backend/app/db/models/transcript.py` | Transcript model |
| `backend/app/db/models/summary.py` | Summary model + UrgencyTag enum |
| `backend/app/middleware/clerk_auth.py` | JWKS fetch + JWT decode + request.state injection |
| `backend/app/schemas/user.py` | UserOut pydantic schema |
| `backend/app/schemas/visit.py` | VisitCreate, VisitOut schemas |
| `backend/app/schemas/job.py` | JobOut, ConfirmOut schemas |
| `backend/app/api/v1/router.py` | Includes all v1 sub-routers |
| `backend/app/api/v1/auth.py` | GET /users/me |
| `backend/app/api/v1/visits.py` | POST /visits, GET /visits |
| `backend/app/api/v1/jobs.py` | POST /jobs/transcribe, POST /jobs/{id}/confirm |
| `backend/app/services/s3.py` | generate_presigned_post, range_get_magic_bytes, delete_object |
| `backend/app/workers/celery_app.py` | Celery app + beat schedule |
| `backend/app/workers/tasks/transcribe.py` | transcribe_audio task |
| `backend/app/workers/tasks/finalize.py` | finalize_visit task (no-op stub) |
| `backend/app/workers/tasks/cleanup.py` | orphan_cleanup beat task |
| `backend/tests/conftest.py` | pytest fixtures: db session, test client, fake auth |
| `backend/tests/test_health.py` | GET /health |
| `backend/tests/test_auth.py` | /users/me auth tests |
| `backend/tests/test_visits.py` | POST /visits tests |
| `backend/tests/test_jobs.py` | POST /jobs/transcribe, /confirm tests |
| `backend/tests/test_cleanup.py` | Orphan cleanup task test |
| `backend/tests/test_worker.py` | Worker task unit tests |

### Frontend — Created

| File | Responsibility |
|---|---|
| `frontend/package.json` | Dependencies |
| `frontend/vite.config.ts` | Vite config with proxy to API |
| `frontend/tailwind.config.ts` | Design tokens |
| `frontend/tsconfig.json` | TypeScript config |
| `frontend/src/main.tsx` | React root + ClerkProvider + RouterProvider |
| `frontend/src/App.tsx` | Route definitions |
| `frontend/src/routes/Landing.tsx` | Public landing page |
| `frontend/src/routes/Dashboard.tsx` | Protected dashboard (visit list) |
| `frontend/src/routes/NewVisit.tsx` | New visit form + recording/upload |
| `frontend/src/components/ProtectedRoute.tsx` | /users/me on mount, 401 → /sign-in |
| `frontend/src/components/recording/RecordingButton.tsx` | Record/pause/stop controls |
| `frontend/src/components/recording/WaveformCanvas.tsx` | Canvas waveform visualizer |
| `frontend/src/components/upload/FileUploadZone.tsx` | Drag-and-drop file picker |
| `frontend/src/components/consent/ConsentModal.tsx` | Pre-recording consent dialog |
| `frontend/src/hooks/useRecorder.ts` | MediaRecorder state machine |
| `frontend/src/lib/api.ts` | axios instance + interceptors |
| `frontend/src/lib/s3Upload.ts` | S3 presigned POST multipart upload |
| `frontend/src/lib/types.ts` | Shared TypeScript types |

### Root

| File | Responsibility |
|---|---|
| `docker-compose.yml` | 5 services: api, worker, beat, postgres, redis |
| `.env.example` | Documented env vars |
| `.github/workflows/ci.yml` | Backend + frontend CI jobs |

---

## Chunk 1: Backend Infrastructure + Database

### Task 1: Monorepo scaffold + Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/Dockerfile`

- [ ] **Step 1.1: Create root directory structure**

```bash
mkdir -p backend/app/db/models backend/app/api/v1 backend/app/middleware \
  backend/app/schemas backend/app/services backend/app/workers/tasks \
  backend/alembic/versions backend/tests \
  frontend/src/routes frontend/src/components/recording \
  frontend/src/components/upload frontend/src/components/consent \
  frontend/src/hooks frontend/src/lib \
  docs/superpowers/specs docs/superpowers/plans \
  .github/workflows
```

- [ ] **Step 1.2: Create `.env.example`**

```bash
# .env.example
DATABASE_URL=postgresql://clearnote:clearnote@localhost:5432/clearnote
REDIS_URL=redis://localhost:6379/0
CLERK_JWKS_URL=https://your-clerk-instance.clerk.accounts.dev/.well-known/jwks.json
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=clearnote-audio
AWS_REGION=us-east-1
CORS_ORIGINS=http://localhost:5173,https://app.clearnote.io
```

- [ ] **Step 1.3: Create `backend/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "clearnote-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.111.0",
  "uvicorn[standard]>=0.30.0",
  "gunicorn>=22.0.0",
  "pydantic-settings>=2.3.0",
  "sqlalchemy>=2.0.30",
  "psycopg2-binary>=2.9.9",
  "alembic>=1.13.0",
  "celery[redis]>=5.4.0",
  "boto3>=1.34.0",
  "python-jose[cryptography]>=3.3.0",
  "httpx>=0.27.0",
  "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "pytest-postgresql>=6.0.0",
  "pytest-mock>=3.14.0",
  "freezegun>=1.5.0",
  "ruff>=0.5.0",
  "mypy>=1.10.0",
  "types-python-jose",
  "httpx>=0.27.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.12"
strict = false
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
  "--postgresql-host=localhost",
  "--postgresql-port=5432",
  "--postgresql-user=clearnote",
  "--postgresql-password=clearnote",
  "--postgresql-dbname=clearnote_test",
]
```

- [ ] **Step 1.4: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 1.5: Create `docker-compose.yml`**

```yaml
services:
  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    env_file: .env
    volumes:
      - ./backend:/app

  worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    depends_on:
      - postgres
      - redis
    env_file: .env
    volumes:
      - ./backend:/app

  beat:
    build: ./backend
    command: celery -A app.workers.celery_app beat --loglevel=info
    depends_on:
      - redis
    env_file: .env
    volumes:
      - ./backend:/app

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: clearnote
      POSTGRES_USER: clearnote
      POSTGRES_PASSWORD: clearnote
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

- [ ] **Step 1.6: Commit scaffold**

```bash
git init
git add docker-compose.yml .env.example backend/pyproject.toml backend/Dockerfile
git commit -m "chore: scaffold monorepo structure, Docker Compose, and pyproject.toml"
```

---

### Task 2: FastAPI app + health endpoint (TDD)

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 2.1: Write failing health test**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient

def test_health_returns_ok(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 2.2: Create `backend/app/config.py`**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://clearnote:clearnote@localhost:5432/clearnote"
    redis_url: str = "redis://localhost:6379/0"
    clerk_jwks_url: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket_name: str = "clearnote-audio"
    aws_region: str = "us-east-1"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        # Strip whitespace from each element to handle "http://a.com, http://b.com"
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
```

- [ ] **Step 2.3: Create `backend/app/db/base.py`**

```python
# backend/app/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 2.4: Create `backend/app/db/session.py`**

```python
# backend/app/db/session.py
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2.5: Create `backend/app/main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="ClearNote API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 2.6: Create `backend/tests/conftest.py` (minimal — expands in later tasks)**

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 2.7: Run health test**

```bash
cd backend && pip install -e ".[dev]" && pytest tests/test_health.py -v
```

Expected: `PASSED`

- [ ] **Step 2.8: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: add FastAPI app factory, config, health endpoint"
```

---

### Task 3: Database models + Alembic migrations (TDD)

**Files:**
- Create: `backend/app/db/models/user.py`
- Create: `backend/app/db/models/visit.py`
- Create: `backend/app/db/models/job.py`
- Create: `backend/app/db/models/transcript.py`
- Create: `backend/app/db/models/summary.py`
- Create: `backend/app/db/models/__init__.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/001_initial.py`
- Create: `backend/tests/test_migrations.py`

- [ ] **Step 3.1: Write failing migration test**

```python
# backend/tests/test_migrations.py
from sqlalchemy import inspect, text
from app.db.session import engine


def test_all_tables_exist():
    """After alembic upgrade head, all 5 tables must exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table in ["users", "visits", "jobs", "transcripts", "summaries"]:
        assert table in tables, f"Missing table: {table}"


def test_visit_status_enum_values(db):
    """visit_status ENUM has exactly the right values."""
    result = db.execute(
        text("SELECT unnest(enum_range(NULL::visit_status))::text")
    ).scalars().all()
    assert set(result) == {"pending", "processing", "ready", "failed"}
```

- [ ] **Step 3.2: Create model files**

```python
# backend/app/db/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    clerk_user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

```python
# backend/app/db/models/visit.py
import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, Enum as SAEnum, ARRAY, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import enum


class VisitStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    doctor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[VisitStatus] = mapped_column(
        SAEnum(VisitStatus, name="visit_status"), default=VisitStatus.pending
    )
    audio_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

```python
# backend/app/db/models/job.py
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import enum


class JobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("visit_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id", ondelete="CASCADE"))
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)  # NOT NULL — written at job creation
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status"), default=JobStatus.queued
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

```python
# backend/app/db/models/transcript.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Transcript(Base):
    __tablename__ = "transcripts"
    __table_args__ = (UniqueConstraint("visit_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id", ondelete="CASCADE"))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunks: Mapped[list] = mapped_column(JSONB, default=list)
    language_detected: Mapped[str] = mapped_column(String(10), default="en")
    wer_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
```

```python
# backend/app/db/models/summary.py
import uuid
from sqlalchemy import Text, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import enum


class UrgencyTag(str, enum.Enum):
    normal = "normal"
    follow_up = "follow-up"
    referral = "referral"
    prescription = "prescription"
    urgent = "urgent"


class Summary(Base):
    __tablename__ = "summaries"
    __table_args__ = (UniqueConstraint("visit_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"))
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    medications: Mapped[list] = mapped_column(JSONB, default=list)
    diagnoses: Mapped[list] = mapped_column(JSONB, default=list)
    action_items: Mapped[list] = mapped_column(JSONB, default=list)
    urgency_tag: Mapped[UrgencyTag] = mapped_column(
        SAEnum(UrgencyTag, name="urgency_tag"), default=UrgencyTag.normal
    )
    translated_overview: Mapped[str | None] = mapped_column(Text, nullable=True)
```

```python
# backend/app/db/models/__init__.py
from .user import User
from .visit import Visit, VisitStatus
from .job import Job, JobStatus
from .transcript import Transcript
from .summary import Summary, UrgencyTag

__all__ = ["User", "Visit", "VisitStatus", "Job", "JobStatus", "Transcript", "Summary", "UrgencyTag"]
```

- [ ] **Step 3.3: Set up Alembic**

```bash
cd backend && alembic init alembic
```

Update `backend/alembic/env.py` — replace the `run_migrations_online` section:

```python
# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.config import settings
from app.db.base import Base
import app.db.models  # noqa: F401 — ensures all models are imported

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3.4: Generate + edit initial migration**

```bash
cd backend && alembic revision --autogenerate -m "initial"
```

Then rename the generated file to `001_initial.py` and verify it creates all 5 tables and 3 ENUMs. Confirm it contains `create_table` calls for: `users`, `visits`, `jobs`, `transcripts`, `summaries`.

- [ ] **Step 3.5: Run migration against local Postgres**

```bash
alembic upgrade head
```

Expected: All 5 tables created, no errors.

- [ ] **Step 3.6: Update `conftest.py` with DB fixtures**

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.db.base import Base
from app.db.session import get_db


@pytest.fixture(scope="session")
def db_engine(postgresql_noproc):
    """postgresql_noproc fixture: connects to external Postgres (GHA service or local).
    Configured via pyproject.toml addopts (host, port, user, password, dbname).
    Does NOT spawn a new pg_ctl process — avoids conflicts with GHA service container."""
    p = postgresql_noproc
    conn_str = (
        f"postgresql://{p.user}:{p.password}@{p.host}:{p.port}/{p.dbname}"
    )
    engine = create_engine(conn_str)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(db_engine) -> Session:
    TestingSessionLocal = sessionmaker(bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 3.7: Run migration tests**

```bash
cd backend && pytest tests/test_migrations.py -v
```

Expected: Both tests PASS.

- [ ] **Step 3.8: Commit**

```bash
git add backend/app/db/ backend/alembic/ backend/tests/
git commit -m "feat: add database models and Alembic initial migration"
```

---

### Task 4: Clerk auth middleware + /users/me (TDD)

**Files:**
- Create: `backend/app/middleware/clerk_auth.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/v1/router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 4.1: Write failing auth tests**

```python
# backend/tests/test_auth.py
import pytest
from unittest.mock import patch, MagicMock


def test_users_me_returns_401_without_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_users_me_returns_401_with_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert response.status_code == 401


def test_users_me_upserts_and_returns_user(client, db, mock_clerk_user):
    """mock_clerk_user fixture patches JWT decode to return a known clerk_user_id."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {mock_clerk_user['token']}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == mock_clerk_user["email"]
    assert body["preferred_language"] == "en"


def test_users_me_upsert_is_idempotent(client, db, mock_clerk_user):
    """Calling /users/me twice with same Clerk ID doesn't create duplicate user."""
    for _ in range(2):
        client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {mock_clerk_user['token']}"})
    from app.db.models import User
    count = db.query(User).filter(User.clerk_user_id == mock_clerk_user["clerk_user_id"]).count()
    assert count == 1
```

- [ ] **Step 4.2: Add `mock_clerk_user` fixture to `conftest.py`**

```python
# Add to backend/tests/conftest.py
import uuid


@pytest.fixture
def mock_clerk_user(monkeypatch):
    """Patch ClerkAuthMiddleware to inject a known user without real JWKS."""
    user_data = {
        "clerk_user_id": f"user_{uuid.uuid4().hex[:8]}",
        "email": "test@example.com",
        "token": "fake-token",
    }

    async def fake_dispatch(self, request, call_next):
        request.state.clerk_user_id = user_data["clerk_user_id"]
        request.state.clerk_email = user_data["email"]
        return await call_next(request)

    from app.middleware import clerk_auth
    monkeypatch.setattr(clerk_auth.ClerkAuthMiddleware, "dispatch", fake_dispatch)
    return user_data
```

- [ ] **Step 4.3: Create `backend/app/middleware/clerk_auth.py`**

```python
# backend/app/middleware/clerk_auth.py
import httpx
from jose import jwt, JWTError
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

UNPROTECTED = {"/health", "/api/v1/auth/login"}  # extend as needed
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.clerk_jwks_url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in UNPROTECTED or not request.url.path.startswith("/api/"):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(
                {"error": {"code": "UNAUTHORIZED", "message": "Missing token"}}, status_code=401
            )

        token = auth.removeprefix("Bearer ").strip()
        try:
            jwks = await _get_jwks()
            payload = jwt.decode(token, jwks, algorithms=["RS256"])
            request.state.clerk_user_id = payload["sub"]
            request.state.clerk_email = payload.get("email", "")
        except (JWTError, Exception):
            return JSONResponse(
                {"error": {"code": "UNAUTHORIZED", "message": "Invalid token"}}, status_code=401
            )

        return await call_next(request)
```

- [ ] **Step 4.4: Create `backend/app/schemas/user.py`**

```python
# backend/app/schemas/user.py
import uuid
from datetime import datetime
from pydantic import BaseModel


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    preferred_language: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4.5: Create `backend/app/api/v1/auth.py`**

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(request: Request, db: Session = Depends(get_db)):
    clerk_user_id = request.state.clerk_user_id
    email = request.state.clerk_email

    stmt = (
        insert(User)
        .values(clerk_user_id=clerk_user_id, email=email)
        .on_conflict_do_update(
            index_elements=["clerk_user_id"],
            set_={"email": email},
        )
        .returning(User)
    )
    result = db.execute(stmt)
    db.commit()
    user = result.scalars().one()
    return user
```

- [ ] **Step 4.6: Create `backend/app/api/v1/router.py`**

```python
# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import auth

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
```

- [ ] **Step 4.7: Update `backend/app/main.py` to add middleware + router**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware.clerk_auth import ClerkAuthMiddleware
from app.api.v1.router import router as api_router

app = FastAPI(title="ClearNote API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ClerkAuthMiddleware)
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 4.8: Run auth tests**

```bash
cd backend && pytest tests/test_auth.py tests/test_health.py -v
```

Expected: All tests PASS.

- [ ] **Step 4.9: Commit**

```bash
git add backend/app/middleware/ backend/app/schemas/ backend/app/api/ backend/tests/
git commit -m "feat: add Clerk auth middleware and /users/me endpoint"
```

---

### Task 5: Visits + Jobs endpoints (TDD)

**Files:**
- Create: `backend/app/schemas/visit.py`
- Create: `backend/app/schemas/job.py`
- Create: `backend/app/api/v1/visits.py`
- Create: `backend/app/api/v1/jobs.py`
- Create: `backend/app/services/s3.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/test_visits.py`
- Create: `backend/tests/test_jobs.py`

- [ ] **Step 5.1: Write failing visit tests**

```python
# backend/tests/test_visits.py
from datetime import date, datetime, timezone


def test_create_visit_requires_auth(client):
    response = client.post("/api/v1/visits", json={})
    assert response.status_code == 401


def test_create_visit_success(client, mock_clerk_user):
    response = client.post(
        "/api/v1/visits",
        json={
            "title": "Dr. Smith - Cardiology",
            "visit_date": str(date.today()),
            "doctor_name": "Dr. Smith",
            "consent_at": datetime.now(timezone.utc).isoformat(),
        },
        headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert "visit_id" in body
    assert body["status"] == "pending"


def test_create_visit_missing_title_returns_422(client, mock_clerk_user):
    response = client.post(
        "/api/v1/visits",
        json={"visit_date": str(date.today()), "consent_at": datetime.now(timezone.utc).isoformat()},
        headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
    )
    assert response.status_code == 422
```

- [ ] **Step 5.2: Write failing job tests**

```python
# backend/tests/test_jobs.py
from datetime import date, datetime, timezone
from unittest.mock import patch, MagicMock
import uuid


def _create_visit(client, mock_clerk_user) -> str:
    resp = client.post(
        "/api/v1/visits",
        json={
            "title": "Test Visit",
            "visit_date": str(date.today()),
            "consent_at": datetime.now(timezone.utc).isoformat(),
        },
        headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
    )
    return resp.json()["visit_id"]


def test_transcribe_creates_job(client, mock_clerk_user):
    visit_id = _create_visit(client, mock_clerk_user)
    with patch("app.services.s3.generate_presigned_post") as mock_s3:
        mock_s3.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {"key": f"visits/{visit_id}/audio", "policy": "abc"},
        }
        response = client.post(
            "/api/v1/jobs/transcribe",
            json={"visit_id": visit_id},
            headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
        )
    assert response.status_code == 201
    body = response.json()
    assert "job_id" in body
    assert "upload_url" in body
    assert "upload_fields" in body
    assert isinstance(body["upload_fields"], dict)


def test_confirm_with_valid_audio_enqueues_task(client, db, mock_clerk_user):
    visit_id = _create_visit(client, mock_clerk_user)
    with patch("app.services.s3.generate_presigned_post") as mock_s3:
        mock_s3.return_value = {"url": "https://s3.amazonaws.com/bucket", "fields": {}}
        job_resp = client.post(
            "/api/v1/jobs/transcribe",
            json={"visit_id": visit_id},
            headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
        )
    job_id = job_resp.json()["job_id"]

    with patch("app.services.s3.get_magic_bytes") as mock_magic, \
         patch("app.api.v1.jobs.transcribe_chain") as mock_chain:
        mock_magic.return_value = b"\x1a\x45\xdf\xa3\x00\x00\x00\x00\x00\x00\x00\x00"
        mock_chain.return_value = MagicMock(id="celery-task-id")
        response = client.post(
            f"/api/v1/jobs/{job_id}/confirm",
            headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_confirm_non_audio_returns_422(client, db, mock_clerk_user):
    visit_id = _create_visit(client, mock_clerk_user)
    with patch("app.services.s3.generate_presigned_post") as mock_s3:
        mock_s3.return_value = {"url": "https://s3.amazonaws.com/bucket", "fields": {}}
        job_resp = client.post(
            "/api/v1/jobs/transcribe",
            json={"visit_id": visit_id},
            headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
        )
    job_id = job_resp.json()["job_id"]

    with patch("app.services.s3.get_magic_bytes") as mock_magic:
        mock_magic.return_value = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # PNG header
        response = client.post(
            f"/api/v1/jobs/{job_id}/confirm",
            headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
        )
    assert response.status_code == 422


def test_confirm_idempotent(client, db, mock_clerk_user):
    """Second confirm on same job returns 200 without re-enqueuing."""
    visit_id = _create_visit(client, mock_clerk_user)
    with patch("app.services.s3.generate_presigned_post") as mock_s3:
        mock_s3.return_value = {"url": "https://s3.amazonaws.com/bucket", "fields": {}}
        job_resp = client.post(
            "/api/v1/jobs/transcribe",
            json={"visit_id": visit_id},
            headers={"Authorization": f"Bearer {mock_clerk_user['token']}"},
        )
    job_id = job_resp.json()["job_id"]

    with patch("app.services.s3.get_magic_bytes") as mock_magic, \
         patch("app.api.v1.jobs.transcribe_chain") as mock_chain:
        mock_magic.return_value = b"\x1a\x45\xdf\xa3\x00\x00\x00\x00\x00\x00\x00\x00"
        mock_chain.return_value = MagicMock(id="task-id")
        client.post(f"/api/v1/jobs/{job_id}/confirm",
                    headers={"Authorization": f"Bearer {mock_clerk_user['token']}"})
        # Second call
        mock_chain.reset_mock()
        response = client.post(f"/api/v1/jobs/{job_id}/confirm",
                               headers={"Authorization": f"Bearer {mock_clerk_user['token']}"})

    assert response.status_code == 200
    mock_chain.assert_not_called()  # not re-enqueued
```

- [ ] **Step 5.3: Create `backend/app/schemas/visit.py`**

```python
# backend/app/schemas/visit.py
import uuid
from datetime import date, datetime
from pydantic import BaseModel


class VisitCreate(BaseModel):
    title: str
    visit_date: date
    doctor_name: str | None = None
    consent_at: datetime


class VisitOut(BaseModel):
    visit_id: uuid.UUID
    status: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 5.4: Create `backend/app/schemas/job.py`**

```python
# backend/app/schemas/job.py
import uuid
from pydantic import BaseModel


class JobOut(BaseModel):
    job_id: uuid.UUID
    upload_url: str
    upload_fields: dict[str, str]


class ConfirmOut(BaseModel):
    status: str
```

- [ ] **Step 5.5: Create `backend/app/services/s3.py`**

```python
# backend/app/services/s3.py
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.config import settings

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _s3_client


AUDIO_MAGIC_BYTES = {
    b"\x1a\x45\xdf\xa3": "webm",   # WebM/MKV
    b"\xff\xfb": "mp3",            # MP3
    b"\xff\xf3": "mp3",
    b"\xff\xf2": "mp3",
    b"ID3": "mp3",                 # MP3 ID3 tag
    b"RIFF": "wav",                # WAV (check offset 8 for "WAVE")
    b"\x00\x00\x00\x18ftyp": "m4a",  # M4A (check offset 4)
    b"\x00\x00\x00\x20ftyp": "mp4",
}


def generate_presigned_post(s3_key: str, expiry: int = 900) -> dict:
    client = get_s3_client()
    return client.generate_presigned_post(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Conditions=[
            ["starts-with", "$Content-Type", "audio/"],
            ["content-length-range", 1, 524_288_000],
        ],
        ExpiresIn=expiry,
    )


def get_magic_bytes(s3_key: str, timeout: float = 5.0) -> bytes:
    """Fetch first 12 bytes from S3 to check file type. Raises on timeout/error."""
    import botocore.config
    client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=botocore.config.Config(connect_timeout=timeout, read_timeout=timeout),
    )
    resp = client.get_object(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Range="bytes=0-11",
    )
    return resp["Body"].read()


def is_valid_audio(magic: bytes) -> bool:
    for prefix, _ in AUDIO_MAGIC_BYTES.items():
        if magic.startswith(prefix):
            return True
    # M4A: "ftyp" starts at offset 4
    if len(magic) >= 8 and magic[4:8] == b"ftyp":
        return True
    return False


def delete_object(s3_key: str) -> None:
    get_s3_client().delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
```

- [ ] **Step 5.6: Create `backend/app/api/v1/visits.py`**

```python
# backend/app/api/v1/visits.py
import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Visit, VisitStatus, User
from app.schemas.visit import VisitCreate, VisitOut

router = APIRouter(prefix="/visits", tags=["visits"])


def _get_user(request: Request, db: Session) -> User:
    from sqlalchemy.dialects.postgresql import insert
    stmt = (
        insert(User)
        .values(clerk_user_id=request.state.clerk_user_id, email=request.state.clerk_email)
        .on_conflict_do_update(
            index_elements=["clerk_user_id"], set_={"email": request.state.clerk_email}
        )
        .returning(User)
    )
    result = db.execute(stmt)
    db.commit()
    return result.scalars().one()


@router.post("", response_model=VisitOut, status_code=status.HTTP_201_CREATED)
def create_visit(body: VisitCreate, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    visit = Visit(
        user_id=user.id,
        title=body.title,
        visit_date=body.visit_date,
        doctor_name=body.doctor_name,
        consent_at=body.consent_at,
        status=VisitStatus.pending,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return VisitOut(visit_id=visit.id, status=visit.status.value)
```

- [ ] **Step 5.7: Create `backend/app/api/v1/jobs.py`**

```python
# backend/app/api/v1/jobs.py
import uuid
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from botocore.exceptions import BotoCoreError, ClientError
from app.db.session import get_db
from app.db.models import Visit, VisitStatus, Job, JobStatus
from app.schemas.job import JobOut, ConfirmOut
from app.services import s3 as s3_service
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["jobs"])


class TranscribeRequest(BaseModel):
    visit_id: uuid.UUID


def transcribe_chain(visit_id: str):
    """Import here to avoid circular imports and allow mocking in tests."""
    from celery import chain
    from app.workers.tasks.transcribe import transcribe_audio
    from app.workers.tasks.finalize import finalize_visit
    return chain(transcribe_audio.s(visit_id), finalize_visit.s()).apply_async()


@router.post("/transcribe", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def start_transcribe(body: TranscribeRequest, request: Request, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == body.visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    s3_key = f"visits/{visit.id}/audio"
    presigned = s3_service.generate_presigned_post(s3_key)

    job = Job(visit_id=visit.id, s3_key=s3_key, status=JobStatus.queued)
    db.add(job)
    db.commit()
    db.refresh(job)

    return JobOut(
        job_id=job.id,
        upload_url=presigned["url"],
        upload_fields=presigned["fields"],
    )


@router.post("/{job_id}/confirm", response_model=ConfirmOut)
def confirm_upload(job_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    visit = db.query(Visit).filter(Visit.id == job.visit_id).first()

    # Step 1 (spec order): Key-mismatch check — job already confirmed with a different key
    if visit and visit.audio_s3_key and visit.audio_s3_key != job.s3_key:
        raise HTTPException(status_code=409, detail="Job already confirmed with a different S3 key")

    # Step 2 (spec order): Idempotency — already processing or done, skip re-enqueue
    if visit and visit.status in (VisitStatus.processing, VisitStatus.ready):
        return ConfirmOut(status="queued")

    # Step 3 (spec order): Magic bytes check (5s timeout)
    # - S3 unavailable (timeout/connection error) → 503
    # - File fetched but non-audio magic bytes → 422
    try:
        magic = s3_service.get_magic_bytes(job.s3_key)
    except (BotoCoreError, ClientError, Exception):
        raise HTTPException(status_code=503, detail="Storage unavailable")

    if not s3_service.is_valid_audio(magic):
        raise HTTPException(status_code=422, detail="Uploaded file is not a valid audio format")

    visit.audio_s3_key = job.s3_key
    db.commit()

    result = transcribe_chain(str(visit.id))
    job.celery_task_id = result.id
    job.status = JobStatus.processing
    db.commit()

    return ConfirmOut(status="queued")
```

- [ ] **Step 5.8: Update router**

```python
# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import auth, visits, jobs

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(visits.router)
router.include_router(jobs.router)
```

- [ ] **Step 5.9: Run all backend tests**

```bash
cd backend && pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 5.10: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: add visits and jobs endpoints with S3 presigned POST"
```

---

### Task 6: Celery workers (TDD)

**Files:**
- Create: `backend/app/workers/celery_app.py`
- Create: `backend/app/workers/tasks/transcribe.py`
- Create: `backend/app/workers/tasks/finalize.py`
- Create: `backend/app/workers/tasks/cleanup.py`
- Create: `backend/tests/test_worker.py`
- Create: `backend/tests/test_cleanup.py`

- [ ] **Step 6.1: Write failing worker tests**

```python
# backend/tests/test_worker.py
import uuid
from datetime import date, datetime, timezone
from app.db.models import Visit, VisitStatus, Transcript


def _make_visit(db, user_id) -> Visit:
    visit = Visit(
        user_id=user_id,
        title="Test",
        visit_date=date.today(),
        consent_at=datetime.now(timezone.utc),
        status=VisitStatus.pending,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


def test_transcribe_audio_transitions_to_processing_then_ready(db, test_user):
    """Run tasks synchronously with CELERY_TASK_ALWAYS_EAGER."""
    from app.workers.tasks.transcribe import transcribe_audio
    from app.workers.tasks.finalize import finalize_visit

    visit = _make_visit(db, test_user.id)

    # Run synchronously (always_eager set in test config)
    visit_id = str(visit.id)
    transcribe_audio(visit_id)  # direct call simulates eager execution
    db.refresh(visit)
    assert visit.status == VisitStatus.processing

    finalize_visit(visit_id)
    db.refresh(visit)
    assert visit.status == VisitStatus.ready


def test_transcribe_creates_transcript_row(db, test_user):
    from app.workers.tasks.transcribe import transcribe_audio

    visit = _make_visit(db, test_user.id)
    transcribe_audio(str(visit.id))
    db.refresh(visit)

    transcript = db.query(Transcript).filter(Transcript.visit_id == visit.id).first()
    assert transcript is not None
    assert len(transcript.raw_text) > 0


def test_transcribe_is_idempotent(db, test_user):
    """Running transcribe_audio twice doesn't create duplicate transcript rows."""
    from app.workers.tasks.transcribe import transcribe_audio

    visit = _make_visit(db, test_user.id)
    transcribe_audio(str(visit.id))
    transcribe_audio(str(visit.id))  # second call

    from sqlalchemy import func
    count = db.query(func.count(Transcript.id)).filter(Transcript.visit_id == visit.id).scalar()
    assert count == 1
```

```python
# backend/tests/test_cleanup.py
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
```

- [ ] **Step 6.2: Add `test_user` fixture to conftest**

```python
# Add to backend/tests/conftest.py
@pytest.fixture
def test_user(db):
    from app.db.models import User
    import uuid
    user = User(
        clerk_user_id=f"user_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:6]}@example.com",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

- [ ] **Step 6.3: Create `backend/app/workers/celery_app.py`**

```python
# backend/app/workers/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "clearnote",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.transcribe",
        "app.workers.tasks.finalize",
        "app.workers.tasks.cleanup",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    beat_schedule={
        "cleanup-orphaned-visits": {
            "task": "app.workers.tasks.cleanup.cleanup_orphaned_visits",
            "schedule": crontab(minute="*/15"),
        }
    },
)
```

- [ ] **Step 6.4: Create `backend/app/workers/tasks/transcribe.py`**

```python
# backend/app/workers/tasks/transcribe.py
import time
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Visit, VisitStatus, Transcript
from sqlalchemy.dialects.postgresql import insert as pg_insert


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def transcribe_audio(self, visit_id: str) -> str:
    db = SessionLocal()
    try:
        visit = db.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            return visit_id

        visit.status = VisitStatus.processing
        db.commit()

        time.sleep(3)  # Stub: simulate processing

        # Idempotent upsert
        stmt = (
            pg_insert(Transcript)
            .values(
                visit_id=visit_id,
                raw_text=f"Mock transcript for visit {visit_id}.",
                chunks=[],
                language_detected="en",
            )
            .on_conflict_do_update(
                index_elements=["visit_id"],
                set_={"raw_text": f"Mock transcript for visit {visit_id}."},
            )
        )
        db.execute(stmt)
        db.commit()
        return visit_id
    except Exception as exc:
        visit = db.query(Visit).filter(Visit.id == visit_id).first()
        if visit:
            visit.status = VisitStatus.failed
            db.commit()
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
    finally:
        db.close()
```

- [ ] **Step 6.5: Create `backend/app/workers/tasks/finalize.py`**

```python
# backend/app/workers/tasks/finalize.py
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Visit, VisitStatus, Job, JobStatus


@celery_app.task
def finalize_visit(visit_id: str) -> None:
    """No-op stub that completes the two-task chain. Sets visit status to ready."""
    db = SessionLocal()
    try:
        visit = db.query(Visit).filter(Visit.id == visit_id).first()
        if visit:
            visit.status = VisitStatus.ready
            db.commit()

        job = db.query(Job).filter(Job.visit_id == visit_id).first()
        if job:
            job.status = JobStatus.done
            db.commit()
    finally:
        db.close()
```

- [ ] **Step 6.6: Create `backend/app/workers/tasks/cleanup.py`**

```python
# backend/app/workers/tasks/cleanup.py
from datetime import datetime, timezone, timedelta
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Visit, VisitStatus


@celery_app.task
def cleanup_orphaned_visits() -> int:
    """Mark visits stuck in pending for >30 minutes as failed."""
    db = SessionLocal()
    try:
        # Use datetime.now(timezone.utc) — NOT datetime.utcnow() (deprecated in 3.12,
    # returns naive datetime which breaks comparison against TIMESTAMPTZ columns)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        orphans = (
            db.query(Visit)
            .filter(Visit.status == VisitStatus.pending, Visit.created_at < cutoff)
            .all()
        )
        for visit in orphans:
            visit.status = VisitStatus.failed
        db.commit()
        return len(orphans)
    finally:
        db.close()
```

- [ ] **Step 6.7: Run all backend tests**

```bash
cd backend && pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6.8: Commit**

```bash
git add backend/app/workers/ backend/tests/test_worker.py backend/tests/test_cleanup.py
git commit -m "feat: add Celery two-task chain stub and orphan cleanup beat task"
```

---

## Chunk 2: Frontend + CI

### Task 7: Frontend scaffold (React + Vite + Tailwind + Clerk)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 7.1: Initialize frontend with Vite**

```bash
cd frontend && npm create vite@latest . -- --template react-ts
npm install
```

- [ ] **Step 7.2: Install dependencies**

```bash
npm install \
  react-router-dom@6 \
  @clerk/clerk-react \
  axios \
  tailwindcss@3 autoprefixer postcss \
  class-variance-authority clsx tailwind-merge \
  lucide-react

npm install -D \
  @types/node \
  vitest @vitest/ui @testing-library/react @testing-library/jest-dom \
  eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin \
  eslint-plugin-react-hooks

npx tailwindcss init -p
npx shadcn@latest init
```

When shadcn prompts: TypeScript=yes, style=Default, base color=Slate, CSS variables=yes, src dir=yes.

- [ ] **Step 7.3: Configure `frontend/tailwind.config.ts`**

```ts
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#1A56A4", dark: "#0F3D7A" },
        success: "#0E7C6E",
        warning: "#B45309",
        danger: "#B91C1C",
        neutral: { 50: "#F9FAFB", 900: "#111827" },
        surface: "#FFFFFF",
        border: "#E5E7EB",
      },
    },
  },
} satisfies Config;
```

- [ ] **Step 7.4: Create `frontend/src/lib/types.ts`**

```ts
// frontend/src/lib/types.ts
export interface User {
  id: string;
  email: string;
  preferred_language: string;
  created_at: string;
}

export interface VisitOut {
  visit_id: string;
  status: "pending" | "processing" | "ready" | "failed";
}

export interface JobOut {
  job_id: string;
  upload_url: string;
  upload_fields: Record<string, string>;
}
```

- [ ] **Step 7.5: Create `frontend/src/lib/api.ts`**

```ts
// frontend/src/lib/api.ts
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

// Injected by ProtectedRoute — updated dynamically
let _getToken: (() => Promise<string | null>) | null = null;

export function setTokenProvider(fn: () => Promise<string | null>) {
  _getToken = fn;
}

api.interceptors.request.use(async (config) => {
  if (_getToken) {
    const token = await _getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 handler — NOT applied to /users/me (handled separately in ProtectedRoute)
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url = error.config?.url ?? "";
    if (error.response?.status === 401 && !url.includes("/users/me")) {
      window.location.href = "/sign-in";
    }
    return Promise.reject(error);
  }
);
```

- [ ] **Step 7.6: Create `frontend/src/components/ProtectedRoute.tsx`**

```tsx
// frontend/src/components/ProtectedRoute.tsx
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { Navigate } from "react-router-dom";
import { api, setTokenProvider } from "@/lib/api";
import type { User } from "@/lib/types";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [checking, setChecking] = useState(true);
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) { setChecking(false); return; }

    setTokenProvider(async () => getToken());

    api.get<User>("/api/v1/users/me")
      .then(() => { setAuthorized(true); setChecking(false); })
      .catch(() => { setAuthorized(false); setChecking(false); });
  }, [isLoaded, isSignedIn, getToken]);

  if (!isLoaded || checking) return <div className="p-8 text-center">Loading…</div>;
  if (!isSignedIn || !authorized) return <Navigate to="/sign-in" replace />;
  return <>{children}</>;
}
```

- [ ] **Step 7.7: Create routes**

```tsx
// frontend/src/routes/Landing.tsx
export function Landing() {
  return (
    <main className="min-h-screen bg-neutral-50 flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold text-primary-dark">ClearNote</h1>
      <p className="text-neutral-900 text-lg max-w-md text-center">
        AI-powered medical visit intelligence. Never forget what your doctor said.
      </p>
      <a href="/sign-up" className="bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-dark">
        Get Started
      </a>
    </main>
  );
}
```

```tsx
// frontend/src/routes/Dashboard.tsx
export function Dashboard() {
  return (
    <main className="min-h-screen bg-neutral-50 p-8">
      <h1 className="text-2xl font-bold text-neutral-900 mb-4">Your Visits</h1>
      <p className="text-neutral-900">No visits yet. Record your first visit.</p>
      <a href="/visits/new" className="mt-4 inline-block bg-primary text-white px-4 py-2 rounded-lg">
        New Visit
      </a>
    </main>
  );
}
```

```tsx
// frontend/src/routes/NewVisit.tsx
export function NewVisit() {
  return (
    <main className="min-h-screen bg-neutral-50 p-8">
      <h1 className="text-2xl font-bold text-neutral-900 mb-4">New Visit</h1>
      <p className="text-neutral-900">Recording setup coming soon.</p>
    </main>
  );
}
```

- [ ] **Step 7.8: Create `frontend/src/App.tsx`**

```tsx
// frontend/src/App.tsx
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { SignIn, SignUp } from "@clerk/clerk-react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Landing } from "@/routes/Landing";
import { Dashboard } from "@/routes/Dashboard";
import { NewVisit } from "@/routes/NewVisit";

const router = createBrowserRouter([
  { path: "/", element: <Landing /> },
  { path: "/sign-in", element: <SignIn routing="path" path="/sign-in" /> },
  { path: "/sign-up", element: <SignUp routing="path" path="/sign-up" /> },
  {
    path: "/dashboard",
    element: <ProtectedRoute><Dashboard /></ProtectedRoute>,
  },
  {
    path: "/visits/new",
    element: <ProtectedRoute><NewVisit /></ProtectedRoute>,
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
```

- [ ] **Step 7.9: Create `frontend/src/main.tsx`**

```tsx
// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { ClerkProvider } from "@clerk/clerk-react";
import App from "./App";
import "./index.css";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
if (!PUBLISHABLE_KEY) throw new Error("Missing VITE_CLERK_PUBLISHABLE_KEY");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
      <App />
    </ClerkProvider>
  </React.StrictMode>
);
```

- [ ] **Step 7.10: Create `frontend/.env.example`**

```
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

- [ ] **Step 7.11: Add vitest config to `vite.config.ts`**

```ts
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: { proxy: { "/api": "http://localhost:8000" } },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

Create `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 7.12: Write and run frontend smoke test**

```ts
// frontend/src/routes/Landing.test.tsx
import { render, screen } from "@testing-library/react";
import { Landing } from "./Landing";

test("landing page renders ClearNote heading", () => {
  render(<Landing />);
  expect(screen.getByText("ClearNote")).toBeInTheDocument();
});
```

```bash
cd frontend && npm run test -- --run
```

Expected: PASS.

- [ ] **Step 7.13: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React frontend with Clerk, routing, ProtectedRoute"
```

---

### Task 8: Audio recording component (TDD)

**Files:**
- Create: `frontend/src/hooks/useRecorder.ts`
- Create: `frontend/src/components/recording/WaveformCanvas.tsx`
- Create: `frontend/src/components/recording/RecordingButton.tsx`
- Create: `frontend/src/components/consent/ConsentModal.tsx`
- Create: `frontend/src/hooks/useRecorder.test.ts`

- [ ] **Step 8.1: Write failing recorder hook test**

```ts
// frontend/src/hooks/useRecorder.test.ts
import { renderHook, act } from "@testing-library/react";
import { useRecorder } from "./useRecorder";

// Mock MediaRecorder
const mockStart = vi.fn();
const mockStop = vi.fn();
const mockPause = vi.fn();
const mockResume = vi.fn();

class MockMediaRecorder {
  state = "inactive";
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  start() { this.state = "recording"; mockStart(); }
  stop() { this.state = "inactive"; mockStop(); this.onstop?.(); }
  pause() { this.state = "paused"; mockPause(); }
  resume() { this.state = "recording"; mockResume(); }
}

vi.stubGlobal("MediaRecorder", MockMediaRecorder);

const mockGetUserMedia = vi.fn().mockResolvedValue({
  getTracks: () => [{ stop: vi.fn() }],
});
Object.defineProperty(navigator, "mediaDevices", {
  value: { getUserMedia: mockGetUserMedia },
});

test("starts in idle state", () => {
  const { result } = renderHook(() => useRecorder());
  expect(result.current.state).toBe("idle");
});

test("transitions to recording on startRecording", async () => {
  const { result } = renderHook(() => useRecorder());
  await act(async () => { await result.current.startRecording(); });
  expect(result.current.state).toBe("recording");
  expect(mockStart).toHaveBeenCalled();
});

test("transitions to stopped and produces blob on stopRecording", async () => {
  const { result } = renderHook(() => useRecorder());
  await act(async () => { await result.current.startRecording(); });
  act(() => { result.current.stopRecording(); });
  expect(result.current.state).toBe("stopped");
});
```

- [ ] **Step 8.2: Implement `frontend/src/hooks/useRecorder.ts`**

```ts
// frontend/src/hooks/useRecorder.ts
import { useState, useRef, useCallback } from "react";

export type RecorderState = "idle" | "recording" | "paused" | "stopped";

export interface RecorderResult {
  state: RecorderState;
  blob: Blob | null;
  elapsedSeconds: number;
  analyserNode: AnalyserNode | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
}

export function useRecorder(): RecorderResult {
  const [state, setState] = useState<RecorderState>("idle");
  const [blob, setBlob] = useState<Blob | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    setAnalyserNode(analyser);

    const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
    mediaRecorderRef.current = recorder;
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
      setBlob(audioBlob);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };

    recorder.start(100);
    setState("recording");
    setElapsedSeconds(0);
    timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
  }, []);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    if (timerRef.current) clearInterval(timerRef.current);
    setState("stopped");
  }, []);

  const pauseRecording = useCallback(() => {
    mediaRecorderRef.current?.pause();
    if (timerRef.current) clearInterval(timerRef.current);
    setState("paused");
  }, []);

  const resumeRecording = useCallback(() => {
    mediaRecorderRef.current?.resume();
    timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    setState("recording");
  }, []);

  return { state, blob, elapsedSeconds, analyserNode, startRecording, stopRecording, pauseRecording, resumeRecording };
}
```

- [ ] **Step 8.3: Create `frontend/src/components/recording/WaveformCanvas.tsx`**

```tsx
// frontend/src/components/recording/WaveformCanvas.tsx
import { useEffect, useRef } from "react";

interface Props { analyserNode: AnalyserNode | null; isActive: boolean; }

export function WaveformCanvas({ analyserNode, isActive }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number | null>(null);

  useEffect(() => {
    if (!analyserNode || !isActive) {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      return;
    }

    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animRef.current = requestAnimationFrame(draw);
      analyserNode.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#F9FAFB";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        ctx.fillStyle = "#1A56A4";
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }
    };
    draw();

    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, [analyserNode, isActive]);

  return <canvas ref={canvasRef} width={300} height={80} className="w-full rounded border border-border" />;
}
```

- [ ] **Step 8.4: Create `frontend/src/components/consent/ConsentModal.tsx`**

```tsx
// frontend/src/components/consent/ConsentModal.tsx
interface Props { open: boolean; onAccept: () => void; onDecline: () => void; }

export function ConsentModal({ open, onAccept, onDecline }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-xl p-6 max-w-md w-full shadow-xl">
        <h2 className="text-xl font-bold text-neutral-900 mb-3">Recording Consent</h2>
        <p className="text-neutral-900 text-sm mb-4">
          This will record audio of your medical visit. The recording is processed by AI
          to generate a summary. Audio is deleted after processing by default.
          You agree that you have consent from all parties being recorded.
        </p>
        <div className="flex gap-3 justify-end">
          <button onClick={onDecline} className="px-4 py-2 border border-border rounded-lg text-neutral-900 hover:bg-neutral-50">
            Cancel
          </button>
          <button onClick={onAccept} className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark">
            I Consent, Start Recording
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 8.5: Create `frontend/src/components/recording/RecordingButton.tsx`**

```tsx
// frontend/src/components/recording/RecordingButton.tsx
import type { RecorderState } from "@/hooks/useRecorder";

interface Props {
  state: RecorderState;
  onStart: () => void;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
}

export function RecordingButton({ state, onStart, onStop, onPause, onResume }: Props) {
  const formatTime = (s: number) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  if (state === "idle") {
    return (
      <button onClick={onStart} className="w-full bg-primary text-white py-4 rounded-xl font-medium text-lg hover:bg-primary-dark">
        Start Recording
      </button>
    );
  }
  if (state === "recording") {
    return (
      <div className="flex gap-3">
        <button onClick={onPause} className="flex-1 border border-border py-3 rounded-xl">Pause</button>
        <button onClick={onStop} className="flex-1 bg-danger text-white py-3 rounded-xl">Stop</button>
      </div>
    );
  }
  if (state === "paused") {
    return (
      <div className="flex gap-3">
        <button onClick={onResume} className="flex-1 bg-primary text-white py-3 rounded-xl">Resume</button>
        <button onClick={onStop} className="flex-1 bg-danger text-white py-3 rounded-xl">Stop</button>
      </div>
    );
  }
  return <div className="text-success font-medium text-center py-3">Recording complete ✓</div>;
}
```

- [ ] **Step 8.6: Run recording tests**

```bash
cd frontend && npm run test -- --run
```

Expected: All tests PASS.

- [ ] **Step 8.7: Commit**

```bash
git add frontend/src/hooks/ frontend/src/components/
git commit -m "feat: add audio recording hook, waveform visualizer, consent modal"
```

---

### Task 9: S3 upload utility + NewVisit flow

**Files:**
- Create: `frontend/src/lib/s3Upload.ts`
- Create: `frontend/src/components/upload/FileUploadZone.tsx`
- Modify: `frontend/src/routes/NewVisit.tsx`
- Create: `frontend/src/lib/s3Upload.test.ts`

- [ ] **Step 9.1: Write failing s3Upload test**

```ts
// frontend/src/lib/s3Upload.test.ts
import { uploadToS3 } from "./s3Upload";

test("appends all upload_fields before file field in FormData", async () => {
  const appendedKeys: string[] = [];
  const mockFormData = {
    append: (key: string) => { appendedKeys.push(key); },
  };
  vi.spyOn(global, "FormData").mockImplementation(() => mockFormData as unknown as FormData);

  const mockXHR = {
    upload: { onprogress: null },
    onload: null as (() => void) | null,
    onerror: null,
    open: vi.fn(),
    send: vi.fn().mockImplementation(function(this: typeof mockXHR) {
      this.onload?.();
    }),
  };
  vi.stubGlobal("XMLHttpRequest", vi.fn(() => mockXHR));

  const fields = { key: "test", policy: "abc", signature: "xyz" };
  await uploadToS3({
    uploadUrl: "https://s3.example.com",
    uploadFields: fields,
    blob: new Blob(["audio"], { type: "audio/webm" }),
    onProgress: vi.fn(),
  });

  // All field keys must appear before "file"
  const fileIndex = appendedKeys.indexOf("file");
  expect(fileIndex).toBeGreaterThan(-1);
  Object.keys(fields).forEach((k) => {
    expect(appendedKeys.indexOf(k)).toBeLessThan(fileIndex);
  });
});
```

- [ ] **Step 9.2: Implement `frontend/src/lib/s3Upload.ts`**

```ts
// frontend/src/lib/s3Upload.ts
export interface S3UploadOptions {
  uploadUrl: string;
  uploadFields: Record<string, string>;
  blob: Blob;
  onProgress?: (pct: number) => void;
}

export interface S3UploadHandle {
  promise: Promise<void>;
  cancel: () => void;
}

export function uploadToS3({ uploadUrl, uploadFields, blob, onProgress }: S3UploadOptions): Promise<void> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();

    // IMPORTANT: All policy fields must precede the file field
    for (const [key, value] of Object.entries(uploadFields)) {
      formData.append(key, value);
    }
    formData.append("file", blob);

    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status === 204 || xhr.status === 200) resolve();
      else reject(new Error(`S3 upload failed: ${xhr.status}`));
    };
    xhr.onerror = () => reject(new Error("S3 upload network error"));
    xhr.open("POST", uploadUrl);
    xhr.send(formData);
  });
}
```

- [ ] **Step 9.3: Create `frontend/src/components/upload/FileUploadZone.tsx`**

```tsx
// frontend/src/components/upload/FileUploadZone.tsx
import { useRef, useState } from "react";

const ALLOWED_EXTENSIONS = ["mp3", "m4a", "wav", "mp4", "webm"];
const MAX_BYTES = 500 * 1024 * 1024;

interface Props { onFile: (file: File) => void; }

export function FileUploadZone({ onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  const validate = (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported format. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return false;
    }
    if (file.size > MAX_BYTES) {
      setError("File exceeds 500MB limit.");
      return false;
    }
    setError(null);
    return true;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validate(file)) onFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && validate(file)) onFile(file);
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-primary"
      onClick={() => inputRef.current?.click()}
    >
      <input ref={inputRef} type="file" accept=".mp3,.m4a,.wav,.mp4,.webm" className="hidden" onChange={handleChange} />
      <p className="text-neutral-900">Drag and drop an audio file, or click to browse</p>
      <p className="text-sm text-neutral-900 mt-1">MP3, M4A, WAV, MP4, WebM — max 500MB</p>
      {error && <p className="text-danger text-sm mt-2">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 9.4: Update `frontend/src/routes/NewVisit.tsx` with full recording flow**

```tsx
// frontend/src/routes/NewVisit.tsx
import { useState } from "react";
import { useRecorder } from "@/hooks/useRecorder";
import { RecordingButton } from "@/components/recording/RecordingButton";
import { WaveformCanvas } from "@/components/recording/WaveformCanvas";
import { ConsentModal } from "@/components/consent/ConsentModal";
import { FileUploadZone } from "@/components/upload/FileUploadZone";
import { uploadToS3 } from "@/lib/s3Upload";
import { api } from "@/lib/api";
import type { VisitOut, JobOut } from "@/lib/types";

type Step = "form" | "record" | "upload-progress" | "done";

export function NewVisit() {
  const [step, setStep] = useState<Step>("form");
  const [showConsent, setShowConsent] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [title, setTitle] = useState("");
  const [visitDate, setVisitDate] = useState(new Date().toISOString().slice(0, 10));
  const [doctorName, setDoctorName] = useState("");
  const [consentAt, setConsentAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recorder = useRecorder();

  const handleConsentAccept = async () => {
    const ts = new Date().toISOString();
    setConsentAt(ts);
    setShowConsent(false);
    await recorder.startRecording();
    setStep("record");
  };

  const handleStopAndUpload = async () => {
    recorder.stopRecording();
    if (!recorder.blob) return;
    await submitAudio(recorder.blob);
  };

  const submitAudio = async (blob: Blob) => {
    setStep("upload-progress");
    try {
      const visitResp = await api.post<VisitOut>("/api/v1/visits", {
        title,
        visit_date: visitDate,
        doctor_name: doctorName || undefined,
        consent_at: consentAt ?? new Date().toISOString(),
      });

      const jobResp = await api.post<JobOut>("/api/v1/jobs/transcribe", {
        visit_id: visitResp.data.visit_id,
      });

      await uploadToS3({
        uploadUrl: jobResp.data.upload_url,
        uploadFields: jobResp.data.upload_fields,
        blob,
        onProgress: setUploadProgress,
      });

      await api.post(`/api/v1/jobs/${jobResp.data.job_id}/confirm`);
      setStep("done");
    } catch (e) {
      setError("Upload failed. Please try again.");
      setStep("form");
    }
  };

  if (step === "done") {
    return (
      <main className="min-h-screen bg-neutral-50 p-8 flex flex-col items-center justify-center">
        <div className="text-success text-5xl mb-4">✓</div>
        <h2 className="text-2xl font-bold text-neutral-900">Visit submitted!</h2>
        <p className="text-neutral-900 mt-2">Your recording is being processed.</p>
        <a href="/dashboard" className="mt-4 bg-primary text-white px-6 py-2 rounded-lg">Back to Dashboard</a>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-neutral-50 p-8 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-neutral-900 mb-6">New Visit</h1>

      <ConsentModal
        open={showConsent}
        onAccept={handleConsentAccept}
        onDecline={() => setShowConsent(false)}
      />

      {step === "form" && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-900 mb-1">Visit Title *</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)}
              placeholder="Dr. Smith - Cardiology"
              className="w-full border border-border rounded-lg px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-900 mb-1">Visit Date *</label>
            <input type="date" value={visitDate} onChange={(e) => setVisitDate(e.target.value)}
              className="w-full border border-border rounded-lg px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-900 mb-1">Doctor Name</label>
            <input value={doctorName} onChange={(e) => setDoctorName(e.target.value)}
              placeholder="Optional"
              className="w-full border border-border rounded-lg px-3 py-2" />
          </div>

          {error && <p className="text-danger text-sm">{error}</p>}

          <div className="pt-4 space-y-3">
            <button
              onClick={() => { if (title) setShowConsent(true); }}
              disabled={!title}
              className="w-full bg-primary text-white py-3 rounded-xl font-medium disabled:opacity-50"
            >
              Record Visit
            </button>
            <p className="text-center text-neutral-900 text-sm">or upload an existing file</p>
            <FileUploadZone onFile={async (file) => {
              setConsentAt(new Date().toISOString());
              await submitAudio(file);
            }} />
          </div>
        </div>
      )}

      {step === "record" && (
        <div className="space-y-4">
          <WaveformCanvas analyserNode={recorder.analyserNode} isActive={recorder.state === "recording"} />
          <p className="text-center text-2xl font-mono text-neutral-900">
            {String(Math.floor(recorder.elapsedSeconds / 60)).padStart(2, "0")}:
            {String(recorder.elapsedSeconds % 60).padStart(2, "0")}
          </p>
          <RecordingButton
            state={recorder.state}
            onStart={() => setShowConsent(true)}
            onStop={handleStopAndUpload}
            onPause={recorder.pauseRecording}
            onResume={recorder.resumeRecording}
          />
        </div>
      )}

      {step === "upload-progress" && (
        <div className="space-y-4">
          <p className="text-neutral-900 font-medium">Uploading…</p>
          <div className="w-full bg-neutral-50 rounded-full h-3 border border-border">
            <div className="bg-primary h-3 rounded-full transition-all" style={{ width: `${uploadProgress}%` }} />
          </div>
          <p className="text-center text-neutral-900">{uploadProgress}%</p>
        </div>
      )}
    </main>
  );
}
```

- [ ] **Step 9.5: Run all frontend tests**

```bash
cd frontend && npm run test -- --run
```

Expected: All tests PASS.

- [ ] **Step 9.6: Commit**

```bash
git add frontend/src/lib/s3Upload.ts frontend/src/lib/s3Upload.test.ts \
  frontend/src/components/upload/ frontend/src/routes/NewVisit.tsx
git commit -m "feat: add S3 presigned POST upload utility and full NewVisit flow"
```

---

### Task 10: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 10.1: Create `.github/workflows/ci.yml`**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: clearnote_test
          POSTGRES_USER: clearnote
          POSTGRES_PASSWORD: clearnote
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - name: Install dependencies
        run: cd backend && pip install -e ".[dev]"
      - name: Lint (ruff)
        run: cd backend && ruff check app/ tests/
      - name: Type check (mypy)
        run: cd backend && mypy app/
      - name: Test (pytest)
        env:
          DATABASE_URL: postgresql://clearnote:clearnote@localhost:5432/clearnote_test
          REDIS_URL: redis://localhost:6379/0
          CLERK_JWKS_URL: ""
          AWS_ACCESS_KEY_ID: ""
          AWS_SECRET_ACCESS_KEY: ""
          S3_BUCKET_NAME: test-bucket
          CORS_ORIGINS: http://localhost:5173
        run: cd backend && pytest tests/ -v --tb=short

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Lint (eslint)
        run: cd frontend && npx eslint src/ --ext .ts,.tsx
      - name: Type check (tsc)
        run: cd frontend && npx tsc --noEmit
      - name: Test (vitest)
        run: cd frontend && npm run test -- --run
```

- [ ] **Step 10.2: Verify CI locally**

```bash
# Backend
cd backend && ruff check app/ && mypy app/ && pytest tests/ -v

# Frontend
cd frontend && npx eslint src/ --ext .ts,.tsx && npx tsc --noEmit && npm run test -- --run
```

Expected: All checks pass.

- [ ] **Step 10.3: Commit and push**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflow for backend and frontend"
git push
```

Verify the Actions tab on GitHub shows green.

---

## Final Verification

- [ ] Run `docker compose up` and verify all 5 services start
- [ ] `curl localhost:8000/health` returns `{"status":"ok","version":"0.1.0"}`
- [ ] Run `alembic upgrade head` — no errors, 5 tables visible in psql
- [ ] Open `http://localhost:5173` — Landing page renders
- [ ] Navigate to `/dashboard` while signed out — redirects to `/sign-in`
- [ ] Register a Clerk account, sign in — lands on Dashboard
- [ ] Navigate to `/visits/new` — form renders, consent modal appears on "Record Visit"

---

## Acceptance Criteria Checklist

| ID | Criterion | Verified |
|---|---|---|
| S1-1 | `GET /health` → 200 `{"status":"ok"}` | [ ] |
| S1-2 | `alembic upgrade head` creates 5 tables + 3 ENUMs | [ ] |
| S1-3 | Invalid JWT → 401; valid JWT → 200 user object | [ ] |
| S1-4 | `/` renders; `/dashboard` redirects unauthenticated | [ ] |
| S1-5 | `docker compose up` → 5 services; `/health` 200 | [ ] |
| S1-6 | GitHub Actions passes on push to main | [ ] |
| S2-1 | Register/verify/login/logout flow works | [ ] |
| S2-2 | Browser records WebM; waveform animates; timer counts; playback works | [ ] |
| S2-3 | Consent modal appears; `visits.consent_at` stored | [ ] |
| S2-4 | 100MB file uploads to S3; progress shows; object exists | [ ] |
| S2-5 | `POST /visits` → pending; `POST /jobs/transcribe` → job_id + upload_fields | [ ] |
| S2-6 | After `/confirm`, worker: pending→processing→ready in ≤10s (happy path) | [ ] |
| S2-7 | PNG file upload → `/confirm` returns 422 | [ ] |
| S2-8 | Second `/confirm` → 200, no duplicate Celery task | [ ] |
| S2-9 | Visit backdated 31min → marked failed after beat cycle | [ ] |
