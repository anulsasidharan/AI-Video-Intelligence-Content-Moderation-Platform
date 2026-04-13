import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin

SUPPORTED_EVENTS = [
    "video.processed",
    "moderation.flagged",
    "moderation.reviewed",
    "stream.alert",
    "stream.stopped",
]


class WebhookEndpoint(Base, UUIDMixin, TimestampMixin):
    """Registered outbound webhook endpoint."""

    __tablename__ = "webhook_endpoints"

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str | None] = mapped_column(String(512), nullable=True)  # HMAC-SHA256 key
    events: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list of event names
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Delivery stats
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_delivery_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
