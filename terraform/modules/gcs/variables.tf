variable "project_id" {
  description = "GCP project ID (used to ensure globally unique bucket names)."
  type        = string
}

variable "project" {
  description = "Short project name prefix for bucket names."
  type        = string
  default     = "vidshield"
}

variable "region" {
  description = "GCS bucket location (regional)."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "app_sa_email" {
  description = "Application service account email to grant objectAdmin access."
  type        = string
}

variable "cors_origins" {
  description = "List of allowed CORS origins for GCS buckets."
  type        = list(string)
  default     = ["*"]
}

variable "force_destroy" {
  description = "Allow Terraform to delete non-empty buckets. Set true only for dev."
  type        = bool
  default     = false
}
