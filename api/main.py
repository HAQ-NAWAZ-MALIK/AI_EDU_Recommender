"""
FastAPI backend for EduRecommender.

Endpoints
---------
POST /recommend
    Top-3 personalised recommendations for a user profile.
GET  /content
    Full educational content catalogue.
GET  /users
    All mock user profiles.
GET  /health
    Liveness check.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data import get_all_content, get_all_users
from app.recommender import get_recommendations
from app.schemas import ContentItem, RecommendationResponse, UserProfile

app = FastAPI(
    title="EduRecommender API",
    description=(
        "Personalised educational content recommendations "
        "using embeddings + LLM re-ranking."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/content", response_model=list[ContentItem])
def list_content() -> list[ContentItem]:
    """Return the full content catalogue."""
    return get_all_content()


@app.get("/users")
def list_users():
    """Return all mock user profiles."""
    return get_all_users()


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(profile: UserProfile) -> RecommendationResponse:
    """Accept a user profile and return top-3 recommendations."""
    return get_recommendations(profile)
