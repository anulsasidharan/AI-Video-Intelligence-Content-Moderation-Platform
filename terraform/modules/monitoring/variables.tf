variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "project" {
  description = "Short project name prefix."
  type        = string
  default     = "vidshield"
}

variable "region" {
  description = "GCP region."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "alert_email" {
  description = "Email address for alert notifications. Leave empty to skip notification channel creation."
  type        = string
  default     = ""
}

variable "gke_cluster_name" {
  description = "GKE cluster name — used to scope metric filters."
  type        = string
}

variable "cloud_sql_instance" {
  description = "Cloud SQL instance name — used to scope metric filters."
  type        = string
}

variable "redis_instance_id" {
  description = "Cloud Memorystore Redis instance ID — used to scope metric filters."
  type        = string
}

variable "api_5xx_threshold" {
  description = "Number of 5xx errors per 5 minutes that triggers the alert."
  type        = number
  default     = 10
}

variable "api_health_check_host" {
  description = "Hostname for the API uptime check (e.g. api.vidshield.ai). Leave empty to skip."
  type        = string
  default     = ""
}
