"""
Audit API — admin-only access and agent audit trails.

GET /audit/access   paginated access audit log (login/logout events; skip/limit)
GET /audit/moderation    paginated AI moderation audit (per video; skip/limit)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.dependencies import get_db
from app.models.audit import AccessAuditLog
from app.models.moderation import ModerationResult
from app.models.video import Video
from app.schemas.audit import (
    AccessAuditListResponse,
    AccessAuditLogResponse,
    ModerationAuditEntry,
    ModerationAuditListResponse,
    ViolationDetail,
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get(
    "/access",
    response_model=AccessAuditListResponse,
    summary="List access audit log entries (admin only)",
)
async def list_access_audit(
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None, description="Filter by action: login | logout"),
    status: str | None = Query(None, description="Filter by status: success | failure"),
    email: str | None = Query(None, description="Filter by email (partial match)"),
) -> AccessAuditListResponse:
    q = select(AccessAuditLog)
    if action:
        q = q.where(AccessAuditLog.action == action)
    if status:
        q = q.where(AccessAuditLog.status == status)
    if email:
        q = q.where(AccessAuditLog.email.ilike(f"%{email}%"))

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    q = q.order_by(desc(AccessAuditLog.created_at)).offset(skip).limit(limit)
    rows = (await db.execute(q)).scalars().all()

    return AccessAuditListResponse(
        items=[AccessAuditLogResponse.model_validate(r) for r in rows],
        total=total,
    )


@router.get(
    "/moderation",
    response_model=ModerationAuditListResponse,
    summary="List moderation audit entries per video (admin only)",
)
async def list_moderation_audit(
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = Query(None, description="Filter by moderation status"),
) -> ModerationAuditListResponse:
    base = select(ModerationResult).join(Video, ModerationResult.video_id == Video.id)
    if status:
        base = base.where(ModerationResult.status == status)

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar_one()

    q = select(ModerationResult, Video).join(Video, ModerationResult.video_id == Video.id)
    if status:
        q = q.where(ModerationResult.status == status)
    q = q.order_by(desc(ModerationResult.created_at)).offset(skip).limit(limit)
    rows = (await db.execute(q)).all()

    items: list[ModerationAuditEntry] = []
    for mod_result, video in rows:
        raw_violations = mod_result.violations or []
        violations = [
            ViolationDetail(
                category=v.get("category"),
                confidence=v.get("confidence"),
                frame_ids=v.get("frame_ids"),
                timestamp_ms=v.get("timestamp_ms"),
                timestamps=v.get("timestamps"),
                rule=v.get("rule"),
                agent=v.get("agent"),
                description=v.get("description"),
                severity=v.get("severity"),
            )
            for v in raw_violations
            if isinstance(v, dict)
        ]
        st = mod_result.status
        status_str = st.value if hasattr(st, "value") else str(st)
        ra = mod_result.review_action
        review_action_str = ra.value if ra is not None and hasattr(ra, "value") else None
        items.append(
            ModerationAuditEntry(
                moderation_result_id=mod_result.id,
                video_id=video.id,
                video_title=video.title,
                status=status_str,
                overall_confidence=mod_result.overall_confidence,
                ai_model=mod_result.ai_model,
                processing_time_ms=mod_result.processing_time_ms,
                violations=violations,
                summary=mod_result.summary,
                reviewed_by_id=mod_result.reviewed_by,
                review_action=review_action_str,
                review_notes=mod_result.review_notes,
                reviewed_at=mod_result.reviewed_at,
                override_decision=mod_result.override_decision,
                override_at=mod_result.override_at,
                created_at=mod_result.created_at,
            )
        )

    return ModerationAuditListResponse(items=items, total=total)
