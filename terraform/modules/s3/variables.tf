variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_account_id" {
  description = "AWS account ID, used to construct globally unique bucket names."
  type        = string
}

variable "video_lifecycle_transition_days" {
  description = "Days before raw video objects transition to S3-IA storage class."
  type        = number
  default     = 30
}

variable "artifact_expiration_days" {
  description = "Days before intermediate analysis artifacts are deleted."
  type        = number
  default     = 90
}

variable "allowed_cors_origins" {
  description = "Origins allowed in CORS rules for presigned-URL uploads."
  type        = list(string)
  default     = ["*"]
}

variable "force_destroy" {
  description = "Allow bucket deletion even when non-empty (only for dev/staging)."
  type        = bool
  default     = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
