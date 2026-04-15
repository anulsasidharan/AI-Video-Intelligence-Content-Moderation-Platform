locals {
  name_prefix = "${var.project_id}-${var.environment}"
}

# ── Application Service Account ────────────────────────────────────────────────
# Used by GKE workloads (backend API, Celery workers) via Workload Identity.
# Permissions are scoped to the minimum needed for production operation.

resource "google_service_account" "app" {
  account_id   = "${var.environment}-vidshield-app"
  display_name = "VidShield App (${var.environment})"
  description  = "GKE workloads — Workload Identity principal for backend + worker pods"
  project      = var.project_id
}

# GCS: read/write videos, thumbnails, artifacts
resource "google_project_iam_member" "app_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Secret Manager: read secrets at pod startup
resource "google_project_iam_member" "app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Pub/Sub: publish and subscribe
resource "google_project_iam_member" "app_pubsub_editor" {
  project = var.project_id
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Cloud SQL: connect via Cloud SQL Auth Proxy
resource "google_project_iam_member" "app_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Cloud Monitoring: write custom metrics
resource "google_project_iam_member" "app_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Cloud Trace: write trace data
resource "google_project_iam_member" "app_trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Cloud Logging: write logs
resource "google_project_iam_member" "app_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# ── GKE Node Service Account ───────────────────────────────────────────────────
# Minimal permissions for GKE nodes: pull images from Artifact Registry,
# write logs and metrics. Workload-level permissions are handled by the app SA.

resource "google_service_account" "gke_node" {
  account_id   = "${var.environment}-vidshield-gke-node"
  display_name = "VidShield GKE Node (${var.environment})"
  description  = "GKE node pool service account — least privilege"
  project      = var.project_id
}

# Pull images from Artifact Registry
resource "google_project_iam_member" "gke_node_gar_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

# Write logs to Cloud Logging
resource "google_project_iam_member" "gke_node_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

# Write metrics to Cloud Monitoring
resource "google_project_iam_member" "gke_node_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

# Read project metadata (used by GKE system components)
resource "google_project_iam_member" "gke_node_metadata_viewer" {
  project = var.project_id
  role    = "roles/stackdriver.resourceMetadata.writer"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

# ── Deployer Service Account (GitHub Actions) ──────────────────────────────────

resource "google_service_account" "deployer" {
  account_id   = "${var.environment}-vidshield-deployer"
  display_name = "VidShield GitHub Actions Deployer (${var.environment})"
  description  = "CI/CD: builds images, pushes to Artifact Registry, deploys to GKE"
  project      = var.project_id
}

# Push images to Artifact Registry
resource "google_project_iam_member" "deployer_gar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Deploy to GKE (set image on deployments, run Jobs)
resource "google_project_iam_member" "deployer_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Invalidate Cloud CDN cache on frontend deploys
resource "google_project_iam_member" "deployer_compute_viewer" {
  project = var.project_id
  role    = "roles/compute.networkViewer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_cdn_invalidator" {
  project = var.project_id
  role    = "roles/compute.networkAdmin"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# ── Workload Identity Federation for GitHub Actions ───────────────────────────
# Allows GitHub Actions to authenticate as the deployer SA without a key file.

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "${var.environment}-github-pool"
  project                   = var.project_id
  display_name              = "GitHub Actions — ${var.environment}"
  description               = "WIF pool for GitHub Actions OIDC authentication"
  disabled                  = false
}

resource "google_iam_workload_identity_pool_provider" "github_oidc" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "${var.environment}-github-oidc"
  project                            = var.project_id
  display_name                       = "GitHub OIDC Provider"
  description                        = "Maps GitHub OIDC tokens to GCP identities"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  # Attribute mapping: translate GitHub OIDC claims to Google attributes
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.actor"      = "assertion.actor"
    "attribute.ref"        = "assertion.ref"
  }

  # Restrict to the specific GitHub repository
  attribute_condition = "assertion.repository == '${var.github_org}/${var.github_repo}'"
}

# Allow GitHub Actions (from the configured repo) to impersonate the deployer SA
resource "google_service_account_iam_member" "github_wif_deployer" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_org}/${var.github_repo}"
}

# ── Workload Identity binding for GKE pods ────────────────────────────────────
# Binds the Kubernetes SA "vidshield-app" in the "vidshield" namespace
# to the GCP app service account.

resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.app.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[vidshield/vidshield-app]"
}
