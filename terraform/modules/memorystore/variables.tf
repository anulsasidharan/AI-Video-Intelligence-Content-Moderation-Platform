variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region for the Memorystore instance."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "instance_name" {
  description = "Name of the Memorystore Redis instance."
  type        = string
}

variable "tier" {
  description = "Service tier: BASIC (no replication) or STANDARD_HA (replicated, automatic failover)."
  type        = string
  default     = "BASIC"

  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.tier)
    error_message = "tier must be BASIC or STANDARD_HA."
  }
}

variable "memory_size_gb" {
  description = "Redis in-memory capacity in GB."
  type        = number
  default     = 1
}

variable "network_id" {
  description = "VPC network ID for private connectivity."
  type        = string
}

variable "reserved_ip_range" {
  description = "Name of the reserved IP range for private services access."
  type        = string
}

variable "enable_transit_encryption" {
  description = "Enable TLS in-transit encryption. Requires clients to use TLS connections."
  type        = bool
  default     = false
}
