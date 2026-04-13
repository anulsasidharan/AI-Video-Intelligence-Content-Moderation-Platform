variable "project" {
  description = "Project name used as a prefix for all resource names."
  type        = string
  default     = "vidshield"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID. Used to construct globally unique names (e.g. S3 buckets)."
  type        = string
}

variable "availability_zones" {
  description = "List of AZs to use (must be within aws_region)."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# ── VPC ────────────────────────────────────────────────────────────────────────

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "single_nat_gateway" {
  description = "Use a single NAT GW (cheaper for dev/staging). Set false for prod."
  type        = bool
  default     = true
}

# ── ECS images ─────────────────────────────────────────────────────────────────

variable "ecr_backend_image" {
  description = "Full ECR URI for the backend image."
  type        = string
}

variable "ecr_frontend_image" {
  description = "Full ECR URI for the frontend image."
  type        = string
}

# ── ECS sizing ─────────────────────────────────────────────────────────────────

variable "api_cpu" {
  type    = number
  default = 512
}

variable "api_memory" {
  type    = number
  default = 1024
}

variable "api_desired_count" {
  type    = number
  default = 1
}

variable "worker_cpu" {
  type    = number
  default = 1024
}

variable "worker_memory" {
  type    = number
  default = 2048
}

variable "worker_desired_count" {
  type    = number
  default = 1
}

variable "frontend_cpu" {
  type    = number
  default = 256
}

variable "frontend_memory" {
  type    = number
  default = 512
}

variable "frontend_desired_count" {
  type    = number
  default = 1
}

# ── Secrets ARNs (provisioned outside Terraform) ─────────────────────────────

variable "db_secret_arn" {
  description = "ARN of Secrets Manager secret containing DATABASE_URL."
  type        = string
}

variable "redis_secret_arn" {
  description = "ARN of Secrets Manager secret containing REDIS_URL."
  type        = string
}

variable "secret_key_arn" {
  description = "ARN of Secrets Manager secret containing the app SECRET_KEY."
  type        = string
}

variable "openai_api_key_arn" {
  description = "ARN of Secrets Manager secret for OPENAI_API_KEY."
  type        = string
}

variable "pinecone_api_key_arn" {
  description = "ARN of Secrets Manager secret for PINECONE_API_KEY."
  type        = string
}

variable "sentry_dsn_arn" {
  description = "ARN of Secrets Manager secret for SENTRY_DSN. Leave empty to skip."
  type        = string
  default     = ""
}

variable "db_password_secret_arn" {
  description = "ARN of Secrets Manager secret containing the RDS master password."
  type        = string
}

# ── RDS ────────────────────────────────────────────────────────────────────────

variable "rds_instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "rds_allocated_storage" {
  type    = number
  default = 20
}

variable "rds_max_allocated_storage" {
  type    = number
  default = 100
}

variable "rds_multi_az" {
  type    = bool
  default = false
}

variable "rds_backup_retention_days" {
  type    = number
  default = 7
}

variable "rds_deletion_protection" {
  type    = bool
  default = false
}

variable "rds_skip_final_snapshot" {
  type    = bool
  default = true
}

# ── ElastiCache ────────────────────────────────────────────────────────────────

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}

variable "redis_num_cache_nodes" {
  type    = number
  default = 1
}

# ── S3 / CloudFront ────────────────────────────────────────────────────────────

variable "s3_force_destroy" {
  type    = bool
  default = false
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS (must be in us-east-1). Leave empty to skip HTTPS."
  type        = string
  default     = ""
}

variable "domain_aliases" {
  type    = list(string)
  default = []
}

variable "cloudfront_price_class" {
  type    = string
  default = "PriceClass_100"
}

variable "cors_origins" {
  type    = string
  default = "[\"*\"]"
}

# ── WAF ────────────────────────────────────────────────────────────────────────

variable "waf_ip_rate_limit" {
  description = "Max requests per IP per 5-minute window before WAF blocks the IP. AWS minimum: 100."
  type        = number
  default     = 2000
}

variable "waf_enable_crs" {
  description = "Enable AWS Managed Core Rule Set (OWASP Top 10 protections)."
  type        = bool
  default     = true
}

variable "waf_enable_ip_reputation" {
  description = "Enable AWS Managed IP Reputation list (botnet / tor exit node blocking)."
  type        = bool
  default     = true
}

variable "waf_enable_known_bad_inputs" {
  description = "Enable AWS Managed Known Bad Inputs rule set (Log4j, SSRF, etc.)."
  type        = bool
  default     = true
}

# ── Monitoring ─────────────────────────────────────────────────────────────────

variable "alarm_email" {
  description = "Email address to subscribe to the alerts SNS topic. Leave empty to skip."
  type        = string
  default     = ""
}

variable "api_5xx_threshold" {
  type    = number
  default = 10
}

variable "tags" {
  type    = map(string)
  default = {}
}
