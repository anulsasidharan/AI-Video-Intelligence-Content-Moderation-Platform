"""Subscriptions and payment records for user billing and admin revenue reporting."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    TRIALING = "trialing"
    PAST_DUE = "past_due"


class PaymentStatus(str, enum.Enum):
    PAID = "paid"
    PENDING = "pending"
    FAILED = "failed"


class UserSubscription(Base, UUIDMixin, TimestampMixin):
    """One row per portal user — tracks Stripe plan and customer reference."""

    __tablename__ = "user_subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan_key: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SubscriptionPlan.FREE.value
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SubscriptionStatus.ACTIVE.value
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    external_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (Index("ix_user_subscriptions_stripe_customer_id", "stripe_customer_id"),)


class BillingPayment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "billing_payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PaymentStatus.PAID.value
    )
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    external_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
