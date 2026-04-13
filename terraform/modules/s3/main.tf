locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = merge(
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )

  # Bucket names must be globally unique; include account ID as suffix
  videos_bucket     = "${local.name_prefix}-videos-${var.aws_account_id}"
  thumbnails_bucket = "${local.name_prefix}-thumbnails-${var.aws_account_id}"
  artifacts_bucket  = "${local.name_prefix}-artifacts-${var.aws_account_id}"
}

# ── Videos Bucket ──────────────────────────────────────────────────────────────

resource "aws_s3_bucket" "videos" {
  bucket        = local.videos_bucket
  force_destroy = var.force_destroy
  tags          = merge(local.common_tags, { Name = local.videos_bucket, Purpose = "video-storage" })
}

resource "aws_s3_bucket_versioning" "videos" {
  bucket = aws_s3_bucket.videos.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "videos" {
  bucket                  = aws_s3_bucket.videos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"
    filter {
      prefix = ""
    }
    transition {
      days          = var.video_lifecycle_transition_days
      storage_class = "STANDARD_IA"
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET", "DELETE", "HEAD"]
    allowed_origins = var.allowed_cors_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

# ── Thumbnails Bucket ──────────────────────────────────────────────────────────

resource "aws_s3_bucket" "thumbnails" {
  bucket        = local.thumbnails_bucket
  force_destroy = var.force_destroy
  tags          = merge(local.common_tags, { Name = local.thumbnails_bucket, Purpose = "thumbnails" })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "thumbnails" {
  bucket = aws_s3_bucket.thumbnails.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "thumbnails" {
  bucket                  = aws_s3_bucket.thumbnails.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Artifacts Bucket ───────────────────────────────────────────────────────────

resource "aws_s3_bucket" "artifacts" {
  bucket        = local.artifacts_bucket
  force_destroy = var.force_destroy
  tags          = merge(local.common_tags, { Name = local.artifacts_bucket, Purpose = "ai-artifacts" })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-artifacts"
    status = "Enabled"
    filter {
      prefix = ""
    }
    expiration {
      days = var.artifact_expiration_days
    }
  }
}
