# ── Artifact Registry Docker Repository ───────────────────────────────────────

resource "google_artifact_registry_repository" "docker" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  format        = "DOCKER"
  description   = "VidShield AI container images — ${var.environment}"

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

# ── IAM — Deployer (GitHub Actions) can push images ───────────────────────────

resource "google_artifact_registry_repository_iam_member" "deployer_writer" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.docker.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${var.deployer_sa}"
}

# ── IAM — GKE nodes can pull images ───────────────────────────────────────────

resource "google_artifact_registry_repository_iam_member" "gke_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.docker.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${var.gke_node_sa}"
}
