# VidShield AI — Manual GCP Deployment Runbook

This runbook is a **structured, step-by-step operator guide** for deploying VidShield AI on **Google Cloud Platform** in alignment with the repository’s **application configuration** (`backend/app/config.py`), **CI/CD workflows** (`.github/workflows/cd-prod.yml`, `cd-staging.yml`), and **[GCP-ARCHITECTURE-DESIGN.md](GCP-ARCHITECTURE-DESIGN.md)**.

**Audience:** Platform engineers and SREs who own GCP projects, networking, GKE, and secrets.

**Assumptions:**

- You have **Organization / Billing Administrator** access or a pre-provisioned project with billing enabled.
- You deploy **staging** and **production** in separate projects or in one project with strict naming and IAM separation (recommended: **two GCP projects**).
- Container images match workflow names: **`vidshieldai-backend`**, **`vidshieldai-agent`** (worker), **`vidshieldai-frontend`** in **Artifact Registry**.
- GKE workloads use namespace **`vidshield`** and Deployments **`vidshield-backend`**, **`vidshield-worker`**, **`vidshield-frontend`** (container names **`api`**, **`worker`**, **`frontend`**) so **GitHub Actions** `kubectl set image` succeeds without changes.

**Gap (manifests):** A committed **`k8s/`** directory may not exist in every checkout (`task.md`). This runbook describes **what to create** and **how to verify**; apply YAML from your internal repo or generate from Helm/Kustomize until upstream manifests land.

**Conventions:** Replace placeholders:

| Placeholder | Example |
|-------------|---------|
| `PROJECT_ID` | `my-vidshield-prod` |
| `REGION` | `us-central1` |
| `GAR_REPO` | `vidshield` |
| `CLUSTER` | `vidshield-gke-prod` |
| `ENV_DOMAIN` | `app.vidshield.example.com` |

---

## Table of contents

1. [Purpose and scope](#1-purpose-and-scope)  
2. [Prerequisites](#2-prerequisites)  
3. [Create or select a GCP project](#3-create-or-select-a-gcp-project)  
4. [Enable required APIs](#4-enable-required-apis)  
5. [Networking (VPC)](#5-networking-vpc)  
6. [IAM and service accounts](#6-iam-and-service-accounts)  
7. [Artifact Registry](#7-artifact-registry)  
8. [Secret Manager](#8-secret-manager)  
9. [Cloud SQL (PostgreSQL 16)](#9-cloud-sql-postgresql-16)  
10. [Memorystore for Redis](#10-memorystore-for-redis)  
11. [Cloud Storage (GCS)](#11-cloud-storage-gcs)  
12. [Google Kubernetes Engine (GKE)](#12-google-kubernetes-engine-gke)  
13. [Workload Identity (GKE ↔ GCP APIs)](#13-workload-identity-gke--gcp-apis)  
14. [Kubernetes manifests (reference shape)](#14-kubernetes-manifests-reference-shape)  
15. [Ingress, TLS, and load balancing](#15-ingress-tls-and-load-balancing)  
16. [Cloud CDN and cache invalidation](#16-cloud-cdn-and-cache-invalidation)  
17. [GitHub Actions — Workload Identity Federation](#17-github-actions--workload-identity-federation)  
18. [Database migrations](#18-database-migrations)  
19. [Data plane verification](#19-data-plane-verification)  
20. [Day-2 operations](#20-day-2-operations)  
21. [Security checklist](#21-security-checklist)  
22. [Related documents](#22-related-documents)

---

## 1. Purpose and scope

**In scope:** GCP resources for API, workers, frontend, PostgreSQL, Redis, object storage, secrets, HTTPS entry, optional CDN, and CI authentication.

**Out of scope:** Configuring OpenAI, Pinecone, Stripe, SendGrid, or Twilio accounts (only where to store credentials in Secret Manager).

---

## 2. Prerequisites

1. Install **Google Cloud SDK** (`gcloud`) and `kubectl` on your workstation.
2. Authenticate: `gcloud auth login` and `gcloud config set project PROJECT_ID`.
3. Ensure **billing** is linked to the project.
4. Reserve a **DNS zone** or registrar access for your public hostname(s).
5. Confirm **quotas** for GKE nodes (if Standard), Cloud SQL instances, and Memorystore in `REGION`.

---

## 3. Create or select a GCP project

1. In Google Cloud Console → **IAM & Admin** → **Create Project**, set **Project name** and note **Project ID** (`PROJECT_ID`).
2. Link a **billing account** to the project.
3. (Recommended) Enable **Organization policies** later for constraints (e.g. `constraints/compute.requireOsLogin`, domain restricted sharing) per your org standards.

---

## 4. Enable required APIs

Run (adjust project):

```bash
gcloud config set project PROJECT_ID

gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  servicenetworking.googleapis.com \
  compute.googleapis.com \
  dns.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudresourcemanager.googleapis.com \
  certificatemanager.googleapis.com
```

**Note:** If you use **Cloud CDN**, backend configuration uses Compute API resources (URL maps, backend services). Pub/Sub is optional for future async patterns.

---

## 5. Networking (VPC)

### 5.1 Create VPC and subnets

1. **VPC network** → **Create** → name `vidshield-vpc`, custom subnets.
2. Create subnets:
   - **`gke-subnet`** — `REGION`, primary IPv4 range e.g. `10.10.0.0/20` (sized for nodes + pods depending on GKE mode).
   - **`psc-range` or connector** — If using **Private Service Connect** for Cloud SQL, allocate a **peering range** (e.g. `10.20.0.0/16`) reserved for **Service Networking** (see Cloud SQL section).
3. Enable **Private Google Access** on subnets that host nodes without public IPs (recommended).

### 5.2 Cloud NAT (optional but common)

If nodes or workloads need **outbound internet** (e.g. OpenAI API) without public IPs:

1. **Cloud Router** in `REGION`.
2. **Cloud NAT** attached to `gke-subnet` (or node subnet) via the router.

### 5.3 Firewall rules

1. Allow **health checks** from Google probe ranges to node ports if using Network Load Balancing (see [GKE firewall docs](https://cloud.google.com/kubernetes-engine/docs/how-to/firewalls)).
2. Allow **ingress** from load balancer to NodePort/Service ports as required by your Ingress controller.
3. Restrict **SSH / RDP**; prefer **Identity-Aware Proxy** for admin access if you use VMs.

---

## 6. IAM and service accounts

### 6.1 Runtime service account (GKE workloads)

1. Create **`vidshield-workload@PROJECT_ID.iam.gserviceaccount.com`**.
2. Grant least privilege for runtime:
   - **Secret Manager Secret Accessor** on secrets the app reads (or a single project-level policy if you use a naming prefix and accept broader access — prefer per-secret bindings).
   - **Cloud SQL Client** if using Cloud SQL Auth Proxy or IAM database auth.
   - **Storage Object Admin** or narrower **Object User/ Creator** on the **videos** GCS bucket (and thumbnails/artifacts buckets if split).
3. Optional: **Cloud Trace Agent** / **Error Reporting Writer** if you add instrumentation.

### 6.2 GitHub Actions deployer service account

1. Create **`github-deploy@PROJECT_ID.iam.gserviceaccount.com`** (name arbitrary).
2. Grant:
   - **Artifact Registry Writer** on the Docker repository.
   - **Kubernetes Engine Developer** on the cluster (or a custom role allowing `container.deployments.update` + `get` + `rollout` in namespace `vidshield`).
   - If using CDN invalidation: **Compute Load Balancer Admin** or a narrower role allowing `compute.urlMaps.invalidateCache` on the URL map resource.
3. Bind this SA as **Workload Identity User** for the WIF provider (section 17).

---

## 7. Artifact Registry

1. Console → **Artifact Registry** → **Create repository**.
   - Format: **Docker**
   - Location: **`REGION`**
   - Name: **`GAR_REPO`** (e.g. `vidshield` — must match `GAR_REPOSITORY` secret in GitHub).
2. Full image path pattern:

   `REGION-docker.pkg.dev/PROJECT_ID/GAR_REPO/IMAGE:TAG`

3. Test push from workstation:

   ```bash
   gcloud auth configure-docker REGION-docker.pkg.dev
   docker pull hello-world
   docker tag hello-world REGION-docker.pkg.dev/PROJECT_ID/GAR_REPO/test:manual
   docker push REGION-docker.pkg.dev/PROJECT_ID/GAR_REPO/test:manual
   ```

4. (Optional) **Cleanup policies** for untagged or old images.

---

## 8. Secret Manager

Create secrets **one per value** or **JSON bundles** per your standards. Minimum set derived from `backend/app/config.py` and workflows:

| Secret (example name) | Used by | Notes |
|----------------------|---------|--------|
| `database-url` | API, worker | `postgresql+asyncpg://...` for API; workers need sync URL or same with driver note — align with `config.py` derivation |
| `redis-url` | API, worker | Include DB index `0` for app; Celery can derive `/1` and `/2` |
| `secret-key` | API, worker | Strong random |
| `openai-api-key` | API, worker | If workers call OpenAI |
| `sendgrid-api-key`, `sendgrid-from-email` | API, worker | Both need email paths |
| `twilio-*` | API, worker | If WhatsApp enabled |
| `stripe-*` | API | Webhook secret on API only |
| `gcp-project-id` | API, worker | Or set via Deployment env literal |
| `cors-origins` | API | JSON string array |

**Frontend build secrets (GitHub Actions, not Secret Manager on cluster):**

- `NEXT_PUBLIC_API_URL` — public site URL (e.g. `https://ENV_DOMAIN`)
- `API_UPSTREAM_URL` — in-cluster or internal API base for Next rewrites (e.g. `http://vidshield-backend.vidshield.svc.cluster.local:8000`)

**Populate example:**

```bash
echo -n 'postgresql+asyncpg://USER:PASS@/vidshield?host=/cloudsql/PROJECT_ID:REGION:INSTANCE' | \
  gcloud secrets create database-url --data-file=-
```

Mount secrets using **Workload Identity** + **CSI Secret Store driver**, **External Secrets Operator**, or sync-to-Kubernetes-Secret in your pipeline. Do not commit raw secrets to git.

---

## 9. Cloud SQL (PostgreSQL 16)

### 9.1 Create instance

1. **SQL** → **Create instance** → **PostgreSQL 16**.
2. **Instance ID** e.g. `vidshield-sql-prod`.
3. **Region** `REGION`; **Zonal** or **Regional** (HA) per RTO/RPO.
4. **Connectivity**:
   - Enable **Private IP**; allocate **Service Networking** connection (VPC peering) using the reserved range from §5.
   - Disable **Public IP** for production if policy requires.
5. **Users:** create application user and password; store in Secret Manager.
6. **Databases:** create `vidshield`.

### 9.2 Connection string for async SQLAlchemy

Use Unix socket or private IP format supported by your driver. Common pattern with **Cloud SQL Auth Proxy** sidecar:

- Sidecar listens on `127.0.0.1:5432` in the pod; `DATABASE_URL` points to that host.

Or **private IP** directly from pods:

- `postgresql+asyncpg://USER:PASSWORD@10.x.x.x:5432/vidshield`

### 9.3 Authorized networks

If you temporarily use public IP (not recommended for prod), restrict **Authorized networks** to known egress IPs only.

---

## 10. Memorystore for Redis

1. **Memorystore** → **Create instance** → **Redis**, **Tier** Standard or Basic.
2. Same **VPC** as GKE; choose **private IP** in a range non-overlapping with GKE pod CIDR.
3. **TLS:** if enabled, use `rediss://` in `REDIS_URL` (application sets SSL context in Celery when `rediss://` is used).
4. **Auth string:** if required, append per Memorystore documentation.

**Capacity:** size for peak Celery queue depth + rate-limit keys + refresh token storage.

---

## 11. Cloud Storage (GCS)

1. **Cloud Storage** → **Create bucket** — name globally unique (e.g. `PROJECT_ID-vidshield-videos`).
2. **Location:** same `REGION` or multi-region per compliance.
3. **Uniform bucket-level access:** enabled.
4. **Lifecycle:** e.g. transition cold artifacts after N days.
5. **CORS:** if browsers upload directly to signed URLs, configure CORS JSON to allow your HTTPS origin and `PUT`/`GET` methods.
6. **IAM:** grant **`vidshield-workload`** `roles/storage.objectAdmin` (or tighter custom role) on this bucket.

**Application env:** `GCS_BUCKET_NAME`, `GCP_PROJECT_ID`, `GCS_PRESIGNED_URL_EXPIRE`. On GKE with Workload Identity, leave **`GCS_SERVICE_ACCOUNT_KEY_PATH`** empty so **ADC** signs V4 URLs.

---

## 12. Google Kubernetes Engine (GKE)

### 12.1 Create cluster

**Option A — Autopilot (simpler ops)**

1. **Kubernetes Engine** → **Create** → **Autopilot** → region `REGION`.
2. Enable **Workload Identity**: during create, ensure **Workload Identity** is enabled (default on new Autopilot clusters).

**Option B — Standard (more control)**

1. Create cluster with **Workload Identity** enabled.
2. Node pool in `gke-subnet`; use **Container-Optimized OS**; size nodes for FFmpeg/ML CPU/memory.

### 12.2 Cluster credentials

```bash
gcloud container clusters get-credentials CLUSTER --region REGION --project PROJECT_ID
kubectl config current-context
```

### 12.3 Namespace

```bash
kubectl create namespace vidshield
```

---

## 13. Workload Identity (GKE ↔ GCP APIs)

1. Note **cluster project number** and **Workload Identity pool**:

   `PROJECT_ID.svc.id.goog`

2. Create Kubernetes Service Accounts (example):

   - `ksa-api` in namespace `vidshield` for backend pods.
   - `ksa-worker` for worker pods (can share one KSA if desired).

3. Annotate KSA:

   ```yaml
   metadata:
     annotations:
       iam.gke.io/gcp-service-account: vidshield-workload@PROJECT_ID.iam.gserviceaccount.com
   ```

4. Bind IAM:

   ```bash
   gcloud iam service-accounts add-iam-policy-binding \
     vidshield-workload@PROJECT_ID.iam.gserviceaccount.com \
     --role roles/iam.workloadIdentityUser \
     --member "serviceAccount:PROJECT_ID.svc.id.goog[vidshield/ksa-api]"
   ```

5. Set **`serviceAccountName: ksa-api`** on Pod templates for API and worker (or separate GSAs for stricter split).

---

## 14. Kubernetes manifests (reference shape)

Until `k8s/` exists in-repo, maintain equivalent YAML. Minimum objects:

| Kind | Name | Purpose |
|------|------|---------|
| `Deployment` | `vidshield-backend` | Container `api`, port 8000, env from secrets |
| `Deployment` | `vidshield-worker` | Container `worker`, same image as agent build, Celery command with **all queues** |
| `Deployment` | `vidshield-frontend` | Container `frontend`, port 3000 |
| `Service` | ClusterIP for each | Internal routing |
| `Service` or `Ingress` | Public entry | HTTPS termination at LB or Ingress |
| `PodDisruptionBudget` | optional | HA during node drains |
| `HorizontalPodAutoscaler` | optional | CPU-based scale |

**Worker command (critical):** must include:

`--queues video,moderation,analytics,cleanup,reports,notifications,streams`

**API env highlights:**

- `FORWARDED_ALLOW_IPS=*` or LB subnet CIDRs (see [DEPLOYMENT.md](DEPLOYMENT.md)).
- `APP_ENV=production`, `DEBUG=false`.

**Reference skeleton (illustrative only — adjust resources and probes):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vidshield-backend
  namespace: vidshield
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vidshield-backend
  template:
    metadata:
      labels:
        app: vidshield-backend
    spec:
      serviceAccountName: ksa-api
      containers:
        - name: api
          image: REGION-docker.pkg.dev/PROJECT_ID/GAR_REPO/vidshieldai-backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: FORWARDED_ALLOW_IPS
              value: "*"
            # Inject DATABASE_URL, REDIS_URL, SECRET_KEY, GCS_*, OPENAI_*, etc. from Secret
```

Apply: `kubectl apply -f manifests/ -n vidshield`.

---

## 15. Ingress, TLS, and load balancing

### 15.1 Managed certificates

1. **Certificate Manager** or **Ingress static IP + managed cert** — reserve global/regional IP per design.
2. Create **Google-managed certificate** for `ENV_DOMAIN` (and `api.ENV_DOMAIN` if split).

### 15.2 Ingress

1. Use **GKE Ingress** (GCE) or **Gateway API** per your standard.
2. **BackendConfig** (if using neg / backend services): set **timeout** high enough for long requests and **WebSocket** / Socket.IO (e.g. 3600s where appropriate).
3. **Health checks:** HTTP path **`/health`** on port 8000 for API service.

### 15.3 Same-origin frontend

Public hostname should route:

- `/` → frontend Service (`3000`).
- `/api/v1` → backend Service (`8000`) **or** frontend-only with **`API_UPSTREAM_URL`** to backend Service (matches Next standalone pattern in [DEPLOYMENT.md](DEPLOYMENT.md)).

---

## 16. Cloud CDN and cache invalidation

1. After Ingress and backend services exist, attach **Cloud CDN** on the backend service for static assets if desired.
2. Note the **URL map name** used by the HTTPS load balancer.
3. Set GitHub repository variable **`CLOUD_CDN_URL_MAP`** to that name so `cd-prod.yml` can run:

   ```bash
   gcloud compute url-maps invalidate-cdn-cache CLOUD_CDN_URL_MAP --path "/*" --async
   ```

---

## 17. GitHub Actions — Workload Identity Federation

### 17.1 Create Workload Identity Pool (for GitHub)

1. **IAM & Admin** → **Workload Identity Federation** → **Create pool** e.g. `github-pool`.
2. **Create provider** → **OIDC** → Issuer `https://token.actions.githubusercontent.com`.
3. **Attribute mapping** (typical):

   - `google.subject` = `assertion.sub`
   - `attribute.repository` = `assertion.repository`
   - `attribute.ref` = `assertion.ref`

4. **Allow attribute condition** restricting to your org/repo, e.g.:

   `attribute.repository=="ORG/Project-6-AI-Video-Intelligence-Content-Moderation-Platform_GCP"`

### 17.2 Bind GitHub to deployer SA

```bash
gcloud iam service-accounts add-iam-policy-binding github-deploy@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/ORG/REPO_NAME"
```

### 17.3 GitHub repository secrets

Align with workflows:

| Secret | Purpose |
|--------|---------|
| `GCP_PROJECT_ID` | Project ID |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Full provider resource name |
| `GCP_SERVICE_ACCOUNT` | `github-deploy@...` email |
| `GAR_LOCATION` | e.g. `us-central1` |
| `GAR_REPOSITORY` | Artifact Registry repo id |
| `GKE_CLUSTER_PROD` / `GKE_CLUSTER_STAGING` | Cluster name |
| `GKE_CLUSTER_LOCATION` | Region or zone |
| `NEXT_PUBLIC_API_URL` | Public URL for frontend build |
| `API_UPSTREAM_URL` | Internal API URL for Next rewrites |

Repository **variable:** `CLOUD_CDN_URL_MAP` (optional).

---

## 18. Database migrations

Run **Alembic** against Cloud SQL before serving traffic on a new revision:

**Option A — one-shot Job**

```bash
kubectl run alembic-migrate -n vidshield --rm -it \
  --image=REGION-docker.pkg.dev/PROJECT_ID/GAR_REPO/vidshieldai-backend:TAG \
  --restart=Never \
  --env="DATABASE_URL=..." \
  --command -- alembic upgrade head
```

**Option B — Makefile** from a bastion or CI job with `DATABASE_URL` (see [DEPLOYMENT.md](DEPLOYMENT.md)).

---

## 19. Data plane verification

1. **`kubectl get pods -n vidshield`** — all `Running`.
2. **`curl -k https://ENV_DOMAIN/health`** via LB or port-forward — `{"status":"ok",...}`.
3. **Auth:** register/login via API; confirm JWT issuance.
4. **Upload URL:** `POST /api/v1/videos/upload-url` with Bearer token; receive signed URL; `PUT` small test object to GCS; confirm object in bucket.
5. **Worker:** enqueue a short task; confirm logs in **Cloud Logging** for worker pod; Redis queue depth drops.
6. **WebSocket / Socket.IO:** from browser, connect to `/socket.io/` if exposed; verify no mixed-content errors (check `FORWARDED_ALLOW_IPS` if redirects break HTTPS).

---

## 20. Day-2 operations

### 20.1 Rollout and rollback

- **Roll forward:** push images with tag; GitHub Actions runs `kubectl set image` + `rollout status`.
- **Rollback:** `kubectl rollout undo deployment/vidshield-backend -n vidshield` (and worker/frontend as needed).
- **Pin version:** set image digest in Deployment for immutable provenance.

### 20.2 Scaling

- `kubectl scale deployment/vidshield-worker --replicas=N -n vidshield`
- Tune **HPA** max replicas against **Memorystore** connection limits and **Cloud SQL** max connections.

### 20.3 Backups

- **Cloud SQL:** enable automated backups and PITR; test restore quarterly.
- **GCS:** versioning or **Object Versioning** for critical buckets; lifecycle for cost.

### 20.4 Upgrades

- **GKE release channel:** Regular or Stable; plan monthly control plane upgrades.
- **Node upgrades:** maintenance windows; drain nodes respect **PDBs**.

---

## 21. Security checklist

1. No **JSON service account keys** on cluster unless unavoidable; prefer **Workload Identity**.
2. **Secret Manager** access scoped to required secrets only.
3. **Cloud SQL** not exposed to `0.0.0.0/0`.
4. **Cloud Armor** on public LB for OWASP-style rules and IP allowlists if needed.
5. **Binary Authorization** (optional) for image provenance.
6. **VPC egress controls** for sensitive environments (Private Google Access + restricted.googleapis.com if required).
7. **Audit logs:** **Admin Activity** log sinks to BigQuery or Chronicle if mandated.

---

## 22. Related documents

- **[GCP-ARCHITECTURE-DESIGN.md](GCP-ARCHITECTURE-DESIGN.md)** — diagrams and service mapping  
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — compose, CI/CD summary, env checklist  
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — application structure  
- **[task.md](../task.md)** — Terraform module migration status (I-02–I-07, I-15, I-16)

---

**Document maintenance:** When `k8s/` manifests are committed, add a subsection linking to paths and update §14 to reference concrete files instead of illustrative YAML.
