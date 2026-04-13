"""Pydantic schemas for support tickets."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SupportTicketCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(None, max_length=50)
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=10)


class SupportTicketResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    subject: str
    message: str
    status: str
    priority: str
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketResponse]
    total: int
    page: int
    page_size: int


class SupportTicketStatusUpdate(BaseModel):
    status: str
    priority: str | None = None
    admin_notes: str | None = None
