locals {
  name_prefix = var.instance_name
}

# ── Cloud SQL Instance ─────────────────────────────────────────────────────────

resource "google_sql_database_instance" "postgres" {
  name             = var.instance_name
  project          = var.project_id
  region           = var.region
  database_version = var.database_version

  # Prevent accidental deletion in production
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    availability_type = var.availability_type # ZONAL (dev) or REGIONAL (prod)
    disk_autoresize   = true
    disk_size         = var.disk_size_gb
    disk_type         = "PD_SSD"

    # Private IP only — no public IP exposed
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id

      # SSL required for all connections
      ssl_mode = "ENCRYPTED_ONLY"
    }

    # Automated backups with point-in-time recovery
    backup_configuration {
      enabled                        = var.backup_enabled
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.backup_enabled
      transaction_log_retention_days = var.backup_enabled ? 7 : 1

      backup_retention_settings {
        retained_backups = var.backup_retained_count
        retention_unit   = "COUNT"
      }
    }

    # Performance insights — equivalent to RDS Performance Insights
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = false
      record_client_address   = false
    }

    # Maintenance window: Sunday 05:00 UTC (low-traffic window)
    maintenance_window {
      day          = 1 # Sunday
      hour         = 5
      update_track = "stable"
    }

    # Database flags — mirrors the RDS parameter group settings
    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000" # log queries slower than 1 second
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    database_flags {
      name  = "max_connections"
      value = "200"
    }

    user_labels = {
      environment = var.environment
      managed-by  = "terraform"
    }
  }

  # Cloud SQL depends on the private VPC peering connection existing first
  depends_on = [var.private_vpc_connection]

  lifecycle {
    # Ignore changes to the first-boot password (managed externally via Secret Manager)
    ignore_changes = [settings[0].backup_configuration[0].start_time]
  }
}

# ── Database ───────────────────────────────────────────────────────────────────

resource "google_sql_database" "app" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
  charset  = "UTF8"
}

# ── Database User ──────────────────────────────────────────────────────────────
# Password is managed in GCP Secret Manager; Terraform only creates the user.
# The password is set once and then rotated manually or via Secret Manager.

resource "google_sql_user" "app" {
  name     = var.db_username
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
  password = var.db_password

  lifecycle {
    ignore_changes = [password]
  }
}
