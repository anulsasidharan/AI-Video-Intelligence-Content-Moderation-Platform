# ── Cloud Armor Security Policy ────────────────────────────────────────────────
# Replaces the AWS WAF module. Cloud Armor is attached to the GKE Load Balancer
# backend service via the GKE Ingress annotation:
#   cloud.google.com/backend-config: '{"default": "vidshield-backend-config"}'
#
# Protection layers:
#   1. Adaptive Protection (ML-based DDoS detection)
#   2. IP rate limiting per client IP
#   3. Pre-configured OWASP rules (XSS, SQLi, LFI, RFI, Scanner Detection)

locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "google_compute_security_policy" "policy" {
  name        = "${local.name_prefix}-armor-policy"
  project     = var.project_id
  description = "VidShield Cloud Armor security policy — ${var.environment}"

  # ── Adaptive Protection (ML-based DDoS mitigation) ─────────────────────────

  adaptive_protection_config {
    layer_7_ddos_defense_config {
      enable = true
    }
  }

  # ── Rule 1000: Block known malicious IPs (pre-configured threat intelligence) -

  dynamic "rule" {
    for_each = var.enable_owasp ? [1] : []
    content {
      action      = "deny(403)"
      priority    = 1000
      description = "Block IP reputation list — botnets, tor, scanners"

      match {
        expr {
          expression = "evaluatePreconfiguredWaf('sourceiplist-known-malicious-ips', {'sensitivity': 4})"
        }
      }
    }
  }

  # ── Rule 2000: Rate limiting — block IPs exceeding threshold ───────────────

  rule {
    action      = "throttle"
    priority    = 2000
    description = "Rate limit: ${var.ip_rate_limit} req/min per IP"

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }

    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"

      rate_limit_threshold {
        count        = var.ip_rate_limit
        interval_sec = 60
      }

      # Ban the IP for 5 minutes after exceeding the limit
      ban_duration_sec = 300
      ban_threshold {
        count        = var.ip_rate_limit * 2
        interval_sec = 60
      }
    }
  }

  # ── Rule 3000: XSS protection ──────────────────────────────────────────────

  dynamic "rule" {
    for_each = var.enable_owasp ? [1] : []
    content {
      action      = "deny(403)"
      priority    = 3000
      description = "Pre-configured WAF: XSS (Cross-Site Scripting)"

      match {
        expr {
          expression = "evaluatePreconfiguredWaf('xss-v33-stable', {'sensitivity': 1})"
        }
      }
    }
  }

  # ── Rule 4000: SQLi protection ─────────────────────────────────────────────

  dynamic "rule" {
    for_each = var.enable_owasp ? [1] : []
    content {
      action      = "deny(403)"
      priority    = 4000
      description = "Pre-configured WAF: SQL injection"

      match {
        expr {
          expression = "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1})"
        }
      }
    }
  }

  # ── Rule 5000: LFI protection ──────────────────────────────────────────────

  dynamic "rule" {
    for_each = var.enable_owasp ? [1] : []
    content {
      action      = "deny(403)"
      priority    = 5000
      description = "Pre-configured WAF: Local File Inclusion"

      match {
        expr {
          expression = "evaluatePreconfiguredWaf('lfi-v33-stable', {'sensitivity': 1})"
        }
      }
    }
  }

  # ── Rule 6000: RFI protection ──────────────────────────────────────────────

  dynamic "rule" {
    for_each = var.enable_owasp ? [1] : []
    content {
      action      = "deny(403)"
      priority    = 6000
      description = "Pre-configured WAF: Remote File Inclusion"

      match {
        expr {
          expression = "evaluatePreconfiguredWaf('rfi-v33-stable', {'sensitivity': 0})"
        }
      }
    }
  }

  # ── Rule 7000: Scanner Detection ──────────────────────────────────────────

  dynamic "rule" {
    for_each = var.enable_owasp ? [1] : []
    content {
      action      = "deny(403)"
      priority    = 7000
      description = "Pre-configured WAF: Scanner and probe detection"

      match {
        expr {
          expression = "evaluatePreconfiguredWaf('scannerdetection-v33-stable', {'sensitivity': 1})"
        }
      }
    }
  }

  # ── Rule 8000: Protocol attack protection ─────────────────────────────────

  dynamic "rule" {
    for_each = var.enable_owasp ? [1] : []
    content {
      action      = "deny(403)"
      priority    = 8000
      description = "Pre-configured WAF: HTTP protocol attack"

      match {
        expr {
          expression = "evaluatePreconfiguredWaf('protocolattack-v33-stable', {'sensitivity': 1})"
        }
      }
    }
  }

  # ── Default rule (lowest priority): allow all remaining traffic ────────────

  rule {
    action      = "allow"
    priority    = 2147483647
    description = "Default allow rule"

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}
