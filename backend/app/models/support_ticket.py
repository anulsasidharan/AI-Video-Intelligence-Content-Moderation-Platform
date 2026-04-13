"""Support ticket model — for the public /support form and admin panel."""

from __future__ import annotations

import enum

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SupportTicket(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "support_tickets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=TicketStatus.OPEN.value, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default=TicketPriority.MEDIUM.value
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
