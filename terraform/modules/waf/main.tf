# W-02 AWS WAF v2 WebACL Module
#
# Creates a WAF WebACL with four protection layers:
#
#   1. IP Reputation List  — blocks known botnets, tor exit nodes, and scanner IPs
#                            (AWS-managed, updated continuously)
#   2. Rate-Based Rule     — blocks any single IP that exceeds ip_rate_limit
#                            requests in a 5-minute window
#   3. Core Rule Set (CRS) — guards against SQLi, XSS, path traversal, etc.
#                            (AWS managed, OWASP Top 10 coverage)
#   4. Known Bad Inputs    — blocks Log4Shell, SSRF, Spring4Shell exploit patterns
#
# Scope:
#   CLOUDFRONT — attach to a CloudFront distribution (must be deployed in us-east-1)
#   REGIONAL   — attach to an ALB/API Gateway in any region via
#                aws_wafv2_web_acl_association
#
# CloudWatch metrics are enabled for every rule so you can build dashboards
# and alarms in the monitoring module.

locals {
  name_prefix = "${var.project}-${var.environment}-${lower(var.scope)}"
  common_tags = merge(
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
      Component   = "waf"
    },
    var.tags,
  )
}

# ── WAF WebACL ─────────────────────────────────────────────────────────────────

resource "aws_wafv2_web_acl" "this" {
  name        = "${local.name_prefix}-webacl"
  description = "VidShield WAF — ${var.scope} scope"
  scope       = var.scope

  # Default action: allow all requests that do not match a BLOCK rule
  default_action {
    allow {}
  }

  # ── Rule 1: IP Reputation List ─────────────────────────────────────────────
  # Blocks IPs flagged by Amazon's threat intelligence (botnets, tor, scanners).
  # This is the cheapest and most effective first line of defence.

  dynamic "rule" {
    for_each = var.enable_ip_reputation ? [1] : []
    content {
      name     = "AWSManagedRulesAmazonIpReputationList"
      priority = 10

      override_action {
        none {} # honour the managed rule's own BLOCK actions
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesAmazonIpReputationList"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${local.name_prefix}-ip-reputation"
        sampled_requests_enabled   = true
      }
    }
  }

  # ── Rule 2: IP-Based Rate Limiting ─────────────────────────────────────────
  # Blocks any single IPv4/IPv6 address that fires more than ip_rate_limit
  # requests in any 5-minute rolling window (AWS WAF's fixed evaluation period).
  # This is the primary DDoS mitigation layer.

  rule {
    name     = "IPRateLimit"
    priority = 20

    action {
      block {
        custom_response {
          response_code = 429
          response_header {
            name  = "Retry-After"
            value = "300"
          }
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = var.ip_rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-ip-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 3: Core Rule Set (OWASP Top 10) ──────────────────────────────────
  # Covers SQLi, XSS, LFI/RFI, command injection, HTTP protocol violations.
  # SizeRestrictions_BODY is overridden to COUNT (not BLOCK) because the
  # video upload endpoint sends large multipart bodies.

  dynamic "rule" {
    for_each = var.enable_crs ? [1] : []
    content {
      name     = "AWSManagedRulesCommonRuleSet"
      priority = 30

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesCommonRuleSet"

          # Override the body-size restriction rule to COUNT instead of BLOCK
          # so large video upload multipart requests are not rejected.
          rule_action_override {
            name = "SizeRestrictions_BODY"
            action_to_use {
              count {}
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${local.name_prefix}-crs"
        sampled_requests_enabled   = true
      }
    }
  }

  # ── Rule 4: Known Bad Inputs ───────────────────────────────────────────────
  # Blocks Log4Shell (CVE-2021-44228), Spring4Shell, SSRF, and other
  # active exploit patterns.

  dynamic "rule" {
    for_each = var.enable_known_bad_inputs ? [1] : []
    content {
      name     = "AWSManagedRulesKnownBadInputsRuleSet"
      priority = 40

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesKnownBadInputsRuleSet"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${local.name_prefix}-known-bad-inputs"
        sampled_requests_enabled   = true
      }
    }
  }

  # ── Top-level visibility config ────────────────────────────────────────────

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-webacl"
    sampled_requests_enabled   = true
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-webacl" })
}

# ── CloudWatch Log Group for full WAF request logging ──────────────────────────
# WAF log group names MUST start with "aws-waf-logs-".

resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${local.name_prefix}"
  retention_in_days = 30
  tags              = merge(local.common_tags, { Name = "aws-waf-logs-${local.name_prefix}" })
}

resource "aws_wafv2_web_acl_logging_configuration" "this" {
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
  resource_arn            = aws_wafv2_web_acl.this.arn

  # Only log requests that were inspected (not passed by the default allow action
  # before any rule matched) — reduces log volume while keeping blocked requests.
  logging_filter {
    default_behavior = "DROP"

    filter {
      behavior = "KEEP"
      condition {
        action_condition {
          action = "BLOCK"
        }
      }
      requirement = "MEETS_ANY"
    }

    filter {
      behavior = "KEEP"
      condition {
        action_condition {
          action = "COUNT"
        }
      }
      requirement = "MEETS_ANY"
    }
  }
}
