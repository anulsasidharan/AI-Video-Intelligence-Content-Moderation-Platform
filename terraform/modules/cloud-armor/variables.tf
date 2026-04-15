variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "project" {
  description = "Short project name prefix."
  type        = string
  default     = "vidshield"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "ip_rate_limit" {
  description = "Maximum number of requests per IP per minute before throttling kicks in."
  type        = number
  default     = 100
}

variable "enable_owasp" {
  description = "Enable pre-configured OWASP WAF rules (XSS, SQLi, LFI, RFI, scanner detection, protocol attack)."
  type        = bool
  default     = true
}
