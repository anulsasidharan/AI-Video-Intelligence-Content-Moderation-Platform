"""Stripe webhook handler — POST /api/v1/billing/webhook.

Verifies Stripe signature and routes events to billing service functions.
Raw request body MUST be preserved for signature verification.
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

_HANDLED_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
}


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook receiver (signature-verified)",
    include_in_schema=False,
)
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    import stripe  # type: ignore[import-untyped]

    from app.config import settings
    from app.services import billing_service

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as exc:
        logger.warning("stripe_webhook_invalid_signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature.",
        ) from exc
    except Exception as exc:
        logger.error("stripe_webhook_parse_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse webhook payload.",
        ) from exc

    # SDK v10+: Event is a typed object — use attribute access, not dict access
    event_type: str = event.type
    logger.info("stripe_webhook_received", event_type=event_type, event_id=event.id)

    if event_type not in _HANDLED_EVENTS:
        return {"received": True}

    data = event.data.object

    if event_type == "checkout.session.completed":
        stripe.api_key = settings.STRIPE_SECRET_KEY
        sub_id = getattr(data, "subscription", None)
        if sub_id:
            subscription = stripe.Subscription.retrieve(sub_id)
            await billing_service.sync_subscription_from_stripe(db, subscription)

    elif event_type == "customer.subscription.updated":
        await billing_service.sync_subscription_from_stripe(db, data)

    elif event_type == "customer.subscription.deleted":
        from sqlalchemy import select

        from app.models.billing import UserSubscription

        customer_id: str = data.customer
        deleted_sub_id: str = data.id
        sub = await db.scalar(
            select(UserSubscription).where(UserSubscription.stripe_customer_id == customer_id)
        )
        if sub:
            # Only reset to free if the deleted subscription is the user's
            # currently active one — ignore cancellation of duplicates
            if sub.external_subscription_id == deleted_sub_id:
                sub.plan_key = "free"
                sub.status = "canceled"
                sub.external_subscription_id = None
                sub.current_period_end = None
                await db.commit()
                logger.info(
                    "stripe_subscription_canceled",
                    customer_id=customer_id,
                    user_id=str(sub.user_id),
                )
            else:
                logger.info(
                    "stripe_duplicate_sub_deleted_ignored",
                    customer_id=customer_id,
                    deleted_sub_id=deleted_sub_id,
                    active_sub_id=sub.external_subscription_id,
                )

    elif event_type == "invoice.paid":
        await billing_service.record_payment_from_invoice(db, data)

    elif event_type == "invoice.payment_failed":
        await billing_service.handle_payment_failed(db, data)

    return {"received": True}
