"""Tests for C-02 InsightChain — LLM mocked via _llm injection."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.chains.insight_chain import InsightOutput, run_insight_chain


def _mock_llm(payload: dict) -> MagicMock:
    response = MagicMock()
    response.content = json.dumps(payload)
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=response)
    return llm


@pytest.mark.asyncio
async def test_insight_happy_path():
    payload = {
        "key_insights": [
            "Cooking techniques demonstrated",
            "Professional kitchen setting",
        ],
        "content_themes": ["culinary arts", "food preparation"],
        "risk_signals": [],
        "audience_suitability": "general",
    }
    result = await run_insight_chain(
        transcript="Gordon Ramsay demonstrates knife skills.",
        topics=["cooking", "knives"],
        entities=["Gordon Ramsay"],
        scene_summary={"safe": 12, "other": 1},
        _llm=_mock_llm(payload),
    )
    assert isinstance(result, InsightOutput)
    assert "Cooking techniques demonstrated" in result.key_insights
    assert "culinary arts" in result.content_themes
    assert result.risk_signals == []
    assert result.audience_suitability == "general"


@pytest.mark.asyncio
async def test_insight_with_risk_signals():
    payload = {
        "key_insights": ["Violent confrontation depicted"],
        "content_themes": ["conflict", "aggression"],
        "risk_signals": ["physical violence shown", "aggressive language"],
        "audience_suitability": "adults",
    }
    result = await run_insight_chain(
        transcript="A fight broke out.",
        topics=["violence"],
        entities=[],
        scene_summary={"safe": 5, "violence": 4},
        _llm=_mock_llm(payload),
    )
    assert len(result.risk_signals) == 2
    assert result.audience_suitability == "adults"


@pytest.mark.asyncio
async def test_insight_no_input():
    payload = {
        "key_insights": [],
        "content_themes": [],
        "risk_signals": [],
        "audience_suitability": "general",
    }
    result = await run_insight_chain(_llm=_mock_llm(payload))
    assert result.key_insights == []
    assert result.audience_suitability == "general"


@pytest.mark.asyncio
async def test_insight_llm_failure_returns_fallback():
    llm = MagicMock()
    llm.ainvoke = AsyncMock(side_effect=Exception("rate limited"))

    result = await run_insight_chain(
        transcript="test",
        topics=["test"],
        _llm=llm,
    )
    assert result.key_insights == []
    assert result.content_themes == []
    assert any("failed" in s.lower() for s in result.risk_signals)
    assert result.audience_suitability == "general"


@pytest.mark.asyncio
async def test_insight_restricted_suitability():
    payload = {
        "key_insights": [],
        "content_themes": ["explicit content"],
        "risk_signals": ["explicit imagery"],
        "audience_suitability": "restricted",
    }
    result = await run_insight_chain(
        transcript="",
        scene_summary={"nudity": 5},
        _llm=_mock_llm(payload),
    )
    assert result.audience_suitability == "restricted"
