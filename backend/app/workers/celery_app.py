"""
W-01 Celery Application

Initialises the Celery app, configures broker/backend from settings,
defines task routing, shared task defaults, structured logging signals,
and exposes a sync SQLAlchemy session factory for use in worker tasks.

Usage:
    from app.workers.celery_app import celery_app, sync_session

Worker startup (listen on every routed queue; required in production):
    celery -A app.workers.celery_app worker \\
      --queues video,moderation,analytics,cleanup,reports,notifications,streams
"""

from __future__ import annotations

import ssl
from collections.abc import Generator
from contextlib import contextmanager

import structlog
from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun, task_retry
from sqlalchemy.orm import Session

from app.config import settings
from app.core.sync_db import (
    _SessionFactory,
)  # noqa: F401 — re-exported so tests can patch it here

logger = structlog.get_logger(__name__)


@contextmanager
def sync_session() -> Generator[Session, None, None]:
    """Yield a sync DB session; commit on success, rollback on error.

    Defined here (not just re-exported from sync_db) so that tests can patch
    ``app.workers.celery_app._SessionFactory`` and have it take effect.
    """
    session: Session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Celery app ─────────────────────────────────────────────────────────────────

celery_app = Celery("vidshield")

# ElastiCache uses TLS (rediss://) — disable cert verification (Amazon CA not in
# container trust store). For plain redis:// no SSL options are needed.
_use_tls = settings.CELERY_BROKER_URL.startswith("rediss://")
_ssl_opts: dict = {"ssl_cert_reqs": ssl.CERT_NONE} if _use_tls else {}

celery_app.conf.update(
    # Broker & backend
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    broker_use_ssl=_ssl_opts or None,
    redis_backend_use_ssl=_ssl_opts or None,
    # Serialisation
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Default retry policy
    task_max_retries=3,
    task_default_retry_delay=60,  # seconds
    # Task routing: each domain gets its own queue
    task_routes={
        "app.workers.video_tasks.*": {"queue": "video"},
        "app.workers.moderation_tasks.*": {"queue": "moderation"},
        "app.workers.stream_tasks.*": {"queue": "streams"},
        "app.workers.analytics_tasks.*": {"queue": "analytics"},
        "app.workers.cleanup_tasks.*": {"queue": "cleanup"},
        "app.workers.report_tasks.*": {"queue": "reports"},
        "app.workers.notification_tasks.*": {"queue": "notifications"},
    },
    # Result expiry (24 h)
    result_expires=86_400,
    # Celery Beat: scheduled tasks
    beat_schedule={
        "daily-digest-0800-utc": {
            "task": "app.workers.notification_tasks.send_daily_digests_beat_task",
            "schedule": 86_400,  # every 24 hours
            "options": {"queue": "notifications"},
        },
    },
)

# Explicitly import task modules so Celery registers them on worker startup.
# autodiscover_tasks() appends ".tasks" to each entry, which does not match
# our module layout — direct imports are the reliable alternative.
import app.workers.analytics_tasks  # noqa: E402, F401
import app.workers.cleanup_tasks  # noqa: E402, F401
import app.workers.moderation_tasks  # noqa: E402, F401
import app.workers.notification_tasks  # noqa: E402, F401
import app.workers.report_tasks  # noqa: E402, F401
import app.workers.stream_tasks  # noqa: E402, F401
import app.workers.video_tasks  # noqa: E402, F401

# ── Structured logging signals ─────────────────────────────────────────────────


@task_prerun.connect
def _on_task_prerun(task_id: str, task, args, kwargs, **_kw) -> None:
    logger.info("celery_task_start", task_id=task_id, task_name=task.name)


@task_postrun.connect
def _on_task_postrun(task_id: str, task, retval, state, **_kw) -> None:
    logger.info("celery_task_done", task_id=task_id, task_name=task.name, state=state)


@task_retry.connect
def _on_task_retry(request, reason, einfo, **_kw) -> None:
    logger.warning(
        "celery_task_retry",
        task_id=request.id,
        task_name=request.task,
        reason=str(reason),
    )


@task_failure.connect
def _on_task_failure(task_id: str, exception, traceback, sender, **_kw) -> None:
    logger.error(
        "celery_task_failed",
        task_id=task_id,
        task_name=sender.name,
        error=str(exception),
    )
