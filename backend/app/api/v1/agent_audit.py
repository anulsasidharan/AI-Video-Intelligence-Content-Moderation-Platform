"""
Admin Agent Audit API — persistent audit trail of AI agent activities.

Canonical: GET /api/v1/admin/agent-audit
Alias (no API version): GET /api/admin/agent-audit

Query params:
    - agent_id
    - status
    - action_type
    - start_date
    - end_date
    - page
    - limit
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.dependencies import get_db
from app.models.agent_audit import AgentAuditLog, AgentAuditStatus
from app.schemas.agent_audit import AgentAuditListResponse, AgentAuditLogResponse


# Shared handler (mounted under two URL prefixes).
async def list_agent_audit_logs(
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    agent_id: str | None = Query(None, description="Filter by agent id"),  # noqa: B008
    status: AgentAuditStatus | None = Query(  # noqa: B008
        None, description="Filter by status"
    ),
    action_type: str | None = Query(  # noqa: B008
        None, description="Filter by action type"
    ),
    start_date: datetime | None = Query(  # noqa: B008
        None, description="Filter: event timestamp >= start_date"
    ),
    end_date: datetime | None = Query(  # noqa: B008
        None, description="Filter: event timestamp <= end_date"
    ),
    page: int = Query(1, ge=1),  # noqa: B008
    limit: int = Query(50, ge=1, le=200),  # noqa: B008
) -> AgentAuditListResponse:
    q = select(AgentAuditLog)

    if agent_id:
        q = q.where(AgentAuditLog.agent_id == agent_id)
    if status:
        q = q.where(AgentAuditLog.status == status)
    if action_type:
        q = q.where(AgentAuditLog.action_type == action_type)

    # Prefer event_timestamp when present; otherwise fall back to created_at.
    ts_col = func.coalesce(AgentAuditLog.event_timestamp, AgentAuditLog.created_at)
    if start_date:
        q = q.where(ts_col >= start_date)
    if end_date:
        q = q.where(ts_col <= end_date)

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0

    offset = (page - 1) * limit
    q = q.order_by(desc(AgentAuditLog.created_at)).offset(offset).limit(limit)
    rows = (await db.execute(q)).scalars().all()

    return AgentAuditListResponse(
        items=[AgentAuditLogResponse.model_validate(r) for r in rows],
        total=int(total),
    )


# Mounted at /api/v1/admin/agent-audit via app.api.v1.router
router = APIRouter(prefix="/admin/agent-audit", tags=["agent-audit"])
router.add_api_route(
    "",
    list_agent_audit_logs,
    methods=["GET"],
    response_model=AgentAuditListResponse,
    summary="List AI agent activities (admin only)",
)
router.add_api_route(
    "/",
    list_agent_audit_logs,
    methods=["GET"],
    response_model=AgentAuditListResponse,
    summary="List AI agent activities (admin only)",
)

# Mounted at /api/admin/agent-audit in app.main (non-versioned alias; hidden from OpenAPI duplicate)
router_alias = APIRouter(
    prefix="/admin/agent-audit",
    tags=["agent-audit"],
    include_in_schema=False,
)
router_alias.add_api_route(
    "",
    list_agent_audit_logs,
    methods=["GET"],
    response_model=AgentAuditListResponse,
    summary="List AI agent activities (admin only)",
)
router_alias.add_api_route(
    "/",
    list_agent_audit_logs,
    methods=["GET"],
    response_model=AgentAuditListResponse,
    summary="List AI agent activities (admin only)",
)
