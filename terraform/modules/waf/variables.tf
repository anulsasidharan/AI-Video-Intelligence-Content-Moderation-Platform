variable "project" {
  type        = string
  description = "Project name prefix."
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev / staging / prod)."
}

variable "scope" {
  type        = string
  description = "WAF scope: CLOUDFRONT or REGIONAL."
  validation {
    condition     = contains(["CLOUDFRONT", "REGIONAL"], var.scope)
    error_message = "scope must be CLOUDFRONT or REGIONAL."
  }
}

variable "ip_rate_limit" {
  type        = number
  description = "Max requests per IP per 5-minute window before blocking. AWS WAF minimum is 100."
  default     = 2000
}

variable "enable_crs" {
  type        = bool
  description = "Enable the AWS Managed Core Rule Set (guards against SQLi, XSS, etc.)."
  default     = true
}

variable "enable_ip_reputation" {
  type        = bool
  description = "Enable AWS Managed IP Reputation list (botnets, tor exit nodes, scanners)."
  default     = true
}

variable "enable_known_bad_inputs" {
  type        = bool
  description = "Enable AWS Managed Known Bad Inputs rule set (Log4j, SSRF, etc.)."
  default     = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
