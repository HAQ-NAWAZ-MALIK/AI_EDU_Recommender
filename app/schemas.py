"""
Pydantic models for the recommendation system.

Defines the data contracts shared between the API layer, the
recommendation pipeline, and the frontend.

Classes
-------
Difficulty
    Enum of content difficulty tiers.
LearningStyle
    Enum of supported learner styles.
ContentFormat
    Enum of content delivery formats.
ContentItem
    A single educational resource.
UserProfile
    A learner's preferences used to personalise results.
Recommendation
    One ranked suggestion returned to the user.
PipelineStep
    Timing / status record for a single pipeline stage.
RecommendationResponse
    Top-level response envelope.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class Difficulty(str, Enum):
    """Content difficulty tier."""

    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class LearningStyle(str, Enum):
    """Learner's preferred modality."""

    VISUAL = "visual"
    READING = "reading"
    HANDS_ON = "hands-on"


class ContentFormat(str, Enum):
    """Delivery format of a content item."""

    VIDEO = "video"
    SLIDES = "slides"
    LECTURE = "lecture"


class PipelineStatus(str, Enum):
    """Outcome of a pipeline step."""

    DONE = "done"
    SKIPPED = "skipped"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------
class ContentItem(BaseModel):
    """A single educational content item."""

    id: int
    title: str
    description: str
    difficulty: Difficulty
    duration_minutes: int = Field(..., gt=0)
    tags: list[str]
    format: ContentFormat


class UserProfile(BaseModel):
    """A learner's profile used to personalise recommendations."""

    user_id: str
    name: str
    goal: str
    learning_style: LearningStyle
    preferred_difficulty: Difficulty
    time_per_day: int = Field(..., gt=0, description="Available minutes per day")
    viewed_content_ids: list[int] = Field(default_factory=list)
    interest_tags: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """A single recommendation returned to the user."""

    rank: int = Field(..., ge=1)
    id: int
    title: str
    format: str
    difficulty: str
    duration_minutes: int
    tags: list[str]
    explanation: str = Field(..., description="Why this was recommended")
    match_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score 0-1",
    )


class PipelineStep(BaseModel):
    """One step in the recommendation pipeline log."""

    step: str
    status: PipelineStatus
    detail: str
    duration_ms: int = 0


class RecommendationResponse(BaseModel):
    """Top-level response envelope."""

    user_id: str
    recommendations: list[Recommendation]
    pipeline_log: list[PipelineStep] = Field(default_factory=list)
    llm_reasoning: Optional[str] = Field(
        None, description="Raw LLM reasoning text"
    )
    total_duration_ms: int = 0
