"""
Email Notification Service — SendGrid integration.

Handles:
  - Transactional emails for moderation alerts and system events
  - HTML + plain-text multi-part messages
  - Dynamic template support via SendGrid template IDs
  - Email categorisation for analytics tracking
  - Delivery status via SendGrid response metadata

Public API:
    await service.send(to_email, subject, html_body, plain_body, category, template_id, template_data)
    await service.send_moderation_complete(to_email, user_name, video_title, status, report_url)
    await service.send_content_flagged(to_email, user_name, video_title, violation_type, severity)
    await service.send_daily_digest(to_email, user_name, stats)
    await service.send_system_alert(to_email, user_name, alert_type, details)
"""

from __future__ import annotations

import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Category,
    Content,
    From,
    Mail,
    MimeType,
    To,
)

from app.config import settings

logger = structlog.get_logger(__name__)

# ── Email category constants ───────────────────────────────────────────────────
CAT_MODERATION_ALERT = "moderation_alert"
CAT_SYSTEM_NOTIFICATION = "system_notification"
CAT_DIGEST = "daily_digest"
CAT_POLICY_VIOLATION = "policy_violation"


class EmailService:
    """Thin async-friendly wrapper around the SendGrid v3 mail API."""

    def __init__(self) -> None:
        self._client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self._from_email = settings.SENDGRID_FROM_EMAIL
        self._from_name = settings.SENDGRID_FROM_NAME

    # ── Low-level send ─────────────────────────────────────────────────────────

    def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: str | None = None,
        category: str | None = None,
        template_id: str | None = None,
        template_data: dict | None = None,
    ) -> dict:
        """
        Send a single transactional email.

        Returns the SendGrid response metadata dict with message_id and status_code.
        Raises on HTTP errors (non-2xx).
        """
        mail = Mail()
        mail.from_email = From(self._from_email, self._from_name)
        mail.to = To(to_email)
        mail.subject = subject

        if template_id:
            mail.template_id = template_id
            if template_data:
                mail.dynamic_template_data = template_data
        else:
            contents = [Content(MimeType.html, html_body)]
            if plain_body:
                contents.append(Content(MimeType.text, plain_body))
            mail.content = contents

        if category:
            mail.category = Category(category)

        response = self._client.send(mail)

        message_id: str = response.headers.get("X-Message-Id", "")
        logger.info(
            "email_sent",
            to=to_email,
            subject=subject,
            status_code=response.status_code,
            message_id=message_id,
        )

        return {
            "message_id": message_id,
            "status_code": response.status_code,
        }

    # ── High-level helpers ─────────────────────────────────────────────────────

    def send_moderation_complete(
        self,
        to_email: str,
        user_name: str,
        video_title: str,
        status: str,
        report_url: str | None = None,
    ) -> dict:
        """Email sent when AI moderation analysis finishes for a video."""
        status_label = status.replace("_", " ").title()
        status_color = {
            "approved": "#16a34a",
            "rejected": "#dc2626",
            "flagged": "#d97706",
        }.get(status.lower(), "#6b7280")

        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">VidShield AI</h1>
          </div>
          <div style="background:#f8fafc;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#1e293b">Moderation Complete</h2>
            <p style="color:#475569">Hi {user_name},</p>
            <p style="color:#475569">
              Your video <strong>"{video_title}"</strong> has been reviewed by our AI moderation system.
            </p>
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:16px;margin:16px 0">
              <p style="margin:0;font-size:14px;color:#64748b">Decision</p>
              <p style="margin:4px 0 0;font-size:22px;font-weight:700;color:{status_color}">{status_label}</p>
            </div>
            {f'<p><a href="{report_url}" style="display:inline-block;background:#0f172a;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:600">View Full Report</a></p>' if report_url else ""}
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              This is an automated message from VidShield AI. Please do not reply.
            </p>
          </div>
        </div>
        """
        plain_body = (
            f"Hi {user_name},\n\n"
            f'Your video "{video_title}" moderation is complete.\n'
            f"Decision: {status_label}\n" + (f"View report: {report_url}\n" if report_url else "")
        )

        return self.send(
            to_email=to_email,
            subject=f"[VidShield] Moderation complete — {video_title}",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_MODERATION_ALERT,
        )

    def send_content_flagged(
        self,
        to_email: str,
        user_name: str,
        video_title: str,
        violation_type: str,
        severity: str,
    ) -> dict:
        """Email sent when a policy violation is detected."""
        severity_color = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#d97706",
            "low": "#2563eb",
        }.get(severity.lower(), "#6b7280")

        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">VidShield AI</h1>
          </div>
          <div style="background:#fff7ed;padding:24px;border:1px solid #fed7aa;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#9a3412">Content Flagged</h2>
            <p style="color:#475569">Hi {user_name},</p>
            <p style="color:#475569">
              Our AI system has detected a policy violation in your video <strong>"{video_title}"</strong>.
            </p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
              <tr>
                <td style="padding:8px;background:#f8fafc;font-size:13px;color:#64748b;width:40%">Violation Type</td>
                <td style="padding:8px;font-weight:600;color:#1e293b">{violation_type.replace("_", " ").title()}</td>
              </tr>
              <tr>
                <td style="padding:8px;background:#f8fafc;font-size:13px;color:#64748b">Severity</td>
                <td style="padding:8px;font-weight:700;color:{severity_color}">{severity.upper()}</td>
              </tr>
            </table>
            <p style="color:#475569">
              Please review the content and take appropriate action. You may appeal this decision
              through your VidShield dashboard.
            </p>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              This is an automated message from VidShield AI. Please do not reply.
            </p>
          </div>
        </div>
        """
        plain_body = (
            f"Hi {user_name},\n\n"
            f'A policy violation was detected in your video "{video_title}".\n'
            f"Violation: {violation_type}\n"
            f"Severity: {severity.upper()}\n\n"
            "Please review the content in your VidShield dashboard."
        )

        return self.send(
            to_email=to_email,
            subject=f"[VidShield] Content flagged — {video_title}",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_POLICY_VIOLATION,
        )

    def send_daily_digest(
        self,
        to_email: str,
        user_name: str,
        stats: dict,
    ) -> dict:
        """Daily digest email summarising the day's moderation activity."""
        total = stats.get("total", 0)
        approved = stats.get("approved", 0)
        flagged = stats.get("flagged", 0)
        rejected = stats.get("rejected", 0)
        date_label = stats.get("date", "Today")

        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">VidShield AI — Daily Digest</h1>
          </div>
          <div style="background:#f8fafc;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#1e293b">Activity Summary — {date_label}</h2>
            <p style="color:#475569">Hi {user_name}, here is your moderation summary for {date_label}.</p>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin:16px 0">
              <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:12px;text-align:center">
                <p style="margin:0;font-size:28px;font-weight:700;color:#1e293b">{total}</p>
                <p style="margin:4px 0 0;font-size:12px;color:#64748b">Total</p>
              </div>
              <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:12px;text-align:center">
                <p style="margin:0;font-size:28px;font-weight:700;color:#16a34a">{approved}</p>
                <p style="margin:4px 0 0;font-size:12px;color:#64748b">Approved</p>
              </div>
              <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:12px;text-align:center">
                <p style="margin:0;font-size:28px;font-weight:700;color:#d97706">{flagged}</p>
                <p style="margin:4px 0 0;font-size:12px;color:#64748b">Flagged</p>
              </div>
              <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:12px;text-align:center">
                <p style="margin:0;font-size:28px;font-weight:700;color:#dc2626">{rejected}</p>
                <p style="margin:4px 0 0;font-size:12px;color:#64748b">Rejected</p>
              </div>
            </div>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              You are receiving this digest because you opted in to daily summaries.
              Update your preferences in the VidShield dashboard.
            </p>
          </div>
        </div>
        """
        plain_body = (
            f"Hi {user_name},\n\nDaily digest for {date_label}:\n"
            f"  Total:    {total}\n"
            f"  Approved: {approved}\n"
            f"  Flagged:  {flagged}\n"
            f"  Rejected: {rejected}\n"
        )

        return self.send(
            to_email=to_email,
            subject=f"[VidShield] Daily digest — {date_label}",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_DIGEST,
        )

    def send_welcome(self, to_email: str, user_name: str) -> dict:
        """Welcome email sent on new user registration."""
        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">Welcome to VidShield AI</h1>
          </div>
          <div style="background:#f8fafc;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#1e293b">Hi {user_name}, you're all set!</h2>
            <p style="color:#475569">
              Your VidShield AI account has been created. You can now upload videos for
              AI-powered content moderation and access real-time insights.
            </p>
            <ul style="color:#475569;line-height:1.8">
              <li>Upload videos for automatic moderation</li>
              <li>Configure moderation policies</li>
              <li>Monitor live streams in real time</li>
              <li>Generate detailed compliance reports</li>
            </ul>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              This is an automated message from VidShield AI. Please do not reply.
            </p>
          </div>
        </div>
        """
        plain_body = (
            f"Hi {user_name},\n\nWelcome to VidShield AI!\n"
            "Your account has been created. Log in to start moderating content."
        )
        return self.send(
            to_email=to_email,
            subject="Welcome to VidShield AI",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_SYSTEM_NOTIFICATION,
        )

    def send_password_changed(self, to_email: str, user_name: str) -> dict:
        """Security alert when a user changes their password."""
        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">VidShield AI — Security Alert</h1>
          </div>
          <div style="background:#fefce8;padding:24px;border:1px solid #fde68a;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#92400e">Password Changed</h2>
            <p style="color:#475569">Hi {user_name},</p>
            <p style="color:#475569">
              Your VidShield AI account password was changed successfully.
            </p>
            <p style="color:#b45309;font-weight:600">
              If you did not make this change, contact support immediately and reset your password.
            </p>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              This is an automated security notification from VidShield AI.
            </p>
          </div>
        </div>
        """
        plain_body = (
            f"Hi {user_name},\n\nYour VidShield AI password was changed.\n"
            "If you did not make this change, contact support immediately."
        )
        return self.send(
            to_email=to_email,
            subject="[VidShield] Your password has been changed",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_SYSTEM_NOTIFICATION,
        )

    def send_password_reset(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
        expires_minutes: int = 30,
    ) -> dict:
        """Password reset link email sent when a user requests to reset their password."""
        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">VidShield AI — Password Reset</h1>
          </div>
          <div style="background:#f8fafc;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#1e293b">Reset your password</h2>
            <p style="color:#475569">Hi {user_name},</p>
            <p style="color:#475569">
              We received a request to reset the password for your VidShield AI account.
              Click the button below to choose a new password.
            </p>
            <p style="margin:24px 0">
              <a href="{reset_url}"
                 style="display:inline-block;background:#0f172a;color:#fff;padding:12px 28px;
                        border-radius:6px;text-decoration:none;font-weight:600;font-size:15px">
                Reset Password
              </a>
            </p>
            <p style="color:#64748b;font-size:13px">
              This link expires in <strong>{expires_minutes} minutes</strong>.
              If you did not request a password reset, you can safely ignore this email —
              your password will not be changed.
            </p>
            <p style="color:#64748b;font-size:12px;word-break:break-all;margin-top:16px">
              If the button above does not work, copy and paste this URL into your browser:<br/>
              <span style="color:#2563eb">{reset_url}</span>
            </p>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              This is an automated security email from VidShield AI. Please do not reply.
            </p>
          </div>
        </div>
        """
        plain_body = (
            f"Hi {user_name},\n\n"
            "We received a request to reset your VidShield AI password.\n\n"
            f"Reset link (expires in {expires_minutes} minutes):\n{reset_url}\n\n"
            "If you did not request this, ignore this email — your password will not change."
        )
        return self.send(
            to_email=to_email,
            subject="[VidShield] Reset your password",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_SYSTEM_NOTIFICATION,
        )

    def send_password_reset_confirmation(self, to_email: str, user_name: str) -> dict:
        """Confirmation email sent after a successful password reset."""
        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">VidShield AI — Security Alert</h1>
          </div>
          <div style="background:#f0fdf4;padding:24px;border:1px solid #bbf7d0;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#166534">Password Reset Successful</h2>
            <p style="color:#475569">Hi {user_name},</p>
            <p style="color:#475569">
              Your VidShield AI account password has been reset successfully.
              You can now log in with your new password.
            </p>
            <p style="color:#b45309;font-weight:600">
              If you did not perform this action, contact support immediately and secure
              your email account.
            </p>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              This is an automated security notification from VidShield AI. Please do not reply.
            </p>
          </div>
        </div>
        """
        plain_body = (
            f"Hi {user_name},\n\n"
            "Your VidShield AI password has been reset successfully.\n"
            "If you did not do this, contact support immediately."
        )
        return self.send(
            to_email=to_email,
            subject="[VidShield] Your password has been reset",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_SYSTEM_NOTIFICATION,
        )

    def send_system_alert(
        self,
        to_email: str,
        user_name: str,
        alert_type: str,
        details: str,
    ) -> dict:
        """System-level alert (quota warnings, API errors, etc.)."""
        html_body = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;padding:16px 24px;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">VidShield AI — System Alert</h1>
          </div>
          <div style="background:#fef2f2;padding:24px;border:1px solid #fecaca;border-top:none;border-radius:0 0 8px 8px">
            <h2 style="margin-top:0;color:#991b1b">{alert_type.replace("_", " ").title()}</h2>
            <p style="color:#475569">Hi {user_name},</p>
            <p style="color:#475569">{details}</p>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
              This is an automated system alert from VidShield AI.
            </p>
          </div>
        </div>
        """
        plain_body = f"Hi {user_name},\n\n[{alert_type.upper()}] {details}"

        return self.send(
            to_email=to_email,
            subject=f"[VidShield] System alert — {alert_type.replace('_', ' ').title()}",
            html_body=html_body,
            plain_body=plain_body,
            category=CAT_SYSTEM_NOTIFICATION,
        )
