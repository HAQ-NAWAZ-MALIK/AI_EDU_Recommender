"""
LLM-based re-ranking of candidate content items.

Uses an OpenAI-compatible chat-completion endpoint to re-rank retrieval
results.  Falls back to a deterministic rule-based ranker when no API key
is configured (or when the LLM call fails).

Swap the model by changing ``LLM_MODEL`` in ``.env``.

Public API
----------
rerank(profile, candidates) -> RerankResult
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

import requests as http_requests

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.schemas import ContentItem, LearningStyle, Recommendation, UserProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are an expert educational content recommender. Re-rank the candidate
items for the learner below and return the top 3 as a strict JSON array.

CONSTRAINTS:
1. Prefer items matching the learner's preferred difficulty.
2. Each item's duration_minutes must fit the learner's time_per_day budget.
3. Favour formats that suit the learning style \
(visual -> video, reading -> slides/lecture, hands-on -> video/lecture).
4. Never recommend already-viewed content.
5. Provide a concise, personalised explanation (1-2 sentences) per pick.

Return ONLY a JSON array with exactly 3 objects, each having:
  rank (int 1-3), id (int), title (str), format (str), difficulty (str),
  duration_minutes (int), tags (list[str]), explanation (str).
No text outside the JSON array.\
"""

# ---------------------------------------------------------------------------
# Style -> preferred formats mapping
# ---------------------------------------------------------------------------
_STYLE_FORMAT_MAP: dict[str, set[str]] = {
    LearningStyle.VISUAL: {"video"},
    LearningStyle.READING: {"slides", "lecture"},
    LearningStyle.HANDS_ON: {"video", "lecture"},
}

_DIFFICULTY_ORDER: dict[str, int] = {
    "Beginner": 0,
    "Intermediate": 1,
    "Advanced": 2,
}


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------
@dataclass
class RerankResult:
    """Outcome of the re-ranking step."""

    recommendations: list[Recommendation] = field(default_factory=list)
    reasoning_raw: str | None = None
    method: str = "llm"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _build_user_prompt(
    profile: UserProfile,
    candidates: list[ContentItem],
) -> str:
    """Assemble the user-turn content for the chat-completion request."""
    items_json = json.dumps(
        [item.model_dump() for item in candidates], indent=2
    )
    return (
        f"### Learner Profile\n"
        f"- Name: {profile.name}\n"
        f"- Goal: {profile.goal}\n"
        f"- Learning style: {profile.learning_style}\n"
        f"- Preferred difficulty: {profile.preferred_difficulty}\n"
        f"- Time per day: {profile.time_per_day} minutes\n"
        f"- Interests: {', '.join(profile.interest_tags)}\n"
        f"- Already viewed IDs: {profile.viewed_content_ids}\n\n"
        f"### Candidate Items\n```json\n{items_json}\n```\n\n"
        f"Re-rank and return the top 3 as a JSON array."
    )


def _call_llm(system: str, user: str) -> tuple[str, str | None]:
    """Send a chat-completion request; return ``(text, reasoning)``."""
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    resp = http_requests.post(
        LLM_BASE_URL, json=payload, headers=headers, timeout=60
    )
    resp.raise_for_status()

    message = resp.json()["choices"][0]["message"]
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning") or "").strip()

    response_text = content if content else reasoning
    if not response_text:
        raise ValueError("LLM returned an empty response.")

    # Strip markdown code fences
    response_text = re.sub(r"```(?:json)?\s*", "", response_text)
    response_text = response_text.replace("```", "").strip()

    return response_text, reasoning or None


def _extract_json_array(raw: str) -> list[dict]:
    """Find and parse the largest valid JSON array in *raw*."""
    best: list[dict] = []
    for i, ch in enumerate(raw):
        if ch != "[":
            continue
        depth = 0
        for j in range(i, len(raw)):
            if raw[j] == "[":
                depth += 1
            elif raw[j] == "]":
                depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(raw[i : j + 1])
                    if (
                        isinstance(parsed, list)
                        and len(parsed) > len(best)
                        and all(isinstance(x, dict) for x in parsed)
                    ):
                        best = parsed
                except (json.JSONDecodeError, ValueError):
                    pass
                break
    return best


def _parse_llm_response(
    raw: str,
    candidates: list[ContentItem],
) -> list[Recommendation]:
    """Map the LLM JSON output to ``Recommendation`` objects."""
    items = _extract_json_array(raw)
    if not items:
        raise ValueError("No valid JSON array found in LLM response.")

    cand_map = {c.id: c for c in candidates}
    recommendations: list[Recommendation] = []

    for idx, item in enumerate(items[:3], start=1):
        cid = item.get("id")
        fallback = cand_map.get(cid)
        recommendations.append(
            Recommendation(
                rank=idx,
                id=cid,
                title=item.get("title", fallback.title if fallback else ""),
                format=item.get("format", fallback.format if fallback else ""),
                difficulty=item.get(
                    "difficulty", fallback.difficulty if fallback else ""
                ),
                duration_minutes=item.get(
                    "duration_minutes",
                    fallback.duration_minutes if fallback else 0,
                ),
                tags=item.get("tags", fallback.tags if fallback else []),
                explanation=item.get(
                    "explanation", "Recommended based on your profile."
                ),
            )
        )
    return recommendations


# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------
def _rule_based_rerank(
    profile: UserProfile,
    candidates: list[ContentItem],
) -> RerankResult:
    """Score candidates heuristically when the LLM is unavailable."""
    user_tags = set(profile.interest_tags)
    preferred_formats = _STYLE_FORMAT_MAP.get(profile.learning_style, set())
    pref_diff = _DIFFICULTY_ORDER.get(profile.preferred_difficulty, 1)

    scored: list[tuple[float, ContentItem]] = []
    for item in candidates:
        if item.id in profile.viewed_content_ids:
            continue
        if item.duration_minutes > profile.time_per_day:
            continue

        tag_overlap = len(user_tags & set(item.tags)) / max(len(user_tags), 1)
        format_bonus = 0.2 if item.format in preferred_formats else 0.0
        diff_penalty = (
            abs(_DIFFICULTY_ORDER.get(item.difficulty, 1) - pref_diff) * 0.15
        )

        scored.append((tag_overlap + format_bonus - diff_penalty, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    recommendations: list[Recommendation] = []
    for rank, (score, item) in enumerate(scored[:3], start=1):
        common = set(item.tags) & user_tags
        recommendations.append(
            Recommendation(
                rank=rank,
                id=item.id,
                title=item.title,
                format=item.format,
                difficulty=item.difficulty,
                duration_minutes=item.duration_minutes,
                tags=item.tags,
                explanation=(
                    f"Matched on tags ({', '.join(common)}), "
                    f"format fits your {profile.learning_style} style, "
                    f"and difficulty is {item.difficulty}."
                ),
                match_score=round(score, 3),
            )
        )

    return RerankResult(
        recommendations=recommendations,
        reasoning_raw=(
            "Rule-based scoring: tag overlap + format match "
            "+ difficulty proximity."
        ),
        method="rule-based",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def rerank(
    profile: UserProfile,
    candidates: list[ContentItem],
) -> RerankResult:
    """Re-rank *candidates* for *profile*.

    Uses the LLM when an API key is configured; falls back to rule-based
    scoring otherwise (or on any LLM error).
    """
    if not LLM_API_KEY:
        logger.info("No API key configured — using rule-based fallback.")
        return _rule_based_rerank(profile, candidates)

    try:
        user_prompt = _build_user_prompt(profile, candidates)
        response_text, reasoning_raw = _call_llm(_SYSTEM_PROMPT, user_prompt)
        recs = _parse_llm_response(response_text, candidates)
        return RerankResult(
            recommendations=recs,
            reasoning_raw=reasoning_raw,
            method="llm",
        )
    except Exception as exc:
        logger.warning("LLM call failed (%s), falling back to rules.", exc)
        return _rule_based_rerank(profile, candidates)
