"""
W-05 Report Generation Tasks

Async Celery worker that:
1. Loads report job configuration from the database
2. Queries aggregated data via report_service
3. Generates a PDF via pdf_service (ReportLab)
4. Uploads the PDF to S3 via storage_service
5. Updates job status (ready / failed)

Queue: reports

Entry point:
    generate_report_pdf_task.apply_async(kwargs={"job_id": "<uuid>"}, queue="reports")
"""

from __future__ import annotations

import json
import uuid
from contextlib import suppress

import structlog
from celery import shared_task
from sqlalchemy import select

from app.core.sync_db import sync_session
from app.models.report import ReportJob, ReportStatus
from app.schemas.report import ReportFilters

logger = structlog.get_logger(__name__)

_GCS_PREFIX = "reports/"


@shared_task(
    bind=True,
    name="app.workers.report_tasks.generate_report_pdf_task",
    max_retries=2,
    default_retry_delay=30,
)
def generate_report_pdf_task(self, job_id: str) -> dict:
    """
    Generate a PDF report for the given ReportJob id and upload it to GCS.

    Returns a dict with { job_id, status, s3_key } on success.
    """
    log = logger.bind(job_id=job_id, celery_task_id=self.request.id)
    log.info("report_task_start")

    try:
        return _run(job_id, log)
    except Exception as exc:
        log.error("report_task_error", error=str(exc))
        _fail_job(job_id, str(exc))
        raise self.retry(exc=exc) from exc


def _run(job_id: str, log) -> dict:
    # ── 1. Load job ────────────────────────────────────────────────────────────
    # Read ALL attributes inside the session block — accessing them after the
    # `with` exits raises DetachedInstanceError (SQLAlchemy expires on close).
    with sync_session() as db:
        result = db.execute(select(ReportJob).where(ReportJob.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"ReportJob {job_id} not found in database.")

        report_type = job.report_type
        orientation = job.orientation.value if job.orientation else "portrait"
        title = job.title
        raw_filters = job.filters
        raw_columns = job.columns

    filters_obj = ReportFilters()
    if raw_filters:
        try:
            filters_obj = ReportFilters.model_validate_json(raw_filters)
        except Exception as e:
            log.warning("report_filters_parse_error", error=str(e))

    columns: list[str] | None = None
    if raw_columns:
        with suppress(Exception):
            columns = json.loads(raw_columns)

    log.info("report_task_fetching_data", report_type=report_type.value)

    # ── 2. Fetch data (sync wrapper around async service) ──────────────────────
    import asyncio

    from app.services.report_service import fetch_report_data

    async def _fetch() -> dict:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

        from app.config import settings

        # Create a fresh engine per task — do NOT use get_engine() whose
        # connection pool is bound to a previous event loop, which causes
        # "Future attached to a different loop" with asyncpg when asyncio.run()
        # creates a new loop on each Celery task execution.
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
        )
        try:
            async with AsyncSession(engine) as async_db:
                return await fetch_report_data(
                    db=async_db,
                    report_type=report_type,
                    filters=filters_obj,
                    columns=columns,
                    page=1,
                    page_size=10_000,  # fetch all rows for PDF
                )
        finally:
            await engine.dispose()

    # Always create a fresh event loop — Celery's prefork workers reuse processes
    # and a reused loop causes "Future attached to different loop" errors with asyncpg.
    data = asyncio.run(_fetch())

    rows = data["rows"]
    summary = data["summary"]
    report_columns = data["columns"]

    log.info("report_task_data_ready", row_count=len(rows))

    # ── 3. Generate PDF ────────────────────────────────────────────────────────
    from app.services.pdf_service import generate_pdf

    pdf_bytes = generate_pdf(
        report_title=title,
        report_type=report_type.value,
        columns=report_columns,
        rows=rows,
        summary=summary,
        orientation=orientation,
    )

    log.info("report_task_pdf_generated", size_bytes=len(pdf_bytes))

    # ── 4. Upload to GCS ───────────────────────────────────────────────────────
    from io import BytesIO

    from app.services.storage_service import get_storage_service

    storage = get_storage_service()
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:80]
    gcs_key = f"{_GCS_PREFIX}{job_id}/{safe_title}.pdf"

    storage.upload_fileobj(
        fileobj=BytesIO(pdf_bytes),
        s3_key=gcs_key,  # parameter name kept for StorageService interface compatibility
        content_type="application/pdf",
    )

    log.info("report_task_uploaded", gcs_key=gcs_key)

    # ── 5. Mark job ready ──────────────────────────────────────────────────────
    with sync_session() as db:
        result = db.execute(select(ReportJob).where(ReportJob.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job:
            job.status = ReportStatus.READY
            job.s3_key = gcs_key  # column name kept to avoid migration
            job.file_size_bytes = len(pdf_bytes)
            job.row_count = len(rows)
            db.commit()

    log.info("report_task_done", job_id=job_id, gcs_key=gcs_key)
    return {"job_id": job_id, "status": "ready", "s3_key": gcs_key}


def _fail_job(job_id: str, error: str) -> None:
    """Mark the job as failed in the database without raising."""
    try:
        with sync_session() as db:
            result = db.execute(select(ReportJob).where(ReportJob.id == uuid.UUID(job_id)))
            job = result.scalar_one_or_none()
            if job:
                job.status = ReportStatus.FAILED
                job.error_message = error[:1000]
                db.commit()
    except Exception as e:
        logger.error("report_task_fail_update_error", job_id=job_id, error=str(e))
