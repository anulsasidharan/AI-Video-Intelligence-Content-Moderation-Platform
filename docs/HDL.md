# VidShield AI — High-Level Design (HDL)

This document is the **High-Level Design (HDL)** for VidShield AI: scope, actors, logical components, deployment topology, and cross-cutting concerns. It aligns with the **implemented** codebase (`backend/`, `frontend/`, `terraform/`, `.github/workflows/`). Production deployment targets **Google Cloud (GKE, Artifact Registry, GCS)** per CI workflows; see **[GCP-ARCHITECTURE-DESIGN.md](GCP-ARCHITECTURE-DESIGN.md)** and **[GCP_DEPLOYMENT_RUNBOOK.md](GCP_DEPLOYMENT_RUNBOOK.md)**.

**Related:** [LDL.md](LDL.md) (module-level design), [ARCHITECTURE.md](ARCHITECTURE.md), [DEPLOYMENT.md](DEPLOYMENT.md), [PRD.md](PRD.md).

---

## 1. Purpose and scope

**VidShield AI** provides:

- Ingestion and lifecycle management for **recorded videos** (metadata, object keys in DB — legacy column name `s3_key` holds **GCS** keys — status, URL-based workflows).
- **AI-assisted moderation** (results, queue, human review, admin override) driven by LangGraph/LangChain pipelines and Celery workers.
- **Policies**, **webhooks**, **analytics**, **live streams** with alerts and moderation controls.
- **Reports** (async jobs, templates, PDF/GCS artifacts), **notifications** (email, in-app, WhatsApp), **billing** (Stripe), and **audit** surfaces (access, moderation, agent activity).
- A **Next.js** web application for operators and administrators, backed by a single **FastAPI** API surface.

**Out of scope in this repository:** native mobile apps; separate partner-only codebases (partners consume the same REST API).

---

## 2. Stakeholders and actors

| Actor | Description | Primary interface |
|--------|-------------|-------------------|
| **Operator** | Day-to-day video and moderation user | Web app (`operator` role) |
| **Administrator** | User management, audits, support tickets, billing metrics | Web app (`admin` role) |
| **API consumer** | Integrations / automation | REST `/api/v1` with JWT (`api_consumer` role where used) |
| **Anonymous user** | Registration, password reset, newsletter, support ticket submission | Public REST endpoints |
| **Platform operations** | Deployments, scaling, secrets | GCP, GKE, Terraform, GitHub Actions |

---

## 3. Logical system context

```mermaid
flowchart LR
  subgraph people["People"]
    OP[Operator]
    AD[Administrator]
  end
  VS[VidShield AI\nWeb + API + Workers]
  subgraph ext["External systems"]
    OAI[OpenAI]
    PC[Pinecone]
    ST[Stripe]
    SG[SendGrid]
    TW[Twilio]
    GCS[Google Cloud Storage]
  end
  OP -->|HTTPS| VS
  AD -->|HTTPS| VS
  VS -->|API| OAI
  VS -->|API| PC
  VS -->|API + webhooks| ST
  VS -->|API| SG
  VS -->|API| TW
  VS -->|API| GCS
```

---

## 4. Major building blocks

```mermaid
flowchart TB
  subgraph client_tier["Client tier"]
    WEB[Next.js 14 web app]
  end
  subgraph app_tier["Application tier — GKE / Docker"]
    API[FastAPI + Socket.IO ASGI]
    WRK[Celery workers]
  end
  subgraph data_tier["Data tier"]
    PG[(PostgreSQL 16)]
    RD[(Redis 7)]
    GCSObj[(Google Cloud Storage)]
  end
  WEB -->|"/api/v1 rewrites or direct"| API
  API --> PG
  API --> RD
  API --> GCSObj
  WRK --> PG
  WRK --> RD
  WRK --> GCSObj
```

| Block | Responsibility |
|--------|------------------|
| **Web app** | UI, auth session handling, API client, optional mock API routes, server rewrites to backend |
| **API** | REST `/api/v1`, JWT auth, validation, orchestration into services, WebSocket/Socket.IO entry |
| **Workers** | Long-running video/moderation/analytics/report/notification/stream tasks |
| **PostgreSQL** | System of record for users, videos, moderation, policies, billing, audits, etc. |
| **Redis** | Rate limiting, Celery broker/backend, refresh-token / ephemeral patterns |
| **GCS** | Video objects, thumbnails, generated report files (signed URL access) |

---

## 5. Deployment views

### 5.1 Production (GCP — as defined in CI/CD)

- **Compute:** **Google Kubernetes Engine (GKE)** — Deployments for **API** (`vidshield-backend`), **worker** (`vidshield-worker`), **frontend** (`vidshield-frontend`) in namespace **`vidshield`**; images from **Artifact Registry**.
- **Networking:** **External HTTP(S) load balancing** or **Ingress for GKE** in front of API/frontend; private connectivity for **Cloud SQL** and **Memorystore** (VPC, private IP, firewall rules).
- **Data:** **Cloud SQL for PostgreSQL 16**, **Memorystore for Redis 7**, **GCS** bucket(s) for media and reports.
- **Edge:** **Cloud CDN** optional; production CD can invalidate cache via repository variable **`CLOUD_CDN_URL_MAP`** and `gcloud compute url-maps invalidate-cdn-cache` (see `cd-prod.yml`).
- **CI/CD:** **GitHub Actions** — `ci.yml` for quality gates; **`cd-prod.yml`** / **`cd-staging.yml`** for docker build/push to Artifact Registry + `kubectl set image` rollouts on GKE, authenticated with **Workload Identity Federation**.

### 5.2 Local / developer

- **Docker Compose:** `postgres`, `redis`, `backend`, `worker`, `frontend` with hot-reload on API and mounted source where configured.

### 5.3 Kubernetes manifests

- **GKE** is the primary production orchestrator. Committed manifests may live under **`k8s/`** when added; Makefile targets can apply, run migrate job, tail logs, and rollouts. Until manifests are in-repo, operators maintain equivalent YAML separately (see **DEPLOYMENT.md**, **GCP_DEPLOYMENT_RUNBOOK.md**).

---

## 6. High-level data flows

### 6.1 Video upload (conceptual)

1. Client requests presigned upload URL from API.  
2. Client uploads bytes directly to **GCS** (via signed URL from the API).  
3. Client confirms or worker processes file → metadata persisted in **PostgreSQL**, status transitions, moderation pipeline **enqueued** to Celery.

### 6.2 Moderation decision path (conceptual)

1. Worker loads video context, runs **AI graph/chain** (OpenAI, optional Pinecone tools).  
2. **Moderation result** and optional **queue item** persisted.  
3. Webhooks / notifications dispatched per configuration.

### 6.3 Browser → API in production

1. Browser loads **HTTPS** Next.js app.  
2. Same-origin **`/api/v1/*`** requests hit Next server; **rewrites** forward to internal **`API_UPSTREAM_URL`**.  
3. API returns JSON; success responses wrapped in **`{ "data": ... }`** (middleware).

---

## 7. Security and compliance (high level)

- **Authentication:** JWT bearer tokens; refresh token flow with Redis-backed invalidation patterns (see auth routes).
- **Authorization:** Role-based dependencies — `admin`, `operator`, `api_consumer` on selected routes.
- **Transport:** TLS at Google HTTPS load balancer / managed certificates; app configured for `CORS_ORIGINS` allowlist.
- **Abuse controls:** Redis-backed **rate limiting** with tiered limits per route class; fail-open if Redis unavailable.
- **Secrets:** Environment variables / **Secret Manager** (operations concern; not hardcoded in application source); **Workload Identity** for GKE → GCS and other GCP APIs without JSON keys.
- **Audit:** Access audit log, moderation audit views, agent audit log for AI observability.

---

## 8. Observability and operations

- **Structured logging:** `structlog` across API and Celery signals.
- **Health:** `GET /health` for liveness-style checks.
- **Sentry:** `SENTRY_DSN` exists in settings; SDK wiring is not present in `app/` (optional future wiring).

---

## 9. Non-functional characteristics (as implemented)

| Concern | Approach |
|---------|-----------|
| **Scalability** | Stateless API pods; horizontal GKE scaling; Celery worker pool scaling |
| **Availability** | Multi-zone GKE and regional Cloud SQL / Memorystore patterns; Deployment rollouts |
| **Consistency** | PostgreSQL transactional writes; eventual consistency for async worker side effects |
| **Performance** | Redis caching/rate limits; async SQLAlchemy on API; sync sessions in workers |

---

## 10. Document map

| Document | Level |
|----------|--------|
| **HDL.md** (this file) | Context, components, deployment, flows |
| **LDL.md** | Packages, routes, schemas, queues, key sequences |
| **ARCHITECTURE.md** | Middleware stack, folder layout, integration detail |
| **API_SPEC.md** | HTTP contract |
| **DB_SCHEMA.md** | Physical schema |
| **DEPLOYMENT.md** | Commands and environment variables |
| **GCP-ARCHITECTURE-DESIGN.md** | GCP diagrams and service inventory |
| **GCP_DEPLOYMENT_RUNBOOK.md** | Manual GCP setup and operations |
