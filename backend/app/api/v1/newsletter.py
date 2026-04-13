"""Public newsletter signup (landing footer — Stay in the loop)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.billing import NewsletterSignupRequest, NewsletterSignupResponse
from app.services.billing_service import record_newsletter_signup

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


@router.post(
    "",
    response_model=NewsletterSignupResponse,
    status_code=status.HTTP_200_OK,
    summary="Subscribe to product updates (no auth)",
)
async def newsletter_subscribe(
    body: NewsletterSignupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NewsletterSignupResponse:
    _created, message = await record_newsletter_signup(db, body.email)
    return NewsletterSignupResponse(ok=True, message=message)
