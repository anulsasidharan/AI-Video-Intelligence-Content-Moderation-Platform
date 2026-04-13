"""Tests for C-03 SummaryChain — LLM mocked via _llm injection."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.chains.summary_chain import SummaryOutput, run_summary_chain


def _mock_llm(payload: dict) -> MagicMock:
    """Build a mock ChatOpenAI that returns the given payload."""
    response = MagicMock()
    response.content = json.dumps(payload)
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=response)
    return llm


@pytest.mark.asyncio
async def test_summary_happy_path():
    payload = {
        "executive_summary": "A cooking tutorial about pasta recipes.",
        "key_moments": ["Introduction of ingredients", "Boiling the pasta"],
        "content_rating": "G",
    }
    result = await run_summary_chain(
        transcript="Today we are making delicious pasta.",
        content_summary="Cooking tutorial.",
        duration_seconds=120.0,
        topics=["cooking", "pasta"],
        _llm=_mock_llm(payload),
    )
    assert isinstance(result, SummaryOutput)
    assert result.executive_summary == "A cooking tutorial about pasta recipes."
    assert "Boiling the pasta" in result.key_moments
    assert result.content_rating == "G"


@pytest.mark.asyncio
async def test_summary_no_transcript():
    payload = {
        "executive_summary": "No transcript available; visual-only summary.",
        "key_moments": [],
        "content_rating": "PG",
    }
    result = await run_summary_chain(
        transcript="",
        content_summary="Visual content with no audio.",
        _llm=_mock_llm(payload),
    )
    assert result.executive_summary == "No transcript available; visual-only summary."
    assert result.content_rating == "PG"


@pytest.mark.asyncio
async def test_summary_adult_rating():
    payload = {
        "executive_summary": "Mature content for adults.",
        "key_moments": ["Graphic scene at 2:30"],
        "content_rating": "R",
    }
    result = await run_summary_chain(
        transcript="Adult content warning.",
        content_summary="Mature drama film.",
        _llm=_mock_llm(payload),
    )
    assert result.content_rating == "R"


@pytest.mark.asyncio
async def test_summary_llm_failure_returns_fallback():
    llm = MagicMock()
    llm.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))

    result = await run_summary_chain(
        transcript="Some transcript.",
        content_summary="Some content.",
        _llm=llm,
    )
    assert "failed" in result.executive_summary.lower() or "Summary" in result.executive_summary
    assert result.key_moments == []
    assert result.content_rating == "G"  # safe default on failure


@pytest.mark.asyncio
async def test_summary_defaults():
    """SummaryOutput model defaults are sensible."""
    out = SummaryOutput(executive_summary="Test summary.")
    assert out.key_moments == []
    assert out.content_rating == "G"
