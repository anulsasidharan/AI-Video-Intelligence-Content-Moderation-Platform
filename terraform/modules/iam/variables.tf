variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "github_org" {
  description = "GitHub organisation or user that owns the repository."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (without the org prefix)."
  type        = string
  default     = "vidshield-ai"
}

variable "gar_repository_id" {
  description = "Artifact Registry repository ID. Used as a label/reference only."
  type        = string
  default     = "vidshield"
}
