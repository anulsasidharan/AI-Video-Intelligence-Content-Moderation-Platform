# ── Project ────────────────────────────────────────────────────────────────────

variable "project_id" {
  description = "GCP project ID (e.g. vidshield-prod)."
  type        = string
}

variable "project" {
  description = "Short project name used as a prefix in resource names."
  type        = string
  default     = "vidshield"
}

variable "region" {
  description = "GCP region for all regional resources."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

# ── GitHub (Workload Identity Federation) ─────────────────────────────────────

variable "github_org" {
  description = "GitHub organisation or user name that owns the repo."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (without the org prefix)."
  type        = string
  default     = "vidshield-ai"
}

# ── VPC ────────────────────────────────────────────────────────────────────────

variable "subnet_cidr" {
  description = "Primary CIDR for the GKE/workloads subnet."
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
  description = "CIDR for the GKE control plane private endpoint."
  type        = string
  default     = "172.16.0.0/28"
}

variable "private_services_cidr" {
  description = "CIDR allocated for VPC peering with managed services (Cloud SQL, Memorystore)."
  type        = string
  default     = "10.64.0.0/16"
}

# ── GKE ────────────────────────────────────────────────────────────────────────

variable "gke_cluster_name" {
  description = "Name of the GKE cluster."
  type        = string
}

variable "gke_machine_type" {
  description = "Machine type for GKE worker nodes."
  type        = string
  default     = "e2-standard-4"
}

variable "gke_min_nodes" {
  description = "Minimum number of nodes per zone for autoscaling."
  type        = number
  default     = 1
}

variable "gke_max_nodes" {
  description = "Maximum number of nodes per zone for autoscaling."
  type        = number
  default     = 5
}

variable "gke_disk_size_gb" {
  description = "Boot disk size in GB for each GKE node."
  type        = number
  default     = 50
}

# ── Artifact Registry ─────────────────────────────────────────────────────────

variable "gar_repository" {
  description = "Artifact Registry repository ID (e.g. vidshield)."
  type        = string
  default     = "vidshield"
}

# ── Cloud SQL ─────────────────────────────────────────────────────────────────

variable "db_tier" {
  description = "Cloud SQL machine tier (e.g. db-f1-micro, db-g1-small, db-custom-2-4096)."
  type        = string
  default     = "db-g1-small"
}

variable "db_disk_size_gb" {
  description = "Initial disk size in GB for Cloud SQL."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Database name to create inside the Cloud SQL instance."
  type        = string
  default     = "vidshield"
}

variable "db_username" {
  description = "Database user to create."
  type        = string
  default     = "vidshield"
}

# ── Memorystore Redis ─────────────────────────────────────────────────────────

variable "redis_tier" {
  description = "Redis service tier: BASIC or STANDARD_HA."
  type        = string
  default     = "BASIC"

  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "redis_tier must be BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size_gb" {
  description = "Redis in-memory size in GB."
  type        = number
  default     = 1
}

# ── GCS ────────────────────────────────────────────────────────────────────────

variable "cors_origins" {
  description = "List of allowed CORS origins for GCS buckets."
  type        = list(string)
  default     = ["*"]
}

# ── Cloud Armor ───────────────────────────────────────────────────────────────

variable "armor_ip_rate_limit" {
  description = "Max requests per IP per minute before Cloud Armor blocks the request."
  type        = number
  default     = 100
}

variable "armor_enable_owasp" {
  description = "Enable Cloud Armor pre-configured OWASP WAF rules."
  type        = bool
  default     = true
}

# ── Monitoring ────────────────────────────────────────────────────────────────

variable "alert_email" {
  description = "Email address for Cloud Monitoring alert notifications. Leave empty to skip."
  type        = string
  default     = ""
}
