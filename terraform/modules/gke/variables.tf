variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region for the cluster."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "cluster_name" {
  description = "Name of the GKE cluster."
  type        = string
}

variable "network_id" {
  description = "VPC network ID the cluster will be placed in."
  type        = string
}

variable "subnetwork_id" {
  description = "Subnetwork ID for the GKE nodes."
  type        = string
}

variable "pods_range_name" {
  description = "Secondary range name for GKE pods."
  type        = string
}

variable "services_range_name" {
  description = "Secondary range name for GKE services."
  type        = string
}

variable "master_ipv4_cidr" {
  description = "CIDR block for the GKE control plane private endpoint (/28)."
  type        = string
  default     = "172.16.0.0/28"
}

variable "node_machine_type" {
  description = "Machine type for worker nodes."
  type        = string
  default     = "e2-standard-4"
}

variable "min_nodes" {
  description = "Minimum number of nodes per zone."
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum number of nodes per zone."
  type        = number
  default     = 5
}

variable "disk_size_gb" {
  description = "Boot disk size in GB for each node."
  type        = number
  default     = 50
}

variable "gke_node_sa" {
  description = "Service account email for GKE nodes."
  type        = string
}
