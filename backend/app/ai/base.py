"""
Base agent class shared by all specialist agents.

Provides:
- Structured logging via structlog
- OpenAI async client (lazily initialised)
- Retry helper with exponential back-off
- Standard interface: async def run(state) -> dict
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from openai import AsyncOpenAI

from app.config import settings

logger = structlog.get_logger(__name__)

_DEFAULT_RETRIES = 3
_BASE_DELAY = 1.0  # seconds


class BaseAgent:
    """Abstract base for all LangGraph agent nodes."""

    name: str = "base_agent"

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    # ── OpenAI client ────────────────────────────────────────────────────────

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    # ── Retry helper ─────────────────────────────────────────────────────────

    async def _call_with_retry(
        self,
        coro_fn,
        *args: Any,
        retries: int = _DEFAULT_RETRIES,
        **kwargs: Any,
    ) -> Any:
        """Call an async function with exponential back-off on transient errors."""
        delay = _BASE_DELAY
        last_exc: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                return await coro_fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "agent_retry",
                    agent=self.name,
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt < retries:
                    await asyncio.sleep(delay)
                    delay *= 2
        raise RuntimeError(
            f"[{self.name}] Failed after {retries} attempts: {last_exc}"
        ) from last_exc

    # ── Interface ─────────────────────────────────────────────────────────────

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        """Process the shared state and return a partial update dict."""
        raise NotImplementedError

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(raw: str | None) -> str:
        """Strip markdown code fences and whitespace so json.loads never fails on formatting."""
        text = (raw or "").strip()
        # Remove ```json ... ``` or ``` ... ``` wrappers that gpt-4o sometimes adds
        if text.startswith("```"):
            lines = text.splitlines()
            # Drop first line (```json or ```) and last ``` line
            inner = [line for line in lines[1:] if line.strip() != "```"]
            text = "\n".join(inner).strip()
        return text or "{}"

    def _mark_completed(self, state: dict[str, Any]) -> list[str]:
        # With operator.add reducer, return only the NEW item to append
        return [self.name]

    def _append_error(self, state: dict[str, Any], msg: str) -> list[str]:
        # With operator.add reducer, return only the NEW error to append
        return [f"[{self.name}] {msg}"]
