"""Landing page newsletter / Stay in the loop signups."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class NewsletterSignup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "newsletter_signups"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
