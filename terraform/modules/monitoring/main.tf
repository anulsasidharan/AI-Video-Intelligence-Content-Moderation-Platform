locals {
  name_prefix = "${var.project}-${var.environment}"
}

# ── Notification Channel ───────────────────────────────────────────────────────

resource "google_monitoring_notification_channel" "email" {
  count = var.alert_email != "" ? 1 : 0

  project      = var.project_id
  display_name = "VidShield Ops — ${var.environment}"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }

  force_delete = true
}

locals {
  notification_channels = var.alert_email != "" ? [
    google_monitoring_notification_channel.email[0].id
  ] : []
}

# ── Log-Based Metrics ──────────────────────────────────────────────────────────
# Equivalent to CloudWatch Log Metric Filters

resource "google_logging_metric" "api_5xx_errors" {
  name    = "${local.name_prefix}-api-5xx-errors"
  project = var.project_id
  filter  = <<-EOT
    resource.type="k8s_container"
    resource.labels.container_name="api"
    jsonPayload.status>=500
  EOT

  metric_descriptor {
    metric_kind  = "DELTA"
    value_type   = "INT64"
    unit         = "1"
    display_name = "API 5xx Errors"
  }
}

resource "google_logging_metric" "celery_task_failures" {
  name    = "${local.name_prefix}-celery-failures"
  project = var.project_id
  filter  = <<-EOT
    resource.type="k8s_container"
    resource.labels.container_name="worker"
    jsonPayload.status="FAILURE"
  EOT

  metric_descriptor {
    metric_kind  = "DELTA"
    value_type   = "INT64"
    unit         = "1"
    display_name = "Celery Task Failures"
  }
}

# ── Alert Policies ─────────────────────────────────────────────────────────────

# GKE: API container CPU > 80%
resource "google_monitoring_alert_policy" "gke_api_cpu" {
  project      = var.project_id
  display_name = "[${var.environment}] GKE API Container CPU > 80%"
  combiner     = "OR"

  conditions {
    display_name = "API container CPU utilization"

    condition_threshold {
      filter          = "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${var.gke_cluster_name}\" AND resource.labels.container_name=\"api\" AND metric.type=\"kubernetes.io/container/cpu/request_utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      duration        = "300s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "604800s" # auto-close after 7 days if not resolved
  }

  documentation {
    content   = "The GKE API container CPU utilization has exceeded 80% for more than 5 minutes in the ${var.environment} environment. Check HPA and consider scaling up."
    mime_type = "text/markdown"
  }
}

# GKE: Worker container CPU > 85%
resource "google_monitoring_alert_policy" "gke_worker_cpu" {
  project      = var.project_id
  display_name = "[${var.environment}] GKE Worker Container CPU > 85%"
  combiner     = "OR"

  conditions {
    display_name = "Celery worker CPU utilization"

    condition_threshold {
      filter          = "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${var.gke_cluster_name}\" AND resource.labels.container_name=\"worker\" AND metric.type=\"kubernetes.io/container/cpu/request_utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.85
      duration        = "300s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "Celery worker CPU is above 85%. AI video analysis pipeline may be backlogged. Consider scaling up the worker deployment."
    mime_type = "text/markdown"
  }
}

# GKE: Pod restart loop (CrashLoopBackOff)
resource "google_monitoring_alert_policy" "pod_restarts" {
  project      = var.project_id
  display_name = "[${var.environment}] GKE Pod Restart Rate High"
  combiner     = "OR"

  conditions {
    display_name = "Pod restart count"

    condition_threshold {
      filter          = "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${var.gke_cluster_name}\" AND metric.type=\"kubernetes.io/container/restart_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "600s"

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.labels.pod_name"]
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "86400s"
  }

  documentation {
    content   = "A pod in the ${var.environment} cluster is restarting frequently. Likely a CrashLoopBackOff. Run: kubectl get pods -n vidshield"
    mime_type = "text/markdown"
  }
}

# Cloud SQL: CPU > 80%
resource "google_monitoring_alert_policy" "cloud_sql_cpu" {
  project      = var.project_id
  display_name = "[${var.environment}] Cloud SQL CPU > 80%"
  combiner     = "OR"

  conditions {
    display_name = "Cloud SQL CPU utilization"

    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"${var.project_id}:${var.cloud_sql_instance}\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      duration        = "300s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "Cloud SQL CPU is above 80%. Consider upgrading the instance tier or optimising slow queries. Check query insights in the GCP Console."
    mime_type = "text/markdown"
  }
}

# Cloud SQL: active connections > 150
resource "google_monitoring_alert_policy" "cloud_sql_connections" {
  project      = var.project_id
  display_name = "[${var.environment}] Cloud SQL Connections > 150"
  combiner     = "OR"

  conditions {
    display_name = "Cloud SQL active connections"

    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"${var.project_id}:${var.cloud_sql_instance}\" AND metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\""
      comparison      = "COMPARISON_GT"
      threshold_value = 150
      duration        = "60s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "Cloud SQL active connections exceeded 150. Check for connection pool leaks (PgBouncer may be needed). Current max_connections is 200."
    mime_type = "text/markdown"
  }
}

# Cloud SQL: disk utilization > 80%
resource "google_monitoring_alert_policy" "cloud_sql_disk" {
  project      = var.project_id
  display_name = "[${var.environment}] Cloud SQL Disk > 80%"
  combiner     = "OR"

  conditions {
    display_name = "Cloud SQL disk utilization"

    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"${var.project_id}:${var.cloud_sql_instance}\" AND metric.type=\"cloudsql.googleapis.com/database/disk/utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      duration        = "300s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "604800s"
  }
}

# Memorystore: memory usage > 85%
resource "google_monitoring_alert_policy" "redis_memory" {
  project      = var.project_id
  display_name = "[${var.environment}] Redis Memory > 85%"
  combiner     = "OR"

  conditions {
    display_name = "Redis memory usage ratio"

    condition_threshold {
      filter          = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${var.redis_instance_id}\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.85
      duration        = "300s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "Redis memory is above 85%. Since maxmemory-policy is allkeys-lru, eviction is happening. Consider increasing the Memorystore tier."
    mime_type = "text/markdown"
  }
}

# API 5xx error rate (log-based metric)
resource "google_monitoring_alert_policy" "api_5xx" {
  project      = var.project_id
  display_name = "[${var.environment}] API 5xx Error Rate High"
  combiner     = "OR"

  conditions {
    display_name = "API 5xx error count"

    condition_threshold {
      filter          = "resource.type=\"k8s_container\" AND metric.type=\"logging.googleapis.com/user/${local.name_prefix}-api-5xx-errors\""
      comparison      = "COMPARISON_GT"
      threshold_value = var.api_5xx_threshold
      duration        = "300s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "The API is returning more than ${var.api_5xx_threshold} 5xx errors per 5-minute window. Check pod logs: kubectl logs -f deployment/vidshield-backend -n vidshield"
    mime_type = "text/markdown"
  }

  depends_on = [google_logging_metric.api_5xx_errors]
}

# ── Uptime Checks ──────────────────────────────────────────────────────────────

resource "google_monitoring_uptime_check_config" "api_health" {
  count = var.api_health_check_host != "" ? 1 : 0

  project      = var.project_id
  display_name = "[${var.environment}] API Health Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/health"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.api_health_check_host
    }
  }

  content_matchers {
    content = "healthy"
    matcher = "CONTAINS_STRING"
  }
}

# Alert when uptime check fails from 2+ regions
resource "google_monitoring_alert_policy" "api_uptime" {
  count = var.api_health_check_host != "" ? 1 : 0

  project      = var.project_id
  display_name = "[${var.environment}] API Uptime Check Failed"
  combiner     = "OR"

  conditions {
    display_name = "Uptime check failure"

    condition_threshold {
      filter          = "resource.type=\"uptime_url\" AND metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.labels.check_id=\"${google_monitoring_uptime_check_config.api_health[0].uptime_check_id}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "120s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.labels.host"]
      }
    }
  }

  notification_channels = local.notification_channels
  alert_strategy {
    auto_close = "86400s"
  }

  documentation {
    content   = "The API health check at /health is failing from multiple GCP regions. The service may be down."
    mime_type = "text/markdown"
  }
}

# ── Cloud Monitoring Dashboard ──────────────────────────────────────────────────

resource "google_monitoring_dashboard" "main" {
  project = var.project_id
  dashboard_json = jsonencode({
    displayName = "VidShield — ${upper(var.environment)} Overview"
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "GKE API — CPU Utilization"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${var.gke_cluster_name}\" AND resource.labels.container_name=\"api\" AND metric.type=\"kubernetes.io/container/cpu/request_utilization\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis             = { label = "CPU Utilization", scale = "LINEAR" }
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "GKE Worker — CPU Utilization"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${var.gke_cluster_name}\" AND resource.labels.container_name=\"worker\" AND metric.type=\"kubernetes.io/container/cpu/request_utilization\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis             = { label = "CPU Utilization", scale = "LINEAR" }
            }
          }
        },
        {
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Cloud SQL — CPU & Connections"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"${var.project_id}:${var.cloud_sql_instance}\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\""
                      aggregation = {
                        alignmentPeriod  = "60s"
                        perSeriesAligner = "ALIGN_MEAN"
                      }
                    }
                  }
                  plotType       = "LINE"
                  legendTemplate = "CPU"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"${var.project_id}:${var.cloud_sql_instance}\" AND metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\""
                      aggregation = {
                        alignmentPeriod  = "60s"
                        perSeriesAligner = "ALIGN_MEAN"
                      }
                    }
                  }
                  plotType       = "LINE"
                  legendTemplate = "Connections"
                }
              ]
              timeshiftDuration = "0s"
              yAxis             = { label = "Value", scale = "LINEAR" }
            }
          }
        },
        {
          xPos   = 6
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Redis — Memory Usage Ratio"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${var.redis_instance_id}\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis             = { label = "Usage Ratio", scale = "LINEAR" }
            }
          }
        },
        {
          yPos   = 8
          width  = 12
          height = 4
          widget = {
            title = "API 5xx Error Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"k8s_container\" AND metric.type=\"logging.googleapis.com/user/${local.name_prefix}-api-5xx-errors\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "STACKED_BAR"
              }]
              timeshiftDuration = "0s"
              yAxis             = { label = "Errors / min", scale = "LINEAR" }
            }
          }
        }
      ]
    }
  })
}
