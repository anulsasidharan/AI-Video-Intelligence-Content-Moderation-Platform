"""Tests for app.core.logging — setup_logging and get_logger."""

import logging

from app.core.logging import get_logger, setup_logging

# ── setup_logging ─────────────────────────────────────────────────────────────


def test_setup_logging_runs_without_error(monkeypatch):
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.DEBUG", False)
    setup_logging()  # should not raise


def test_setup_logging_dev_mode(monkeypatch):
    monkeypatch.setattr("app.config.settings.APP_ENV", "development")
    monkeypatch.setattr("app.config.settings.DEBUG", True)
    setup_logging()  # should not raise


def test_setup_logging_silences_noisy_loggers(monkeypatch):
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.DEBUG", False)
    setup_logging()

    uvicorn_access = logging.getLogger("uvicorn.access")
    sqlalchemy_engine = logging.getLogger("sqlalchemy.engine")
    assert uvicorn_access.level == logging.WARNING
    assert sqlalchemy_engine.level == logging.WARNING


def test_setup_logging_root_level_debug_when_debug(monkeypatch):
    monkeypatch.setattr("app.config.settings.APP_ENV", "development")
    monkeypatch.setattr("app.config.settings.DEBUG", True)
    setup_logging()
    assert logging.getLogger().level == logging.DEBUG


def test_setup_logging_root_level_info_when_not_debug(monkeypatch):
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.DEBUG", False)
    setup_logging()
    assert logging.getLogger().level == logging.INFO


# ── get_logger ────────────────────────────────────────────────────────────────


def test_get_logger_returns_bound_logger():
    logger = get_logger("test.module")
    assert logger is not None


def test_get_logger_default_name():
    logger = get_logger()
    assert logger is not None


def test_get_logger_can_log_without_raising(monkeypatch):
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.DEBUG", False)
    setup_logging()
    logger = get_logger("test")
    # Should not raise
    logger.info("test event", key="value")
    logger.warning("warning event")
    logger.error("error event", error="something went wrong")
