variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "ecs_cluster_name" {
  type = string
}

variable "api_service_name" {
  type = string
}

variable "worker_service_name" {
  type = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix (the part after 'loadbalancer/') for CloudWatch metric dimensions."
  type        = string
}

variable "rds_instance_id" {
  description = "RDS instance identifier for DB alarms."
  type        = string
}

variable "redis_replication_group_id" {
  description = "ElastiCache replication group ID for cache alarms."
  type        = string
}

variable "alarm_actions" {
  description = "List of SNS topic ARNs to notify on alarm state."
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of SNS topic ARNs to notify on OK state."
  type        = list(string)
  default     = []
}

variable "api_5xx_threshold" {
  description = "Number of API 5xx errors per 5 minutes before firing an alarm."
  type        = number
  default     = 10
}

variable "cpu_utilization_threshold" {
  description = "ECS task CPU utilization (%) above which the alarm fires."
  type        = number
  default     = 80
}

variable "memory_utilization_threshold" {
  description = "ECS task memory utilization (%) above which the alarm fires."
  type        = number
  default     = 85
}

variable "db_connection_threshold" {
  description = "Number of DB connections above which the alarm fires."
  type        = number
  default     = 100
}

variable "log_retention_days" {
  description = "Default retention for CloudWatch log groups created by this module."
  type        = number
  default     = 30
}

variable "tags" {
  type    = map(string)
  default = {}
}
