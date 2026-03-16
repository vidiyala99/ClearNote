# ClearNote — Phase 1 Foundation Design Spec

**Date:** 2026-03-14
**Phase:** 1 of 4 (Sprints 1–2)
**Status:** Approved

---

## 1. Overview

Phase 1 establishes the full-stack scaffold for ClearNote: a monorepo with a FastAPI backend and React/TypeScript frontend, wired together via Docker Compose locally, with CI enforcing lint, type-check, and tests on every push.

By end of Sprint 2, a user can: register, log in, record or upload audio, consent to recording, trigger an upload to S3, and see a job queued (stub pipeline returns mock transcript). No real AI inference — that is Phase 2.

---

## 2. Repository Layout

```
clearnote/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/        # users, visits, jobs, transcripts, summaries
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       ├── auth.py
│   │   │       ├── visits.py
│   │   │       └── jobs.py
│   │   ├── middleware/
│   │   │   └── clerk_auth.py
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks/
│   │   │       ├── transcribe.py
│   │   │       └── finalize.py  # no-op stub, establishes chain
│   │   └── schemas/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml          # includes pytest-postgresql config
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── routes/
│   │   │   ├── Landing.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── NewVisit.tsx
│   │   ├── components/
│   │   │   ├── recording/
│   │   │   │   ├── RecordingButton.tsx
│   │   │   │   └── WaveformCanvas.tsx
│   │   │   ├── upload/
│   │   │   │   └── FileUploadZone.tsx
│   │   │   └── ui/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── s3Upload.ts
│   │   └── hooks/
│   │       └── useRecorder.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── package.json
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## 3. Backend Design

### 3.1 FastAPI App

- Python 3.12, FastAPI, Uvicorn
- `pydantic-settings` for all config
- CORS: `CORSMiddleware` with `CORS_ORIGINS` env var as a **comma-separated string** (e.g., `http://localhost:5173,https://app.clearnote.io`), parsed to a list in `config.py`. Registered in `main.py` before any route.
- SQLAlchemy in **sync mode** (`sessionmaker`, `psycopg2` driver). FastAPI endpoints use `Depends(get_db)`. Celery workers use the same sync `SessionLocal`. No async DB complexity.
- `GET /health` → `{"status": "ok", "version": "0.1.0"}`
- All routes under `/api/v1/`

### 3.2 Database Models (5 tables)

**users**
| Column | Type |
|---|---|
| id | UUID PK |
| email | VARCHAR(255) UNIQUE NOT NULL |
| clerk_user_id | VARCHAR(100) UNIQUE NOT NULL |
| preferred_language | VARCHAR(10) DEFAULT 'en' |
| created_at | TIMESTAMPTZ DEFAULT now() |
| deleted_at | TIMESTAMPTZ nullable |

**visits**
| Column | Type |
|---|---|
| id | UUID PK |
| user_id | UUID FK → users.id CASCADE |
| title | VARCHAR(200) NOT NULL |
| visit_date | DATE NOT NULL |
| doctor_name | VARCHAR(200) nullable |
| status | ENUM('pending','processing','ready','failed') DEFAULT 'pending' |
| audio_s3_key | VARCHAR(500) nullable |
| tags | TEXT[] DEFAULT '{}' |
| consent_at | TIMESTAMPTZ NOT NULL |
| created_at / updated_at | TIMESTAMPTZ |

**jobs**
| Column | Type |
|---|---|
| id | UUID PK |
| visit_id | UUID FK → visits.id CASCADE, UNIQUE |
| s3_key | VARCHAR(500) NOT NULL — set at job creation, before upload |
| status | ENUM('queued','processing','done','failed') DEFAULT 'queued' |
| celery_task_id | VARCHAR(255) nullable — set after enqueue |
| created_at | TIMESTAMPTZ |

`jobs.s3_key` is written at `POST /jobs/transcribe` time (deterministic path: `visits/{visit_id}/audio`). The confirm handler reads `jobs.s3_key` to perform the magic bytes check.

**transcripts**
| Column | Type |
|---|---|
| id | UUID PK |
| visit_id | UUID FK → visits.id CASCADE, UNIQUE |
| raw_text | TEXT NOT NULL |
| chunks | JSONB DEFAULT '[]' |
| language_detected | VARCHAR(10) DEFAULT 'en' |
| wer_confidence | FLOAT nullable |

**summaries**
| Column | Type |
|---|---|
| id | UUID PK |
| visit_id | UUID FK → visits.id, UNIQUE |
| overview | TEXT nullable |
| medications | JSONB DEFAULT '[]' |
| diagnoses | JSONB DEFAULT '[]' |
| action_items | JSONB DEFAULT '[]' |
| urgency_tag | ENUM('normal','follow-up','referral','prescription','urgent') DEFAULT 'normal' |
| translated_overview | TEXT nullable |

Alembic initial migration creates all 5 tables and 3 ENUMs (`visit_status`, `job_status`, `urgency_tag`).

**Test suite:** Uses `pytest-postgresql` in **noproc mode** (`postgresql_noproc` fixture) pointing at the GHA service container via `--postgresql-host=localhost`. No separate `pg_ctl` process. Configured in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "--postgresql-host=localhost --postgresql-port=5432 --postgresql-user=clearnote --postgresql-password=clearnote --postgresql-dbname=clearnote_test"
```

### 3.3 Clerk Auth Middleware

- On startup: fetch JWKS from `CLERK_JWKS_URL` env var
- Per request: extract `Authorization: Bearer`, decode RS256 JWT, inject `clerk_user_id` from `sub` into `request.state`
- 401 → `{"error": {"code": "UNAUTHORIZED"}}`

**`GET /api/v1/users/me`:**
- INSERT ... ON CONFLICT (clerk_user_id) DO UPDATE SET email = EXCLUDED.email — idempotent upsert
- The frontend `ProtectedRoute` wrapper calls this endpoint on mount using the raw Clerk token, with its **own** try/catch. If it returns 401, `ProtectedRoute` redirects to `/sign-in` directly (not via the global interceptor). This closes the gap where the global interceptor is suppressed for this endpoint.

### 3.4 Visit Lifecycle & S3 Upload

**Sequence:**
1. `POST /api/v1/visits` `{title, visit_date, doctor_name, consent_at}` → creates visit (`status=pending`), returns `{visit_id}`
2. `POST /api/v1/jobs/transcribe` `{visit_id}` → backend:
   - Computes deterministic S3 key: `visits/{visit_id}/audio`
   - Creates job row (`jobs.s3_key = computed_key`, `jobs.status = 'queued'`)
   - Generates **S3 presigned POST** (not PUT) with policy: `content-type` starts with `audio/`, `content-length-range 1 524288000`
   - Returns `{job_id, upload_url, upload_fields: Record<string, string>}`
   - `upload_fields` is the verbatim dict from `boto3.generate_presigned_post()` (e.g., `key`, `AWSAccessKeyId`, `x-amz-security-token`, `policy`, `x-amz-signature`). Frontend appends all fields before the `file` field — order matters for AWS S3 presigned POST.
3. Frontend submits multipart/form-data POST to `upload_url` with all `upload_fields` appended first, then the audio blob as `file`. Progress tracked via XHR `upload.onprogress`.
4. `POST /api/v1/jobs/{job_id}/confirm` (no body required — backend reads `jobs.s3_key`):
   - **Key mismatch check (first):** if `jobs.audio_s3_key` is set and differs from `jobs.s3_key` (shouldn't happen in normal flow), return 409 `{"error": {"code": "JOB_ALREADY_CONFIRMED"}}`
   - **Idempotency check (second):** if `visits.status` is already `processing` or `ready`, return 200 immediately — no re-enqueue
   - **Magic bytes check:** S3 range GET of first 12 bytes from `jobs.s3_key` (timeout 5s). If S3 unreachable → 503. If bytes don't match WebM / MP3 / M4A / WAV / MP4 magic → 422.
   - On success: update `visits.audio_s3_key = jobs.s3_key`, enqueue Celery chain, update `jobs.celery_task_id`, return `{status: "queued"}`
5. Celery worker executes (Phase 1 stub)

**Orphan cleanup:** Celery beat task every 15 min. Query: `SELECT * FROM visits WHERE status='pending' AND created_at < (datetime.utcnow() - timedelta(minutes=30))` — uses Python-side `datetime.utcnow()` (not `func.now()`) so `freezegun` can intercept it in tests. Sets `status='failed'`, queues S3 key deletion. Test: insert a visit with `created_at` backdated 31 minutes in the fixture (no mocking needed).

**Frontend upload validation:** extension in {mp3, m4a, wav, mp4, webm} and size ≤500MB checked client-side before `POST /jobs/transcribe`.

### 3.5 Celery Worker (Two-Task Chain)

Celery chain: `chain(transcribe_audio.s(visit_id), finalize_visit.s())` — two tasks from day 1, establishing the Phase 2 wiring.

**`transcribe_audio(visit_id)`:**
1. Set `visit.status = 'processing'`
2. Sleep 3 seconds
3. Upsert transcript (INSERT ... ON CONFLICT visit_id DO UPDATE raw_text, chunks) — idempotent
4. Returns `visit_id` (passed to next task in chain)
- Dev/test retry: no automatic retry in dev (controlled by `CELERY_TASK_ALWAYS_EAGER=True` in tests). Production retry: 3x, backoff 30/90/270s — this config is for Phase 2's real tasks; the stub inherits it but won't fail in normal conditions.

**`finalize_visit(visit_id)`:** (no-op stub)
1. Set `visit.status = 'ready'`
2. Set `jobs.status = 'done'`
- No retry needed for stub.

---

## 4. Frontend Design

### 4.1 Stack

- React 18 + TypeScript + Vite
- Tailwind CSS with design tokens: `primary: #1A56A4`, `primary-dark: #0F3D7A`, `success: #0E7C6E`, `warning: #B45309`, `danger: #B91C1C`, `neutral-50: #F9FAFB`, `neutral-900: #111827`
- shadcn/ui (Button, Card, Badge, Modal, Toast, Progress)
- react-router-dom v6
- Clerk React SDK (`<ClerkProvider>`)

### 4.2 Routes

| Path | Component | Auth |
|---|---|---|
| `/` | Landing | Public |
| `/sign-in` | Clerk `<SignIn>` | Public |
| `/sign-up` | Clerk `<SignUp>` | Public |
| `/dashboard` | Dashboard | Protected |
| `/visits/new` | NewVisit | Protected |

`<ProtectedRoute>` calls `/users/me` on mount, catches 401, redirects to `/sign-in`. Global 401 interceptor applies to all other endpoints only.

### 4.3 Recording Component

- `useRecorder` hook: MediaRecorder (WebM/Opus), state machine `idle → recording → paused → stopped`, AnalyserNode wired to WaveformCanvas
- `WaveformCanvas`: canvas + requestAnimationFrame + frequency bar graph
- Timer: `MM:SS` via setInterval
- Consent modal shown before `startRecording()`; `consent_at` timestamp sent in `POST /visits`

### 4.4 S3 Upload (`s3Upload.ts`)

- Takes `{upload_url, upload_fields, blob}` — **appends all `upload_fields` before the `file` field** in FormData (order required by AWS)
- XHR for progress events: exposes `{progress: number, cancel: () => void, promise: Promise<void>}`
- On success (S3 204): calls `POST /jobs/{job_id}/confirm`
- On error/cancel: toast notification; visit stays `pending` (beat task cleans up)

### 4.5 API Client

- `axios` instance, `VITE_API_URL` base
- Request interceptor: `Authorization: Bearer` from Clerk
- Response interceptor: 401 → `/sign-in` redirect (suppressed for `/users/me`)

---

## 5. Docker Compose (Local Dev)

Services: `api` (uvicorn :8000), `worker` (celery worker), `beat` (celery beat), `postgres` (16-alpine :5432), `redis` (7-alpine :6379). Single `backend/Dockerfile`, different `CMD`. `.env` file (not committed) contains: `DATABASE_URL`, `REDIS_URL`, `CLERK_JWKS_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `CORS_ORIGINS`.

---

## 6. CI (GitHub Actions)

**Backend job:**
1. Postgres 16 service container (host: `localhost`, port: `5432`, db: `clearnote_test`)
2. `ruff check`
3. `mypy app/`
4. `pytest tests/` — uses `postgresql_noproc` fixture pointing at service container (no port conflict with managed `pg_ctl`)

**Frontend job:**
1. `eslint src/`
2. `tsc --noEmit`
3. `vitest run`

Both must pass.

---

## 7. Acceptance Criteria

| ID | Story | Criterion |
|---|---|---|
| S1-1 | Health endpoint | `GET /health` → HTTP 200, `{"status": "ok"}` |
| S1-2 | DB migrations | `alembic upgrade head` on fresh Postgres creates 5 tables + 3 ENUMs, no error |
| S1-3 | Clerk auth | Missing/invalid JWT → 401; valid JWT → 200 with `{id, email, preferred_language}` |
| S1-4 | Frontend scaffold | `/` renders Landing; `/dashboard` renders Dashboard or redirects unauthenticated users |
| S1-5 | Docker Compose | `docker compose up` starts 5 services; `curl localhost:8000/health` → 200 |
| S1-6 | CI | GitHub Actions passes (lint + typecheck + tests) on push to main |
| S2-1 | Auth flow | User registers, verifies email, logs in → redirected to `/dashboard`; logout → `/` |
| S2-2 | Recording | Browser records WebM blob; waveform animates; timer increments; playback works |
| S2-3 | Consent | Consent modal appears before recording; `visits.consent_at` set in DB |
| S2-4 | S3 upload | 100MB WebM uploaded to S3 via presigned POST; progress bar updates; S3 object exists |
| S2-5 | Job creation | `POST /visits` → visit with `status=pending`; `POST /jobs/transcribe` → `{job_id, upload_url, upload_fields}` |
| S2-6 | Worker (happy path) | After `POST /confirm` (no exceptions), visit transitions `pending→processing→ready` within 10s; transcript row with non-empty `raw_text` created |
| S2-7 | Magic bytes rejection | `POST /confirm` after uploading a PNG file returns 422 |
| S2-8 | Confirm idempotency | Second `POST /confirm` on same job returns 200 without creating duplicate Celery task |
| S2-9 | Orphan cleanup | Visit with `created_at` backdated 31 min and `status=pending` is marked `failed` after beat task runs |

---

## 8. Out of Scope for Phase 1

- Real AI inference (Phase 2)
- WebSocket job status streaming (Phase 2)
- Visit detail / summary / transcript / Q&A UI (Phase 3)
- PDF generation, sharing (Phase 3)
- Rate limiting, Sentry, PostHog, production deploy (Phase 4)
- HIPAA BAA, EHR integration, native apps (v2/v3 roadmap)
