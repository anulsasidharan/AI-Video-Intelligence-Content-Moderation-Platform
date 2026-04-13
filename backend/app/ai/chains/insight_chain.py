"""
C-02 Insight Chain

LangChain LCEL chain that extracts structured content insights from a video's
transcript, topic list, detected entities, and scene classification summary.

Uses gpt-4o to identify key themes, risk signals, and audience suitability.

Public API:
    result = await run_insight_chain(
        transcript="...",
        topics=["cooking", "knife"],
        entities=["Gordon Ramsay"],
        scene_summary={"safe": 10, "violence": 1},
    )
    result.key_insights         # list[str]
    result.content_themes       # list[str]
    result.risk_signals         # list[str]
    result.audience_suitability # str
"""

from __future__ import annotations

import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"

# ── Output schema ─────────────────────────────────────────────────────────────


class InsightOutput(BaseModel):
    key_insights: list[str] = Field(
        default_factory=list,
        description="Up to 5 notable insights derived from the video content.",
    )
    content_themes: list[str] = Field(
        default_factory=list,
        description="Recurring themes or subjects identified in the video.",
    )
    risk_signals: list[str] = Field(
        default_factory=list,
        description="Content signals that may warrant closer moderation attention.",
    )
    audience_suitability: str = Field(
        default="general",
        description=(
            "Who this content is appropriate for: general | children | teens | adults | restricted"
        ),
    )


# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM = """\
You are an AI content insights analyst for a video intelligence platform.
Given structured information about a video (transcript, topics, entities, scene breakdown),
extract actionable insights for content moderators and platform operators.

Return a JSON object:
{
  "key_insights": ["<insight 1>", ...],
  "content_themes": ["<theme 1>", ...],
  "risk_signals": ["<signal 1>", ...],
  "audience_suitability": "general" | "children" | "teens" | "adults" | "restricted"
}

Keep each list to at most 5 items. Be factual and concise.
No markdown, no extra text.
"""

_USER_TEMPLATE = """\
Analyse the following video metadata and provide insights.

Transcript excerpt: {transcript}
Topics: {topics}
Entities: {entities}
Scene breakdown (category → frame count): {scene_summary}

Return only the JSON object.
"""


# ── Public API ────────────────────────────────────────────────────────────────


async def run_insight_chain(
    transcript: str = "",
    topics: list[str] | None = None,
    entities: list[str] | None = None,
    scene_summary: dict[str, int] | None = None,
    *,
    _llm: ChatOpenAI | None = None,
) -> InsightOutput:
    """
    Extract structured content insights from video metadata.

    Args:
        transcript:    Transcript text (will be truncated to first 2000 chars).
        topics:        Topic list from ContentAnalyzer.
        entities:      Named entities from MetadataExtractor.
        scene_summary: Scene category → frame count from SceneClassifier.
        _llm:          Override LLM for testing.

    Returns:
        InsightOutput with key_insights, content_themes, risk_signals, audience_suitability.
    """
    llm = _llm or ChatOpenAI(
        model=_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
    )

    user_content = _USER_TEMPLATE.format(
        transcript=transcript[:2000] if transcript else "(no transcript)",
        topics=", ".join(topics) if topics else "none",
        entities=", ".join(entities) if entities else "none",
        scene_summary=json.dumps(scene_summary) if scene_summary else "{}",
    )

    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=user_content),
    ]

    logger.info(
        "insight_chain_start",
        topics=topics,
        entity_count=len(entities) if entities else 0,
    )

    try:
        response = await llm.ainvoke(messages)
        raw: str = response.content or "{}"
        data = json.loads(raw)
        result = InsightOutput(
            key_insights=data.get("key_insights", []),
            content_themes=data.get("content_themes", []),
            risk_signals=data.get("risk_signals", []),
            audience_suitability=data.get("audience_suitability", "general"),
        )
        logger.info(
            "insight_chain_done",
            suitability=result.audience_suitability,
            risk_count=len(result.risk_signals),
        )
        return result
    except Exception as exc:
        logger.error("insight_chain_error", error=str(exc))
        return InsightOutput(
            key_insights=[],
            content_themes=[],
            risk_signals=[f"Insight extraction failed: {exc}"],
            audience_suitability="general",
        )
