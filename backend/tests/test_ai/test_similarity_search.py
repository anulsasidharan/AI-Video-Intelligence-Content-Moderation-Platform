"""Tests for T-05 SimilaritySearch — Pinecone index mocked."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ai.tools.similarity_search import (
    SimilaritySearchError,
    SimilaritySearchResult,
    query_similar,
    upsert_vectors,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _fake_query_response(matches: list[dict]) -> dict:
    return {"matches": matches}


def _mock_index(query_response: dict | None = None, query_side_effect=None) -> MagicMock:
    idx = MagicMock()
    idx.query = MagicMock(
        return_value=query_response or {"matches": []},
        side_effect=query_side_effect,
    )
    idx.upsert = MagicMock(return_value=None)
    return idx


_EMBEDDING = [0.1, 0.2, 0.3]


# ── query_similar ─────────────────────────────────────────────────────────────


def test_query_similar_happy_path():
    matches = [
        {
            "id": "v1",
            "score": 0.95,
            "metadata": {"video_id": "abc", "category": "violence"},
        },
        {"id": "v2", "score": 0.87, "metadata": {"video_id": "def"}},
    ]
    index = _mock_index(query_response=_fake_query_response(matches))

    result = query_similar(_EMBEDDING, top_k=2, _index=index)

    assert isinstance(result, SimilaritySearchResult)
    assert len(result.matches) == 2
    assert result.matches[0].id == "v1"
    assert result.matches[0].score == 0.95
    assert result.matches[0].metadata["category"] == "violence"
    assert result.error is None


def test_query_similar_empty_results():
    index = _mock_index(query_response={"matches": []})
    result = query_similar(_EMBEDDING, _index=index)

    assert result.matches == []
    assert result.error is None


def test_query_similar_with_filter():
    index = _mock_index(query_response={"matches": []})
    query_similar(
        _EMBEDDING,
        filter={"category": "nudity"},
        _index=index,
    )
    call_kwargs = index.query.call_args.kwargs
    assert call_kwargs.get("filter") == {"category": "nudity"}


def test_query_similar_no_filter_excludes_filter_key():
    index = _mock_index(query_response={"matches": []})
    query_similar(_EMBEDDING, _index=index)
    call_kwargs = index.query.call_args.kwargs
    assert "filter" not in call_kwargs


def test_query_similar_pinecone_error_returns_error_result():
    index = _mock_index(query_side_effect=Exception("Pinecone 503"))
    result = query_similar(_EMBEDDING, _index=index)

    assert result.matches == []
    assert "Pinecone 503" in (result.error or "")


def test_query_similar_top_k_passed():
    index = _mock_index(query_response={"matches": []})
    query_similar(_EMBEDDING, top_k=10, _index=index)
    call_kwargs = index.query.call_args.kwargs
    assert call_kwargs["top_k"] == 10


def test_query_similar_namespace_passed():
    index = _mock_index(query_response={"matches": []})
    query_similar(_EMBEDDING, namespace="reference", _index=index)
    call_kwargs = index.query.call_args.kwargs
    assert call_kwargs["namespace"] == "reference"


# ── upsert_vectors ────────────────────────────────────────────────────────────


def test_upsert_vectors_happy_path():
    index = _mock_index()
    vectors = [
        {"id": "v1", "values": _EMBEDDING, "metadata": {"video_id": "abc"}},
        {"id": "v2", "values": _EMBEDDING},
    ]
    count = upsert_vectors(vectors, _index=index)

    assert count == 2
    index.upsert.assert_called_once()
    call_kwargs = index.upsert.call_args.kwargs
    assert call_kwargs["namespace"] == "violations"  # default


def test_upsert_vectors_custom_namespace():
    index = _mock_index()
    upsert_vectors([{"id": "v1", "values": _EMBEDDING}], namespace="reference", _index=index)
    call_kwargs = index.upsert.call_args.kwargs
    assert call_kwargs["namespace"] == "reference"


def test_upsert_vectors_pinecone_error_raises():
    index = MagicMock()
    index.upsert = MagicMock(side_effect=Exception("connection refused"))

    with pytest.raises(SimilaritySearchError, match="Upsert failed"):
        upsert_vectors([{"id": "v1", "values": _EMBEDDING}], _index=index)


def test_upsert_vectors_returns_correct_count():
    index = _mock_index()
    vectors = [{"id": f"v{i}", "values": _EMBEDDING} for i in range(7)]
    count = upsert_vectors(vectors, _index=index)
    assert count == 7


# ── SimilaritySearchError propagation ────────────────────────────────────────


def test_similarity_search_error_propagates_from_query():
    """SimilaritySearchError raised inside should not be swallowed."""

    def _raise(*args, **kwargs):
        raise SimilaritySearchError("test propagation")

    index = MagicMock()
    index.query = MagicMock(side_effect=_raise)

    # SimilaritySearchError is re-raised, not caught as a generic Exception
    with pytest.raises(SimilaritySearchError, match="test propagation"):
        query_similar(_EMBEDDING, _index=index)
