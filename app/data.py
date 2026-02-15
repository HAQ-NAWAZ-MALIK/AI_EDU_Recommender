"""
Mock educational content catalogue and user profiles.

In production this module would be replaced by a database adapter.
The helpers below expose a read-only view over the in-memory data.
"""

from __future__ import annotations

from app.schemas import (
    ContentFormat,
    ContentItem,
    Difficulty,
    LearningStyle,
    UserProfile,
)

# ---------------------------------------------------------------------------
# Content catalogue (10 items)
# ---------------------------------------------------------------------------
CONTENT_ITEMS: list[ContentItem] = [
    ContentItem(
        id=1,
        title="Introduction to Kubernetes for ML Engineers",
        description=(
            "Hands-on deployment walkthrough using Docker and Kubernetes. "
            "Covers pod creation, service exposure, and scaling ML "
            "inference endpoints."
        ),
        difficulty=Difficulty.INTERMEDIATE,
        duration_minutes=45,
        tags=["kubernetes", "ml", "deployment", "docker"],
        format=ContentFormat.VIDEO,
    ),
    ContentItem(
        id=2,
        title="Python for Data Science \u2013 From Zero to Pandas",
        description=(
            "Beginner-friendly course covering Python basics, NumPy arrays, "
            "and Pandas DataFrames for exploratory data analysis."
        ),
        difficulty=Difficulty.BEGINNER,
        duration_minutes=60,
        tags=["python", "data-science", "pandas", "numpy"],
        format=ContentFormat.LECTURE,
    ),
    ContentItem(
        id=3,
        title="Deep Learning Fundamentals with PyTorch",
        description=(
            "Build neural networks from scratch using PyTorch. Covers "
            "tensors, autograd, CNNs, and training loops with real datasets."
        ),
        difficulty=Difficulty.INTERMEDIATE,
        duration_minutes=90,
        tags=["deep-learning", "pytorch", "neural-networks", "ml"],
        format=ContentFormat.VIDEO,
    ),
    ContentItem(
        id=4,
        title="MLOps Pipeline Design Patterns",
        description=(
            "Slide deck covering CI/CD for ML models, feature stores, "
            "model registries, and monitoring in production."
        ),
        difficulty=Difficulty.ADVANCED,
        duration_minutes=30,
        tags=["mlops", "ci-cd", "deployment", "monitoring"],
        format=ContentFormat.SLIDES,
    ),
    ContentItem(
        id=5,
        title="Natural Language Processing with Transformers",
        description=(
            "Understand attention mechanisms, BERT, and GPT architectures. "
            "Includes fine-tuning a text classifier on custom data."
        ),
        difficulty=Difficulty.ADVANCED,
        duration_minutes=75,
        tags=["nlp", "transformers", "bert", "ml"],
        format=ContentFormat.LECTURE,
    ),
    ContentItem(
        id=6,
        title="Data Engineering with Apache Spark",
        description=(
            "Process large-scale datasets using PySpark. Covers RDDs, "
            "DataFrames, Spark SQL, and integration with cloud storage."
        ),
        difficulty=Difficulty.INTERMEDIATE,
        duration_minutes=50,
        tags=["data-engineering", "spark", "python", "big-data"],
        format=ContentFormat.VIDEO,
    ),
    ContentItem(
        id=7,
        title="Git & GitHub for Collaborative Projects",
        description=(
            "Learn branching strategies, pull requests, merge conflicts, "
            "and GitHub Actions for automating workflows."
        ),
        difficulty=Difficulty.BEGINNER,
        duration_minutes=25,
        tags=["git", "github", "collaboration", "ci-cd"],
        format=ContentFormat.SLIDES,
    ),
    ContentItem(
        id=8,
        title="Building REST APIs with FastAPI",
        description=(
            "Create production-ready REST APIs with FastAPI. Covers path "
            "parameters, Pydantic validation, async handlers, and "
            "OpenAPI docs."
        ),
        difficulty=Difficulty.INTERMEDIATE,
        duration_minutes=40,
        tags=["fastapi", "python", "api", "backend"],
        format=ContentFormat.VIDEO,
    ),
    ContentItem(
        id=9,
        title="AI Model Deployment on AWS SageMaker",
        description=(
            "Step-by-step guide to packaging, deploying, and A/B testing "
            "ML models on AWS SageMaker with auto-scaling."
        ),
        difficulty=Difficulty.ADVANCED,
        duration_minutes=55,
        tags=["aws", "sagemaker", "deployment", "ml"],
        format=ContentFormat.LECTURE,
    ),
    ContentItem(
        id=10,
        title="Prompt Engineering for Large Language Models",
        description=(
            "Master prompt design techniques: few-shot, chain-of-thought, "
            "and system prompts for ChatGPT, Claude, and open-source LLMs."
        ),
        difficulty=Difficulty.BEGINNER,
        duration_minutes=35,
        tags=["llm", "prompt-engineering", "ai", "nlp"],
        format=ContentFormat.SLIDES,
    ),
]


# ---------------------------------------------------------------------------
# User profiles (3 personas)
# ---------------------------------------------------------------------------
USER_PROFILES: list[UserProfile] = [
    UserProfile(
        user_id="u1",
        name="Alice",
        goal=(
            "Learn to deploy ML models into production using "
            "Kubernetes and cloud platforms"
        ),
        learning_style=LearningStyle.VISUAL,
        preferred_difficulty=Difficulty.INTERMEDIATE,
        time_per_day=60,
        viewed_content_ids=[1],
        interest_tags=["ml", "deployment", "kubernetes", "docker"],
    ),
    UserProfile(
        user_id="u2",
        name="Bob",
        goal=(
            "Transition from software engineering to data science "
            "and machine learning"
        ),
        learning_style=LearningStyle.HANDS_ON,
        preferred_difficulty=Difficulty.BEGINNER,
        time_per_day=45,
        viewed_content_ids=[7],
        interest_tags=["python", "data-science", "ml", "numpy"],
    ),
    UserProfile(
        user_id="u3",
        name="Carol",
        goal=(
            "Master advanced NLP and LLM techniques for building "
            "AI-powered applications"
        ),
        learning_style=LearningStyle.READING,
        preferred_difficulty=Difficulty.ADVANCED,
        time_per_day=90,
        viewed_content_ids=[5],
        interest_tags=["nlp", "transformers", "llm", "prompt-engineering"],
    ),
]


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------
def get_all_content() -> list[ContentItem]:
    """Return the full content catalogue."""
    return CONTENT_ITEMS


def get_all_users() -> list[UserProfile]:
    """Return all mock user profiles."""
    return USER_PROFILES


def get_user_by_id(user_id: str) -> UserProfile | None:
    """Look up a user profile by ID, or ``None`` if not found."""
    return next((u for u in USER_PROFILES if u.user_id == user_id), None)
