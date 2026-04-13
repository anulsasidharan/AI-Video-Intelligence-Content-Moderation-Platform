"""Add stripe_customer_id to user_subscriptions and update plan enum values.

Revision ID: 0014_add_stripe_customer_id
Revises: 0013_live_stream_moderation
Create Date: 2026-04-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_add_stripe_customer_id"
down_revision: str | None = "0013_live_stream_moderation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add stripe_customer_id column
    op.add_column(
        "user_subscriptions",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_user_subscriptions_stripe_customer_id",
        "user_subscriptions",
        ["stripe_customer_id"],
    )

    # Rename legacy plan_key values: pro -> starter, enterprise -> growth
    op.execute("UPDATE user_subscriptions SET plan_key = 'starter' WHERE plan_key = 'pro'")
    op.execute("UPDATE user_subscriptions SET plan_key = 'growth' WHERE plan_key = 'enterprise'")

    # Add past_due to allowed status values (stored as plain strings — no DB enum type)


def downgrade() -> None:
    op.drop_index("ix_user_subscriptions_stripe_customer_id", table_name="user_subscriptions")
    op.drop_column("user_subscriptions", "stripe_customer_id")

    # Reverse plan_key renames
    op.execute("UPDATE user_subscriptions SET plan_key = 'pro' WHERE plan_key = 'starter'")
    op.execute("UPDATE user_subscriptions SET plan_key = 'enterprise' WHERE plan_key = 'growth'")
