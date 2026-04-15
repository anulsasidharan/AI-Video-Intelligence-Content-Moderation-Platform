locals {
  # Bucket names must be globally unique; embed project ID as suffix
  videos_bucket     = "${var.project}-${var.environment}-videos-${var.project_id}"
  thumbnails_bucket = "${var.project}-${var.environment}-thumbnails-${var.project_id}"
  artifacts_bucket  = "${var.project}-${var.environment}-artifacts-${var.project_id}"
}

# ── Videos Bucket ──────────────────────────────────────────────────────────────

resource "google_storage_bucket" "videos" {
  name          = local.videos_bucket
  location      = var.region
  project       = var.project_id
  force_destroy = var.force_destroy

  # Uniform bucket-level access: no legacy ACLs; only IAM controls access
  uniform_bucket_level_access = true

  # Versioning enabled so accidental deletes are recoverable
  versioning {
    enabled = true
  }

  # Move raw videos to Nearline after 90 days (cheaper for infrequent access)
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  # Move to Coldline after 365 days for long-term retention
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  # Delete non-current object versions older than 30 days to control costs
  lifecycle_rule {
    condition {
      days_since_noncurrent_time = 30
      with_state                 = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = {
    environment = var.environment
    purpose     = "video-storage"
    managed-by  = "terraform"
  }
}

# ── Thumbnails Bucket ──────────────────────────────────────────────────────────

resource "google_storage_bucket" "thumbnails" {
  name          = local.thumbnails_bucket
  location      = var.region
  project       = var.project_id
  force_destroy = var.force_destroy

  uniform_bucket_level_access = true

  # Thumbnails are regenerable; no versioning needed
  versioning {
    enabled = false
  }

  # Thumbnails rarely accessed after 60 days — move to Nearline
  lifecycle_rule {
    condition {
      age = 60
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type", "Cache-Control"]
    max_age_seconds = 86400
  }

  labels = {
    environment = var.environment
    purpose     = "thumbnails"
    managed-by  = "terraform"
  }
}

# ── AI Artifacts Bucket ────────────────────────────────────────────────────────

resource "google_storage_bucket" "artifacts" {
  name          = local.artifacts_bucket
  location      = var.region
  project       = var.project_id
  force_destroy = var.force_destroy

  uniform_bucket_level_access = true

  versioning {
    enabled = false
  }

  # AI analysis artifacts (frames, transcripts, reports) expire after 90 days
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "ai-artifacts"
    managed-by  = "terraform"
  }
}

# ── IAM — Application Service Account Access ───────────────────────────────────
# The app SA (used by GKE workloads via Workload Identity) gets objectAdmin on
# all three buckets. Public/read access is not granted — URLs are signed by the SA.

resource "google_storage_bucket_iam_member" "videos_app" {
  bucket = google_storage_bucket.videos.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.app_sa_email}"
}

resource "google_storage_bucket_iam_member" "thumbnails_app" {
  bucket = google_storage_bucket.thumbnails.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.app_sa_email}"
}

resource "google_storage_bucket_iam_member" "artifacts_app" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.app_sa_email}"
}

# Thumbnails bucket: allow allUsers to read (Cloud CDN serves these publicly)
resource "google_storage_bucket_iam_member" "thumbnails_public" {
  bucket = google_storage_bucket.thumbnails.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
