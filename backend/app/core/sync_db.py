"""
Synchronous SQLAlchemy session for Celery workers and other non-async code paths.

Kept separate from ``celery_app`` so modules like agent audit logging can persist
without importing the Celery application (avoids circular imports and keeps the
DB layer independent of the task queue).
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
_SessionFactory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


@contextmanager
def sync_session() -> Generator[Session, None, None]:
    """Yield a sync session; commit on success, rollback on error."""
    session: Session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
