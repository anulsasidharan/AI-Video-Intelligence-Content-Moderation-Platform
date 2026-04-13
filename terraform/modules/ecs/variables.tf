variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "aws_account_id" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  description = "Public subnets for the ALB."
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnets for ECS tasks."
  type        = list(string)
}

variable "sg_alb_id" {
  type = string
}

variable "sg_ecs_api_id" {
  type = string
}

variable "sg_ecs_frontend_id" {
  type = string
}

variable "sg_ecs_worker_id" {
  type = string
}

variable "ecr_backend_image" {
  description = "Full ECR image URI for the backend (API + worker). e.g. 123456789.dkr.ecr.us-east-1.amazonaws.com/vidshield-backend:latest"
  type        = string
}

variable "ecr_frontend_image" {
  description = "Full ECR image URI for the frontend."
  type        = string
}

# ── Task sizing ────────────────────────────────────────────────────────────────

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

# ── Secrets ────────────────────────────────────────────────────────────────────

variable "db_secret_arn" {
  description = "ARN of the Secrets Manager secret containing DATABASE_URL."
  type        = string
}

variable "redis_secret_arn" {
  description = "ARN of the Secrets Manager secret containing REDIS_URL."
  type        = string
}

variable "secret_key_arn" {
  description = "ARN of the Secrets Manager secret containing the app SECRET_KEY."
  type        = string
}

variable "openai_api_key_arn" {
  description = "ARN of the Secrets Manager secret for OPENAI_API_KEY."
  type        = string
}

variable "pinecone_api_key_arn" {
  description = "ARN of the Secrets Manager secret for PINECONE_API_KEY."
  type        = string
}

variable "sentry_dsn_arn" {
  description = "ARN of the Secrets Manager secret for SENTRY_DSN. Leave empty to skip."
  type        = string
  default     = ""
}

# ── App config ─────────────────────────────────────────────────────────────────

variable "s3_videos_bucket" {
  type = string
}

variable "s3_thumbnails_bucket" {
  type = string
}

variable "s3_artifacts_bucket" {
  type = string
}

variable "cors_origins" {
  description = "JSON-encoded list of allowed CORS origins."
  type        = string
  default     = "[\"https://app.vidshield.ai\"]"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the ALB HTTPS listener. Leave empty to use HTTP only (not recommended for prod)."
  type        = string
  default     = ""
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "tags" {
  type    = map(string)
  default = {}
}
