locals {
  name_prefix = "${var.project}-${var.environment}"

  # All Pub/Sub topics for VidShield (equivalent to the SQS queues + DLQs)
  topics = {
    video-uploaded    = { retention_days = 7, ack_deadline = 60 }
    video-processed   = { retention_days = 7, ack_deadline = 60 }
    moderation-alerts = { retention_days = 14, ack_deadline = 30 }
    stream-events     = { retention_days = 1, ack_deadline = 30 }
    analytics-events  = { retention_days = 3, ack_deadline = 30 }
  }
}

# ── Topics ─────────────────────────────────────────────────────────────────────

resource "google_pubsub_topic" "topics" {
  for_each = local.topics

  name    = "${local.name_prefix}-${each.key}"
  project = var.project_id

  # Message retention: keep undelivered messages for the configured window
  message_retention_duration = "${each.value.retention_days * 86400}s"

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

# ── Dead Letter Topics ─────────────────────────────────────────────────────────
# Messages that fail delivery after max_delivery_attempts are forwarded here.

resource "google_pubsub_topic" "dlq_topics" {
  for_each = local.topics

  name    = "${local.name_prefix}-${each.key}-dlq"
  project = var.project_id

  message_retention_duration = "${7 * 86400}s" # keep DLQ messages for 7 days

  labels = {
    environment = var.environment
    purpose     = "dead-letter"
    managed-by  = "terraform"
  }
}

# ── Dead Letter Subscriptions ──────────────────────────────────────────────────

resource "google_pubsub_subscription" "dlq_subscriptions" {
  for_each = local.topics

  name    = "${local.name_prefix}-${each.key}-dlq-sub"
  topic   = google_pubsub_topic.dlq_topics[each.key].name
  project = var.project_id

  ack_deadline_seconds       = 600
  message_retention_duration = "${7 * 86400}s"

  expiration_policy {
    ttl = "" # never expire the DLQ subscription
  }

  labels = {
    environment = var.environment
    purpose     = "dead-letter"
    managed-by  = "terraform"
  }
}

# ── Primary Subscriptions ─────────────────────────────────────────────────────
# The Celery workers pull messages from these subscriptions.

resource "google_pubsub_subscription" "subscriptions" {
  for_each = local.topics

  name    = "${local.name_prefix}-${each.key}-sub"
  topic   = google_pubsub_topic.topics[each.key].name
  project = var.project_id

  ack_deadline_seconds       = each.value.ack_deadline
  message_retention_duration = "${each.value.retention_days * 86400}s"

  # Retry policy with exponential backoff
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # Route undeliverable messages to the DLQ after 5 failed attempts
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq_topics[each.key].id
    max_delivery_attempts = 5
  }

  expiration_policy {
    ttl = "" # never expire active subscriptions
  }

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

# ── IAM — Application Service Account ─────────────────────────────────────────
# The app SA (running in GKE via Workload Identity) can publish and subscribe
# to all VidShield topics and subscriptions.

resource "google_pubsub_topic_iam_member" "app_publisher" {
  for_each = local.topics

  project = var.project_id
  topic   = google_pubsub_topic.topics[each.key].name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.app_sa_email}"
}

resource "google_pubsub_subscription_iam_member" "app_subscriber" {
  for_each = local.topics

  project      = var.project_id
  subscription = google_pubsub_subscription.subscriptions[each.key].name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${var.app_sa_email}"
}
