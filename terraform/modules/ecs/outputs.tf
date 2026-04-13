output "cluster_id" {
  description = "ECS cluster ID."
  value       = aws_ecs_cluster.this.id
}

output "cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.this.name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer."
  value       = aws_lb.this.dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID of the ALB (for Route 53 alias records)."
  value       = aws_lb.this.zone_id
}

output "alb_arn" {
  description = "ARN of the ALB."
  value       = aws_lb.this.arn
}

output "api_service_name" {
  description = "ECS service name for the API."
  value       = aws_ecs_service.api.name
}

output "worker_service_name" {
  description = "ECS service name for the Celery worker."
  value       = aws_ecs_service.worker.name
}

output "frontend_service_name" {
  description = "ECS service name for the frontend."
  value       = aws_ecs_service.frontend.name
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task IAM role (used to grant SQS / other resource access)."
  value       = aws_iam_role.ecs_task.arn
}
