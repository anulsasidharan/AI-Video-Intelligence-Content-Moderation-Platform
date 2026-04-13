"""
WhatsApp Notification Service — Twilio integration.

Uses the Twilio WhatsApp Business API (Sandbox or approved account).
All messages sent via approved template-style body text to comply with
WhatsApp Business Policy.

Opt-in management:
  Users must have a whatsapp_number populated on their User record.
  Templates must be pre-approved for production; sandbox accepts freeform.

Public API:
    service.send(to_number, body)
    service.send_moderation_complete(to_number, user_name, video_title, status)
    service.send_content_flagged(to_number, user_name, video_title, violation_type, severity)
    service.send_stream_alert(to_number, stream_title, category, severity, confidence)
    service.send_system_alert(to_number, alert_type, details)
"""

from __future__ import annotations

import structlog
from twilio.rest import Client

from app.config import settings

logger = structlog.get_logger(__name__)

# Prefix for all outbound WhatsApp numbers
_WA_PREFIX = "whatsapp:"


def _wa(number: str) -> str:
    """Normalise a phone number to the whatsapp: URI scheme Twilio expects."""
    number = number.strip()
    if not number.startswith(_WA_PREFIX):
        return f"{_WA_PREFIX}{number}"
    return number


class WhatsAppService:
    """Thin wrapper around the Twilio Messages API for WhatsApp delivery."""

    def __init__(self) -> None:
        self._client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
        )
        self._from_number = _wa(settings.TWILIO_WHATSAPP_NUMBER)

    # ── Low-level send ─────────────────────────────────────────────────────────

    def send(self, to_number: str, body: str) -> dict:
        """
        Send a WhatsApp message.

        Args:
            to_number: Recipient phone number (E.164 or whatsapp:+... format).
            body:      Message body text (max 1600 chars for WhatsApp).

        Returns:
            dict with twilio sid and status.
        """
        message = self._client.messages.create(
            from_=self._from_number,
            to=_wa(to_number),
            body=body[:1600],
        )

        logger.info(
            "whatsapp_sent",
            to=to_number,
            sid=message.sid,
            status=message.status,
        )

        return {"sid": message.sid, "status": message.status}

    # ── High-level helpers ─────────────────────────────────────────────────────

    def send_moderation_complete(
        self,
        to_number: str,
        user_name: str,
        video_title: str,
        status: str,
    ) -> dict:
        """Notify user that moderation is complete (approved/flagged/rejected)."""
        status_label = status.replace("_", " ").upper()
        body = (
            f"*VidShield AI — Moderation Complete*\n\n"
            f"Hi {user_name},\n"
            f'Your video *"{video_title}"* has been reviewed.\n\n'
            f"Decision: *{status_label}*\n\n"
            "Log in to your VidShield dashboard to view the full report."
        )
        return self.send(to_number, body)

    def send_content_flagged(
        self,
        to_number: str,
        user_name: str,
        video_title: str,
        violation_type: str,
        severity: str,
    ) -> dict:
        """Critical alert when a policy violation is detected."""
        severity_emoji = {
            "critical": "🚨",
            "high": "🔴",
            "medium": "🟡",
            "low": "🔵",
        }.get(severity.lower(), "⚠️")

        body = (
            f"{severity_emoji} *VidShield AI — Content Flagged*\n\n"
            f"Hi {user_name},\n"
            f'A policy violation was detected in *"{video_title}"*.\n\n'
            f"Violation: *{violation_type.replace('_', ' ').title()}*\n"
            f"Severity: *{severity.upper()}*\n\n"
            "Please review and take action in your VidShield dashboard."
        )
        return self.send(to_number, body)

    def send_stream_alert(
        self,
        to_number: str,
        stream_title: str,
        category: str,
        severity: str,
        confidence: float,
    ) -> dict:
        """Real-time alert for a live stream policy violation."""
        body = (
            f"🔴 *VidShield AI — Live Stream Alert*\n\n"
            f"Stream: *{stream_title}*\n"
            f"Detected: *{category.replace('_', ' ').title()}*\n"
            f"Severity: *{severity.upper()}*\n"
            f"Confidence: *{int(confidence * 100)}%*\n\n"
            "Immediate review may be required."
        )
        return self.send(to_number, body)

    def send_welcome(self, to_number: str, user_name: str) -> dict:
        """Welcome message on new user registration."""
        body = (
            f"👋 *Welcome to VidShield AI!*\n\n"
            f"Hi {user_name}, your account is ready.\n\n"
            "You can now upload videos for AI-powered content moderation. "
            "Log in to your dashboard to get started."
        )
        return self.send(to_number, body)

    def send_password_changed(self, to_number: str, user_name: str) -> dict:
        """Security alert when password changes."""
        body = (
            f"🔐 *VidShield AI — Security Alert*\n\n"
            f"Hi {user_name}, your account password was changed.\n\n"
            "If you did not make this change, contact support immediately."
        )
        return self.send(to_number, body)

    def send_system_alert(
        self,
        to_number: str,
        alert_type: str,
        details: str,
    ) -> dict:
        """System-level alert (quota warnings, API errors)."""
        body = (
            f"⚠️ *VidShield AI — System Alert*\n\n"
            f"Type: *{alert_type.replace('_', ' ').title()}*\n\n"
            f"{details}"
        )
        return self.send(to_number, body)
