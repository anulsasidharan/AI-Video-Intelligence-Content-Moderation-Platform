"""
W-03 Moderation Tasks

Runs or re-runs moderation decisions, evaluates policy rules, dispatches
outbound webhooks, and enqueues items for human review.

These tasks are triggered either automatically after video processing
or manually by an operator (e.g. policy change → re-evaluate queue).

Public entry points:
    run_moderation_task.delay(video_id, policy_rules)
    apply_policy_task.delay(moderation_result_id, policy_id)
    dispatch_webhooks_task.delay(event, payload)
    enqueue_human_review_task.delay(video_id, moderation_result_id, priority)
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from celery import shared_task

from app.ai.graphs.moderation_workflow import run_moderation_workflow
from app.models.moderation import (
    ModerationQueueItem,
    ModerationResult,
    ModerationStatus,
)
from app.models.webhook import WebhookEndpoint
from app.workers.celery_app import sync_session

logger = structlog.get_logger(__name__)

_WEBHOOK_TIMEOUT_SECONDS = 10


# ── W-03-A: Run / re-run moderation workflow ───────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.moderation_tasks.run_moderation_task",
    max_retries=3,
    default_retry_delay=60,
)
def run_moderation_task(
    self,
    video_id: str,
    policy_rules: list[dict[str, Any]] | None = None,
    content_summary: str = "",
    violations: list[dict[str, Any]] | None = None,
    scene_summary: dict[str, int] | None = None,
    transcript_excerpt: str = "",
    confidence_threshold: float = 0.6,
) -> dict[str, Any]:
    """
    Run the fast moderation workflow (C-05) on an already-processed video.

    Intended for:
    - Re-evaluation after policy changes.
    - Live stream segment re-moderation.
    - Manual operator re-runs.

    Updates the ModerationResult row with the new decision.

    Returns:
        ModerationWorkflowResult as a dict.
    """
    logger.info("run_moderation_task_start", video_id=video_id)

    try:
        result = asyncio.run(
            run_moderation_workflow(
                video_id=video_id,
                content_summary=content_summary,
                violations=violations or [],
                policy_rules=policy_rules or [],
                scene_summary=scene_summary or {},
                transcript_excerpt=transcript_excerpt,
                confidence_threshold=confidence_threshold,
            )
        )
    except Exception as exc:
        logger.error("run_moderation_task_error", video_id=video_id, error=str(exc))
        raise self.retry(exc=exc) from exc

    _DECISION_TO_STATUS: dict[str, ModerationStatus] = {
        "approved": ModerationStatus.APPROVED,
        "rejected": ModerationStatus.REJECTED,
        "escalated": ModerationStatus.ESCALATED,
        "needs_review": ModerationStatus.ESCALATED,
    }
    new_status = _DECISION_TO_STATUS.get(result.decision.value, ModerationStatus.PENDING)

    with sync_session() as db:
        mod = (
            db.query(ModerationResult)
            .filter(ModerationResult.video_id == uuid.UUID(video_id))
            .first()
        )
        if mod:
            mod.status = new_status
            mod.overall_confidence = result.confidence
            mod.updated_at = datetime.now(UTC)

    logger.info(
        "run_moderation_task_done",
        video_id=video_id,
        decision=result.decision.value,
        escalated=result.escalated,
    )
    return result.model_dump()


# ── W-03-B: Apply policy rules ─────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.moderation_tasks.apply_policy_task",
    max_retries=3,
    default_retry_delay=30,
)
def apply_policy_task(
    self,
    moderation_result_id: str,
    policy_id: str,
) -> dict[str, Any]:
    """
    Evaluate active policy rules against an existing ModerationResult and
    update the status according to policy-defined auto-actions.

    Policy auto-action logic:
    - If any violation matches a REJECT rule → REJECTED
    - If any violation matches a FLAG rule → FLAGGED
    - Otherwise → APPROVED (unchanged if already at a higher severity)

    Returns:
        {"moderation_result_id": str, "new_status": str, "policy_id": str}
    """
    from app.models.policy import Policy

    logger.info(
        "apply_policy_task_start",
        moderation_result_id=moderation_result_id,
        policy_id=policy_id,
    )

    try:
        with sync_session() as db:
            mod = db.get(ModerationResult, uuid.UUID(moderation_result_id))
            policy = db.get(Policy, uuid.UUID(policy_id))

            if not mod or not policy:
                logger.warning(
                    "apply_policy_task_not_found",
                    moderation_result_id=moderation_result_id,
                    policy_id=policy_id,
                )
                return {
                    "moderation_result_id": moderation_result_id,
                    "new_status": "not_found",
                    "policy_id": policy_id,
                }

            violations: list[dict] = mod.violations or []
            rules: list[dict] = policy.rules or []

            violation_categories = {v.get("category", "").lower() for v in violations}
            new_status = mod.status

            for rule in rules:
                action = str(rule.get("action", "")).lower()
                category = str(rule.get("category", "")).lower()

                if category and category not in violation_categories:
                    continue

                if action == "reject":
                    new_status = ModerationStatus.REJECTED
                    break
                elif action in ("flag", "escalate") and new_status not in (
                    ModerationStatus.REJECTED,
                ):
                    new_status = ModerationStatus.FLAGGED

            if new_status != mod.status:
                mod.status = new_status
                mod.updated_at = datetime.now(UTC)

        logger.info(
            "apply_policy_task_done",
            moderation_result_id=moderation_result_id,
            new_status=new_status.value,
        )
        return {
            "moderation_result_id": moderation_result_id,
            "new_status": new_status.value,
            "policy_id": policy_id,
        }

    except Exception as exc:
        logger.error("apply_policy_task_error", error=str(exc))
        raise self.retry(exc=exc) from exc


# ── W-03-C: Dispatch outbound webhooks ────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.moderation_tasks.dispatch_webhooks_task",
    max_retries=3,
    default_retry_delay=30,
)
def dispatch_webhooks_task(
    self,
    event: str,
    payload: dict[str, Any],
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """
    Deliver an event payload to all active webhook endpoints that subscribe to
    the given event. Computes an HMAC-SHA256 signature header when a secret is set.

    Args:
        event:     Event name (e.g. "moderation.flagged", "video.processed").
        payload:   Event payload dict.
        tenant_id: Optional tenant filter — only deliver to matching endpoints.

    Returns:
        {"delivered": int, "failed": int, "skipped": int}
    """
    logger.info("dispatch_webhooks_task_start", webhook_event=event, tenant_id=tenant_id)

    delivered = failed = skipped = 0

    with sync_session() as db:
        query = db.query(WebhookEndpoint).filter(WebhookEndpoint.is_active.is_(True))
        if tenant_id:
            query = query.filter(WebhookEndpoint.tenant_id == tenant_id)
        endpoints = query.all()

    body = json.dumps(payload, default=str).encode("utf-8")

    for endpoint in endpoints:
        subscribed: list[str] = endpoint.events or []
        if subscribed and event not in subscribed:
            skipped += 1
            continue

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-VidShield-Event": event,
        }

        if endpoint.secret:
            sig = hmac.new(endpoint.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers["X-VidShield-Signature"] = f"sha256={sig}"

        try:
            resp = httpx.post(
                endpoint.url,
                content=body,
                headers=headers,
                timeout=_WEBHOOK_TIMEOUT_SECONDS,
            )
            with sync_session() as db:
                ep = db.get(WebhookEndpoint, endpoint.id)
                if ep:
                    ep.total_deliveries += 1
                    ep.last_delivery_at = datetime.now(UTC).isoformat()
                    ep.last_status_code = resp.status_code
                    if not resp.is_success:
                        ep.failed_deliveries += 1
                        failed += 1
                    else:
                        delivered += 1
        except Exception as exc:
            logger.warning(
                "dispatch_webhooks_delivery_failed",
                url=endpoint.url,
                webhook_event=event,
                error=str(exc),
            )
            with sync_session() as db:
                ep = db.get(WebhookEndpoint, endpoint.id)
                if ep:
                    ep.failed_deliveries += 1
            failed += 1

    logger.info(
        "dispatch_webhooks_task_done",
        webhook_event=event,
        delivered=delivered,
        failed=failed,
        skipped=skipped,
    )

    if failed > 0:
        raise self.retry(
            exc=RuntimeError(f"{failed} webhook(s) failed for event '{event}'"),
        )

    return {"delivered": delivered, "failed": failed, "skipped": skipped}


# ── W-03-D: Record autonomous AI decision in the audit queue ──────────────────


@shared_task(
    bind=True,
    name="app.workers.moderation_tasks.record_moderation_decision_task",
    max_retries=3,
    default_retry_delay=30,
)
def record_moderation_decision_task(
    self,
    video_id: str,
    moderation_result_id: str | None = None,
    final_status: str = "approved",
    priority: int = 0,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """
    Write the AI's final autonomous decision to the moderation queue as an
    audit log entry.  The decision is already final — this is NOT a pending
    human-approval gate.

    Operators see every AI decision here and may use the override endpoint
    for exceptional corrections, but no human action is required for normal
    operation.

    Idempotent — if an entry already exists for this video it is updated in place.

    Args:
        video_id:             UUID string of the processed video.
        moderation_result_id: UUID string of the related ModerationResult.
        final_status:         The autonomous status string ("approved", "rejected", "flagged").
        priority:             Display priority (2=rejected, 1=flagged, 0=approved).
        tenant_id:            Tenant scope.

    Returns:
        {"queue_item_id": str, "created": bool}
    """
    logger.info(
        "record_moderation_decision_start",
        video_id=video_id,
        final_status=final_status,
    )

    try:
        status_enum = ModerationStatus(final_status)
    except ValueError:
        status_enum = ModerationStatus.APPROVED

    try:
        with sync_session() as db:
            existing = (
                db.query(ModerationQueueItem)
                .filter(ModerationQueueItem.video_id == uuid.UUID(video_id))
                .first()
            )

            if existing:
                existing.status = status_enum
                existing.priority = priority
                existing.moderation_result_id = (
                    uuid.UUID(moderation_result_id)
                    if moderation_result_id
                    else existing.moderation_result_id
                )
                item_id = str(existing.id)
                logger.info("record_moderation_decision_updated", queue_item_id=item_id)
                return {"queue_item_id": item_id, "created": False}

            item = ModerationQueueItem(
                video_id=uuid.UUID(video_id),
                moderation_result_id=(
                    uuid.UUID(moderation_result_id) if moderation_result_id else None
                ),
                status=status_enum,
                priority=priority,
                tenant_id=tenant_id,
            )
            db.add(item)
            db.flush()
            item_id = str(item.id)

        logger.info(
            "record_moderation_decision_done",
            queue_item_id=item_id,
            final_status=final_status,
        )
        return {"queue_item_id": item_id, "created": True}

    except Exception as exc:
        logger.error("record_moderation_decision_error", video_id=video_id, error=str(exc))
        raise self.retry(exc=exc) from exc


# ── Kept for backward compatibility (live-stream segments, re-runs) ────────────


@shared_task(
    bind=True,
    name="app.workers.moderation_tasks.enqueue_human_review_task",
    max_retries=3,
    default_retry_delay=30,
)
def enqueue_human_review_task(
    self,
    video_id: str,
    moderation_result_id: str | None = None,
    priority: int = 0,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Delegates to record_moderation_decision_task with FLAGGED status."""
    return record_moderation_decision_task.apply(
        kwargs=dict(
            video_id=video_id,
            moderation_result_id=moderation_result_id,
            final_status=ModerationStatus.FLAGGED.value,
            priority=priority,
            tenant_id=tenant_id,
        )
    ).get()
