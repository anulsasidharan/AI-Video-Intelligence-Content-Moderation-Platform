variable "project" {
  description = "Project name, used as a prefix for all resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
}

variable "aws_region" {
  description = "AWS region."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets (one per AZ, used for ALB)."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets (one per AZ, used for ECS/RDS/Redis)."
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  description = "List of AZs to deploy subnets into. Must match length of subnet CIDR lists."
  type        = list(string)
}

variable "single_nat_gateway" {
  description = "If true, deploy a single NAT gateway (cost-optimised for dev/staging). If false, one per AZ."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags to merge onto all resources."
  type        = map(string)
  default     = {}
}
