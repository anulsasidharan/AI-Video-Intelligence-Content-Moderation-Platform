"""User billing: subscription summary, payment history, downloadable invoice (HTML),
Stripe Checkout and Customer Portal sessions."""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.exceptions import NotFoundError
from app.dependencies import get_db
from app.schemas.billing import (
    CheckoutSessionResponse,
    PaymentItemResponse,
    PaymentListResponse,
    PortalSessionResponse,
    SubscriptionResponse,
)
from app.services.billing_service import (
    AlreadySubscribedError,
    build_invoice_html,
    create_checkout_session,
    create_portal_session,
    get_subscription_view,
    get_user_payment,
    list_user_payments,
    sync_payments_from_stripe,
    sync_subscription_from_customer,
)

router = APIRouter(prefix="/billing", tags=["billing"])
logger = structlog.get_logger(__name__)

_PAID_PLANS = {"starter", "growth"}


@router.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Current subscription plan for the signed-in user",
)
async def get_my_subscription(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SubscriptionResponse:
    data = await get_subscription_view(db, current_user.id)
    return SubscriptionResponse.model_validate(data)


@router.get(
    "/payments",
    response_model=PaymentListResponse,
    summary="Past payments for the signed-in user",
)
async def list_my_payments(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> PaymentListResponse:
    rows, total = await list_user_payments(db, current_user.id, skip=skip, limit=limit)
    return PaymentListResponse(
        items=[PaymentItemResponse.model_validate(r) for r in rows],
        total=total,
    )


@router.get(
    "/payments/{payment_id}/invoice",
    response_class=HTMLResponse,
    summary="Download invoice as HTML (print / save as PDF from browser)",
)
async def download_invoice(
    payment_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HTMLResponse:
    pay = await get_user_payment(db, current_user.id, payment_id)
    if pay is None:
        raise NotFoundError("Payment", str(payment_id))
    html = build_invoice_html(
        invoice_number=pay.invoice_number,
        paid_at=pay.paid_at,
        amount_cents=pay.amount_cents,
        currency=pay.currency,
        description=pay.description,
        customer_email=current_user.email,
    )
    filename = f"invoice-{pay.invoice_number}.html"
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/checkout",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a Stripe Checkout session for a subscription upgrade",
)
async def create_checkout(
    body: dict,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CheckoutSessionResponse:
    plan_key: str = (body.get("plan") or "").lower().strip()

    if plan_key == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Free plan requires no payment. No checkout needed.",
        )
    if plan_key == "enterprise":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enterprise plan requires a sales conversation. Please contact us.",
        )
    if plan_key not in _PAID_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown plan '{plan_key}'. Valid options: starter, growth.",
        )

    try:
        checkout_url = await create_checkout_session(db, current_user, plan_key)
    except AlreadySubscribedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have an active {exc.current_plan.capitalize()} subscription. "
            "Use the billing portal to change or cancel your plan.",
        ) from exc
    except Exception as exc:
        logger.error("stripe_checkout_error", error=str(exc), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again.",
        ) from exc

    return CheckoutSessionResponse(checkout_url=checkout_url)


@router.post(
    "/portal",
    response_model=PortalSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a Stripe Customer Portal session for self-service billing management",
)
async def create_portal(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PortalSessionResponse:
    try:
        portal_url = await create_portal_session(db, current_user)
    except Exception as exc:
        logger.error("stripe_portal_error", error=str(exc), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again.",
        ) from exc

    return PortalSessionResponse(portal_url=portal_url)


@router.post(
    "/sync-payments",
    status_code=status.HTTP_200_OK,
    summary="Backfill payment history from Stripe (idempotent)",
)
async def sync_payments(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Pull all paid Stripe invoices for the current customer and create any missing BillingPayment records.
    Safe to call multiple times — skips already-recorded invoices.
    """
    try:
        created = await sync_payments_from_stripe(db, current_user)
    except Exception as exc:
        logger.error("stripe_sync_payments_error", error=str(exc), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not sync payments from Stripe.",
        ) from exc
    return {"synced": created}


@router.post(
    "/sync",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Pull latest subscription state from Stripe and update the DB",
)
async def sync_subscription(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SubscriptionResponse:
    """Called by the frontend after a successful Stripe Checkout redirect
    to immediately reflect the new plan without waiting for a webhook."""
    try:
        data = await sync_subscription_from_customer(db, current_user)
    except Exception as exc:
        logger.error("stripe_sync_error", error=str(exc), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not sync subscription from payment provider.",
        ) from exc
    return SubscriptionResponse.model_validate(data)
