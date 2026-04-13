# VidShield AI — Product Requirements (As Implemented)

This document describes **what the repository implements today**, derived from the FastAPI backend, Next.js frontend, workers, and database migrations. It is not a future roadmap.

---

## 1. Product summary

**VidShield AI** is a web-backed platform for **recorded video management**, **AI-assisted moderation**, **live stream monitoring**, **analytics**, **policies**, **webhooks**, **operator notifications**, **PDF/report generation**, **billing (Stripe)**, and **admin observability** (access audit, moderation audit, agent audit, support tickets).

Primary personas:

| Persona | Capabilities in code |
|--------|-------------------------|
| **End user / operator** (`operator`, `api_consumer`) | Dashboard: videos, upload/presign flows, moderation queue & review, policies, live streams, analytics, reports, billing, profile, API keys (CRUD), notifications |
| **Administrator** (`admin`) | All operator capabilities plus user CRUD, audit logs, agent audit log, support ticket management, admin billing metrics, ad-hoc notification dispatch |
| **Anonymous visitor** | Register, login, password reset, newsletter signup, public support ticket submission |

---

## 2. Technology stack (verified)

| Layer | Implementation |
|-------|----------------|
| **Backend** | Python 3.12, FastAPI 0.115, Uvicorn, Pydantic v2, SQLAlchemy 2.0, Alembic |
| **Auth** | JWT access + refresh (`python-jose`), bcrypt passwords |
| **Database** | PostgreSQL 16 (asyncpg + psycopg2 for migrations/workers) |
| **Cache / broker** | Redis 7; Celery 5.4 with JSON serialization |
| **AI** | OpenAI SDK, LangChain 0.2.x, LangGraph 0.2.x; configurable `OPENAI_MODEL` / `OPENAI_MINI_MODEL` (defaults `gpt-4o` / `gpt-4o-mini`) |
| **Vector search** | Pinecone client (`PINECONE_API_KEY`, `PINECONE_INDEX`) |
| **Storage** | AWS S3 via boto3 (`S3_BUCKET_NAME`, presigned URLs) |
| **Video / media** | FFmpeg (container), OpenCV headless, `yt-dlp` for URL-based ingestion |
| **Realtime** | `python-socketio` ASGI wrapper around FastAPI (`app.main:asgi_app`); native FastAPI WebSocket on `/api/v1/live/ws/streams/{stream_id}` |
| **Email / WhatsApp** | SendGrid (`sendgrid`), Twilio (`twilio`) |
| **Payments** | Stripe (`stripe`) + webhook route |
| **PDF** | ReportLab for report artifacts |
| **Frontend** | Next.js 14.2 (App Router), React 18, Tailwind, Radix UI, TanStack Query, Zustand, Socket.IO client, Axios |
| **Observability** | `structlog`; optional `SENTRY_DSN` |

---

## 3. Implemented feature areas

### 3.1 Authentication & session

- User registration and login with JWT pair (access typed `access`, refresh typed `refresh`).
- Token refresh and logout (refresh token invalidation via Redis key pattern in auth service).
- Forgot password + reset password with `password_reset_tokens` and rate limiting config (`PASSWORD_RESET_RATE_LIMIT`).
- `/api/v1/auth/me` returns current user.
- **Access audit**: login/logout attempts persisted to `access_audit_logs` (IP, user-agent, status).

### 3.2 User profile & RBAC

- Roles: `admin`, `operator`, `api_consumer` (`UserRole` enum).
- Self-service: change password, update profile including address fields and WhatsApp number.
- Admin: list/create/update/delete users; block users (`is_blocked`, `blocked_at`, `blocked_reason`).

### 3.3 Videos

- Paginated list with filters; create video records; get/update/delete single video.
- **Presigned upload URL** generation; **URL analysis** (`/videos/analyze-url`); **duplicate check**; **bulk delete**.
- Status polling endpoint `GET /videos/{id}/status`.
- Storage integration for playback/thumbnail presigned URLs when S3 is configured.

### 3.4 Moderation

- Queue listing with filters; per-video moderation result fetch.
- Human review submission and admin override endpoints.
- Clear queue / delete queue item (operator-scoped routes per `moderation.py`).

### 3.5 Policies

- CRUD-style API: list, create, get, update, delete, toggle active state.
- JSON `rules` and string `default_action` on `policies` table.

### 3.6 Live streams & alerts

- CRUD-style stream lifecycle: list/create/get/stop stream.
- Start/stop **live moderation**; ingest frames (`POST .../frames`).
- List stream alerts; create alerts; dismiss single / dismiss all.
- WebSocket for stream channel (path under `/api/v1/live/...`).

### 3.7 Analytics

- Summary, violations breakdown, export-style read endpoint (see `analytics.py`).

### 3.8 Webhooks (outbound)

- Register/list/get/update/delete webhook endpoints; test delivery.

### 3.9 API keys (developer surface)

- Authenticated users can list, create (returns raw key once), rename, revoke API keys.
- **Note:** Keys are persisted as SHA-256 hashes; **no request-path API key authentication dependency** was found in `app/api/deps.py` — partner auth in practice is JWT Bearer as implemented.

### 3.10 Reports

- Preview and async **generate** report jobs (Celery `reports` queue).
- List jobs, templates CRUD, download, delete job.

### 3.11 Billing & newsletter

- Stripe checkout, portal, subscription read, payments list, invoice fetch, sync helpers.
- Stripe webhook: `POST /api/v1/billing/webhook` (signature verified; hidden from OpenAPI).
- Newsletter email signup table + route.
- Admin billing metrics: revenue and subscribers.

### 3.12 Support

- Public ticket creation; admin list/update.

### 3.13 Notifications

- In-app list, mark read, read-all, delete.
- Preferences get/replace.
- Operator-facing **send** endpoint enqueueing Celery tasks (email / in-app / WhatsApp).
- Event-types catalog endpoint.

### 3.14 Audit & compliance surfaces

- **Access audit** and **moderation audit** listing (admin).
- **Agent audit** log listing (admin) at `/api/v1/admin/agent-audit` and alias `/api/admin/agent-audit`.

### 3.15 AI pipeline (backend)

- LangGraph graphs (`video_analysis_graph`, `moderation_workflow`), chains (`moderation_chain`, `insight_chain`, `summary_chain`), agents (orchestrator, content analyzer, safety checker, metadata extractor, scene classifier, report generator, live stream moderator), and tools (frames, Whisper transcription, OCR, object detection, similarity search, face analyzer) exist under `backend/app/ai/`.
- Celery tasks in `video_tasks`, `moderation_tasks`, `analytics_tasks`, `cleanup_tasks`, `report_tasks`, `notification_tasks`, `stream_tasks` route to dedicated queues.

### 3.16 Frontend (Next.js)

- Marketing/home, auth, legal pages, docs-style pages, and authenticated **(app)** routes: dashboard variants (analytics, billing, users, API keys, audit, support tickets, etc.), videos, moderation, live, reports.
- `NEXT_PUBLIC_MOCK_API` toggles mock API routes vs Next rewrites to backend.

---

## 4. Non-goals / gaps (honest reflection of code)

- **Mobile apps** are not part of this repo.
- **API keys** are manageable via API but **not wired as an alternate auth mechanism** on protected routes in the inspected dependency layer.
- **Multi-tenant** fields (`tenant_id`) exist on several models; enforcement depth varies by endpoint — treat as partial scoping unless verified per route.

---

## 5. User stories (implemented)

1. **As an operator**, I can upload or register a video, track processing status, and open detail with presigned playback when S3 is available.
2. **As an operator**, I can run moderation review workflows and apply overrides where permitted.
3. **As an operator**, I can define policies and connect webhook endpoints for outbound events.
4. **As an admin**, I can manage users, read access and moderation audits, inspect AI agent audit entries, and handle support tickets.
5. **As a billing user**, I can start Stripe checkout and manage subscription via portal webhooks updating `user_subscriptions` / `billing_payments`.
6. **As any authenticated user**, I can manage notification preferences and in-app notifications.

---

## 6. Related engineering docs

- `docs/ARCHITECTURE.md` — components and flows  
- `docs/API_SPEC.md` — HTTP surface  
- `docs/DB_SCHEMA.md` — tables and relations  
- `docs/DEPLOYMENT.md` — Docker, CI/CD, Terraform/Kubernetes references  
