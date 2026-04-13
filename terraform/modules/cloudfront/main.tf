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

# ── Origin Access Control for S3 ──────────────────────────────────────────────

resource "aws_cloudfront_origin_access_control" "thumbnails" {
  name                              = "${local.name_prefix}-oac-thumbnails"
  description                       = "OAC for thumbnails bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ── S3 Bucket Policy — allow CloudFront OAC ───────────────────────────────────

data "aws_iam_policy_document" "thumbnails_cf_policy" {
  statement {
    sid    = "AllowCloudFrontServicePrincipal"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${var.thumbnails_bucket_id}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.this.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "thumbnails" {
  bucket = var.thumbnails_bucket_id
  policy = data.aws_iam_policy_document.thumbnails_cf_policy.json
}

# ── CloudFront Distribution ────────────────────────────────────────────────────

resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = var.price_class
  comment             = "${local.name_prefix} CDN"
  aliases             = length(var.domain_aliases) > 0 ? var.domain_aliases : null
  default_root_object = ""
  web_acl_id          = var.web_acl_id != "" ? var.web_acl_id : null

  # Origin 1: ALB (API + frontend SSR)
  origin {
    domain_name = var.alb_dns_name
    origin_id   = "alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = var.certificate_arn != "" ? "https-only" : "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Origin 2: S3 thumbnails (static assets via OAC)
  origin {
    domain_name              = var.thumbnails_bucket_regional_domain
    origin_id                = "s3-thumbnails"
    origin_access_control_id = aws_cloudfront_origin_access_control.thumbnails.id
  }

  # Default cache behaviour — forward to ALB (API + Next.js)
  default_cache_behavior {
    target_origin_id       = "alb"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Origin", "Host"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # Thumbnails path — cache aggressively from S3
  ordered_cache_behavior {
    path_pattern           = "/thumbnails/*"
    target_origin_id       = "s3-thumbnails"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 3600
    default_ttl = 86400
    max_ttl     = 604800
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn            = var.certificate_arn != "" ? var.certificate_arn : null
    ssl_support_method             = var.certificate_arn != "" ? "sni-only" : null
    minimum_protocol_version       = var.certificate_arn != "" ? "TLSv1.2_2021" : null
    cloudfront_default_certificate = var.certificate_arn == ""
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-cloudfront" })
}
