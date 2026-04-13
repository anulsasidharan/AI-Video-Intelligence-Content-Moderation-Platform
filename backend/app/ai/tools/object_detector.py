"""
T-04 Object Detector Tool

Detects objects, people, animals, vehicles, and scene elements in video frames
using GPT-4o vision.  Returns a flat deduplicated list of detected objects and
a per-frame breakdown.

Public API:
    result = await detect_objects(
        frames=["<base64-jpeg>", ...],
        max_frames=8,
    )
    result.objects           # list[str]       deduplicated across all frames
    result.frame_detections  # list[list[str]] per-frame object lists
    result.error             # str | None      set on failure; pipeline continues
"""

from __future__ import annotations

import json

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"
_MAX_FRAMES_DEFAULT = 8

_SYSTEM = """\
You are a vision AI specialising in object detection. Given one or more video frames,
identify all notable objects, people, animals, vehicles, and scene elements visible
in each frame.

Return a JSON object:
{
  "objects": ["<deduplicated list of detected objects across all frames>"],
  "frame_detections": [["<obj1>", "<obj2>"], ["<obj3>"], ...]
}
"objects" is a flat, deduplicated list across all input frames.
"frame_detections" is a per-frame list in the same order as the input frames.
No markdown, no extra text.
"""


# ── Output schema ─────────────────────────────────────────────────────────────


class ObjectDetectionResult(BaseModel):
    objects: list[str] = Field(
        default_factory=list,
        description="Deduplicated detected objects across all frames",
    )
    frame_detections: list[list[str]] = Field(
        default_factory=list,
        description="Per-frame detected object lists (same order as input frames)",
    )
    error: str | None = None


# ── Public API ────────────────────────────────────────────────────────────────


async def detect_objects(
    frames: list[str],
    *,
    max_frames: int = _MAX_FRAMES_DEFAULT,
    _client: AsyncOpenAI | None = None,
) -> ObjectDetectionResult:
    """
    Detect objects in base64-encoded JPEG frames via GPT-4o vision.

    Args:
        frames:     List of base64-encoded JPEG frames.
        max_frames: Maximum number of frames to include in one API call.
        _client:    AsyncOpenAI client override — use in tests to avoid live calls.

    Returns:
        ObjectDetectionResult with deduplicated objects and per-frame breakdown.
        On API failure, returns an ObjectDetectionResult with error set and empty
        lists so the pipeline can continue without object detection data.
    """
    if not frames:
        return ObjectDetectionResult()

    client = _client or AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    frames_to_process = frames[:max_frames]

    content: list[dict] = []
    for frame_b64 in frames_to_process:
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
                f"Detect all objects in these {len(frames_to_process)} frame(s). "
                "Return only the JSON object."
            ),
        }
    )

    logger.info("object_detector_start", frame_count=len(frames_to_process))

    try:
        response = await client.chat.completions.create(
            model=_MODEL,
            max_tokens=512,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": content},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        result = ObjectDetectionResult(
            objects=data.get("objects", []),
            frame_detections=data.get("frame_detections", []),
        )
        logger.info("object_detector_done", object_count=len(result.objects))
        return result
    except Exception as exc:
        logger.error("object_detector_error", error=str(exc))
        return ObjectDetectionResult(error=str(exc))
