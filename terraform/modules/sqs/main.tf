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

# ── Dead Letter Queue ──────────────────────────────────────────────────────────

resource "aws_sqs_queue" "video_dlq" {
  name                      = "${local.name_prefix}-video-processing-dlq"
  message_retention_seconds = var.dlq_retention_seconds
  sqs_managed_sse_enabled   = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-video-processing-dlq" })
}

# ── Video Processing Queue ─────────────────────────────────────────────────────

resource "aws_sqs_queue" "video_processing" {
  name                       = "${local.name_prefix}-video-processing"
  visibility_timeout_seconds = var.video_queue_visibility_timeout
  message_retention_seconds  = var.video_queue_retention_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.video_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-video-processing" })
}

# ── Moderation Queue ───────────────────────────────────────────────────────────

resource "aws_sqs_queue" "moderation_dlq" {
  name                      = "${local.name_prefix}-moderation-dlq"
  message_retention_seconds = var.dlq_retention_seconds
  sqs_managed_sse_enabled   = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-moderation-dlq" })
}

resource "aws_sqs_queue" "moderation" {
  name                       = "${local.name_prefix}-moderation"
  visibility_timeout_seconds = var.video_queue_visibility_timeout
  message_retention_seconds  = var.video_queue_retention_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.moderation_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-moderation" })
}

# ── Queue Policy — allow ECS task role to send/receive/delete ─────────────────

data "aws_iam_policy_document" "video_processing_policy" {
  statement {
    sid    = "AllowECSTaskAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [var.ecs_task_role_arn]
    }

    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility",
    ]

    resources = [aws_sqs_queue.video_processing.arn]
  }
}

data "aws_iam_policy_document" "moderation_policy" {
  statement {
    sid    = "AllowECSTaskAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [var.ecs_task_role_arn]
    }

    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility",
    ]

    resources = [aws_sqs_queue.moderation.arn]
  }
}

resource "aws_sqs_queue_policy" "video_processing" {
  queue_url = aws_sqs_queue.video_processing.url
  policy    = data.aws_iam_policy_document.video_processing_policy.json
}

resource "aws_sqs_queue_policy" "moderation" {
  queue_url = aws_sqs_queue.moderation.url
  policy    = data.aws_iam_policy_document.moderation_policy.json
}
