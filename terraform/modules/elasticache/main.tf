locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = merge(
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )
}

resource "aws_elasticache_subnet_group" "this" {
  name        = "${local.name_prefix}-redis-subnet-group"
  description = "ElastiCache subnet group for ${local.name_prefix}"
  subnet_ids  = var.subnet_ids

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-redis-subnet-group" })
}

resource "aws_elasticache_parameter_group" "redis7" {
  name        = "${local.name_prefix}-redis7"
  family      = "redis7"
  description = "Redis 7 parameter group for ${local.name_prefix}"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-redis7-params" })
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${local.name_prefix}-redis"
  description          = "Redis 7 for ${local.name_prefix} - cache, broker, result backend"

  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_nodes
  parameter_group_name = aws_elasticache_parameter_group.redis7.name
  subnet_group_name    = aws_elasticache_subnet_group.this.name
  security_group_ids   = [var.security_group_id]

  port = 6379

  at_rest_encryption_enabled = var.at_rest_encryption_enabled
  transit_encryption_enabled = var.transit_encryption_enabled

  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = "04:00-05:00"
  maintenance_window       = "mon:05:00-mon:06:00"

  auto_minor_version_upgrade = true
  apply_immediately          = false

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-redis" })
}
