"""
A-04 Metadata Extractor Agent

Extracts structured metadata from video frames and transcript:
entities, brands, keywords, OCR text, detected objects, locations.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.ai.base import BaseAgent
from app.ai.prompts.analysis_prompts import (
    METADATA_EXTRACT_SYSTEM,
    METADATA_EXTRACT_USER,
)
from app.ai.schemas import MetadataResult

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"


class MetadataExtractorAgent(BaseAgent):
    name = "metadata_extractor"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        frames: list[str] = state.get("frames") or []
        transcript: str = state.get("transcript") or ""
        video_id: str = state.get("video_id", "")

        logger.info(
            "metadata_extractor_start",
            video_id=video_id,
            frame_count=len(frames),
            has_transcript=bool(transcript),
        )

        try:
            result = await self._call_with_retry(self._extract, frames, transcript)
            logger.info("metadata_extractor_done", video_id=video_id)
            return {
                "metadata": result.model_dump(),
                "completed_agents": self._mark_completed(state),
            }
        except Exception as exc:
            logger.error("metadata_extractor_error", video_id=video_id, error=str(exc))
            return {
                "metadata": MetadataResult().model_dump(),
                "errors": self._append_error(state, str(exc)),
                "completed_agents": self._mark_completed(state),
            }

    async def _extract(self, frames: list[str], transcript: str) -> MetadataResult:
        # Build content: first frame as visual context + text prompt
        content: list[dict] = []

        if frames:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frames[0]}",
                        "detail": "low",
                    },
                }
            )

        content.append(
            {
                "type": "text",
                "text": METADATA_EXTRACT_USER.format(
                    transcript=transcript[:2000] if transcript else "(no transcript)",
                    frame_count=len(frames),
                ),
            }
        )

        response = await self.client.chat.completions.create(
            model=_MODEL,
            max_tokens=512,
            messages=[
                {"role": "system", "content": METADATA_EXTRACT_SYSTEM},
                {"role": "user", "content": content},
            ],
        )

        raw = self._extract_json(response.choices[0].message.content)
        data = json.loads(raw)

        return MetadataResult(
            entities=data.get("entities", []),
            brands=data.get("brands", []),
            keywords=data.get("keywords", []),
            ocr_text=data.get("ocr_text", []),
            objects_detected=data.get("objects_detected", []),
            locations=data.get("locations", []),
        )
