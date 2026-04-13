"""Quick smoke-test for the SendGrid email service."""

from app.services.email_service import EmailService

TO = "your.real@email.com"  # <-- change this

svc = EmailService()
result = svc.send_moderation_complete(
    to_email=TO,
    user_name="Test User",
    video_title="My Test Video",
    status="approved",
    report_url="http://localhost:3000/reports",
)
print("Result:", result)
