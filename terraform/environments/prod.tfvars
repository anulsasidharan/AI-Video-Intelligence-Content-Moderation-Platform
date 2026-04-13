# ── prod.tfvars ────────────────────────────────────────────────────────────────
# Full-scale production configuration.
# Multi-AZ RDS, two NAT gateways, deletion protection, sensitive alarms.
# terraform apply -var-file=environments/prod.tfvars

project        = "vidshieldai"
environment    = "prod"
aws_region     = "us-east-1"
aws_account_id = "602498848126"

availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
vpc_cidr             = "10.2.0.0/16"
public_subnet_cidrs  = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
private_subnet_cidrs = ["10.2.11.0/24", "10.2.12.0/24", "10.2.13.0/24"]
single_nat_gateway   = false # one NAT GW per AZ for high availability

# ECS sizing — production scale
api_cpu                = 1024
api_memory             = 2048
api_desired_count      = 2
worker_cpu             = 2048
worker_memory          = 4096
worker_desired_count   = 2
frontend_cpu           = 512
frontend_memory        = 1024
frontend_desired_count = 2

# RDS — production grade: Multi-AZ, deletion protection, 30-day backups
rds_instance_class        = "db.r8g.large"
rds_allocated_storage     = 50
rds_max_allocated_storage = 500
rds_multi_az              = true
rds_backup_retention_days = 30
rds_deletion_protection   = true
rds_skip_final_snapshot   = false

# ElastiCache — two replicas for HA
redis_node_type       = "cache.r7g.large"
redis_num_cache_nodes = 2

# S3 — never allow force destruction
s3_force_destroy = false

# CloudFront — global CDN, custom domain with ACM cert
cloudfront_price_class = "PriceClass_All"
# certificate_arn = "arn:aws:acm:us-east-1:602498848126:certificate/<cert-id>"
domain_aliases = ["orionvexa.ca", "www.orionvexa.ca"]
cors_origins   = "[\"https://orionvexa.ca\",\"https://www.orionvexa.ca\",\"https://*.orionvexa.ca\"]"

# ECR images
ecr_backend_image  = "602498848126.dkr.ecr.us-east-1.amazonaws.com/vidshieldai-backend-prod:latest"
ecr_frontend_image = "602498848126.dkr.ecr.us-east-1.amazonaws.com/vidshieldai-frontend-prod:latest"

# Secrets Manager ARNs
db_password_secret_arn = "arn:aws:secretsmanager:us-east-1:602498848126:secret:vidshieldai/prod/db-password-hUQ8J2"
db_secret_arn          = "arn:aws:secretsmanager:us-east-1:602498848126:secret:vidshieldai/prod/db-secret-Vs9ivB"
redis_secret_arn       = "arn:aws:secretsmanager:us-east-1:602498848126:secret:redis_url-atZHYy"
secret_key_arn         = "arn:aws:secretsmanager:us-east-1:602498848126:secret:SECRET_KEY-6o4XtX"
openai_api_key_arn     = "arn:aws:secretsmanager:us-east-1:602498848126:secret:OPENAI_API_KEY-sSWSJz"
pinecone_api_key_arn   = "arn:aws:secretsmanager:us-east-1:602498848126:secret:PINECONE_API_KEY-CpsRmh"

# Monitoring — tight thresholds for production SLA
api_5xx_threshold = 5
alarm_email       = "anu.sasidharan@orionvexa.ca"

tags = {
  CostCenter  = "engineering"
  Team        = "platform"
  Criticality = "production"
}
