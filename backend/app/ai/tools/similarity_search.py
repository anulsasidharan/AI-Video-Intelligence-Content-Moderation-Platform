"""
T-05 Similarity Search Tool

Vector similarity search using Pinecone.  Used by SafetyChecker and
ReportGenerator to match content embeddings against known violations or
reference material stored in the vector index.

The Pinecone index is initialised lazily on first use (singleton per process).
A test-injection point (_index) is provided so unit tests never hit Pinecone.

Public API:
    # Query
    result = query_similar(
        query_embedding=[0.1, 0.2, ...],
        top_k=5,
        namespace="violations",
        filter={"category": "violence"},
    )
    result.matches   # list[SimilarityMatch] with id, score, metadata

    # Upsert
    count = upsert_vectors(
        vectors=[{"id": "v1", "values": [...], "metadata": {"video_id": "abc"}}],
        namespace="violations",
    )
"""

from __future__ import annotations

import structlog
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger(__name__)

_DEFAULT_TOP_K = 5
_DEFAULT_NAMESPACE = "violations"


# ── Output schemas ────────────────────────────────────────────────────────────


class SimilarityMatch(BaseModel):
    id: str
    score: float
    metadata: dict = Field(default_factory=dict)


class SimilaritySearchResult(BaseModel):
    matches: list[SimilarityMatch] = Field(default_factory=list)
    namespace: str = _DEFAULT_NAMESPACE
    error: str | None = None


# ── Errors ────────────────────────────────────────────────────────────────────


class SimilaritySearchError(RuntimeError):
    pass


# ── Pinecone index singleton ──────────────────────────────────────────────────

_pinecone_index = None


def _get_index():
    """Lazily initialise and return the Pinecone index (singleton per process)."""
    global _pinecone_index
    if _pinecone_index is None:
        try:
            from pinecone import Pinecone  # type: ignore[import-untyped]
        except ImportError as exc:
            raise SimilaritySearchError(
                "pinecone package is not installed. Add 'pinecone>=3.0.0' to project dependencies."
            ) from exc

        if not settings.PINECONE_API_KEY:
            raise SimilaritySearchError("PINECONE_API_KEY is not configured.")

        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _pinecone_index = pc.Index(settings.PINECONE_INDEX)
        logger.info("pinecone_index_initialised", index=settings.PINECONE_INDEX)

    return _pinecone_index


# ── Public API ────────────────────────────────────────────────────────────────


def query_similar(
    query_embedding: list[float],
    *,
    top_k: int = _DEFAULT_TOP_K,
    namespace: str = _DEFAULT_NAMESPACE,
    filter: dict | None = None,
    _index=None,  # injection point for tests
) -> SimilaritySearchResult:
    """
    Query Pinecone for the top-k most similar vectors.

    Args:
        query_embedding: Dense embedding vector to query against.
        top_k:           Number of results to return (default 5).
        namespace:       Pinecone namespace to query (default "violations").
        filter:          Optional metadata filter dict passed to Pinecone.
        _index:          Pinecone index override — use in tests to avoid live calls.

    Returns:
        SimilaritySearchResult with ranked matches.
        On failure, returns a result with error set and empty matches so the
        pipeline can continue without similarity data.
    """
    try:
        index = _index if _index is not None else _get_index()

        kwargs: dict = {
            "vector": query_embedding,
            "top_k": top_k,
            "namespace": namespace,
            "include_metadata": True,
        }
        if filter:
            kwargs["filter"] = filter

        logger.info("similarity_search_query", top_k=top_k, namespace=namespace)
        response = index.query(**kwargs)

        matches = [
            SimilarityMatch(
                id=m["id"],
                score=float(m.get("score", 0.0)),
                metadata=m.get("metadata") or {},
            )
            for m in (response.get("matches") or [])
        ]

        logger.info("similarity_search_done", match_count=len(matches))
        return SimilaritySearchResult(matches=matches, namespace=namespace)

    except SimilaritySearchError:
        raise
    except Exception as exc:
        logger.error("similarity_search_error", error=str(exc))
        return SimilaritySearchResult(error=str(exc), namespace=namespace)


def upsert_vectors(
    vectors: list[dict],
    *,
    namespace: str = _DEFAULT_NAMESPACE,
    _index=None,  # injection point for tests
) -> int:
    """
    Upsert vectors into Pinecone.

    Args:
        vectors:   List of dicts with keys:
                     - id (str)            required
                     - values (list[float]) required
                     - metadata (dict)     optional
        namespace: Pinecone namespace (default "violations").
        _index:    Pinecone index override — use in tests to avoid live calls.

    Returns:
        Number of vectors upserted.

    Raises:
        SimilaritySearchError: On Pinecone API or connectivity failure.
    """
    try:
        index = _index if _index is not None else _get_index()
        logger.info("similarity_search_upsert", count=len(vectors), namespace=namespace)
        index.upsert(vectors=vectors, namespace=namespace)
        return len(vectors)
    except SimilaritySearchError:
        raise
    except Exception as exc:
        logger.error("similarity_search_upsert_error", error=str(exc))
        raise SimilaritySearchError(f"Upsert failed: {exc}") from exc
