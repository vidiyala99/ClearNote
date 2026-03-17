# ClearNote — Phase 2: AI Inference & Streaming

**Date:** 2026-03-17
**Phase:** 2 of 4
**Status:** Draft

---

## 1. Overview

Phase 2 moves ClearNote from a static scaffold to a fully functional AI application. We replace the stub Celery tasks with real Speech-to-Text (Whisper API / Gemini) and LLM-driven medical summarization, and add a WebSocket layer for real-time status updates in the dashboard views.

By end of Phase 2, a user can:
1. Record audio that uploads to S3
2. View real-time "Processing..." state transitions on the dashboard
3. Read an AI-generated clinical transcript and summary upon completion

---

## 2. Architecture & Components

### 2.1 AI Pipeline (Celery Worker)
- **Task 1: `transcribe_audio(visit_id)`**
  - Download audio from S3 via `boto3.download_file()`
  - Send audio to OpenAI Whisper API (or local FastAPI GPU-host if applicable)
  - Write standard string back to `transcripts` table with `chunks` JSONB timestamps.
- **Task 2: `summarize_visit(visit_id)`**
  - Read `raw_text` from transcription output
  - Prompt an LLM (OpenAI Gpt-4o / Google Gemini-1.5-Pro) with structured system guidelines to parse SOAP Notes, Medications, and Action Items.
  - Write output triggers to `summaries` table.

### 2.2 WebSocket Streaming (Real-time update)
- **API `/ws/notifications/{user_id}`**:
  - Maintain absolute connected clients list inside FastAPI app state using `ConnectionManager`.
  - When Celery worker finishes a job, broadcast a `{"visit_id": UUID, "status": "ready"}` payload directly to the connected client.
- **Frontend listener**:
  - Connect to WebSocket server on `<Dashboard />` mount.
  - Trigger refreshes or state sets when any status broadcast matches visual keys.

---

## 3. Implementation Checklist

### Chunk 1: AI Integration (Backend)

- [ ] **Task 11: Setup OpenAI / Gemini client services**
  - Create `backend/app/services/ai.py` incorporating Whisper-1 structure and Completion APIs structure payloads.
- [ ] **Task 12: Update `transcribe_audio` worker**
  - Fetch audio ➝ transcribe via AI service ➝ upserts transcript row.
- [ ] **Task 13: Create `summarize_visit` worker**
  - Read transcript ➝ structure prompt ➝ upsert summary row ➝ trigger completion status updates correctly.

### Chunk 2: Real-time Streams (WebSockets)

- [ ] **Task 14: FastAPI WebSocket implementation**
  - Create `backend/app/api/v1/websocket.py` with ConnectionManager setup binding `request.state.clerk_user_id` on connect.
- [ ] **Task 15: Broadcast triggers during worker completion**
  - Issue Redis `PUBLISH` inside workers layout ➝ Read inside WebSocket streams to fire event triggers asynchronously.

### Chunk 3: Frontend Polishes

- [ ] **Task 16: Setup `useWebSocket` hook in React**
  - Listening and invalidating lists triggers on receiving `"ready"` states.
- [ ] **Task 17: Layout detail visuals**
  - Expand visit detail pages rendering transcript and summary lists correctly inside beautiful interface grids.

---

## 4. Acceptance Criteria

| ID | Story |
|---|---|
| S2-1 | **Real Translation**: Uploading a 20s recording saves accurate English transcript strings in `transcripts` table. |
| S2-2 | **Real Summary**: LLM generates valid JSON lists for Medications lists is fully bound inside `summaries`. |
| S2-3 | **Auto Refresh**: Background tasks completion instantly triggers green "Ready" state loads in dashboard grid without manual reload. |
| S2-4 | **Failure handling**: Invalid API Keys or missing Audio S3 files report `failed` without crashing workers state loops. |
