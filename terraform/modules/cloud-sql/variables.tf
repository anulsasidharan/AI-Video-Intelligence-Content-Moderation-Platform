variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region for the Cloud SQL instance."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "instance_name" {
  description = "Name of the Cloud SQL instance. Must be unique within the project."
  type        = string
}

variable "database_version" {
  description = "PostgreSQL version (e.g. POSTGRES_16)."
  type        = string
  default     = "POSTGRES_16"
}

variable "tier" {
  description = "Machine type for the Cloud SQL instance (e.g. db-f1-micro, db-g1-small, db-custom-2-4096)."
  type        = string
  default     = "db-g1-small"
}

variable "availability_type" {
  description = "ZONAL (single-AZ) or REGIONAL (HA with failover replica)."
  type        = string
  default     = "ZONAL"

  validation {
    condition     = contains(["ZONAL", "REGIONAL"], var.availability_type)
    error_message = "availability_type must be ZONAL or REGIONAL."
  }
}

variable "disk_size_gb" {
  description = "Initial disk size in GB. disk_autoresize is always enabled."
  type        = number
  default     = 20
}

variable "network_id" {
  description = "VPC network ID for private IP connectivity."
  type        = string
}

variable "private_vpc_connection" {
  description = "ID of the google_service_networking_connection. Used as depends_on via variable."
  type        = string
}

variable "db_name" {
  description = "Name of the application database to create."
  type        = string
  default     = "vidshield"
}

variable "db_username" {
  description = "Application database user to create."
  type        = string
  default     = "vidshield"
}

variable "db_password" {
  description = "Initial password for the database user. Stored in Secret Manager; rotated manually after bootstrap."
  type        = string
  sensitive   = true
  default     = ""
}

variable "deletion_protection" {
  description = "Prevent Terraform from deleting the instance. Set true in prod."
  type        = bool
  default     = false
}

variable "backup_enabled" {
  description = "Enable automated backups and point-in-time recovery."
  type        = bool
  default     = true
}

variable "backup_retained_count" {
  description = "Number of automated backups to retain."
  type        = number
  default     = 7
}
