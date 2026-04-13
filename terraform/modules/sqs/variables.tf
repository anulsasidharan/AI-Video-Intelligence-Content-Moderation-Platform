variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "video_queue_visibility_timeout" {
  description = "Visibility timeout in seconds for the video processing queue. Should be >= max task duration."
  type        = number
  default     = 900 # 15 minutes
}

variable "video_queue_retention_seconds" {
  description = "How long SQS retains a message (seconds)."
  type        = number
  default     = 86400 # 24 hours
}

variable "dlq_retention_seconds" {
  description = "How long the DLQ retains failed messages."
  type        = number
  default     = 345600 # 4 days
}

variable "max_receive_count" {
  description = "Number of delivery attempts before a message moves to the DLQ."
  type        = number
  default     = 3
}

variable "ecs_task_role_arn" {
  description = "IAM role ARN for ECS tasks that need to publish/consume SQS messages."
  type        = string
  default     = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
