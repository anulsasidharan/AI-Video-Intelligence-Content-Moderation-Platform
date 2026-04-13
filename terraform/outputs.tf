output "vpc_id" {
  description = "VPC ID."
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name — point your domain here."
  value       = module.ecs.alb_dns_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name."
  value       = module.cloudfront.distribution_domain_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = module.ecs.cluster_name
}

output "rds_endpoint" {
  description = "RDS connection endpoint."
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "redis_primary_endpoint" {
  description = "ElastiCache Redis primary endpoint."
  value       = module.elasticache.primary_endpoint
  sensitive   = true
}

output "videos_bucket" {
  description = "S3 bucket name for videos."
  value       = module.s3.videos_bucket_id
}

output "thumbnails_bucket" {
  description = "S3 bucket name for thumbnails."
  value       = module.s3.thumbnails_bucket_id
}

output "artifacts_bucket" {
  description = "S3 bucket name for AI artifacts."
  value       = module.s3.artifacts_bucket_id
}

output "video_processing_queue_url" {
  description = "SQS URL for the video processing queue."
  value       = module.sqs.video_processing_queue_url
}

output "moderation_queue_url" {
  description = "SQS URL for the moderation queue."
  value       = module.sqs.moderation_queue_url
}

output "alerts_topic_arn" {
  description = "SNS topic ARN for infrastructure alerts."
  value       = module.monitoring.alerts_topic_arn
}

output "cloudwatch_dashboard" {
  description = "CloudWatch dashboard name."
  value       = module.monitoring.dashboard_name
}

output "waf_cloudfront_arn" {
  description = "ARN of the WAF WebACL attached to CloudFront."
  value       = module.waf_cloudfront.web_acl_arn
}

output "waf_alb_arn" {
  description = "ARN of the WAF WebACL attached to the ALB."
  value       = module.waf_alb.web_acl_arn
}
