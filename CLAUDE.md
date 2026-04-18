# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (from `backend/`)
```bash
pip install -e .[dev]                              # install with dev deps
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info

pytest                                             # all tests (requires Postgres)
pytest tests/test_visits.py                        # single file
ruff check .                                       # lint
mypy app/                                          # type check
```

### Frontend (from `frontend/`)
```bash
npm install
npm run dev       # http://localhost:5173
npm run test      # vitest run (all)
npx vitest run src/routes/Dashboard.test.tsx       # single file
npm run build     # tsc + vite build
```

### Infrastructure
```bash
docker compose up -d postgres redis   # start only deps
docker compose up --build             # full stack in Docker
```

## Architecture

### Request flow
1. Clerk JWT middleware (`app/middleware/clerk_auth.py`) validates every request except `/health`, `/docs`, `/openapi.json`, `/redoc`. It injects `request.state.clerk_user_id` and `request.state.email`.
2. API handlers in `app/api/v1/` read `request.state.clerk_user_id` to resolve the `User` row; there is no separate auth dependency — each handler does its own lookup.
3. Vite proxies `/api/*` to `localhost:8000` in development (`vite.config.ts`).

### Visit processing pipeline
Visits move through a status state machine (`pending → processing → ready/failed`):
1. `POST /visits` creates a `Visit` with `status=pending` and enqueues a Celery chain.
2. Workers in `app/workers/tasks/` run in order: `transcribe` → `summarize` → `finalize`.
3. Status updates are pushed via Redis pub/sub; the `WebSocketManager` in `app/api/v1/websocket.py` subscribes and forwards to connected clients.
4. A beat task (`cleanup_orphans`, every 15 min) handles stuck/orphaned jobs.

### Frontend auth + guest preview
`ProtectedRoute` wraps authenticated routes. `/dashboard` is wrapped with `allowGuestPreview=true`, which lets unauthenticated users see demo data. All other protected routes redirect to `/sign-in`.

### DB models
`app/db/models/`: `User`, `Visit`, `Job`, `Transcript`, `Summary`. Alembic manages migrations (`alembic/`). The `Visit` model has a `visit_status` enum; `Job` has a `job_status` enum; `Summary` has an `urgency_tag` enum — all are Postgres-native enums, so new values require a migration.

### Backend test setup
`tests/conftest.py` uses `pytest-postgresql`. Tests run against a real Postgres instance using transactional savepoints (each test rolls back). The `worker_sessionlocal` fixture patches `SessionLocal` inside Celery task modules so worker code runs inside the same transactional session. The `client` fixture overrides `get_db` with the same session.

On Windows, if `pg_ctl` is not on PATH, tests fall back to an external Postgres at `localhost:5432` (credentials: `clearnote/clearnote`, db: `clearnote_test`).

## Environment

`backend/app/config.py` loads the root `.env` (not `backend/.env`). Required variables: `DATABASE_URL`, `REDIS_URL`, `CLERK_JWKS_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `AWS_REGION`, `CORS_ORIGINS`, `OPENAI_API_KEY`. Copy `.env.example` to `.env` to start.

Frontend uses `VITE_CLERK_PUBLISHABLE_KEY`; defaults to `"pk_test_sample"` if unset (allows local dev without Clerk).
