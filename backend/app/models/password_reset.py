"""
Password Reset Token Model

Stores cryptographically secure, single-use tokens for the forgot-password flow.

Security design:
  - The raw token is never stored in the database.
  - Only the SHA-256 hash of the raw token is persisted.
  - Tokens expire after PASSWORD_RESET_TOKEN_EXPIRE_MINUTES (default 30 min).
  - Tokens are invalidated immediately on use (used_at is set).
  - Old tokens for the same user are automatically invalidated when a new
    request is made (row replaced or checked at lookup time).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PasswordResetToken(Base, UUIDMixin, TimestampMixin):
    """One-time password reset token record."""

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA-256 hex digest of the raw URL token — never store the raw value
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
