"""
T-05 Face Analyzer Tool

Detects faces in video frames using GPT-4o vision and provides:
  - Face count
  - Age estimation per face (rough range, not biometric verification)
  - Minor detection flag (for age-gating on gaming, dating, adult platforms)
  - Liveness indicator (live person vs photo/screen being held up)
  - Restricted content flag (any minor present = restricted)

Used by:
  - Live stream moderation (per-chunk real-time analysis)
  - Recorded video pipeline (batch, added to the analysis graph)

IMPORTANT: Age estimation via vision models is approximate and MUST NOT be
used as the sole basis for age verification in legally regulated contexts.
It is a moderation signal to flag for human review.

Public API:
    result = await analyze_faces(frames=["<base64-jpeg>", ...])
    result.face_count          # int
    result.has_minor           # bool — any face estimated <18
    result.faces               # list[FaceInfo]
    result.liveness_score      # float 0-1 (1 = clearly live person)
    result.restricted_content  # bool — True if minor detected
    result.error               # str | None
"""

from __future__ import annotations

import json

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"
_MAX_FRAMES = 6  # cap frames to control token cost

_SYSTEM_PROMPT = """\
You are a content safety specialist focused on face analysis for video moderation.

Analyze the provided video frame(s) and for each visible face identify:
1. Estimated age range (e.g. "5-10", "13-17", "18-25", "25-35", "35-50", "50+")
2. Whether the person appears to be a minor (under 18 years old)
3. Liveness: does this appear to be a live person (vs a photograph or screen being held up)?

Be conservative: if a person COULD be a minor, flag them as a minor.

Return ONLY a valid JSON object — no markdown, no extra text:
{
  "face_count": <int>,
  "faces": [
    {
      "estimated_age_range": "<range>",
      "is_minor": <bool>,
      "liveness_confidence": <float 0.0-1.0>,
      "notes": "<optional brief note>"
    }
  ],
  "has_minor": <bool>,
  "overall_liveness_score": <float 0.0-1.0>,
  "restricted_content": <bool>,
  "summary": "<one sentence summary>"
}

If no faces are detected, return face_count=0, faces=[], has_minor=false,
restricted_content=false, overall_liveness_score=1.0.
"""


# ── Output schemas ─────────────────────────────────────────────────────────────


class FaceInfo(BaseModel):
    estimated_age_range: str = ""
    is_minor: bool = False
    liveness_confidence: float = 1.0
    notes: str = ""


class FaceAnalysisResult(BaseModel):
    face_count: int = 0
    faces: list[FaceInfo] = Field(default_factory=list)
    has_minor: bool = False
    overall_liveness_score: float = 1.0
    restricted_content: bool = False
    summary: str = ""
    error: str | None = None


# ── Public API ─────────────────────────────────────────────────────────────────


async def analyze_faces(
    frames: list[str],
    *,
    _client: AsyncOpenAI | None = None,
) -> FaceAnalysisResult:
    """
    Analyze faces in base64-encoded JPEG frames.

    Args:
        frames:   List of base64-encoded JPEG frames (capped at _MAX_FRAMES).
        _client:  AsyncOpenAI client override for testing.

    Returns:
        FaceAnalysisResult. On error, returns a result with error set and
        conservative defaults (restricted_content=False so errors do not
        falsely gate content; the caller should log and continue).
    """
    if not frames:
        return FaceAnalysisResult()

    client = _client or AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    frames_to_analyze = frames[:_MAX_FRAMES]

    content: list[dict] = []
    for frame_b64 in frames_to_analyze:
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
                f"Analyze faces in these {len(frames_to_analyze)} frame(s). "
                "Return the JSON object as specified."
            ),
        }
    )

    logger.info("face_analyzer_start", frame_count=len(frames_to_analyze))

    try:
        response = await client.chat.completions.create(
            model=_MODEL,
            max_tokens=512,
            temperature=0,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        )
        raw = (response.choices[0].message.content or "{}").strip()
        # Strip markdown fences if the model wraps in ```json
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        faces = [FaceInfo(**f) for f in data.get("faces", [])]
        result = FaceAnalysisResult(
            face_count=data.get("face_count", 0),
            faces=faces,
            has_minor=data.get("has_minor", False),
            overall_liveness_score=float(data.get("overall_liveness_score", 1.0)),
            restricted_content=data.get("restricted_content", False),
            summary=data.get("summary", ""),
        )
        logger.info(
            "face_analyzer_done",
            face_count=result.face_count,
            has_minor=result.has_minor,
            liveness=result.overall_liveness_score,
        )
        return result

    except Exception as exc:
        logger.error("face_analyzer_error", error=str(exc))
        return FaceAnalysisResult(error=str(exc))
