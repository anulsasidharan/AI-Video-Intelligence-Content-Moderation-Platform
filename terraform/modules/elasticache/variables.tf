variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for the ElastiCache subnet group."
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID to attach to the Redis cluster."
  type        = string
}

variable "node_type" {
  description = "ElastiCache node type."
  type        = string
  default     = "cache.t4g.small"
}

variable "num_cache_nodes" {
  description = "Number of cache nodes (1 for single-node, >1 for cluster)."
  type        = number
  default     = 1
}

variable "engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

variable "at_rest_encryption_enabled" {
  description = "Enable encryption at rest."
  type        = bool
  default     = true
}

variable "transit_encryption_enabled" {
  description = "Enable in-transit TLS encryption."
  type        = bool
  default     = true
}

variable "snapshot_retention_limit" {
  description = "Number of days to retain Redis snapshots."
  type        = number
  default     = 1
}

variable "tags" {
  type    = map(string)
  default = {}
}
