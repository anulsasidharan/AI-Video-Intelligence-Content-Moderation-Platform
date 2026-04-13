"""
Support Ticket API
- POST /support-tickets        — public, no auth required (submit a ticket)
- GET  /support-tickets        — admin only (list all tickets)
- PATCH /support-tickets/{id}  — admin only (update status / notes)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.core.exceptions import NotFoundError
from app.dependencies import get_db
from app.models.support_ticket import SupportTicket
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketListResponse,
    SupportTicketResponse,
    SupportTicketStatusUpdate,
)

router = APIRouter(prefix="/support-tickets", tags=["support"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SupportTicketResponse,
    summary="Submit a support ticket (public — no auth required)",
)
async def create_ticket(
    body: SupportTicketCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SupportTicketResponse:
    ticket = SupportTicket(**body.model_dump())
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return SupportTicketResponse.model_validate(ticket)


@router.get(
    "",
    response_model=SupportTicketListResponse,
    summary="List all support tickets (admin only)",
)
async def list_tickets(
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
) -> SupportTicketListResponse:
    base_q = select(SupportTicket)
    if status_filter:
        base_q = base_q.where(SupportTicket.status == status_filter)

    total = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar_one()

    items_q = (
        base_q.order_by(SupportTicket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(items_q)).scalars().all()

    return SupportTicketListResponse(
        items=[SupportTicketResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
    summary="Update ticket status / notes (admin only)",
)
async def update_ticket(
    ticket_id: str,
    body: SupportTicketStatusUpdate,
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SupportTicketResponse:
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise NotFoundError("Support ticket not found.")

    ticket.status = body.status
    if body.priority is not None:
        ticket.priority = body.priority
    if body.admin_notes is not None:
        ticket.admin_notes = body.admin_notes

    await db.flush()
    await db.refresh(ticket)
    return SupportTicketResponse.model_validate(ticket)
