variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "project" {
  description = "Short project name prefix for topic and subscription names."
  type        = string
  default     = "vidshield"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "app_sa_email" {
  description = "Application service account email — granted publisher and subscriber roles."
  type        = string
}
