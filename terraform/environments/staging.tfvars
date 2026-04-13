# ── staging.tfvars ─────────────────────────────────────────────────────────────
# Near-production topology, smaller instance sizes.
# terraform apply -var-file=environments/staging.tfvars

project     = "vidshield"
environment = "staging"
aws_region  = "us-east-1"
# aws_account_id = "<your-account-id>"   # set via TF_VAR_aws_account_id env var

availability_zones   = ["us-east-1a", "us-east-1b"]
vpc_cidr             = "10.1.0.0/16"
public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24"]
single_nat_gateway   = true # still cost-optimised

# ECS sizing — staging scale
api_cpu                = 512
api_memory             = 1024
api_desired_count      = 1
worker_cpu             = 1024
worker_memory          = 2048
worker_desired_count   = 1
frontend_cpu           = 256
frontend_memory        = 512
frontend_desired_count = 1

# RDS — medium, single-AZ, 7-day backups
rds_instance_class        = "db.t4g.medium"
rds_allocated_storage     = 20
rds_max_allocated_storage = 100
rds_multi_az              = false
rds_backup_retention_days = 7
rds_deletion_protection   = false
rds_skip_final_snapshot   = false

# ElastiCache
redis_node_type       = "cache.t4g.small"
redis_num_cache_nodes = 1

# S3
s3_force_destroy = false

# CloudFront
cloudfront_price_class = "PriceClass_100"
certificate_arn        = "" # set to staging ACM cert ARN if available
domain_aliases         = []
cors_origins           = "[\"https://staging.vidshield.ai\"]"

# Monitoring
api_5xx_threshold = 20
alarm_email       = "" # set to on-call email

tags = {
  CostCenter = "engineering"
  Team       = "platform"
}
