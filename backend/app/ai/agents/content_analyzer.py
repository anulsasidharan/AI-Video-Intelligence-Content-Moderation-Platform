"""
A-02 Content Analyzer Agent

Uses GPT-4o vision on sampled frames + transcript to produce a high-level
content analysis: summary, topics, sentiment, language.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.ai.base import BaseAgent
from app.ai.prompts.analysis_prompts import (
    CONTENT_ANALYSIS_SYSTEM,
    CONTENT_ANALYSIS_USER,
)
from app.ai.schemas import ContentAnalysisResult

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"
_MAX_FRAMES_FOR_ANALYSIS = 8  # send at most 8 frames to keep token usage reasonable


class ContentAnalyzerAgent(BaseAgent):
    name = "content_analyzer"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        frames: list[str] = (state.get("frames") or [])[:_MAX_FRAMES_FOR_ANALYSIS]
        transcript: str = state.get("transcript") or ""
        video_id: str = state.get("video_id", "")

        logger.info(
            "content_analyzer_start",
            video_id=video_id,
            frame_count=len(frames),
            transcript_len=len(transcript),
        )

        try:
            result = await self._call_with_retry(self._analyze, frames, transcript)
            logger.info("content_analyzer_done", video_id=video_id, summary=result.summary[:80])
            return {
                "content_analysis": result.model_dump(),
                "completed_agents": self._mark_completed(state),
            }
        except Exception as exc:
            logger.error("content_analyzer_error", video_id=video_id, error=str(exc))
            return {
                "content_analysis": ContentAnalysisResult(
                    summary="Analysis failed.", raw_response=str(exc)
                ).model_dump(),
                "errors": self._append_error(state, str(exc)),
                "completed_agents": self._mark_completed(state),
            }

    async def _analyze(self, frames: list[str], transcript: str) -> ContentAnalysisResult:
        content: list[dict] = []

        # Attach frames as image_url entries
        for frame_b64 in frames:
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
                "text": CONTENT_ANALYSIS_USER.format(
                    frame_count=len(frames),
                    transcript=(transcript[:3000] if transcript else "(no transcript available)"),
                ),
            }
        )

        response = await self.client.chat.completions.create(
            model=_MODEL,
            max_tokens=512,
            messages=[
                {"role": "system", "content": CONTENT_ANALYSIS_SYSTEM},
                {"role": "user", "content": content},
            ],
        )

        raw = self._extract_json(response.choices[0].message.content)
        data = json.loads(raw)

        return ContentAnalysisResult(
            summary=data.get("summary", ""),
            topics=data.get("topics", []),
            sentiment=data.get("sentiment", "neutral"),
            language=data.get("language", "en"),
            duration_seconds=data.get("duration_seconds"),
            raw_response=raw,
        )
