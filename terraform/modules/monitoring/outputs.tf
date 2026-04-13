output "alerts_topic_arn" {
  description = "SNS topic ARN for infrastructure alerts."
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_name" {
  description = "CloudWatch dashboard name."
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "application_log_group" {
  description = "CloudWatch log group for application logs."
  value       = aws_cloudwatch_log_group.application.name
}
