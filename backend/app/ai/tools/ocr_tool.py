"""
T-03 OCR Tool

Extracts visible text from video frames using GPT-4o vision.
Batches up to max_frames images in a single API call to minimise latency.

Public API:
    result = await run_ocr(
        frames=["<base64-jpeg>", ...],
        max_frames=10,
    )
    result.texts          # list[str]  per-frame text (empty string if none)
    result.combined_text  # str        all text joined with newlines
    result.error          # str | None set on failure; pipeline continues
"""

from __future__ import annotations

import json

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"
_MAX_FRAMES_DEFAULT = 10

_SYSTEM = """\
You are an OCR specialist. Given one or more video frames, extract all visible text
exactly as it appears (signs, captions, overlays, watermarks, on-screen text, etc.).

Return a JSON object:
{
  "texts": ["<text from frame 1>", "<text from frame 2>", ...],
  "combined_text": "<all extracted text joined with newlines>"
}
The "texts" array must have the same length as the number of input frames.
Use an empty string for frames with no visible text.
No markdown, no extra text.
"""


# ── Output schema ─────────────────────────────────────────────────────────────


class OCRResult(BaseModel):
    texts: list[str] = Field(
        default_factory=list,
        description="Per-frame extracted text (same order as input frames)",
    )
    combined_text: str = Field(default="", description="All text joined with newlines")
    error: str | None = None


# ── Public API ────────────────────────────────────────────────────────────────


async def run_ocr(
    frames: list[str],
    *,
    max_frames: int = _MAX_FRAMES_DEFAULT,
    _client: AsyncOpenAI | None = None,
) -> OCRResult:
    """
    Extract visible text from base64-encoded JPEG frames via GPT-4o vision.

    Args:
        frames:     List of base64-encoded JPEG frames.
        max_frames: Maximum number of frames to include in one API call.
        _client:    AsyncOpenAI client override — use in tests to avoid live calls.

    Returns:
        OCRResult with per-frame texts and combined text.
        On API failure, returns an OCRResult with error set and empty texts
        so the pipeline can continue without OCR data.
    """
    if not frames:
        return OCRResult()

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
                f"Extract all visible text from these {len(frames_to_process)} frame(s). "
                "Return only the JSON object."
            ),
        }
    )

    logger.info("ocr_tool_start", frame_count=len(frames_to_process))

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
        # Strip markdown code fences that GPT-4o sometimes adds
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            inner = [line for line in lines[1:] if line.strip() != "```"]
            raw = "\n".join(inner).strip()
        raw = raw or "{}"
        data = json.loads(raw)
        result = OCRResult(
            texts=data.get("texts", []),
            combined_text=data.get("combined_text", ""),
        )
        logger.info("ocr_tool_done", text_len=len(result.combined_text))
        return result
    except Exception as exc:
        logger.error("ocr_tool_error", error=str(exc))
        return OCRResult(error=str(exc))
