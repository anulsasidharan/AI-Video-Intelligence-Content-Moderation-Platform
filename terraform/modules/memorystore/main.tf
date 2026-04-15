# ── Cloud Memorystore Redis 7 ─────────────────────────────────────────────────

resource "google_redis_instance" "cache" {
  name         = var.instance_name
  project      = var.project_id
  region       = var.region
  display_name = "VidShield Redis — ${var.environment}"

  tier           = var.tier # BASIC (dev) or STANDARD_HA (prod)
  memory_size_gb = var.memory_size_gb
  redis_version  = "REDIS_7_0"

  # Private Services Access — same peered range as Cloud SQL
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  authorized_network = var.network_id
  reserved_ip_range  = var.reserved_ip_range

  # Redis configuration: set maxmemory-policy to allkeys-lru so cache
  # evicts least-recently-used keys when memory is full (safe for Celery broker).
  redis_configs = {
    maxmemory-policy       = "allkeys-lru"
    notify-keyspace-events = "" # disable keyspace notifications (reduces overhead)
  }

  # In-transit encryption using server-managed TLS
  transit_encryption_mode = var.enable_transit_encryption ? "SERVER_AUTHENTICATION" : "DISABLED"

  # Auth token disabled — access controlled by VPC private IP only
  auth_enabled = false

  maintenance_policy {
    weekly_maintenance_window {
      day = "TUESDAY"
      start_time {
        hours   = 4
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }
}
