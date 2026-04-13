"""
A-05 Scene Classifier Agent

Classifies each sampled frame independently using GPT-4o vision.
Produces per-frame SceneClassification results stored in state["scene_classifications"].
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.ai.base import BaseAgent
from app.ai.prompts.moderation_prompts import SCENE_CLASSIFY_SYSTEM
from app.ai.schemas import SceneCategory, SceneClassification

logger = structlog.get_logger(__name__)

_VISION_MODEL = "gpt-4o"
_MAX_CONCURRENT = 5  # frames to classify in parallel (rate-limit friendly)


class SceneClassifierAgent(BaseAgent):
    name = "scene_classifier"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        frames: list[str] = state.get("frames") or []
        timestamps: list[float] = state.get("frame_timestamps") or []

        if not frames:
            logger.warning("scene_classifier_no_frames", video_id=state.get("video_id"))
            return {
                "scene_classifications": [],
                "completed_agents": self._mark_completed(state),
            }

        logger.info(
            "scene_classifier_start",
            video_id=state.get("video_id"),
            frame_count=len(frames),
        )

        classifications: list[SceneClassification] = []
        new_errors: list[str] = []

        # Process frames in batches to avoid flooding the API
        for batch_start in range(0, len(frames), _MAX_CONCURRENT):
            batch_frames = frames[batch_start : batch_start + _MAX_CONCURRENT]
            batch_ts = timestamps[batch_start : batch_start + _MAX_CONCURRENT]

            results = await self._classify_batch(
                batch_frames, batch_ts, batch_start, state.get("video_id", "")
            )
            for r, err in results:
                if r:
                    classifications.append(r)
                elif err:
                    new_errors.append(f"[scene_classifier] {err}")

        logger.info(
            "scene_classifier_done",
            video_id=state.get("video_id"),
            classified=len(classifications),
        )

        return {
            "scene_classifications": [c.model_dump() for c in classifications],
            "errors": new_errors,
            "completed_agents": self._mark_completed(state),
        }

    async def _classify_batch(
        self,
        frames: list[str],
        timestamps: list[float],
        start_index: int,
        video_id: str,
    ) -> list[tuple[SceneClassification | None, str | None]]:
        import asyncio

        tasks = [
            self._classify_frame(frame, ts, start_index + i, video_id)
            for i, (frame, ts) in enumerate(zip(frames, timestamps, strict=True))
        ]
        return await asyncio.gather(*tasks)

    async def _classify_frame(
        self,
        frame_b64: str,
        timestamp: float,
        frame_index: int,
        video_id: str,
    ) -> tuple[SceneClassification | None, str | None]:
        try:
            response = await self._call_with_retry(
                self.client.chat.completions.create,
                model=_VISION_MODEL,
                max_tokens=256,
                messages=[
                    {"role": "system", "content": SCENE_CLASSIFY_SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame_b64}",
                                    "detail": "low",
                                },
                            },
                            {
                                "type": "text",
                                "text": "Classify this frame. Return only JSON.",
                            },
                        ],
                    },
                ],
            )
            raw = self._extract_json(response.choices[0].message.content)
            data = json.loads(raw)

            return (
                SceneClassification(
                    frame_index=frame_index,
                    timestamp=timestamp,
                    category=SceneCategory(data.get("category", "safe")),
                    confidence=float(data.get("confidence", 0.5)),
                    sub_categories=data.get("sub_categories", []),
                ),
                None,
            )
        except Exception as exc:
            logger.warning(
                "scene_classify_frame_error",
                video_id=video_id,
                frame_index=frame_index,
                error=str(exc),
            )
            return None, str(exc)
