"""
Recommendation pipeline orchestrator.

Ties together embedding retrieval and LLM re-ranking with caching and
step-by-step timing instrumentation.

Public API
----------
get_recommendations(profile) -> RecommendationResponse
"""

from __future__ import annotations

import time

import numpy as np
from numpy.typing import NDArray

from app.data import get_all_content
from app.embeddings import get_content_embeddings, get_user_embedding, retrieve_top_k
from app.llm_ranker import rerank
from app.schemas import (
    PipelineStatus,
    PipelineStep,
    RecommendationResponse,
    UserProfile,
)

# ---------------------------------------------------------------------------
# Embedding cache (content embeddings rarely change)
# ---------------------------------------------------------------------------
_cached_content_embs: NDArray[np.float32] | None = None
_cache_hash: int | None = None


def _get_cached_content_embeddings() -> NDArray[np.float32]:
    """Return (and cache) content embeddings."""
    global _cached_content_embs, _cache_hash  # noqa: PLW0603
    items = get_all_content()
    current_hash = hash(tuple(item.id for item in items))
    if _cached_content_embs is None or _cache_hash != current_hash:
        _cached_content_embs = get_content_embeddings(items)
        _cache_hash = current_hash
    return _cached_content_embs


# ---------------------------------------------------------------------------
# Timing helper
# ---------------------------------------------------------------------------
def _timed(label: str, fn, *args, **kwargs):
    """Run *fn* and return ``(result, PipelineStep)``."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return result, elapsed_ms


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def get_recommendations(profile: UserProfile) -> RecommendationResponse:
    """Execute the full recommendation pipeline.

    Steps
    -----
    1. Embed content catalogue (cached after first run).
    2. Embed user profile.
    3. Retrieve top-5 candidates via cosine similarity.
    4. Re-rank with LLM (or rule-based fallback) -> top-3.
    """
    log: list[PipelineStep] = []
    t_start = time.perf_counter()
    items = get_all_content()

    # Step 1 — content embeddings
    content_embs, dt = _timed("content_emb", _get_cached_content_embeddings)
    log.append(
        PipelineStep(
            step="Embed content catalogue",
            status=PipelineStatus.DONE,
            detail=(
                f"Encoded {len(items)} items ({dt}ms, "
                f"{'cached' if dt < 50 else 'first run'})"
            ),
            duration_ms=dt,
        )
    )

    # Step 2 — user embedding
    user_emb, dt = _timed("user_emb", get_user_embedding, profile)
    log.append(
        PipelineStep(
            step="Embed user profile",
            status=PipelineStatus.DONE,
            detail=(
                f"Encoded goal + {len(profile.interest_tags)} "
                f"interest tags ({dt}ms)"
            ),
            duration_ms=dt,
        )
    )

    # Step 3 — retrieval
    candidates, dt = _timed(
        "retrieval",
        retrieve_top_k,
        user_emb,
        content_embs,
        items,
        5,
        profile.viewed_content_ids,
    )
    eligible = len(items) - len(profile.viewed_content_ids)
    log.append(
        PipelineStep(
            step="Cosine similarity retrieval",
            status=PipelineStatus.DONE,
            detail=f"Retrieved top-5 from {eligible} candidates ({dt}ms)",
            duration_ms=dt,
        )
    )

    # Step 4 — re-rank
    result, dt = _timed("rerank", rerank, profile, candidates)
    step_name = (
        "LLM re-ranking" if result.method == "llm" else "Rule-based ranking"
    )
    log.append(
        PipelineStep(
            step=step_name,
            status=PipelineStatus.DONE,
            detail=f"Ranked via {result.method} -> top 3 ({dt}ms)",
            duration_ms=dt,
        )
    )

    total_ms = int((time.perf_counter() - t_start) * 1000)

    return RecommendationResponse(
        user_id=profile.user_id,
        recommendations=result.recommendations,
        pipeline_log=log,
        llm_reasoning=result.reasoning_raw,
        total_duration_ms=total_ms,
    )
