"""
Embedding generation and cosine-similarity retrieval.

Supports two providers (controlled by ``EMBEDDING_PROVIDER`` in ``.env``):

* ``"local"``  — sentence-transformers (default: ``all-MiniLM-L6-v2``)
* ``"api"``    — any OpenAI-compatible ``/embeddings`` endpoint

Public API
----------
get_content_embeddings(items)
    Embed a list of content items -> ``(N, dim)`` array.
get_user_embedding(profile)
    Embed a user profile -> ``(1, dim)`` array.
retrieve_top_k(user_emb, content_embs, items, k, exclude_ids)
    Return the *k* most relevant content items by cosine similarity.
"""

from __future__ import annotations

import numpy as np
import requests as http_requests
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity

from app.config import (
    EMBEDDING_API_BASE_URL,
    EMBEDDING_API_KEY,
    EMBEDDING_MODEL_API,
    EMBEDDING_MODEL_LOCAL,
    EMBEDDING_PROVIDER,
)
from app.schemas import ContentItem, UserProfile

# ---------------------------------------------------------------------------
# Lazy-loaded local model (avoids import cost when using the API provider)
# ---------------------------------------------------------------------------
_local_model = None


def _get_local_model():
    """Load the sentence-transformers model on first call."""
    global _local_model  # noqa: PLW0603
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(EMBEDDING_MODEL_LOCAL)
    return _local_model


# ---------------------------------------------------------------------------
# Provider-agnostic embedding function
# ---------------------------------------------------------------------------
def _embed_texts(texts: list[str]) -> NDArray[np.float32]:
    """Return an ``(N, dim)`` array of embeddings for *texts*."""
    if EMBEDDING_PROVIDER == "api":
        return _embed_via_api(texts)
    return _embed_locally(texts)


def _embed_locally(texts: list[str]) -> NDArray[np.float32]:
    """Encode *texts* using the local sentence-transformers model."""
    model = _get_local_model()
    return model.encode(texts, convert_to_numpy=True)


def _embed_via_api(texts: list[str]) -> NDArray[np.float32]:
    """Call an OpenAI-compatible ``/embeddings`` endpoint."""
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": EMBEDDING_MODEL_API, "input": texts}
    resp = http_requests.post(
        EMBEDDING_API_BASE_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = sorted(resp.json()["data"], key=lambda d: d["index"])
    return np.array([d["embedding"] for d in data], dtype=np.float32)


# ---------------------------------------------------------------------------
# Text representation helpers
# ---------------------------------------------------------------------------
def _content_text(item: ContentItem) -> str:
    """Build a single search-friendly string from a content item."""
    return f"{item.title}. {item.description} Tags: {', '.join(item.tags)}"


def _user_text(profile: UserProfile) -> str:
    """Build a single search-friendly string from a user profile."""
    return (
        f"Goal: {profile.goal}. "
        f"Interests: {', '.join(profile.interest_tags)}. "
        f"Learning style: {profile.learning_style}."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_content_embeddings(items: list[ContentItem]) -> NDArray[np.float32]:
    """Embed all content items -> ``(N, dim)``."""
    return _embed_texts([_content_text(item) for item in items])


def get_user_embedding(profile: UserProfile) -> NDArray[np.float32]:
    """Embed a user profile -> ``(1, dim)``."""
    return _embed_texts([_user_text(profile)])


def retrieve_top_k(
    user_emb: NDArray[np.float32],
    content_embs: NDArray[np.float32],
    items: list[ContentItem],
    k: int = 5,
    exclude_ids: list[int] | None = None,
) -> list[ContentItem]:
    """Return the *k* most similar items, excluding already-viewed IDs."""
    excluded = set(exclude_ids or [])
    similarities = cosine_similarity(user_emb, content_embs)[0]

    scored = [
        (idx, score)
        for idx, score in enumerate(similarities)
        if items[idx].id not in excluded
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    return [items[idx] for idx, _ in scored[:k]]
