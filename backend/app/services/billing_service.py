"""Billing helpers: default subscription, payments, revenue aggregates, subscribers list."""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import structlog
from sqlalchemy import (
    String,
    Uuid,
    cast,
    exists,
    func,
    literal,
    null,
    select,
    union_all,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.billing import BillingPayment, PaymentStatus, UserSubscription
from app.models.newsletter import NewsletterSignup
from app.models.user import User

logger = structlog.get_logger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def record_newsletter_signup(db: AsyncSession, email: str) -> tuple[bool, str]:
    """Insert newsletter email. Returns (created, message). Idempotent on duplicate."""
    normalized = _normalize_email(email)
    if not _EMAIL_RE.match(normalized):
        raise ValidationError("Enter a valid email address.")

    existing = await db.scalar(select(NewsletterSignup).where(NewsletterSignup.email == normalized))
    if existing:
        return False, "You're already subscribed — thanks!"

    db.add(NewsletterSignup(email=normalized))
    await db.commit()
    logger.info("newsletter_signup", email=normalized)
    return True, "Thanks — you're on the list."


async def ensure_default_subscription(db: AsyncSession, user_id: uuid.UUID) -> UserSubscription:
    row = await db.scalar(select(UserSubscription).where(UserSubscription.user_id == user_id))
    if row:
        return row
    sub = UserSubscription(
        user_id=user_id,
        plan_key="free",
        status="active",
        current_period_end=None,
    )
    db.add(sub)
    await db.flush()
    return sub


async def get_subscription_view(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    sub = await ensure_default_subscription(db, user_id)
    renews = None
    if sub.current_period_end:
        renews = sub.current_period_end.date().isoformat()
    return {
        "plan_key": sub.plan_key,
        "status": sub.status,
        "current_period_end": sub.current_period_end,
        "renews_label": renews,
    }


async def list_user_payments(
    db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> tuple[list[BillingPayment], int]:
    filt = BillingPayment.user_id == user_id
    total = await db.scalar(select(func.count()).where(filt)) or 0
    q = (
        select(BillingPayment)
        .where(filt)
        .order_by(BillingPayment.paid_at.desc())
        .offset(skip)
        .limit(min(limit, 100))
    )
    rows = (await db.execute(q)).scalars().all()
    return list(rows), int(total)


async def get_user_payment(
    db: AsyncSession, user_id: uuid.UUID, payment_id: uuid.UUID
) -> BillingPayment | None:
    return await db.scalar(
        select(BillingPayment).where(
            BillingPayment.id == payment_id,
            BillingPayment.user_id == user_id,
        )
    )


RevenuePeriod = Literal["daily", "weekly", "monthly", "all"]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _bucket_start(period: RevenuePeriod) -> datetime:
    now = _utc_now()
    if period == "daily":
        return now - timedelta(days=30)
    if period == "weekly":
        return now - timedelta(weeks=12)
    if period == "monthly":
        return now - timedelta(days=365)
    return datetime(2000, 1, 1, tzinfo=UTC)


def _payment_bucket_label(paid_at: datetime, series_granularity: RevenuePeriod) -> str:
    """Stable bucket keys for chart series (SQLite + PostgreSQL)."""
    if paid_at.tzinfo is None:
        paid_at = paid_at.replace(tzinfo=UTC)
    dt = paid_at.astimezone(UTC)
    if series_granularity == "daily":
        return dt.date().isoformat()
    if series_granularity == "weekly":
        y, w, _ = dt.isocalendar()
        return f"{y}-W{w:02d}"
    return dt.strftime("%Y-%m")


def _prev_window_start(period: RevenuePeriod, current_start: datetime) -> datetime:
    now = _utc_now()
    if period == "daily":
        span = now - current_start
        return current_start - span
    if period == "weekly":
        span = now - current_start
        return current_start - span
    if period == "monthly":
        span = now - current_start
        return current_start - span
    # all: compare last 365d vs prior 365d
    return now - timedelta(days=730)


async def admin_revenue_summary(db: AsyncSession, period: RevenuePeriod) -> dict[str, Any]:
    """Paid payments only; series buckets computed in Python for SQLite + PostgreSQL."""
    start = _bucket_start(period)
    now = _utc_now()

    paid = BillingPayment.status == PaymentStatus.PAID.value

    if period == "all":
        current_q = select(func.coalesce(func.sum(BillingPayment.amount_cents), 0)).where(paid)
        total_current = int(await db.scalar(current_q) or 0)
        mid = now - timedelta(days=365)
        first_half = int(
            await db.scalar(
                select(func.coalesce(func.sum(BillingPayment.amount_cents), 0)).where(
                    paid, BillingPayment.paid_at < mid
                )
            )
            or 0
        )
        second_half = int(
            await db.scalar(
                select(func.coalesce(func.sum(BillingPayment.amount_cents), 0)).where(
                    paid, BillingPayment.paid_at >= mid
                )
            )
            or 0
        )
        growth = None
        if first_half > 0:
            growth = round((second_half - first_half) / first_half * 100, 2)
        elif second_half > 0:
            growth = 100.0
        series_start = now - timedelta(days=365 * 3)
        prev_out = first_half if (first_half or second_half) else None
    else:
        prev_start = _prev_window_start(period, start)
        current_q = select(func.coalesce(func.sum(BillingPayment.amount_cents), 0)).where(
            paid, BillingPayment.paid_at >= start, BillingPayment.paid_at <= now
        )
        total_current = int(await db.scalar(current_q) or 0)

        prev_q = select(func.coalesce(func.sum(BillingPayment.amount_cents), 0)).where(
            paid,
            BillingPayment.paid_at >= prev_start,
            BillingPayment.paid_at < start,
        )
        total_prev = int(await db.scalar(prev_q) or 0)

        growth = None
        if total_prev > 0:
            growth = round((total_current - total_prev) / total_prev * 100, 2)
        elif total_current > 0:
            growth = 100.0
        series_start = start
        prev_out = total_prev

    series_granularity: RevenuePeriod = "monthly" if period == "all" else period
    raw_rows = (
        await db.execute(
            select(BillingPayment.paid_at, BillingPayment.amount_cents).where(
                paid,
                BillingPayment.paid_at >= series_start,
                BillingPayment.paid_at <= now,
            )
        )
    ).all()
    acc: dict[str, int] = defaultdict(int)
    for paid_at, cents in raw_rows:
        key = _payment_bucket_label(paid_at, series_granularity)
        acc[key] += int(cents or 0)
    series = [{"label": k, "amount_cents": v} for k, v in sorted(acc.items())]

    return {
        "period": period,
        "currency": "USD",
        "total_cents": total_current,
        "previous_period_total_cents": prev_out,
        "growth_percent": growth,
        "series": series,
    }


async def list_subscribers_union(
    db: AsyncSession, page: int = 1, page_size: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Registered users + newsletter-only emails (deduped, case-insensitive)."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    offset = (page - 1) * page_size

    stmt_users = select(
        User.email.label("email"),
        User.name.label("name"),
        cast(User.role, String).label("role"),
        User.id.label("user_id"),
        User.created_at.label("created_at"),
        literal("account").label("source"),
    )

    nl_exists = exists(
        select(1).where(func.lower(User.email) == func.lower(NewsletterSignup.email))
    )
    stmt_nl = select(
        NewsletterSignup.email.label("email"),
        cast(null(), String).label("name"),
        cast(null(), String).label("role"),
        cast(null(), Uuid(as_uuid=True)).label("user_id"),
        NewsletterSignup.created_at.label("created_at"),
        literal("newsletter").label("source"),
    ).where(~nl_exists)

    unioned = union_all(stmt_users, stmt_nl).subquery()
    count_total = await db.scalar(select(func.count()).select_from(unioned)) or 0

    page_stmt = (
        select(unioned).order_by(unioned.c.created_at.desc()).offset(offset).limit(page_size)
    )
    rows = (await db.execute(page_stmt)).mappings().all()
    out: list[dict[str, Any]] = []
    for r in rows:
        uid = r["user_id"]
        out.append(
            {
                "email": r["email"],
                "name": r["name"],
                "role": r["role"],
                "user_id": (
                    uid if isinstance(uid, uuid.UUID) else (uuid.UUID(str(uid)) if uid else None)
                ),
                "source": r["source"],
                "created_at": r["created_at"],
            }
        )
    return out, int(count_total)


def build_invoice_html(
    *,
    invoice_number: str,
    paid_at: datetime,
    amount_cents: int,
    currency: str,
    description: str | None,
    customer_email: str,
) -> str:
    import html

    amt = amount_cents / 100
    desc = html.escape(description or "VidShield AI subscription / usage")
    inv = html.escape(invoice_number)
    em = html.escape(customer_email)
    dt = paid_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
    cur = html.escape(currency)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Invoice {inv}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; color: #111; }}
h1 {{ font-size: 1.25rem; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
th, td {{ text-align: left; padding: 0.5rem 0; border-bottom: 1px solid #e5e7eb; }}
.footer {{ margin-top: 2rem; font-size: 0.85rem; color: #6b7280; }}
</style></head><body>
<h1>VidShield AI — Invoice</h1>
<p><strong>Invoice #</strong> {inv}<br/>
<strong>Date</strong> {html.escape(dt)}<br/>
<strong>Bill to</strong> {em}</p>
<table>
<thead><tr><th>Description</th><th>Amount</th></tr></thead>
<tbody>
<tr><td>{desc}</td><td>{cur} {amt:.2f}</td></tr>
</tbody>
</table>
<p class="footer">This document was generated by VidShield AI for your records. Print or save as PDF from your browser.</p>
</body></html>"""


# ── Stripe helpers ────────────────────────────────────────────────────────────


def _get_stripe():
    """Return configured stripe module (lazy import so missing key doesn't break startup)."""
    import stripe  # type: ignore[import-untyped]

    from app.config import settings

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


_PLAN_TO_PRICE: dict[str, str] = {}


def _plan_price_id(plan_key: str) -> str:
    from app.config import settings

    mapping = {
        "starter": settings.STRIPE_STARTER_PRICE_ID,
        "growth": settings.STRIPE_GROWTH_PRICE_ID,
    }
    price_id = mapping.get(plan_key, "")
    if not price_id:
        raise ValueError(f"No Stripe price configured for plan '{plan_key}'")
    return price_id


def _price_id_to_plan(stripe_subscription: Any) -> str:
    """Derive plan_key from price ID when metadata.plan_key is missing."""
    from app.config import settings

    reverse = {
        settings.STRIPE_STARTER_PRICE_ID: "starter",
        settings.STRIPE_GROWTH_PRICE_ID: "growth",
    }
    try:
        items_data = getattr(getattr(stripe_subscription, "items", None), "data", None) or []
        if items_data:
            price_id = getattr(items_data[0], "price", None)
            if price_id:
                price_id_str = getattr(price_id, "id", None) or str(price_id)
                return reverse.get(price_id_str, "starter")
    except Exception:
        pass
    return "starter"


def _plan_from_invoice(stripe_invoice: Any) -> str | None:
    """Derive plan_key from the first line item price ID in a Stripe invoice."""
    from app.config import settings

    reverse = {
        settings.STRIPE_STARTER_PRICE_ID: "starter",
        settings.STRIPE_GROWTH_PRICE_ID: "growth",
    }
    try:
        lines = getattr(stripe_invoice, "lines", None)
        lines_data = getattr(lines, "data", None) or []
        if lines_data:
            price = getattr(lines_data[0], "price", None)
            if price:
                price_id = getattr(price, "id", None) or str(price)
                return reverse.get(price_id)
    except Exception:
        pass
    return None


async def get_or_create_stripe_customer(db: AsyncSession, user: User) -> str:
    """Return existing Stripe customer ID or create a new one and persist it."""
    stripe = _get_stripe()
    sub = await ensure_default_subscription(db, user.id)

    if sub.stripe_customer_id:
        return sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=getattr(user, "name", None) or user.email,
        metadata={"user_id": str(user.id)},
    )
    sub.stripe_customer_id = customer.id
    await db.commit()
    logger.info("stripe_customer_created", customer_id=customer.id, user_id=str(user.id))
    return customer.id


class AlreadySubscribedError(Exception):
    """Raised when a user tries to start a checkout for a plan they're already on."""

    def __init__(self, current_plan: str) -> None:
        self.current_plan = current_plan
        super().__init__(f"Already subscribed to {current_plan}")


async def create_checkout_session(db: AsyncSession, user: User, plan_key: str) -> str:
    """Create a Stripe Checkout Session for a subscription upgrade. Returns the URL."""
    from app.config import settings

    # Block duplicate subscriptions — user must use the portal to change/cancel
    sub = await ensure_default_subscription(db, user.id)
    _PAID = {"starter", "growth"}
    if sub.plan_key in _PAID and sub.status in ("active", "trialing"):
        raise AlreadySubscribedError(sub.plan_key)

    stripe = _get_stripe()
    price_id = _plan_price_id(plan_key)
    customer_id = await get_or_create_stripe_customer(db, user)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        subscription_data={"metadata": {"user_id": str(user.id), "plan_key": plan_key}},
    )
    logger.info(
        "stripe_checkout_created",
        session_id=session.id,
        plan_key=plan_key,
        user_id=str(user.id),
    )
    return session.url


async def create_portal_session(db: AsyncSession, user: User) -> str:
    """Create a Stripe Customer Portal session. Returns the URL."""
    from app.config import settings

    stripe = _get_stripe()
    customer_id = await get_or_create_stripe_customer(db, user)

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=settings.STRIPE_CANCEL_URL.split("?")[0],  # /dashboard/billing
    )
    logger.info("stripe_portal_created", user_id=str(user.id))
    return session.url


async def _sub_by_customer(db: AsyncSession, stripe_customer_id: str) -> UserSubscription | None:
    return await db.scalar(
        select(UserSubscription).where(UserSubscription.stripe_customer_id == stripe_customer_id)
    )


async def sync_subscription_from_stripe(db: AsyncSession, stripe_subscription: Any) -> None:
    """Upsert UserSubscription from a Stripe subscription object (SDK v10+)."""
    # Use attribute access for Stripe SDK v10+ objects (no longer dict-like)
    customer_id: str = stripe_subscription.customer
    status: str = stripe_subscription.status
    ext_sub_id: str = stripe_subscription.id

    # current_period_end lives in items.data[0] in newer Stripe API versions
    period_end_ts: int | None = None
    items_data = getattr(getattr(stripe_subscription, "items", None), "data", None) or []
    if items_data:
        period_end_ts = getattr(items_data[0], "current_period_end", None)

    # StripeObject._data is the underlying plain dict (dict() on StripeObject fails in SDK v15)
    metadata_obj = getattr(stripe_subscription, "metadata", None)
    metadata: dict[str, str] = (metadata_obj._data if metadata_obj else None) or {}

    plan_key = metadata.get("plan_key") or _price_id_to_plan(stripe_subscription)
    period_end = datetime.fromtimestamp(period_end_ts, tz=UTC) if period_end_ts else None

    # Map Stripe status to our status
    status_map = {
        "active": "active",
        "trialing": "trialing",
        "canceled": "canceled",
        "incomplete": "past_due",
        "past_due": "past_due",
        "unpaid": "past_due",
    }
    mapped_status = status_map.get(status, "active")

    sub = await _sub_by_customer(db, customer_id)
    if sub is None:
        # Try by user_id from metadata
        user_id_str = metadata.get("user_id")
        if user_id_str:
            sub = await db.scalar(
                select(UserSubscription).where(UserSubscription.user_id == uuid.UUID(user_id_str))
            )
    if sub is None:
        logger.warning("stripe_sync_no_sub_found", customer_id=customer_id)
        return

    sub.stripe_customer_id = customer_id
    sub.plan_key = plan_key
    sub.status = mapped_status
    sub.external_subscription_id = ext_sub_id
    sub.current_period_end = period_end
    await db.commit()
    logger.info(
        "stripe_subscription_synced",
        customer_id=customer_id,
        plan_key=plan_key,
        status=mapped_status,
    )


async def record_payment_from_invoice(db: AsyncSession, stripe_invoice: Any) -> None:
    """Create a BillingPayment row from a paid Stripe invoice (SDK v10+)."""
    if getattr(stripe_invoice, "status", None) != "paid":
        return

    customer_id: str = stripe_invoice.customer
    sub = await _sub_by_customer(db, customer_id)
    if sub is None:
        logger.warning("stripe_invoice_no_sub", customer_id=customer_id)
        return

    invoice_number: str = getattr(stripe_invoice, "number", None) or stripe_invoice.id

    # Idempotency: skip if already recorded
    existing = await db.scalar(
        select(BillingPayment).where(BillingPayment.invoice_number == invoice_number)
    )
    if existing:
        return

    amount_paid: int = getattr(stripe_invoice, "amount_paid", 0)
    currency: str = (getattr(stripe_invoice, "currency", None) or "usd").upper()
    status_transitions = getattr(stripe_invoice, "status_transitions", None)
    paid_ts = (
        getattr(status_transitions, "paid_at", None) if status_transitions else None
    ) or getattr(stripe_invoice, "created", None)
    paid_at = datetime.fromtimestamp(paid_ts, tz=UTC) if paid_ts else _utc_now()
    payment_intent: str | None = getattr(stripe_invoice, "payment_intent", None)

    # Derive plan from invoice lines (price ID) so description is accurate
    # even if the subscription DB record hasn't been updated yet
    plan_key = _plan_from_invoice(stripe_invoice) or sub.plan_key

    payment = BillingPayment(
        user_id=sub.user_id,
        amount_cents=amount_paid,
        currency=currency,
        status=PaymentStatus.PAID.value,
        paid_at=paid_at,
        description=f"VidShield AI — {plan_key.capitalize()} plan subscription",
        invoice_number=invoice_number,
        external_payment_id=payment_intent,
    )
    db.add(payment)
    await db.commit()
    logger.info(
        "stripe_payment_recorded",
        invoice_number=invoice_number,
        amount_cents=amount_paid,
        user_id=str(sub.user_id),
    )


async def handle_payment_failed(db: AsyncSession, stripe_invoice: Any) -> None:
    """Mark subscription as past_due when a payment fails."""
    customer_id: str = stripe_invoice.customer
    sub = await _sub_by_customer(db, customer_id)
    if sub is None:
        return

    sub.status = "past_due"
    await db.commit()
    logger.warning(
        "stripe_payment_failed",
        customer_id=customer_id,
        user_id=str(sub.user_id),
    )


async def sync_payments_from_stripe(db: AsyncSession, user: User) -> int:
    """Fetch all paid Stripe invoices for this customer and create any missing BillingPayment records.

    Idempotent — skips invoices already recorded by invoice_number.
    Returns the number of new records created.
    """
    sub = await ensure_default_subscription(db, user.id)
    if not sub.stripe_customer_id:
        logger.info("sync_payments_no_customer", user_id=str(user.id))
        return 0

    stripe = _get_stripe()
    invoices = stripe.Invoice.list(
        customer=sub.stripe_customer_id,
        status="paid",
        limit=100,
    )

    created = 0
    for invoice in invoices.data:
        invoice_number = getattr(invoice, "number", None) or invoice.id
        existing = await db.scalar(
            select(BillingPayment).where(BillingPayment.invoice_number == invoice_number)
        )
        if existing:
            continue
        await record_payment_from_invoice(db, invoice)
        created += 1

    logger.info("stripe_payments_synced", user_id=str(user.id), created=created)
    return created


async def sync_subscription_from_customer(db: AsyncSession, user: User) -> dict[str, Any]:
    """Pull the latest active subscription from Stripe and update the DB.

    Called immediately after a successful Stripe Checkout redirect so the UI
    reflects the new plan without waiting for a webhook.
    """
    stripe = _get_stripe()
    sub = await ensure_default_subscription(db, user.id)

    if not sub.stripe_customer_id:
        # No Stripe customer yet — nothing to sync
        return await get_subscription_view(db, user.id)

    # List active subscriptions for this customer (SDK v10+: use .data attribute)
    subscriptions = stripe.Subscription.list(
        customer=sub.stripe_customer_id,
        status="active",
        limit=1,
    )

    if subscriptions.data:
        await sync_subscription_from_stripe(db, subscriptions.data[0])
    else:
        # Also check trialing
        subscriptions = stripe.Subscription.list(
            customer=sub.stripe_customer_id,
            status="trialing",
            limit=1,
        )
        if subscriptions.data:
            await sync_subscription_from_stripe(db, subscriptions.data[0])

    # Refresh and return
    await db.refresh(sub)
    return await get_subscription_view(db, user.id)
