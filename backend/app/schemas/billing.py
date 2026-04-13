from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NewsletterSignupRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class NewsletterSignupResponse(BaseModel):
    ok: bool = True
    message: str = "Thanks — you're on the list."


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_key: str
    status: str
    current_period_end: datetime | None
    renews_label: str | None = None


class PaymentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount_cents: int
    currency: str
    status: str
    paid_at: datetime
    description: str | None
    invoice_number: str


class PaymentListResponse(BaseModel):
    items: list[PaymentItemResponse]
    total: int


class RevenueSeriesPoint(BaseModel):
    label: str
    amount_cents: int


class AdminRevenueResponse(BaseModel):
    period: str
    currency: str
    total_cents: int
    previous_period_total_cents: int | None
    growth_percent: float | None
    series: list[RevenueSeriesPoint]


class SubscriberItem(BaseModel):
    email: str
    name: str | None
    role: str | None
    user_id: uuid.UUID | None
    source: str  # account | newsletter
    created_at: datetime


class SubscriberListResponse(BaseModel):
    items: list[SubscriberItem]
    total: int
    page: int
    page_size: int


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class PortalSessionResponse(BaseModel):
    portal_url: str
