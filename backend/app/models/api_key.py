import hashlib
import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ApiKey(Base, UUIDMixin, TimestampMixin):
    """Programmatic API key for a user account."""

    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # SHA-256 hex digest of the raw key — never stored in plaintext
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    # Displayable masked form, e.g. "sk_live_abc1••••••••1234"
    masked: Mapped[str] = mapped_column(String(80), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @staticmethod
    def generate() -> tuple[str, str, str]:
        """
        Generate a new API key.

        Returns:
            (raw_key, key_hash, masked)
            raw_key  — shown to the user exactly once, never stored
            key_hash — SHA-256 hex digest, stored for lookup
            masked   — display-safe form with middle characters replaced
        """
        raw = "sk_live_" + secrets.token_hex(20)  # 48 chars total
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        masked = raw[:12] + "••••••••••••" + raw[-4:]
        return raw, key_hash, masked
