variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "subnet_cidr" {
  description = "Primary CIDR for the workloads subnet."
  type        = string
  default     = "10.0.0.0/20"
}

variable "pods_cidr" {
  description = "Secondary range CIDR for GKE pods."
  type        = string
  default     = "10.48.0.0/14"
}

variable "services_cidr" {
  description = "Secondary range CIDR for GKE services."
  type        = string
  default     = "10.52.0.0/20"
}

variable "master_ipv4_cidr" {
  description = "CIDR for the GKE control plane private endpoint. Must be /28."
  type        = string
  default     = "172.16.0.0/28"
}

variable "private_services_cidr" {
  description = "CIDR block allocated for VPC peering with managed services (Cloud SQL, Memorystore)."
  type        = string
  default     = "10.64.0.0/16"
}
