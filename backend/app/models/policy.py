import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Policy(Base, UUIDMixin, TimestampMixin):
    """Content moderation policy with configurable rules."""

    __tablename__ = "policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # JSON array of rule objects:
    # [{ "category": "violence", "threshold": 0.8, "action": "block" }]
    rules: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Overall action for unmatched content
    default_action: Mapped[str] = mapped_column(String(64), default="allow", nullable=False)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
