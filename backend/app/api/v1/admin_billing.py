"""Admin revenue dashboard and unified subscribers list."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.dependencies import get_db
from app.schemas.billing import (
    AdminRevenueResponse,
    RevenueSeriesPoint,
    SubscriberItem,
    SubscriberListResponse,
)
from app.services.billing_service import admin_revenue_summary, list_subscribers_union

router = APIRouter(prefix="/admin/billing", tags=["admin-billing"])

RevenuePeriod = Literal["daily", "weekly", "monthly", "all"]


@router.get(
    "/revenue",
    response_model=AdminRevenueResponse,
    summary="Revenue totals and time series (paid payments only)",
)
async def get_revenue(
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    period: RevenuePeriod = Query(  # noqa: B008
        "monthly", description="Aggregation window"
    ),
) -> AdminRevenueResponse:
    raw = await admin_revenue_summary(db, period)
    return AdminRevenueResponse(
        period=raw["period"],
        currency=raw["currency"],
        total_cents=raw["total_cents"],
        previous_period_total_cents=raw["previous_period_total_cents"],
        growth_percent=raw["growth_percent"],
        series=[RevenueSeriesPoint(**p) for p in raw["series"]],
    )


@router.get(
    "/subscribers",
    response_model=SubscriberListResponse,
    summary="All registered users plus newsletter-only signups",
)
async def list_subscribers(
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> SubscriberListResponse:
    rows, total = await list_subscribers_union(db, page=page, page_size=page_size)
    return SubscriberListResponse(
        items=[SubscriberItem.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
