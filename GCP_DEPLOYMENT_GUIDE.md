# VidShield AI — GCP Manual Deployment Guide

**Platform:** Google Cloud Platform  
**Target architecture:** GKE (backend + worker + frontend) · Cloud SQL PostgreSQL 16 · Cloud Memorystore Redis 7 · GCS · Artifact Registry · Cloud Load Balancer · Cloud CDN · Pub/Sub · Secret Manager · Workload Identity Federation

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [GCP Project Bootstrap](#2-gcp-project-bootstrap)
3. [Enable Required APIs](#3-enable-required-apis)
4. [IAM Service Accounts](#4-iam-service-accounts)
5. [Secret Manager — Store All Secrets](#5-secret-manager--store-all-secrets)
6. [Terraform State Backend (GCS)](#6-terraform-state-backend-gcs)
7. [Rewrite Terraform for GCP](#7-rewrite-terraform-for-gcp)
8. [Provision Infrastructure with Terraform](#8-provision-infrastructure-with-terraform)
9. [Artifact Registry — Build & Push Images](#9-artifact-registry--build--push-images)
10. [Connect to GKE Cluster](#10-connect-to-gke-cluster)
11. [Kubernetes Namespace & Secrets](#11-kubernetes-namespace--secrets)
12. [Workload Identity — Bind GKE to GCP Services](#12-workload-identity--bind-gke-to-gcp-services)
13. [Deploy Kubernetes Manifests](#13-deploy-kubernetes-manifests)
14. [Run Database Migrations](#14-run-database-migrations)
15. [Cloud Load Balancer & CDN](#15-cloud-load-balancer--cdn)
16. [Pub/Sub Topics & Subscriptions](#16-pubsub-topics--subscriptions)
17. [Monitoring, Alerting & Logging](#17-monitoring-alerting--logging)
18. [Configure GitHub Actions](#18-configure-github-actions)
19. [Smoke-Test & Verification](#19-smoke-test--verification)
20. [Environment-Specific Values Reference](#20-environment-specific-values-reference)
21. [Rollback Procedure](#21-rollback-procedure)

---

## 1. Prerequisites

### 1.1 Required Tools

Install the following tools on your workstation before starting.

```bash
# Verify versions after install
gcloud version          # >= 469.0.0
terraform version       # >= 1.6.0
kubectl version         # >= 1.28
docker version          # >= 24.0
helm version            # >= 3.14 (optional but useful)
```

**Installation links:**
- gcloud CLI: https://cloud.google.com/sdk/docs/install
- Terraform: https://developer.hashicorp.com/terraform/install
- kubectl: `gcloud components install kubectl`
- Docker Desktop: https://docs.docker.com/get-docker/

### 1.2 GCP Account Requirements

- A GCP billing account (Billing Account Admin role)
- Permission to create a new GCP project OR Owner role on an existing project
- A domain name for production (e.g. `vidshield.ai`) — needed for Cloud CDN and SSL

### 1.3 Third-Party API Keys You Must Have Ready

Collect these before starting — you will store them in Secret Manager:

| Key | Where to get it |
|-----|----------------|
| `OPENAI_API_KEY` | platform.openai.com |
| `PINECONE_API_KEY` | app.pinecone.io |
| `SENTRY_DSN` | sentry.io (optional) |
| `SECRET_KEY` | Generate: `openssl rand -hex 32` |

---

## 2. GCP Project Bootstrap

### 2.1 Create the Project

```bash
# Set your billing account ID (find with: gcloud billing accounts list)
BILLING_ACCOUNT="XXXXXX-XXXXXX-XXXXXX"

# Create project
gcloud projects create vidshield-prod \
  --name="VidShield AI Production"

# Or for dev:
gcloud projects create vidshield-dev \
  --name="VidShield AI Dev"

# Link billing
gcloud billing projects link vidshield-prod \
  --billing-account=$BILLING_ACCOUNT

# Set as default for all subsequent commands
gcloud config set project vidshield-prod
```

### 2.2 Set Shell Variables

Set these once in your shell. All commands below reference them.

```bash
# Adjust these for your environment
export PROJECT_ID="vidshield-prod"
export REGION="us-central1"
export ZONE="us-central1-a"
export GKE_CLUSTER="vidshield-gke-prod"
export GAR_REPOSITORY="vidshield"
export GCS_BUCKET_NAME="vidshield-videos-prod"
export DB_INSTANCE="vidshield-pg16-prod"
export REDIS_INSTANCE="vidshield-redis-prod"
export ENV="prod"            # dev | staging | prod

gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

---

## 3. Enable Required APIs

Run this once per project. It takes 2–3 minutes.

```bash
gcloud services enable \
  container.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  pubsub.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  vpcaccess.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com \
  run.googleapis.com \
  --project=$PROJECT_ID

echo "API enablement complete."
```

---

## 4. IAM Service Accounts

VidShield uses three service accounts with least-privilege roles.

### 4.1 Application Service Account (used by GKE workloads)

```bash
gcloud iam service-accounts create vidshield-app \
  --display-name="VidShield Application" \
  --project=$PROJECT_ID

APP_SA="vidshield-app@${PROJECT_ID}.iam.gserviceaccount.com"

# GCS — read/write video storage
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${APP_SA}" \
  --role="roles/storage.objectAdmin"

# Secret Manager — read secrets at runtime
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${APP_SA}" \
  --role="roles/secretmanager.secretAccessor"

# Pub/Sub — publish and subscribe
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${APP_SA}" \
  --role="roles/pubsub.editor"

# Cloud SQL — connect via Cloud SQL Auth Proxy
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${APP_SA}" \
  --role="roles/cloudsql.client"

# Cloud Monitoring — write metrics
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${APP_SA}" \
  --role="roles/monitoring.metricWriter"

# Cloud Trace
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${APP_SA}" \
  --role="roles/cloudtrace.agent"
```

### 4.2 GitHub Actions Deployer Service Account

```bash
gcloud iam service-accounts create vidshield-deployer \
  --display-name="VidShield GitHub Actions Deployer" \
  --project=$PROJECT_ID

DEPLOYER_SA="vidshield-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Push images to Artifact Registry
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${DEPLOYER_SA}" \
  --role="roles/artifactregistry.writer"

# Deploy to GKE
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${DEPLOYER_SA}" \
  --role="roles/container.developer"

# Invalidate Cloud CDN cache
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${DEPLOYER_SA}" \
  --role="roles/compute.networkAdmin"
```

### 4.3 Terraform Service Account

```bash
gcloud iam service-accounts create vidshield-terraform \
  --display-name="VidShield Terraform" \
  --project=$PROJECT_ID

TF_SA="vidshield-terraform@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${TF_SA}" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${TF_SA}" \
  --role="roles/resourcemanager.projectIamAdmin"

# Download key for local Terraform runs (not needed in CI — uses Workload Identity)
gcloud iam service-accounts keys create ~/.config/gcloud/vidshield-terraform-key.json \
  --iam-account=$TF_SA

export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/vidshield-terraform-key.json
```

---

## 5. Secret Manager — Store All Secrets

Store every secret before Terraform runs. Workloads read them at startup via Workload Identity.

### 5.1 Generate and Store Application Secret Key

```bash
SECRET_KEY=$(openssl rand -hex 32)

echo -n "$SECRET_KEY" | gcloud secrets create vidshield-secret-key \
  --data-file=- \
  --replication-policy=automatic \
  --project=$PROJECT_ID
```

### 5.2 Database Password

```bash
DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
echo "Save this DB password: $DB_PASSWORD"   # save it securely now

echo -n "$DB_PASSWORD" | gcloud secrets create vidshield-db-password \
  --data-file=- \
  --replication-policy=automatic \
  --project=$PROJECT_ID
```

### 5.3 Database URL (built after Cloud SQL is created — come back after Step 8)

```bash
# Fill in CLOUD_SQL_PRIVATE_IP after Cloud SQL is provisioned in Step 8
DB_URL="postgresql+asyncpg://vidshield:${DB_PASSWORD}@CLOUD_SQL_PRIVATE_IP:5432/vidshield"
DB_URL_SYNC="postgresql+psycopg2://vidshield:${DB_PASSWORD}@CLOUD_SQL_PRIVATE_IP:5432/vidshield"

echo -n "$DB_URL" | gcloud secrets create vidshield-database-url \
  --data-file=- \
  --replication-policy=automatic \
  --project=$PROJECT_ID

echo -n "$DB_URL_SYNC" | gcloud secrets create vidshield-database-url-sync \
  --data-file=- \
  --replication-policy=automatic \
  --project=$PROJECT_ID
```

### 5.4 Redis URL (built after Memorystore — come back after Step 8)

```bash
# Fill in MEMORYSTORE_IP after Redis is provisioned in Step 8
REDIS_URL="redis://MEMORYSTORE_IP:6379/0"

echo -n "$REDIS_URL" | gcloud secrets create vidshield-redis-url \
  --data-file=- \
  --replication-policy=automatic \
  --project=$PROJECT_ID
```

### 5.5 API Keys

```bash
# OpenAI
echo -n "sk-your-openai-key" | gcloud secrets create vidshield-openai-api-key \
  --data-file=- --replication-policy=automatic --project=$PROJECT_ID

# Pinecone
echo -n "your-pinecone-key" | gcloud secrets create vidshield-pinecone-api-key \
  --data-file=- --replication-policy=automatic --project=$PROJECT_ID

# Sentry (optional)
echo -n "https://your-sentry-dsn" | gcloud secrets create vidshield-sentry-dsn \
  --data-file=- --replication-policy=automatic --project=$PROJECT_ID
```

### 5.6 Verify All Secrets

```bash
gcloud secrets list --project=$PROJECT_ID --filter="name~vidshield"
```

Expected output:

```
NAME                         CREATED              REPLICATION_POLICY
vidshield-database-url       2026-04-13T...       automatic
vidshield-database-url-sync  2026-04-13T...       automatic
vidshield-db-password        2026-04-13T...       automatic
vidshield-openai-api-key     2026-04-13T...       automatic
vidshield-pinecone-api-key   2026-04-13T...       automatic
vidshield-redis-url          2026-04-13T...       automatic
vidshield-secret-key         2026-04-13T...       automatic
vidshield-sentry-dsn         2026-04-13T...       automatic
```

---

## 6. Terraform State Backend (GCS)

Create the GCS bucket that Terraform uses to store remote state. This must be done **before** `terraform init`.

```bash
# State bucket — globally unique name required
TF_STATE_BUCKET="vidshield-tf-state-${PROJECT_ID}"

gcloud storage buckets create gs://${TF_STATE_BUCKET} \
  --location=$REGION \
  --uniform-bucket-level-access \
  --project=$PROJECT_ID

# Enable versioning so you can recover previous state
gcloud storage buckets update gs://${TF_STATE_BUCKET} \
  --versioning

echo "Terraform state bucket: gs://${TF_STATE_BUCKET}"
```

---

## 7. Rewrite Terraform for GCP

> **Note:** The current `terraform/` directory uses the AWS provider (ECS, RDS, ElastiCache, S3, SQS). The branch `feature/GCP-Terraform-development` is where the GCP rewrite lives. The steps below describe what each module must contain. Replace the existing modules with GCP equivalents.

### 7.1 Root `terraform/main.tf` — GCP Provider & Backend

Replace `terraform/main.tf` with:

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "vidshield-tf-state-vidshield-prod"   # match TF_STATE_BUCKET
    prefix = "envs/prod"                            # envs/dev, envs/staging for other envs
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
```

### 7.2 `terraform/variables.tf` — GCP Variables

Key variables to define:

```hcl
variable "project_id"        { type = string }
variable "region"            { type = string; default = "us-central1" }
variable "environment"       { type = string }   # dev | staging | prod
variable "gke_cluster_name"  { type = string }
variable "gke_node_count"    { type = number; default = 2 }
variable "gke_machine_type"  { type = string; default = "e2-standard-4" }
variable "db_tier"           { type = string; default = "db-g1-small" }
variable "redis_tier"        { type = string; default = "BASIC" }
variable "redis_memory_size_gb" { type = number; default = 1 }
variable "gar_repository"    { type = string; default = "vidshield" }
variable "gcs_bucket_name"   { type = string }
variable "alert_email"       { type = string; default = "" }
```

### 7.3 Module: VPC (`terraform/modules/vpc/`)

Replace the AWS VPC module with:

```hcl
# modules/vpc/main.tf
resource "google_compute_network" "vpc" {
  name                    = "${var.project}-${var.environment}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "private" {
  name          = "${var.project}-${var.environment}-private"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.48.0.0/14"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.52.0.0/20"
  }
  private_ip_google_access = true
}

# Cloud Router + NAT for private nodes to reach internet
resource "google_compute_router" "router" {
  name    = "${var.project}-${var.environment}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.project}-${var.environment}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# Private services access for Cloud SQL
resource "google_compute_global_address" "private_ip_range" {
  name          = "${var.project}-${var.environment}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}
```

### 7.4 Module: GKE (`terraform/modules/gke/`)

```hcl
# modules/gke/main.tf
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region

  # Remove default node pool — we manage our own
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = var.network_id
  subnetwork = var.subnetwork_id

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  node_config {
    machine_type    = var.machine_type
    service_account = var.node_service_account
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      env = var.environment
    }
  }

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
```

### 7.5 Module: Cloud SQL (`terraform/modules/cloud-sql/`)

```hcl
# modules/cloud-sql/main.tf
resource "google_sql_database_instance" "postgres" {
  name             = var.instance_name
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = var.tier    # db-f1-micro (dev) / db-g1-small / db-custom-2-4096 (prod)
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_size         = 20

    backup_configuration {
      enabled    = true
      start_time = "03:00"
      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 7 : 1
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_id
    }
  }

  deletion_protection = var.environment == "prod"

  depends_on = [var.private_vpc_connection]
}

resource "google_sql_database" "app_db" {
  name     = "vidshield"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = "vidshield"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}
```

### 7.6 Module: Cloud Memorystore Redis (`terraform/modules/memorystore/`)

```hcl
# modules/memorystore/main.tf
resource "google_redis_instance" "cache" {
  name           = var.instance_name
  tier           = var.tier   # BASIC (dev) / STANDARD_HA (prod)
  memory_size_gb = var.memory_size_gb
  region         = var.region

  authorized_network = var.vpc_id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  redis_version      = "REDIS_7_0"

  labels = {
    env = var.environment
  }
}
```

### 7.7 Module: GCS (`terraform/modules/gcs/`)

```hcl
# modules/gcs/main.tf
locals {
  buckets = {
    videos     = "${var.project}-videos-${var.environment}"
    thumbnails = "${var.project}-thumbnails-${var.environment}"
    artifacts  = "${var.project}-artifacts-${var.environment}"
  }
}

resource "google_storage_bucket" "buckets" {
  for_each = local.buckets

  name          = each.value
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = each.key == "videos"
  }

  lifecycle_rule {
    condition { age = 90 }
    action    { type = "SetStorageClass"; storage_class = "NEARLINE" }
  }

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Grant the app service account access
resource "google_storage_bucket_iam_member" "app_access" {
  for_each = google_storage_bucket.buckets

  bucket = each.value.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.app_service_account}"
}
```

### 7.8 Module: Artifact Registry (`terraform/modules/artifact-registry/`)

```hcl
# modules/artifact-registry/main.tf
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repository_name
  format        = "DOCKER"
  description   = "VidShield AI container images"
}
```

### 7.9 Module: Pub/Sub (`terraform/modules/pubsub/`)

```hcl
# modules/pubsub/main.tf
locals {
  topics = [
    "video-uploaded",
    "video-processed",
    "moderation-alerts",
    "stream-events",
    "analytics-events",
  ]
}

resource "google_pubsub_topic" "topics" {
  for_each = toset(local.topics)
  name     = "vidshield-${each.key}-${var.environment}"
}

resource "google_pubsub_subscription" "subs" {
  for_each = toset(local.topics)

  name  = "vidshield-${each.key}-${var.environment}-sub"
  topic = google_pubsub_topic.topics[each.key].name

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"   # 7 days

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}
```

### 7.10 `terraform/environments/dev.tfvars` — GCP version

Replace the contents with:

```hcl
project_id        = "vidshield-dev"
region            = "us-central1"
environment       = "dev"
gke_cluster_name  = "vidshield-gke-dev"
gke_node_count    = 1
gke_machine_type  = "e2-standard-2"
db_tier           = "db-f1-micro"
redis_tier        = "BASIC"
redis_memory_size_gb = 1
gar_repository    = "vidshield"
gcs_bucket_name   = "vidshield-videos-dev"
alert_email       = ""
```

`staging.tfvars`:

```hcl
project_id        = "vidshield-staging"
region            = "us-central1"
environment       = "staging"
gke_cluster_name  = "vidshield-gke-staging"
gke_node_count    = 2
gke_machine_type  = "e2-standard-2"
db_tier           = "db-g1-small"
redis_tier        = "BASIC"
redis_memory_size_gb = 2
gar_repository    = "vidshield"
gcs_bucket_name   = "vidshield-videos-staging"
alert_email       = "platform-alerts@yourcompany.com"
```

`prod.tfvars`:

```hcl
project_id        = "vidshield-prod"
region            = "us-central1"
environment       = "prod"
gke_cluster_name  = "vidshield-gke-prod"
gke_node_count    = 3
gke_machine_type  = "e2-standard-4"
db_tier           = "db-custom-2-4096"
redis_tier        = "STANDARD_HA"
redis_memory_size_gb = 4
gar_repository    = "vidshield"
gcs_bucket_name   = "vidshield-videos-prod"
alert_email       = "oncall@yourcompany.com"
```

---

## 8. Provision Infrastructure with Terraform

```bash
cd terraform

# Initialise — downloads GCP provider and connects to state bucket
terraform init

# Preview the plan
terraform plan -var-file=environments/${ENV}.tfvars -out=tfplan

# Review the plan output carefully, then apply
terraform apply tfplan
```

### 8.1 Capture Outputs

After apply, capture the key outputs:

```bash
terraform output -json > /tmp/tf-outputs.json

# Extract key values
CLOUD_SQL_IP=$(terraform output -raw cloud_sql_private_ip)
MEMORYSTORE_IP=$(terraform output -raw memorystore_host)
GKE_CLUSTER_NAME=$(terraform output -raw gke_cluster_name)

echo "Cloud SQL private IP: $CLOUD_SQL_IP"
echo "Memorystore host: $MEMORYSTORE_IP"
echo "GKE cluster: $GKE_CLUSTER_NAME"
```

### 8.2 Update Database and Redis Secrets

Now that you have the private IPs, update the secrets you left as placeholders in Step 5:

```bash
DB_PASSWORD=$(gcloud secrets versions access latest \
  --secret=vidshield-db-password --project=$PROJECT_ID)

# Update database URL
DB_URL="postgresql+asyncpg://vidshield:${DB_PASSWORD}@${CLOUD_SQL_IP}:5432/vidshield"
echo -n "$DB_URL" | gcloud secrets versions add vidshield-database-url \
  --data-file=- --project=$PROJECT_ID

DB_URL_SYNC="postgresql+psycopg2://vidshield:${DB_PASSWORD}@${CLOUD_SQL_IP}:5432/vidshield"
echo -n "$DB_URL_SYNC" | gcloud secrets versions add vidshield-database-url-sync \
  --data-file=- --project=$PROJECT_ID

# Update Redis URL
REDIS_URL="redis://${MEMORYSTORE_IP}:6379/0"
echo -n "$REDIS_URL" | gcloud secrets versions add vidshield-redis-url \
  --data-file=- --project=$PROJECT_ID

echo "Secrets updated."
```

---

## 9. Artifact Registry — Build & Push Images

### 9.1 Authenticate Docker to Artifact Registry

```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

### 9.2 Set Image Variables

```bash
IMAGE_TAG="v1.0.0"    # or use git SHA: $(git rev-parse --short HEAD)
GAR_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY}"

BACKEND_IMAGE="${GAR_BASE}/vidshieldai-backend:${IMAGE_TAG}"
WORKER_IMAGE="${GAR_BASE}/vidshieldai-agent:${IMAGE_TAG}"
FRONTEND_IMAGE="${GAR_BASE}/vidshieldai-frontend:${IMAGE_TAG}"
```

### 9.3 Build and Push Backend Image

```bash
docker build \
  --platform linux/amd64 \
  -t "${BACKEND_IMAGE}" \
  -t "${GAR_BASE}/vidshieldai-backend:latest" \
  ./backend

docker push "${BACKEND_IMAGE}"
docker push "${GAR_BASE}/vidshieldai-backend:latest"
```

### 9.4 Build and Push Worker Image

The worker uses the same Dockerfile as the backend (different entrypoint via K8s command):

```bash
docker build \
  --platform linux/amd64 \
  -t "${WORKER_IMAGE}" \
  -t "${GAR_BASE}/vidshieldai-agent:latest" \
  ./backend

docker push "${WORKER_IMAGE}"
docker push "${GAR_BASE}/vidshieldai-agent:latest"
```

### 9.5 Build and Push Frontend Image

```bash
NEXT_PUBLIC_API_URL="https://api.vidshield.ai"   # your actual domain

docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}" \
  --build-arg NEXT_PUBLIC_WS_URL="${NEXT_PUBLIC_API_URL}" \
  --build-arg NEXT_PUBLIC_APP_ENV="production" \
  --build-arg NEXT_PUBLIC_MOCK_API="false" \
  -t "${FRONTEND_IMAGE}" \
  -t "${GAR_BASE}/vidshieldai-frontend:latest" \
  ./frontend

docker push "${FRONTEND_IMAGE}"
docker push "${GAR_BASE}/vidshieldai-frontend:latest"
```

### 9.6 Verify Images in Registry

```bash
gcloud artifacts docker images list \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY}
```

---

## 10. Connect to GKE Cluster

```bash
gcloud container clusters get-credentials $GKE_CLUSTER_NAME \
  --region $REGION \
  --project $PROJECT_ID

# Verify connection
kubectl cluster-info
kubectl get nodes
```

Expected output shows nodes in `Ready` state.

---

## 11. Kubernetes Namespace & Secrets

### 11.1 Create Namespace

```bash
kubectl create namespace vidshield
kubectl config set-context --current --namespace=vidshield
```

### 11.2 Create Kubernetes Secret from Secret Manager Values

This pulls secrets from GCP Secret Manager and creates a K8s Secret. In production, use the External Secrets Operator (ESO) — for manual deployment, use this script:

```bash
# Pull all secret values
SECRET_KEY=$(gcloud secrets versions access latest --secret=vidshield-secret-key --project=$PROJECT_ID)
DATABASE_URL=$(gcloud secrets versions access latest --secret=vidshield-database-url --project=$PROJECT_ID)
DATABASE_URL_SYNC=$(gcloud secrets versions access latest --secret=vidshield-database-url-sync --project=$PROJECT_ID)
REDIS_URL=$(gcloud secrets versions access latest --secret=vidshield-redis-url --project=$PROJECT_ID)
OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=vidshield-openai-api-key --project=$PROJECT_ID)
PINECONE_API_KEY=$(gcloud secrets versions access latest --secret=vidshield-pinecone-api-key --project=$PROJECT_ID)
SENTRY_DSN=$(gcloud secrets versions access latest --secret=vidshield-sentry-dsn --project=$PROJECT_ID 2>/dev/null || echo "")

# Create K8s secret
kubectl create secret generic vidshield-secrets \
  --namespace=vidshield \
  --from-literal=SECRET_KEY="$SECRET_KEY" \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=DATABASE_URL_SYNC="$DATABASE_URL_SYNC" \
  --from-literal=REDIS_URL="$REDIS_URL" \
  --from-literal=CELERY_BROKER_URL="${REDIS_URL/\/0/\/1}" \
  --from-literal=CELERY_RESULT_BACKEND="${REDIS_URL/\/0/\/2}" \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=PINECONE_API_KEY="$PINECONE_API_KEY" \
  --from-literal=SENTRY_DSN="$SENTRY_DSN" \
  --from-literal=GCP_PROJECT_ID="$PROJECT_ID" \
  --from-literal=GCS_BUCKET_NAME="$GCS_BUCKET_NAME"

kubectl get secret vidshield-secrets -n vidshield
```

---

## 12. Workload Identity — Bind GKE to GCP Services

Workload Identity lets GKE pods authenticate as the `vidshield-app` GCP service account without any key files.

### 12.1 Create Kubernetes Service Account

```bash
kubectl create serviceaccount vidshield-app \
  --namespace=vidshield
```

### 12.2 Bind Kubernetes SA to GCP SA

```bash
APP_SA="vidshield-app@${PROJECT_ID}.iam.gserviceaccount.com"

# Allow the K8s SA to impersonate the GCP SA
gcloud iam service-accounts add-iam-policy-binding $APP_SA \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${PROJECT_ID}.svc.id.goog[vidshield/vidshield-app]" \
  --project=$PROJECT_ID

# Annotate the K8s SA
kubectl annotate serviceaccount vidshield-app \
  --namespace=vidshield \
  iam.gke.io/gcp-service-account="${APP_SA}"
```

---

## 13. Deploy Kubernetes Manifests

Create the following manifest files in a `k8s/` directory at the project root.

### 13.1 Backend API Deployment (`k8s/backend-deployment.yaml`)

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
      serviceAccountName: vidshield-app
      containers:
        - name: api
          image: REGION-docker.pkg.dev/PROJECT_ID/vidshield/vidshieldai-backend:IMAGE_TAG
          ports:
            - containerPort: 8000
          env:
            - name: APP_ENV
              value: "production"
            - name: DEBUG
              value: "false"
            - name: FORWARDED_ALLOW_IPS
              value: "*"
          envFrom:
            - secretRef:
                name: vidshield-secrets
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "2Gi"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: vidshield-backend
  namespace: vidshield
spec:
  selector:
    app: vidshield-backend
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vidshield-backend-hpa
  namespace: vidshield
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vidshield-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### 13.2 Worker Deployment (`k8s/worker-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vidshield-worker
  namespace: vidshield
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vidshield-worker
  template:
    metadata:
      labels:
        app: vidshield-worker
    spec:
      serviceAccountName: vidshield-app
      containers:
        - name: worker
          image: REGION-docker.pkg.dev/PROJECT_ID/vidshield/vidshieldai-agent:IMAGE_TAG
          command:
            - "celery"
            - "-A"
            - "app.workers.celery_app"
            - "worker"
            - "--loglevel=info"
            - "--concurrency=2"
            - "--queues=video,moderation,analytics,cleanup,reports,notifications,streams"
          envFrom:
            - secretRef:
                name: vidshield-secrets
          env:
            - name: APP_ENV
              value: "production"
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vidshield-worker-hpa
  namespace: vidshield
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vidshield-worker
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
```

### 13.3 Frontend Deployment (`k8s/frontend-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vidshield-frontend
  namespace: vidshield
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vidshield-frontend
  template:
    metadata:
      labels:
        app: vidshield-frontend
    spec:
      serviceAccountName: vidshield-app
      containers:
        - name: frontend
          image: REGION-docker.pkg.dev/PROJECT_ID/vidshield/vidshieldai-frontend:IMAGE_TAG
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: "production"
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: vidshield-frontend
  namespace: vidshield
spec:
  selector:
    app: vidshield-frontend
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP
```

### 13.4 Ingress (`k8s/ingress.yaml`)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vidshield-ingress
  namespace: vidshield
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "vidshield-static-ip"
    networking.gke.io/managed-certificates: "vidshield-cert"
    kubernetes.io/ingress.allow-http: "false"
spec:
  rules:
    - host: vidshield.ai
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: vidshield-backend
                port:
                  number: 80
          - path: /ws
            pathType: Prefix
            backend:
              service:
                name: vidshield-backend
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: vidshield-frontend
                port:
                  number: 80
---
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: vidshield-cert
  namespace: vidshield
spec:
  domains:
    - vidshield.ai
    - api.vidshield.ai
```

### 13.5 Apply All Manifests

Before applying, substitute real values using `sed`:

```bash
# Substitute placeholders with real values
find k8s/ -name "*.yaml" -exec sed -i \
  -e "s|REGION|${REGION}|g" \
  -e "s|PROJECT_ID|${PROJECT_ID}|g" \
  -e "s|IMAGE_TAG|${IMAGE_TAG}|g" \
  {} \;

# Apply all manifests
kubectl apply -f k8s/ --namespace=vidshield

# Watch rollout
kubectl rollout status deployment/vidshield-backend -n vidshield
kubectl rollout status deployment/vidshield-worker  -n vidshield
kubectl rollout status deployment/vidshield-frontend -n vidshield
```

---

## 14. Run Database Migrations

Run Alembic migrations as a one-off Kubernetes Job:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: vidshield-migrate-$(date +%Y%m%d%H%M%S)
  namespace: vidshield
spec:
  backoffLimit: 3
  template:
    spec:
      serviceAccountName: vidshield-app
      restartPolicy: Never
      containers:
        - name: migrate
          image: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY}/vidshieldai-backend:${IMAGE_TAG}
          command: ["alembic", "upgrade", "head"]
          envFrom:
            - secretRef:
                name: vidshield-secrets
          env:
            - name: APP_ENV
              value: "production"
EOF

# Wait for migration to complete
kubectl wait --for=condition=complete job -l app.kubernetes.io/name=vidshield-migrate \
  -n vidshield --timeout=120s

# Check logs
kubectl logs -n vidshield -l job-name --tail=50
```

### 14.1 Seed Admin User (First Deploy Only)

```bash
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: vidshield-seed-admin
  namespace: vidshield
spec:
  backoffLimit: 1
  template:
    spec:
      serviceAccountName: vidshield-app
      restartPolicy: Never
      containers:
        - name: seed
          image: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY}/vidshieldai-backend:${IMAGE_TAG}
          command: ["python", "scripts/seed_admin.py"]
          envFrom:
            - secretRef:
                name: vidshield-secrets
          env:
            - name: APP_ENV
              value: "production"
EOF

kubectl logs -n vidshield -l job-name=vidshield-seed-admin --tail=20
```

---

## 15. Cloud Load Balancer & CDN

### 15.1 Reserve a Static IP

```bash
gcloud compute addresses create vidshield-static-ip \
  --global \
  --project=$PROJECT_ID

# Get the IP address
LB_IP=$(gcloud compute addresses describe vidshield-static-ip \
  --global --format='value(address)' --project=$PROJECT_ID)

echo "Load balancer IP: $LB_IP"
# Point your DNS A record for vidshield.ai -> $LB_IP
```

### 15.2 Enable Cloud CDN on the Backend Bucket (Thumbnails)

```bash
# Create backend bucket for thumbnails
gcloud compute backend-buckets create vidshield-thumbnails-backend \
  --gcs-bucket-name="vidshield-thumbnails-${ENV}" \
  --enable-cdn \
  --project=$PROJECT_ID

# Cache-control headers: set on GCS objects, Cloud CDN respects them
```

### 15.3 Update the URL Map with CDN

For thumbnails served from GCS via Cloud CDN, add a path rule in the URL map to route `/thumbnails/*` to the backend bucket. This is easiest to do via Terraform (add a `google_compute_url_map` resource with the path matcher).

Manual approach for a quick check:

```bash
# Create URL map
gcloud compute url-maps create vidshield-url-map \
  --default-service=vidshield-frontend-neg \
  --project=$PROJECT_ID

# Add CDN path rule for thumbnails
gcloud compute url-maps add-path-matcher vidshield-url-map \
  --path-matcher-name=cdn-paths \
  --default-service=vidshield-frontend-neg \
  --backend-bucket-path-rules="/thumbnails/*=vidshield-thumbnails-backend" \
  --project=$PROJECT_ID
```

The GKE Ingress from Step 13.4 with the annotation `kubernetes.io/ingress.class: "gce"` automatically creates a Cloud Load Balancer — use that for the application traffic.

---

## 16. Pub/Sub Topics & Subscriptions

If you didn't use the Terraform Pub/Sub module, create topics manually:

```bash
TOPICS=(
  "video-uploaded"
  "video-processed"
  "moderation-alerts"
  "stream-events"
  "analytics-events"
)

for TOPIC in "${TOPICS[@]}"; do
  gcloud pubsub topics create "vidshield-${TOPIC}-${ENV}" \
    --project=$PROJECT_ID

  gcloud pubsub subscriptions create "vidshield-${TOPIC}-${ENV}-sub" \
    --topic="vidshield-${TOPIC}-${ENV}" \
    --ack-deadline=60 \
    --message-retention-duration=7d \
    --project=$PROJECT_ID

  echo "Created topic + subscription: vidshield-${TOPIC}-${ENV}"
done
```

---

## 17. Monitoring, Alerting & Logging

### 17.1 Create an Alerting Notification Channel

```bash
# Email notification channel
gcloud alpha monitoring channels create \
  --display-name="VidShield Ops Email" \
  --type=email \
  --channel-labels=email_address=oncall@yourcompany.com \
  --project=$PROJECT_ID
```

### 17.2 Create Alert Policies via gcloud

**High CPU on GKE nodes:**

```bash
gcloud alpha monitoring policies create \
  --policy='{
    "displayName": "VidShield GKE Node CPU > 80%",
    "conditions": [{
      "displayName": "Node CPU utilization",
      "conditionThreshold": {
        "filter": "resource.type=\"k8s_node\" AND metric.type=\"kubernetes.io/node/cpu/allocatable_utilization\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.8,
        "duration": "300s",
        "aggregations": [{"alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_MEAN"}]
      }
    }],
    "alertStrategy": {"autoClose": "604800s"},
    "combiner": "OR"
  }' \
  --project=$PROJECT_ID
```

**Cloud SQL connections > 80% of max:**

```bash
gcloud alpha monitoring policies create \
  --policy='{
    "displayName": "VidShield Cloud SQL High Connections",
    "conditions": [{
      "displayName": "Database connections",
      "conditionThreshold": {
        "filter": "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 80,
        "duration": "60s",
        "aggregations": [{"alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_MEAN"}]
      }
    }],
    "combiner": "OR"
  }' \
  --project=$PROJECT_ID
```

### 17.3 Log-Based Metrics

Create a metric for backend 5xx errors:

```bash
gcloud logging metrics create vidshield_5xx_errors \
  --description="Backend HTTP 5xx error count" \
  --log-filter='resource.type="k8s_container" AND resource.labels.container_name="api" AND jsonPayload.status>=500' \
  --project=$PROJECT_ID
```

### 17.4 Cloud Monitoring Dashboard

```bash
# Import a pre-built dashboard JSON (create dashboard.json first, or use Cloud Console)
gcloud monitoring dashboards create \
  --config-from-file=monitoring/dashboard.json \
  --project=$PROJECT_ID
```

---

## 18. Configure GitHub Actions

These secrets and variables must be set in your GitHub repository under **Settings → Secrets and variables → Actions**.

### 18.1 Set Up Workload Identity Federation for GitHub Actions

```bash
# Create the Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --description="GitHub Actions pool" \
  --display-name="GitHub Actions" \
  --project=$PROJECT_ID

# Get pool resource name
POOL_NAME=$(gcloud iam workload-identity-pools describe github-pool \
  --location=global \
  --format='value(name)' \
  --project=$PROJECT_ID)

# Create the OIDC provider inside the pool
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub OIDC Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor" \
  --attribute-condition="assertion.repository=='your-org/vidshield-ai'" \
  --project=$PROJECT_ID

# Get provider resource name
PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format='value(name)' \
  --project=$PROJECT_ID)

echo "Provider: $PROVIDER_NAME"

# Allow GitHub Actions (your repo) to impersonate the deployer SA
gcloud iam service-accounts add-iam-policy-binding \
  "vidshield-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/your-org/vidshield-ai" \
  --project=$PROJECT_ID
```

### 18.2 Set GitHub Repository Secrets

Go to **GitHub → your repo → Settings → Secrets → Actions → New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | `vidshield-prod` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | value of `$PROVIDER_NAME` from above |
| `GCP_SERVICE_ACCOUNT` | `vidshield-deployer@vidshield-prod.iam.gserviceaccount.com` |
| `GAR_LOCATION` | `us-central1` |
| `GAR_REPOSITORY` | `vidshield` |
| `GKE_CLUSTER_PROD` | `vidshield-gke-prod` |
| `GKE_CLUSTER_STAGING` | `vidshield-gke-staging` |
| `GKE_CLUSTER_LOCATION` | `us-central1` |
| `NEXT_PUBLIC_API_URL` | `https://api.vidshield.ai` |
| `API_UPSTREAM_URL` | `http://vidshield-backend.vidshield.svc.cluster.local` |

### 18.3 Set GitHub Repository Variables (non-secret)

**Settings → Variables → Actions → New repository variable:**

| Variable | Value |
|----------|-------|
| `CLOUD_CDN_URL_MAP` | `vidshield-url-map` |

---

## 19. Smoke-Test & Verification

### 19.1 Check All Pods Are Running

```bash
kubectl get pods -n vidshield

# Expected: all pods in Running state
# NAME                                  READY   STATUS    RESTARTS   AGE
# vidshield-backend-xxx-yyy             1/1     Running   0          5m
# vidshield-worker-xxx-yyy              1/1     Running   0          5m
# vidshield-frontend-xxx-yyy            1/1     Running   0          5m
```

### 19.2 Check Services and Ingress

```bash
kubectl get svc -n vidshield
kubectl get ingress -n vidshield
kubectl get managedcertificate -n vidshield
```

### 19.3 Health Check the Backend API

```bash
# Port-forward for local testing
kubectl port-forward svc/vidshield-backend 8000:80 -n vidshield &

curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: {"status": "healthy", ...}

curl -s http://localhost:8000/api/v1/ | python3 -m json.tool

kill %1   # stop port-forward
```

### 19.4 Check Celery Worker Is Connected

```bash
# Exec into a worker pod
WORKER_POD=$(kubectl get pod -n vidshield -l app=vidshield-worker -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it $WORKER_POD -n vidshield -- \
  celery -A app.workers.celery_app inspect ping
# Expected: {"celery@<hostname>": {"ok": "pong"}}
```

### 19.5 Check GCS Connectivity

```bash
BACKEND_POD=$(kubectl get pod -n vidshield -l app=vidshield-backend -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it $BACKEND_POD -n vidshield -- \
  python3 -c "
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('${GCS_BUCKET_NAME}')
print('GCS bucket accessible:', bucket.exists())
"
```

### 19.6 Check Secret Manager Access

```bash
kubectl exec -it $BACKEND_POD -n vidshield -- \
  python3 -c "
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = 'projects/${PROJECT_ID}/secrets/vidshield-secret-key/versions/latest'
response = client.access_secret_version(request={'name': name})
print('Secret accessible:', len(response.payload.data) > 0)
"
```

### 19.7 End-to-End: Upload a Test Video

```bash
# Get the ingress external IP
INGRESS_IP=$(kubectl get ingress vidshield-ingress -n vidshield \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Ingress IP: $INGRESS_IP"

# Hit the API (using Host header if DNS not yet set up)
curl -s -H "Host: vidshield.ai" \
  http://${INGRESS_IP}/api/v1/ | python3 -m json.tool
```

---

## 20. Environment-Specific Values Reference

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| GKE machine type | `e2-standard-2` | `e2-standard-2` | `e2-standard-4` |
| GKE node count | 1 | 2 | 3 (+ autoscale to 10) |
| Cloud SQL tier | `db-f1-micro` | `db-g1-small` | `db-custom-2-4096` |
| Cloud SQL HA | Zonal | Zonal | Regional |
| Redis tier | BASIC (1 GB) | BASIC (2 GB) | STANDARD_HA (4 GB) |
| Deletion protection | Off | Off | On |
| GCS force-destroy | Yes | No | No |
| Backend replicas | 1 | 2 | 2–10 (HPA) |
| Worker replicas | 1 | 2 | 2–8 (HPA) |
| Terraform state prefix | `envs/dev` | `envs/staging` | `envs/prod` |

---

## 21. Rollback Procedure

### 21.1 Roll Back a GKE Deployment

```bash
# List revision history
kubectl rollout history deployment/vidshield-backend -n vidshield

# Roll back to previous revision
kubectl rollout undo deployment/vidshield-backend -n vidshield

# Or roll back to a specific revision
kubectl rollout undo deployment/vidshield-backend -n vidshield --to-revision=3

kubectl rollout status deployment/vidshield-backend -n vidshield
```

### 21.2 Roll Back to a Specific Image Tag

```bash
OLD_TAG="v1.0.0"

kubectl set image deployment/vidshield-backend \
  api=${GAR_BASE}/vidshieldai-backend:${OLD_TAG} \
  -n vidshield

kubectl set image deployment/vidshield-worker \
  worker=${GAR_BASE}/vidshieldai-agent:${OLD_TAG} \
  -n vidshield

kubectl set image deployment/vidshield-frontend \
  frontend=${GAR_BASE}/vidshieldai-frontend:${OLD_TAG} \
  -n vidshield
```

### 21.3 Roll Back a Database Migration

```bash
# Roll back one step
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: vidshield-migrate-rollback-$(date +%s)
  namespace: vidshield
spec:
  backoffLimit: 1
  template:
    spec:
      serviceAccountName: vidshield-app
      restartPolicy: Never
      containers:
        - name: rollback
          image: ${GAR_BASE}/vidshieldai-backend:${OLD_TAG}
          command: ["alembic", "downgrade", "-1"]
          envFrom:
            - secretRef:
                name: vidshield-secrets
EOF
```

### 21.4 Roll Back Terraform Changes

```bash
cd terraform

# Find previous state version in GCS
gsutil ls -l gs://${TF_STATE_BUCKET}/envs/${ENV}/

# Restore a specific version
gsutil cp \
  gs://${TF_STATE_BUCKET}/envs/${ENV}/terraform.tfstate#<VERSION_ID> \
  gs://${TF_STATE_BUCKET}/envs/${ENV}/terraform.tfstate

# Then plan and apply to reconcile infrastructure
terraform plan -var-file=environments/${ENV}.tfvars
```

---

## Quick Reference — Most-Used Commands

```bash
# Check pod status
kubectl get pods -n vidshield

# View backend logs (last 100 lines, follow)
kubectl logs -f deployment/vidshield-backend -n vidshield --tail=100

# View worker logs
kubectl logs -f deployment/vidshield-worker -n vidshield --tail=100

# Restart a deployment
kubectl rollout restart deployment/vidshield-backend -n vidshield

# Scale manually
kubectl scale deployment/vidshield-backend --replicas=4 -n vidshield

# Open shell in backend pod
kubectl exec -it deployment/vidshield-backend -n vidshield -- bash

# Run Alembic migration manually
make k8s-migrate

# Deploy a new image tag
make k8s-rollout-backend TAG=v1.2.3 REGISTRY=us-central1-docker.pkg.dev/vidshield-prod/vidshield

# Get cluster nodes
kubectl get nodes -o wide

# Describe a failing pod
kubectl describe pod <pod-name> -n vidshield

# Get events in namespace
kubectl get events -n vidshield --sort-by='.lastTimestamp'
```
