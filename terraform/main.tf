terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state — provision this S3 bucket and DynamoDB table once before first apply:
  #   aws s3api create-bucket --bucket vidshield-tf-state-<account-id> --region us-east-1
  #   aws dynamodb create-table --table-name vidshield-tf-locks \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST --region us-east-1
  #
  # Then uncomment:
  #
  backend "s3" {
    bucket         = "vidshield-tf-state-602498848126"
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "vidshield-tf-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      {
        Project     = var.project
        Environment = var.environment
        ManagedBy   = "terraform"
      },
      var.tags,
    )
  }
}

# ── Data sources ───────────────────────────────────────────────────────────────

data "aws_caller_identity" "current" {}

locals {
  account_id = coalesce(var.aws_account_id, data.aws_caller_identity.current.account_id)
}

# ── Module: VPC & Networking (I-01) ───────────────────────────────────────────

module "vpc" {
  source = "./modules/vpc"

  project              = var.project
  environment          = var.environment
  aws_region           = var.aws_region
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  single_nat_gateway   = var.single_nat_gateway
  tags                 = var.tags
}

# ── Module: RDS PostgreSQL 16 (I-03) ──────────────────────────────────────────

module "rds" {
  source = "./modules/rds"

  project                = var.project
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  subnet_ids             = module.vpc.private_subnet_ids
  security_group_id      = module.vpc.sg_rds_id
  instance_class         = var.rds_instance_class
  allocated_storage      = var.rds_allocated_storage
  max_allocated_storage  = var.rds_max_allocated_storage
  multi_az               = var.rds_multi_az
  backup_retention_days  = var.rds_backup_retention_days
  deletion_protection    = var.rds_deletion_protection
  skip_final_snapshot    = var.rds_skip_final_snapshot
  db_password_secret_arn = var.db_password_secret_arn
  tags                   = var.tags
}

# ── Module: ElastiCache Redis 7 (I-04) ────────────────────────────────────────

module "elasticache" {
  source = "./modules/elasticache"

  project           = var.project
  environment       = var.environment
  subnet_ids        = module.vpc.private_subnet_ids
  security_group_id = module.vpc.sg_redis_id
  node_type         = var.redis_node_type
  num_cache_nodes   = var.redis_num_cache_nodes
  tags              = var.tags
}

# ── Module: S3 Buckets (I-05) ─────────────────────────────────────────────────

module "s3" {
  source = "./modules/s3"

  project        = var.project
  environment    = var.environment
  aws_account_id = local.account_id
  force_destroy  = var.s3_force_destroy
  tags           = var.tags
}

# ── Module: ECS Fargate (I-02) ────────────────────────────────────────────────

module "ecs" {
  source = "./modules/ecs"

  project        = var.project
  environment    = var.environment
  aws_region     = var.aws_region
  aws_account_id = local.account_id

  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  sg_alb_id          = module.vpc.sg_alb_id
  sg_ecs_api_id      = module.vpc.sg_ecs_api_id
  sg_ecs_frontend_id = module.vpc.sg_ecs_frontend_id
  sg_ecs_worker_id   = module.vpc.sg_ecs_worker_id

  ecr_backend_image  = var.ecr_backend_image
  ecr_frontend_image = var.ecr_frontend_image

  api_cpu                = var.api_cpu
  api_memory             = var.api_memory
  api_desired_count      = var.api_desired_count
  worker_cpu             = var.worker_cpu
  worker_memory          = var.worker_memory
  worker_desired_count   = var.worker_desired_count
  frontend_cpu           = var.frontend_cpu
  frontend_memory        = var.frontend_memory
  frontend_desired_count = var.frontend_desired_count

  db_secret_arn        = var.db_secret_arn
  redis_secret_arn     = var.redis_secret_arn
  secret_key_arn       = var.secret_key_arn
  openai_api_key_arn   = var.openai_api_key_arn
  pinecone_api_key_arn = var.pinecone_api_key_arn
  sentry_dsn_arn       = var.sentry_dsn_arn

  s3_videos_bucket     = module.s3.videos_bucket_id
  s3_thumbnails_bucket = module.s3.thumbnails_bucket_id
  s3_artifacts_bucket  = module.s3.artifacts_bucket_id
  cors_origins         = var.cors_origins
  certificate_arn      = var.certificate_arn

  tags = var.tags
}

# ── Module: WAF — CLOUDFRONT scope (W-02a) ────────────────────────────────────
# Must be in us-east-1 for CloudFront. Since our default region is us-east-1
# this module uses the default provider. If you deploy to another region,
# add a provider alias and pass it here via `providers`.

module "waf_cloudfront" {
  source = "./modules/waf"

  project     = var.project
  environment = var.environment
  scope       = "CLOUDFRONT"

  ip_rate_limit           = var.waf_ip_rate_limit
  enable_crs              = var.waf_enable_crs
  enable_ip_reputation    = var.waf_enable_ip_reputation
  enable_known_bad_inputs = var.waf_enable_known_bad_inputs
  tags                    = var.tags
}

# ── Module: WAF — REGIONAL scope for ALB (W-02b) ──────────────────────────────

module "waf_alb" {
  source = "./modules/waf"

  project     = var.project
  environment = var.environment
  scope       = "REGIONAL"

  ip_rate_limit           = var.waf_ip_rate_limit
  enable_crs              = var.waf_enable_crs
  enable_ip_reputation    = var.waf_enable_ip_reputation
  enable_known_bad_inputs = var.waf_enable_known_bad_inputs
  tags                    = var.tags
}

# Attach the REGIONAL WebACL to the ALB
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = module.ecs.alb_arn
  web_acl_arn  = module.waf_alb.web_acl_arn
}

# ── Module: CloudFront CDN (I-05) ─────────────────────────────────────────────

module "cloudfront" {
  source = "./modules/cloudfront"

  project      = var.project
  environment  = var.environment
  alb_dns_name = module.ecs.alb_dns_name

  thumbnails_bucket_regional_domain = "${module.s3.thumbnails_bucket_id}.s3.${var.aws_region}.amazonaws.com"
  thumbnails_bucket_id              = module.s3.thumbnails_bucket_id

  price_class     = var.cloudfront_price_class
  certificate_arn = var.certificate_arn
  domain_aliases  = var.domain_aliases
  web_acl_id      = module.waf_cloudfront.web_acl_arn
  tags            = var.tags
}

# ── Module: SQS Queues (I-06) ─────────────────────────────────────────────────

module "sqs" {
  source = "./modules/sqs"

  project           = var.project
  environment       = var.environment
  ecs_task_role_arn = module.ecs.ecs_task_role_arn
  tags              = var.tags
}

# ── Module: Monitoring (I-07) ─────────────────────────────────────────────────

module "monitoring" {
  source = "./modules/monitoring"

  project     = var.project
  environment = var.environment
  aws_region  = var.aws_region

  ecs_cluster_name           = module.ecs.cluster_name
  api_service_name           = module.ecs.api_service_name
  worker_service_name        = module.ecs.worker_service_name
  alb_arn_suffix             = split("loadbalancer/", module.ecs.alb_arn)[1]
  rds_instance_id            = module.rds.db_instance_id
  redis_replication_group_id = module.elasticache.replication_group_id
  api_5xx_threshold          = var.api_5xx_threshold
  tags                       = var.tags
}

# ── Optional: SNS email subscription ──────────────────────────────────────────

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = module.monitoring.alerts_topic_arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
