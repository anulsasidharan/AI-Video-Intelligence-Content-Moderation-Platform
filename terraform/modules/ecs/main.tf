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
  log_group_api      = "/ecs/${local.name_prefix}/api"
  log_group_worker   = "/ecs/${local.name_prefix}/worker"
  log_group_frontend = "/ecs/${local.name_prefix}/frontend"
}

# ── ECS Cluster ────────────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "this" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-cluster" })
}

resource "aws_ecs_cluster_capacity_providers" "fargate" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

# ── CloudWatch Log Groups ──────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "api" {
  name              = local.log_group_api
  retention_in_days = 30
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = local.log_group_worker
  retention_in_days = 30
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = local.log_group_frontend
  retention_in_days = 14
  tags              = local.common_tags
}

# ── IAM — Execution Role (pull images, read secrets) ──────────────────────────

resource "aws_iam_role" "ecs_execution" {
  name = "${local.name_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "${local.name_prefix}-ecs-execution-secrets"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["secretsmanager:GetSecretValue"]
      Resource = compact([
        var.db_secret_arn,
        var.redis_secret_arn,
        var.secret_key_arn,
        var.openai_api_key_arn,
        var.pinecone_api_key_arn,
        var.sentry_dsn_arn,
      ])
    }]
  })
}

# ── IAM — Task Role (runtime AWS SDK calls) ────────────────────────────────────

resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "${local.name_prefix}-ecs-task-s3"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectTagging",
          "s3:PutObjectTagging",
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_videos_bucket}/*",
          "arn:aws:s3:::${var.s3_thumbnails_bucket}/*",
          "arn:aws:s3:::${var.s3_artifacts_bucket}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::${var.s3_videos_bucket}",
          "arn:aws:s3:::${var.s3_thumbnails_bucket}",
          "arn:aws:s3:::${var.s3_artifacts_bucket}",
        ]
      },
    ]
  })
}

# ── ALB ────────────────────────────────────────────────────────────────────────

resource "aws_lb" "this" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.sg_alb_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false

  access_logs {
    bucket  = ""
    enabled = false
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-alb" })
}

resource "aws_lb_target_group" "api" {
  name        = "${local.name_prefix}-tg-api"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = var.health_check_path
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-tg-api" })
}

resource "aws_lb_target_group" "frontend" {
  name        = "${local.name_prefix}-tg-fe"
  port        = 3000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-tg-fe" })
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = var.certificate_arn != "" ? "redirect" : "forward"

    dynamic "redirect" {
      for_each = var.certificate_arn != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    dynamic "forward" {
      for_each = var.certificate_arn == "" ? [1] : []
      content {
        target_group {
          arn = aws_lb_target_group.frontend.arn
        }
      }
    }
  }
}

resource "aws_lb_listener" "https" {
  count             = var.certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = var.certificate_arn != "" ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      # Socket.IO attaches under /socket.io/ on the API service (same ASGI app as FastAPI).
      values = ["/api/*", "/health", "/docs", "/redoc", "/openapi.json", "/socket.io*"]
    }
  }
}

# ── ECS Task Definitions ───────────────────────────────────────────────────────

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.ecr_backend_image
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]

      command = [
        "sh", "-c",
        "alembic upgrade head && uvicorn app.main:asgi_app --host 0.0.0.0 --port 8000 --workers 2"
      ]

      environment = [
        { name = "APP_ENV", value = var.environment },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET_NAME", value = var.s3_videos_bucket },
        { name = "S3_BUCKET_VIDEOS", value = var.s3_videos_bucket },
        { name = "S3_BUCKET_THUMBNAILS", value = var.s3_thumbnails_bucket },
        { name = "S3_BUCKET_ARTIFACTS", value = var.s3_artifacts_bucket },
        { name = "CORS_ORIGINS", value = var.cors_origins },
      ]

      secrets = concat(
        [
          { name = "DATABASE_URL", valueFrom = var.db_secret_arn },
          { name = "REDIS_URL", valueFrom = var.redis_secret_arn },
          { name = "SECRET_KEY", valueFrom = var.secret_key_arn },
          { name = "OPENAI_API_KEY", valueFrom = var.openai_api_key_arn },
          { name = "PINECONE_API_KEY", valueFrom = var.pinecone_api_key_arn },
        ],
        var.sentry_dsn_arn != "" ? [{ name = "SENTRY_DSN", valueFrom = var.sentry_dsn_arn }] : [],
      )

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group_api
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.ecr_backend_image
      essential = true

      command = [
        "celery", "-A", "app.workers.celery_app", "worker",
        "--loglevel=warning", "--concurrency=4",
        "--queues=video,moderation,analytics,cleanup,reports,notifications,streams",
        "--broker-connection-retry-on-startup=true"
      ]

      environment = [
        { name = "APP_ENV", value = var.environment },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET_NAME", value = var.s3_videos_bucket },
        { name = "S3_BUCKET_VIDEOS", value = var.s3_videos_bucket },
        { name = "S3_BUCKET_THUMBNAILS", value = var.s3_thumbnails_bucket },
        { name = "S3_BUCKET_ARTIFACTS", value = var.s3_artifacts_bucket },
      ]

      secrets = concat(
        [
          { name = "DATABASE_URL", valueFrom = var.db_secret_arn },
          { name = "REDIS_URL", valueFrom = var.redis_secret_arn },
          { name = "SECRET_KEY", valueFrom = var.secret_key_arn },
          { name = "OPENAI_API_KEY", valueFrom = var.openai_api_key_arn },
          { name = "PINECONE_API_KEY", valueFrom = var.pinecone_api_key_arn },
        ],
        var.sentry_dsn_arn != "" ? [{ name = "SENTRY_DSN", valueFrom = var.sentry_dsn_arn }] : [],
      )

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group_worker
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = var.ecr_frontend_image
      essential = true

      portMappings = [
        { containerPort = 3000, protocol = "tcp" }
      ]

      # NEXT_PUBLIC_* is baked at Docker build time; runtime env here is for ops clarity only.
      environment = [
        { name = "NEXT_PUBLIC_APP_ENV", value = var.environment },
        { name = "NEXT_PUBLIC_MOCK_API", value = "false" },
        { name = "NEXT_PUBLIC_API_URL", value = "" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group_frontend
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "frontend"
        }
      }
    }
  ])

  tags = local.common_tags
}

# ── ECS Services ───────────────────────────────────────────────────────────────

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.sg_ecs_api_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = local.common_tags
}

resource "aws_ecs_service" "worker" {
  name            = "${local.name_prefix}-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.sg_ecs_worker_id]
    assign_public_ip = false
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = local.common_tags
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.sg_ecs_frontend_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = local.common_tags
}
