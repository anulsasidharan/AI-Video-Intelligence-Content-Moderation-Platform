output "notification_channel_id" {
  description = "Cloud Monitoring notification channel ID (empty string if alert_email is not set)."
  value       = var.alert_email != "" ? google_monitoring_notification_channel.email[0].id : ""
}

output "dashboard_name" {
  description = "Cloud Monitoring dashboard display name."
  value       = "${var.project}-${var.environment}-dashboard"
}

output "dashboard_id" {
  description = "Cloud Monitoring dashboard resource ID."
  value       = google_monitoring_dashboard.main.id
}

output "api_5xx_metric_name" {
  description = "Log-based metric name for API 5xx errors."
  value       = google_logging_metric.api_5xx_errors.name
}
