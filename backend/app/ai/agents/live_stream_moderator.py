"""
A-07 Live Stream Moderator Agent

Processes a batch of live stream frames (and optional audio chunk) through
three parallel analysis pipelines:

  1. Visual Content Moderation — GPT-4o vision checks for policy violations
     (violence, nudity, hate symbols, drugs, etc.)
  2. OCR — extracts visible text for keyword/brand policy checks
  3. Face Analysis — age estimation, minor detection, liveness check

Results are synthesised into a LiveChunkResult that the Celery task uses to
create Alert DB records and push WebSocket events.

Public API:
    agent = LiveStreamModerator()
    result = await agent.analyze_chunk(
        stream_id="uuid",
        frames=["<b64>", ...],
        transcript_hint="",   # optional short audio transcript for this chunk
    )
    result.violations         # list[LiveViolation]
    result.face_analysis      # FaceAnalysisResult
    result.ocr_text           # str
    result.overall_safe       # bool
    result.highest_severity   # "low" | "medium" | "high" | "critical" | None
"""

from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from typing import Any

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.ai.tools.face_analyzer import FaceAnalysisResult, analyze_faces
from app.ai.tools.ocr_tool import run_ocr
from app.config import settings

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"
_MAX_FRAMES_VISUAL = 5  # keep visual analysis fast for live use

_VISUAL_SYSTEM = """\
You are a real-time content safety moderator for a live video stream.

Analyze the provided frames for policy violations. Categories to check:
- violence: physical harm, weapons, blood, fighting
- nudity: explicit or implicit sexual content, partial nudity
- hate_symbols: hate speech symbols, extremist imagery, discriminatory content
- drugs: drug paraphernalia, substance use
- gambling: gambling activities, casino content (for age-restricted platforms)
- self_harm: content depicting self-harm or suicide
- spam_overlay: watermarks, spam text, malicious URLs visible on screen
- graphic_content: disturbing graphic imagery

Return ONLY a valid JSON object:
{
  "violations": [
    {
      "category": "<category>",
      "severity": "low|medium|high|critical",
      "confidence": <float 0.0-1.0>,
      "description": "<brief description of what was detected>",
      "frame_index": <int, 0-based>
    }
  ],
  "overall_safe": <bool>,
  "content_summary": "<one sentence summary of frame content>",
  "requires_immediate_action": <bool>
}

If no violations are found, return violations=[], overall_safe=true.
Be accurate — false positives waste operator time. Only flag clear violations.
"""


# ── Output schemas ─────────────────────────────────────────────────────────────


class LiveViolation(BaseModel):
    category: str
    severity: str = "medium"
    confidence: float = 0.0
    description: str = ""
    frame_index: int = 0


class LiveChunkResult(BaseModel):
    stream_id: str
    violations: list[LiveViolation] = Field(default_factory=list)
    face_analysis: FaceAnalysisResult = Field(default_factory=FaceAnalysisResult)
    ocr_text: str = ""
    content_summary: str = ""
    overall_safe: bool = True
    requires_immediate_action: bool = False
    highest_severity: str | None = None
    error: str | None = None

    def to_ws_event(self) -> dict[str, Any]:
        """Serialise for WebSocket push to the browser."""
        return {
            "event": "frame.moderated",
            "stream_id": self.stream_id,
            "overall_safe": self.overall_safe,
            "requires_immediate_action": self.requires_immediate_action,
            "highest_severity": self.highest_severity,
            "violations": [v.model_dump() for v in self.violations],
            "face_analysis": {
                "face_count": self.face_analysis.face_count,
                "has_minor": self.face_analysis.has_minor,
                "restricted_content": self.face_analysis.restricted_content,
                "liveness_score": self.face_analysis.overall_liveness_score,
                "summary": self.face_analysis.summary,
            },
            "ocr_text": self.ocr_text,
            "content_summary": self.content_summary,
        }


_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class LiveStreamModerator:
    """
    Lightweight agent for real-time frame analysis.

    Runs visual moderation, OCR, and face analysis in parallel (asyncio.gather)
    to minimise end-to-end latency per chunk.
    """

    def __init__(self, _client: AsyncOpenAI | None = None) -> None:
        self._client = _client or AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # ── Visual content moderation ──────────────────────────────────────────────

    async def _visual_moderation(self, frames: list[str]) -> dict[str, Any]:
        frames_to_check = frames[:_MAX_FRAMES_VISUAL]
        content: list[dict] = []
        for frame_b64 in frames_to_check:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame_b64}",
                        "detail": "low",
                    },
                }
            )
        content.append(
            {
                "type": "text",
                "text": (
                    f"Moderate these {len(frames_to_check)} live stream frame(s) "
                    "for policy violations. Return the JSON object."
                ),
            }
        )

        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                max_tokens=512,
                temperature=0,
                messages=[
                    {"role": "system", "content": _VISUAL_SYSTEM},
                    {"role": "user", "content": content},
                ],
            )
            raw = (response.choices[0].message.content or "{}").strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except Exception as exc:
            logger.error("live_visual_moderation_error", error=str(exc))
            return {
                "violations": [],
                "overall_safe": True,
                "content_summary": "",
                "requires_immediate_action": False,
            }

    # ── Public API ─────────────────────────────────────────────────────────────

    async def analyze_chunk(
        self,
        stream_id: str,
        frames: list[str],
        transcript_hint: str = "",
    ) -> LiveChunkResult:
        """
        Analyze a batch of frames from a live stream.

        Args:
            stream_id:       UUID string of the live stream.
            frames:          List of base64-encoded JPEG frames (2-10 recommended).
            transcript_hint: Short speech-to-text from this chunk (optional).

        Returns:
            LiveChunkResult with violations, face analysis, OCR text, and safety verdict.
        """
        if not frames:
            return LiveChunkResult(stream_id=stream_id, overall_safe=True)

        logger.info("live_chunk_analysis_start", stream_id=stream_id, frames=len(frames))

        # Run all three analyses in parallel
        visual_task = asyncio.create_task(self._visual_moderation(frames))
        ocr_task = asyncio.create_task(run_ocr(frames, max_frames=4, _client=self._client))
        face_task = asyncio.create_task(analyze_faces(frames, _client=self._client))

        visual_data, ocr_result, face_result = await asyncio.gather(
            visual_task, ocr_task, face_task
        )

        # Parse visual violations
        raw_violations = visual_data.get("violations", [])
        violations: list[LiveViolation] = []
        for v in raw_violations:
            with suppress(Exception):
                violations.append(LiveViolation(**v))

        # If minor detected in a face analysis, add as a violation
        if face_result.has_minor and not face_result.error:
            violations.append(
                LiveViolation(
                    category="minor_detected",
                    severity="high",
                    confidence=0.85,
                    description=f"Minor (person under 18) detected. {face_result.summary}",
                    frame_index=0,
                )
            )

        # Include transcript-based check: if hate/threat keywords found
        if transcript_hint:
            _HATE_KEYWORDS = {"kill", "murder", "bomb", "terrorist", "n-word"}
            lower_t = transcript_hint.lower()
            if any(kw in lower_t for kw in _HATE_KEYWORDS):
                violations.append(
                    LiveViolation(
                        category="speech_violation",
                        severity="high",
                        confidence=0.75,
                        description="Potentially harmful speech detected in audio transcript.",
                        frame_index=0,
                    )
                )

        # Compute highest severity
        highest: str | None = None
        for v in violations:
            if highest is None or _SEVERITY_ORDER.get(v.severity, 0) > _SEVERITY_ORDER.get(
                highest, 0
            ):
                highest = v.severity

        overall_safe = len(violations) == 0
        requires_action = visual_data.get("requires_immediate_action", False) or (
            highest in ("high", "critical")
        )

        result = LiveChunkResult(
            stream_id=stream_id,
            violations=violations,
            face_analysis=face_result,
            ocr_text=ocr_result.combined_text,
            content_summary=visual_data.get("content_summary", ""),
            overall_safe=overall_safe,
            requires_immediate_action=requires_action,
            highest_severity=highest,
        )

        logger.info(
            "live_chunk_analysis_done",
            stream_id=stream_id,
            violations=len(violations),
            highest_severity=highest,
            overall_safe=overall_safe,
        )
        return result
