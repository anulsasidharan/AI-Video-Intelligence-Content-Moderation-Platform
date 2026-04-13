"""
Reports API — R-04

Admin-only endpoints for report generation, template management, and PDF download.

Endpoints:
  POST   /reports/preview              — preview paginated report data (JSON)
  POST   /reports/generate             — queue async PDF generation job
  GET    /reports/                     — list report jobs
  GET    /reports/{job_id}             — get job status/details
  GET    /reports/{job_id}/download    — get presigned S3 URL for PDF
  DELETE /reports/{job_id}             — delete a job record
  GET    /reports/templates            — list saved templates
  POST   /reports/templates            — save a new template
  DELETE /reports/templates/{id}       — delete a template
"""

from __future__ import annotations

import json
import uuid
from contextlib import suppress
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.core.exceptions import NotFoundError
from app.dependencies import get_db
from app.models.report import ReportStatus
from app.schemas.report import (
    ReportGenerateRequest,
    ReportJobListResponse,
    ReportJobResponse,
    ReportPreviewRequest,
    ReportPreviewResponse,
    ReportTemplateCreate,
    ReportTemplateResponse,
)
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])
logger = structlog.get_logger(__name__)


def _job_to_response(job) -> ReportJobResponse:
    filters_dict = None
    if job.filters:
        with suppress(Exception):
            filters_dict = json.loads(job.filters)
    columns_list = None
    if job.columns:
        with suppress(Exception):
            columns_list = json.loads(job.columns)
    return ReportJobResponse(
        id=job.id,
        title=job.title,
        report_type=job.report_type,
        status=job.status,
        filters=filters_dict,
        columns=columns_list,
        orientation=job.orientation,
        s3_key=job.s3_key,
        file_size_bytes=job.file_size_bytes,
        row_count=job.row_count,
        error_message=job.error_message,
        celery_task_id=job.celery_task_id,
        template_id=job.template_id,
        generated_by=job.generated_by,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )


def _template_to_response(tmpl) -> ReportTemplateResponse:
    filters_dict = None
    if tmpl.filters:
        with suppress(Exception):
            filters_dict = json.loads(tmpl.filters)
    columns_list = None
    if tmpl.columns:
        with suppress(Exception):
            columns_list = json.loads(tmpl.columns)
    return ReportTemplateResponse(
        id=tmpl.id,
        name=tmpl.name,
        description=tmpl.description,
        report_type=tmpl.report_type,
        filters=filters_dict,
        columns=columns_list,
        orientation=tmpl.orientation,
        is_shared=tmpl.is_shared,
        owner_id=tmpl.owner_id,
        created_at=tmpl.created_at.isoformat(),
        updated_at=tmpl.updated_at.isoformat(),
    )


# ── Preview ────────────────────────────────────────────────────────────────────


@router.post(
    "/preview",
    response_model=ReportPreviewResponse,
    summary="Preview report data (paginated JSON, no PDF)",
)
async def preview_report(
    body: ReportPreviewRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportPreviewResponse:
    data = await report_service.fetch_report_data(
        db=db,
        report_type=body.report_type,
        filters=body.filters,
        columns=body.columns,
        page=body.page,
        page_size=body.page_size,
    )
    return ReportPreviewResponse(
        columns=data["columns"],
        rows=data["rows"],
        total=data["total"],
        page=body.page,
        page_size=body.page_size,
        summary=data["summary"],
    )


# ── Generate (async) ───────────────────────────────────────────────────────────


@router.post(
    "/generate",
    response_model=ReportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue an async PDF report generation job",
)
async def generate_report(
    body: ReportGenerateRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportJobResponse:
    job = await report_service.create_job(db, body, current_user)

    # Dispatch Celery task.
    # Import celery_app FIRST — report_tasks.py imports sync_session from
    # app.core.sync_db (not celery_app), so the Celery application is never
    # configured in the API container unless we import it explicitly here.
    # Without this, apply_async silently uses Celery's default amqp://localhost
    # broker and raises a connection error.
    import app.workers.celery_app  # noqa: F401 — registers broker/backend config
    from app.workers.report_tasks import generate_report_pdf_task

    task = generate_report_pdf_task.apply_async(
        kwargs={"job_id": str(job.id)},
        queue="reports",
    )
    await report_service.mark_job_generating(db, job.id, task.id)
    await db.refresh(job)

    logger.info("report_job_queued", job_id=str(job.id), celery_task_id=task.id)
    return _job_to_response(job)


# ── List jobs ──────────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=ReportJobListResponse,
    summary="List report generation jobs for the current admin",
)
async def list_report_jobs(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),  # noqa: B008
    page_size: int = Query(default=20, ge=1, le=100),  # noqa: B008
    status_filter: ReportStatus | None = Query(  # noqa: B008
        default=None, alias="status"
    ),
) -> ReportJobListResponse:
    jobs, total = await report_service.list_jobs(
        db, current_user, page=page, page_size=page_size, status=status_filter
    )
    return ReportJobListResponse(
        items=[_job_to_response(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Templates — list ───────────────────────────────────────────────────────────
# NOTE: Template routes MUST be registered before /{job_id} routes.
# FastAPI matches paths in declaration order; if /{job_id} comes first,
# the literal string "templates" is parsed as a UUID and the request
# returns 422 Unprocessable Entity instead of reaching the templates handler.


@router.get(
    "/templates",
    response_model=list[ReportTemplateResponse],
    summary="List saved report templates",
)
async def list_templates(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReportTemplateResponse]:
    templates = await report_service.list_templates(db, current_user)
    return [_template_to_response(t) for t in templates]


# ── Templates — create ─────────────────────────────────────────────────────────


@router.post(
    "/templates",
    response_model=ReportTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a new report template",
)
async def create_template(
    body: ReportTemplateCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportTemplateResponse:
    tmpl = await report_service.create_template(db, body, current_user)
    return _template_to_response(tmpl)


# ── Templates — delete ─────────────────────────────────────────────────────────


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a saved report template",
)
async def delete_template(
    template_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    deleted = await report_service.delete_template(db, template_id, current_user)
    if not deleted:
        raise NotFoundError(f"Template {template_id} not found.")


# ── Get single job ─────────────────────────────────────────────────────────────


@router.get(
    "/{job_id}",
    response_model=ReportJobResponse,
    summary="Get details of a specific report job",
)
async def get_report_job(
    job_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportJobResponse:
    job = await report_service.get_job(db, job_id, current_user)
    if not job:
        raise NotFoundError(f"Report job {job_id} not found.")
    return _job_to_response(job)


# ── Download (stream PDF directly) ────────────────────────────────────────────


@router.get(
    "/{job_id}/download",
    summary="Stream the completed PDF report directly to the client",
)
async def download_report(
    job_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    job = await report_service.get_job(db, job_id, current_user)
    if not job:
        raise NotFoundError(f"Report job {job_id} not found.")
    if job.status != ReportStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report is not ready yet (status: {job.status.value}).",
        )
    if not job.s3_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 key missing for a ready report — contact support.",
        )

    from app.services.storage_service import get_storage_service

    storage = get_storage_service()
    pdf_bytes = storage.download_object(job.s3_key)
    filename = job.s3_key.split("/")[-1]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Delete job ─────────────────────────────────────────────────────────────────


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a report job record",
)
async def delete_report_job(
    job_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    deleted = await report_service.delete_job(db, job_id, current_user)
    if not deleted:
        raise NotFoundError(f"Report job {job_id} not found.")
