# VidShield AI — Deployment Guide (As Implemented)

This guide reflects **files that exist in the repository**: Dockerfiles, `docker-compose*.yml`, `Makefile`, GitHub Actions workflows, `terraform/`, and `k8s/`.

---

## 1. Runtime topology

```mermaid
flowchart LR
  subgraph clients
    Browser[Browser]
  end
  subgraph edge
    CF[CloudFront optional]
    ALB[ALB / Ingress]
  end
  subgraph compute
    FE[Next.js frontend :3000]
    API[FastAPI + Socket.IO ASGI :8000]
    WRK[Celery workers]
  end
  subgraph data
    PG[(PostgreSQL 16)]
    RD[(Redis 7)]
    S3[(S3 bucket)]
  end
  Browser --> FE
  Browser --> ALB
  FE -->|rewrites /api/v1| API
  ALB --> API
  API --> PG
  API --> RD
  WRK --> PG
  WRK --> RD
  API --> S3
  WRK --> S3
```

---

## 2. Local development (Docker Compose)

**File:** `docker-compose.yml`

Services:

| Service | Image / build | Ports | Notes |
|---------|---------------|-------|-------|
| `postgres` | `postgres:16-alpine` | Host `5432` | DB `vidshield`, user/password `postgres`/`postgres` |
| `redis` | `redis:7-alpine` | Host `6380` → container `6379` |
| `backend` | `./backend` Dockerfile | `8000` | Runs `alembic upgrade head`, `scripts/seed_admin.py`, then `uvicorn app.main:asgi_app --reload` |
| `worker` | same as backend | — | `celery ... --queues video,moderation,analytics,cleanup,reports,notifications,streams` |
| `frontend` | `./frontend` Dockerfile | `3000` | Build args set `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL`; default `NEXT_PUBLIC_MOCK_API: "true"` in compose |

**Commands:**

```bash
make dev          # docker compose up --build
make dev-d        # detached
make down         # docker compose down
make clean        # down -v --remove-orphans
```

**Backend env:** `backend/.env` (see `backend/.env.example`). Compose overrides `DATABASE_URL`, `REDIS_URL`, Celery URLs, and `CORS_ORIGINS` for the container network.

**Important:** `Makefile` target `dev-backend` runs `uvicorn app.main:app` — the **canonical ASGI app with Socket.IO** is `app.main:asgi_app` (used in `backend/Dockerfile` CMD and docker-compose `backend` service).

---

## 3. Production-style Compose overlay

**File:** `docker-compose.prod.yml`

- Removes public DB/Redis ports.
- Injects secrets and URLs from host environment (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, AWS keys, OpenAI, Pinecone, Sentry, `CORS_ORIGINS`, Stripe-related vars as applicable).
- **Backend command in file:** `uvicorn app.main:app --workers 4` (differs from Dockerfile default `asgi_app` — operators should align on one entrypoint for Socket.IO needs).
- **Worker command:** must pass **`--queues video,moderation,analytics,cleanup,reports,notifications,streams`**. The app routes tasks to named queues (see `backend/app/workers/celery_app.py` `task_routes`); a worker that only listens on the default `celery` queue will **never** run notification, video, or moderation tasks.
- **Frontend build args:** `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, `API_UPSTREAM_URL`, `NEXT_PUBLIC_MOCK_API=false`.

**Makefile:**

```bash
make deploy ENV=staging   # prints message; builds/pushes compose prod stack per Makefile
```

---

## 4. Container images

### Backend (`backend/Dockerfile`)

- Multi-stage: installs `[dev]` extras in build stage, copies site-packages to runtime.
- Runtime installs `ffmpeg`, `libpq5`.
- Exposes `8000`.
- **CMD:** `uvicorn app.main:asgi_app --host 0.0.0.0 --port 8000`

### Frontend (`frontend/Dockerfile`)

- Node 20 Alpine; `npm ci` from lockfile.
- Build args: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_APP_ENV`, `API_UPSTREAM_URL`.
- `next build` with `output: 'standalone'`.
- Runtime: `node server.js` on port `3000`.

**Next.js rewrites:** `frontend/next.config.js` proxies `/api/v1/:path*` to `API_UPSTREAM_URL` or `NEXT_PUBLIC_API_URL` (trimmed) when `NEXT_PUBLIC_MOCK_API !== 'true'`.

---

## 5. Database migrations

Run on any backend host with DB credentials:

```bash
make db-migrate
# or
cd backend && alembic upgrade head
```

Head revision in repo: **`0014_add_stripe_customer_id`** (chain `0001` → … → `0014`).

---

## 6. CI — GitHub Actions

**`.github/workflows/ci.yml`**

- `lint-backend`: `ruff check` + `ruff format --check` on `backend/`
- `lint-frontend`: Node 20, `npm ci`, `npm run lint`
- `test-backend`: Postgres + Redis services, pytest
- Frontend build/test jobs as defined in workflow

**`.github/workflows/cd-prod.yml`**

- Triggers: manual `workflow_dispatch` with `image_tag`, or semver tags `v*.*.*`
- Builds and pushes to ECR:
  - `vidshieldai-backend-prod:${IMAGE_TAG}`
  - `vidshieldai-agent-prod:${IMAGE_TAG}` (same backend context)
  - `vidshieldai-frontend-prod:${IMAGE_TAG}`
- Frontend build-args from secrets: `NEXT_PUBLIC_API_URL`, `API_UPSTREAM_URL`, `NEXT_PUBLIC_APP_ENV=production`, `NEXT_PUBLIC_MOCK_API=false`
- Deploy job updates ECS services (cluster `vidshieldai-cluster-prod`, services `vidshield-prod-api`, `vidshield-prod-worker`, `vidshield-prod-frontend`) — see workflow for exact `aws ecs update-service` usage.

---

## 7. Terraform (AWS)

**Path:** `terraform/`

- `main.tf` wires modules: VPC, RDS PostgreSQL 16, ElastiCache Redis, ECS, S3, CloudFront, SQS, WAF, monitoring.
- Remote state block is present (S3 + DynamoDB lock table IDs appear in `main.tf`; adjust per account).
- Environment tfvars: `terraform/environments/dev.tfvars`, `staging.tfvars`, `prod.tfvars`.

**Commands (from Makefile):**

```bash
make tf-plan ENV=dev
make tf-apply ENV=dev
```

---

## 8. Kubernetes manifests

**Path:** `k8s/`

`Makefile` provides `k8s-apply`, `k8s-migrate`, `k8s-delete`, log tailing, rollouts. Secrets file `k8s/03-secrets.yaml` is called out as applied separately.

---

## 9. Configuration checklist (production)

Set at minimum (names from `backend/app/config.py`):

- `APP_ENV=production`, `DEBUG=false`
- **`FORWARDED_ALLOW_IPS`** — set to **`*`** (or your VPC / ALB subnet CIDRs) on the **API** container. Uvicorn only applies `X-Forwarded-Proto` / `X-Forwarded-For` from trusted hops; the default is `127.0.0.1`, which is wrong behind an ALB, so slash redirects (e.g. `/api/v1/reports` → `/api/v1/reports/`) can incorrectly use `http://` in `Location` and cause **mixed content** from the browser.
- `DATABASE_URL`, `REDIS_URL` (Celery URLs derived if omitted)
- `SECRET_KEY` (strong random)
- `CORS_ORIGINS` JSON list matching browser origins
- `AWS_*`, `S3_BUCKET_NAME` for uploads and report artifacts
- `OPENAI_API_KEY`; optional `PINECONE_*` for similarity tool
- `SENDGRID_*`, `TWILIO_*` if notifications used
- `STRIPE_*` + dashboard webhook URL → `https://<api-host>/api/v1/billing/webhook`
- `FRONTEND_URL` for links in emails/password reset
- `SENTRY_DSN` optional

**Email / WhatsApp troubleshooting (AWS):**

1. **ECS worker command:** the worker container must consume all routed queues (see `docker-compose.yml` `worker.command`). If the worker only runs `celery … worker` with no `--queues`, messages on `notifications`, `video`, `moderation`, etc. are never consumed.
2. **Secrets on both tasks:** forgot-password and reset-confirmation emails are sent **from the API** (`EmailService` in `auth.py`). Moderation and password-changed alerts are sent **from Celery** (`notification_tasks.py`). Inject `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, and Twilio vars into **both** the API and worker task definitions (or a shared secret) so each process can reach the providers.
3. **WhatsApp on violations:** `_notify_moderation_complete` only adds the `whatsapp` channel when status is `FLAGGED` or `REJECTED`, and the user must have `whatsapp_number` set (`notification_dispatcher`).
4. **CloudWatch:** search API logs for `forgot_password_email_failed`; worker logs for `send_email_task_failed` / `celery_task_failed`.

Frontend build-time:

- For same-origin API behind ALB: `NEXT_PUBLIC_APP_ENV=production` makes `frontend/src/lib/constants.ts` use **empty** `NEXT_PUBLIC_API_URL` (browser calls `/api/v1/...` on the page origin).
- Set `API_UPSTREAM_URL` to internal backend base (e.g. `http://backend:8000`) so Next rewrites reach the API.

---

## 10. Health check

- `GET /health` on API → `{"status":"ok","env":...}` (not wrapped by `DataWrapperMiddleware` per `_SKIP_PATHS`).

---

## 11. Branches

Repository is used with multiple branches (`main`, `development`, `testing`) per CI `pull_request` configuration; align release tagging with `cd-prod.yml` semver pattern.
