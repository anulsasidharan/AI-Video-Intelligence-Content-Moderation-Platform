variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "alb_dns_name" {
  description = "DNS name of the ALB to use as the API origin."
  type        = string
}

variable "thumbnails_bucket_regional_domain" {
  description = "Regional domain name of the thumbnails S3 bucket."
  type        = string
}

variable "thumbnails_bucket_id" {
  description = "Thumbnails S3 bucket ID, used to attach the OAC bucket policy."
  type        = string
}

variable "price_class" {
  description = "CloudFront price class (PriceClass_100 = US+EU only, PriceClass_All = global)."
  type        = string
  default     = "PriceClass_100"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS. Must be in us-east-1. Leave empty to use CloudFront default cert."
  type        = string
  default     = ""
}

variable "domain_aliases" {
  description = "Custom domain aliases for the CloudFront distribution."
  type        = list(string)
  default     = []
}

variable "web_acl_id" {
  description = "ARN of the WAF WebACL (CLOUDFRONT scope) to attach. Leave empty to disable WAF."
  type        = string
  default     = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
