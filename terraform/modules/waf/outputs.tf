output "web_acl_arn" {
  description = "ARN of the WAF WebACL — use this to attach to CloudFront or ALB."
  value       = aws_wafv2_web_acl.this.arn
}

output "web_acl_id" {
  description = "ID of the WAF WebACL."
  value       = aws_wafv2_web_acl.this.id
}

output "web_acl_name" {
  description = "Name of the WAF WebACL."
  value       = aws_wafv2_web_acl.this.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group receiving WAF request logs."
  value       = aws_cloudwatch_log_group.waf.arn
}
