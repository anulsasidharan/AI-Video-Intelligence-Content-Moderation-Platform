variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region for the Artifact Registry repository."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "repository_id" {
  description = "Artifact Registry repository ID (e.g. vidshield)."
  type        = string
  default     = "vidshield"
}

variable "deployer_sa" {
  description = "Service account email of the GitHub Actions deployer — granted writer access."
  type        = string
}

variable "gke_node_sa" {
  description = "Service account email of GKE nodes — granted reader access to pull images."
  type        = string
}
