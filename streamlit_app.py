"""
Streamlit frontend for the Personalised Educational Content Recommendation System.

Features
--------
- Dark-only glassmorphism UI with Inter font family.
- **User view** (default) — clean, minimal recommendation output.
- **Developer view** — granular pipeline logs, LLM reasoning, timing.
- **Auto-mode** — selecting a preset profile auto-triggers recommendations.
- Toast-style progress messages with animated transitions.

Run
---
.. code-block:: bash

   streamlit run streamlit_app.py
"""

from __future__ import annotations

import html as html_mod
import time

import streamlit as st

from app.data import get_all_content
from app.recommender import get_recommendations
from app.schemas import UserProfile

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EduRecommender",
    page_icon="\U0001f393",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
_SESSION_DEFAULTS: dict[str, object] = {
    "auto_mode": True,
    "last_preset": None,
    "api_result": None,
    "should_auto_run": False,
}
for _key, _default in _SESSION_DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
FORMAT_ICONS: dict[str, str] = {
    "video": "\U0001f3ac",
    "slides": "\U0001f4ca",
    "lecture": "\U0001f3a4",
}
DIFF_COLORS: dict[str, str] = {
    "Beginner": "\U0001f7e2",
    "Intermediate": "\U0001f7e1",
    "Advanced": "\U0001f534",
}


def _safe(text: str) -> str:
    """HTML-escape user/LLM text to prevent rendering artefacts."""
    return html_mod.escape(str(text))


# ---------------------------------------------------------------------------
# CSS injection (dark glassmorphism theme)
# ---------------------------------------------------------------------------
_CSS = """\
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Root palette ─────────────────────────── */
:root {
    --bg-page: #0b0b18;
    --bg-glass: rgba(22, 22, 45, 0.55);
    --bg-glass-strong: rgba(28, 28, 55, 0.75);
    --glass-border: rgba(255,255,255,0.06);
    --glass-blur: 18px;
    --text-primary: #eaeaf4;
    --text-secondary: #a0a0c4;
    --text-muted: #666690;
    --accent-1: #667eea;
    --accent-2: #764ba2;
    --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --accent-glow: rgba(102,126,234,0.25);
    --pill-bg: rgba(102,126,234,0.12);
    --pill-text: #8b9cf7;
    --success: #34d399;
    --warning: #fbbf24;
    --error: #f87171;
    --info: #60a5fa;
    --reason-border: #8b5cf6;
    --reason-bg: rgba(139,92,246,0.08);
}

/* ── Global ───────────────────────────────── */
html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
.stApp { background: var(--bg-page); }

/* ── Sidebar ──────────────────────────────── */
section[data-testid="stSidebar"] {
    background: rgba(14,14,28,0.92) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--glass-border);
}
section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stTextArea label {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* ── Header ───────────────────────────────── */
.hero { text-align:center; padding:1.2rem 0 0.2rem; }
.hero h1 {
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.6rem; font-weight: 800; letter-spacing: -0.5px;
}
.hero p { color: var(--text-secondary); font-size: 0.95rem; margin-top:2px; }

/* ── Guide chip ───────────────────────────── */
.guide {
    display:inline-flex; align-items:center; gap:8px;
    background: var(--bg-glass); border:1px solid var(--glass-border);
    backdrop-filter: blur(var(--glass-blur));
    border-radius:14px; padding:10px 20px; margin:0.3rem auto 0.8rem;
    font-size:0.85rem; color:var(--text-secondary); max-width:720px;
}

/* ── Glassmorphism card ───────────────────── */
.g-card {
    background: var(--bg-glass);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(var(--glass-blur));
    border-radius: 20px;
    padding: 1.5rem 1.4rem;
    margin-bottom: 0.8rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(.4,0,.2,1);
}
.g-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: var(--accent-gradient); opacity:0;
    transition: opacity 0.3s ease;
}
.g-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 16px 40px var(--accent-glow);
    border-color: rgba(102,126,234,0.3);
}
.g-card:hover::before { opacity:1; }

.g-card .rank {
    display:inline-flex; align-items:center; justify-content:center;
    background: var(--accent-gradient); color:#fff;
    font-weight:800; font-size:0.85rem;
    width:32px; height:32px; border-radius:50%;
    box-shadow: 0 3px 12px var(--accent-glow);
}
.g-card .rank-label {
    color:var(--text-muted); font-size:0.72rem; font-weight:700;
    letter-spacing:0.5px; margin-left:8px;
}
.g-card .card-title {
    color:var(--text-primary); font-size:1.05rem; font-weight:700;
    margin:0.4rem 0 0.5rem; line-height:1.35;
}
.pill {
    display:inline-block;
    background:var(--pill-bg); color:var(--pill-text);
    font-size:0.73rem; font-weight:600;
    padding:3px 10px; border-radius:12px;
    margin:3px 4px 3px 0;
}
.tag {
    display:inline-block;
    background:rgba(102,126,234,0.07); color:rgba(139,156,247,0.7);
    font-size:0.68rem; font-weight:500;
    padding:2px 8px; border-radius:9px;
    margin:2px 3px 2px 0;
}
.why-box {
    background: var(--reason-bg);
    border-left: 3px solid var(--reason-border);
    border-radius: 0 12px 12px 0;
    padding: 0.65rem 1rem;
    margin-top: 0.7rem;
    font-size: 0.86rem;
    color: var(--text-primary);
    line-height: 1.55;
}
.why-box b { color: var(--reason-border); }

/* ── Toast ────────────────────────────────── */
.toast {
    display:flex; align-items:center; gap:10px;
    background: var(--bg-glass-strong);
    border:1px solid var(--glass-border);
    backdrop-filter: blur(12px);
    border-radius:12px; padding:9px 16px;
    margin-bottom:5px; font-size:0.84rem;
    color:var(--text-primary);
    animation: fadeSlide 0.35s ease;
}
.toast.ok   { border-left:3px solid var(--success); }
.toast.err  { border-left:3px solid var(--error); }
.toast.info { border-left:3px solid var(--info); }
.toast .ti  { font-size:1.05rem; flex-shrink:0; }
.toast .tt  { color:var(--text-muted); font-size:0.72rem; margin-left:auto; white-space:nowrap; }
@keyframes fadeSlide {
    from { opacity:0; transform:translateX(-10px); }
    to   { opacity:1; transform:translateX(0); }
}

/* ── Stats strip ──────────────────────────── */
.stats { display:flex; gap:14px; justify-content:center; flex-wrap:wrap; padding:0.5rem 0; }
.stat {
    display:inline-flex; align-items:center; gap:5px;
    background:var(--pill-bg); color:var(--pill-text);
    font-size:0.76rem; font-weight:600;
    padding:5px 14px; border-radius:20px;
}

/* ── Dev-only log box ─────────────────────── */
.logbox {
    background: rgba(12,12,24,0.7);
    border:1px solid var(--glass-border);
    backdrop-filter: blur(10px);
    border-radius:16px; padding:1rem 1.2rem; margin-top:0.4rem;
}
.logbox h4 { color:var(--text-primary); margin:0 0 0.6rem; font-size:0.88rem; }
.log-row {
    display:flex; align-items:center; gap:10px;
    padding:5px 0; border-bottom:1px solid rgba(255,255,255,0.04);
    font-size:0.8rem; color:var(--text-secondary);
}
.log-row:last-child { border-bottom:none; }
.log-row .lr-t { margin-left:auto; color:var(--text-muted); font-size:0.72rem; font-weight:600; }

/* ── Reasoning panel (dev only) ───────────── */
.reason {
    background: var(--reason-bg);
    border:1px solid var(--reason-border);
    backdrop-filter: blur(10px);
    border-radius:16px; padding:1rem 1.2rem; margin-top:0.4rem;
    max-height:300px; overflow-y:auto;
}
.reason h4 { color:var(--reason-border); margin:0 0 0.5rem; font-size:0.88rem; }
.reason pre {
    color:var(--text-secondary); font-size:0.78rem;
    white-space:pre-wrap; word-break:break-word;
    margin:0; line-height:1.5; font-family:'Inter',sans-serif;
}

/* ── Content browser item ─────────────────── */
.c-item {
    background: var(--bg-glass);
    border:1px solid var(--glass-border);
    backdrop-filter: blur(var(--glass-blur));
    border-radius:14px; padding:1rem 1.2rem; margin-bottom:0.5rem;
    transition: border-color 0.2s;
}
.c-item:hover { border-color: rgba(102,126,234,0.3); }
.c-item h4 { color:var(--text-primary); margin:0 0 0.3rem; font-size:0.9rem; }
.c-item p  { color:var(--text-secondary); font-size:0.8rem; margin:0; line-height:1.4; }

/* ── Streamlit overrides ──────────────────── */
.stMarkdown, .stText { color:var(--text-primary); }
h1,h2,h3,h4,h5,h6 { color:var(--text-primary) !important; }
.stExpander { border-color:var(--glass-border) !important; }
.stExpander > details {
    background: var(--bg-glass-strong) !important;
    border-radius:14px !important;
    backdrop-filter: blur(10px);
}
.stExpander > details > summary { color:var(--text-primary) !important; }

/* ── View toggle pill ─────────────────────── */
.view-toggle {
    display:flex; gap:0; justify-content:center; margin:0.5rem 0 0.8rem;
}
.vt-btn {
    padding:6px 18px; font-size:0.78rem; font-weight:600;
    border:1px solid var(--glass-border); cursor:pointer;
    color:var(--text-muted); background:var(--bg-glass);
    transition: all 0.2s;
}
.vt-btn:first-child { border-radius:10px 0 0 10px; }
.vt-btn:last-child  { border-radius:0 10px 10px 0; }
.vt-btn.active {
    background: var(--accent-gradient);
    color:#fff; border-color: var(--accent-1);
}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Preset learner profiles
# ---------------------------------------------------------------------------
PRESETS: dict[str, dict | None] = {
    "\u2014 Select a profile \u2014": None,
    "\U0001f469\u200d\U0001f4bb Alice \u2013 ML Deployment (Intermediate, visual)": {
        "user_id": "u1",
        "name": "Alice",
        "goal": "Learn to deploy ML models into production using Kubernetes and cloud platforms",
        "learning_style": "visual",
        "preferred_difficulty": "Intermediate",
        "time_per_day": 60,
        "viewed_content_ids": [1],
        "interest_tags": ["ml", "deployment", "kubernetes", "docker"],
    },
    "\U0001f468\u200d\U0001f52c Bob \u2013 Data Science Beginner (hands-on)": {
        "user_id": "u2",
        "name": "Bob",
        "goal": "Transition from software engineering to data science and machine learning",
        "learning_style": "hands-on",
        "preferred_difficulty": "Beginner",
        "time_per_day": 45,
        "viewed_content_ids": [7],
        "interest_tags": ["python", "data-science", "ml", "numpy"],
    },
    "\U0001f469\u200d\U0001f3eb Carol \u2013 Advanced NLP (reading)": {
        "user_id": "u3",
        "name": "Carol",
        "goal": "Master advanced NLP and LLM techniques for building AI-powered applications",
        "learning_style": "reading",
        "preferred_difficulty": "Advanced",
        "time_per_day": 90,
        "viewed_content_ids": [5],
        "interest_tags": ["nlp", "transformers", "llm", "prompt-engineering"],
    },
}

ALL_TAGS: list[str] = sorted([
    "ai", "api", "aws", "backend", "bert", "big-data", "ci-cd",
    "collaboration", "data-engineering", "data-science", "deep-learning",
    "deployment", "docker", "fastapi", "git", "github", "kubernetes",
    "llm", "ml", "mlops", "monitoring", "neural-networks", "nlp",
    "numpy", "pandas", "prompt-engineering", "python", "pytorch",
    "sagemaker", "spark", "transformers",
])


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="hero">'
    "    <h1>\U0001f393 EduRecommender</h1>"
    "    <p>Personalised educational content \u00b7 Embeddings + LLM Re-Ranking</p>"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div style="text-align:center">'
    '    <div class="guide">'
    "        <span>\U0001f4d6</span>"
    "        <span>Select a learner profile and get personalised course "
    "recommendations powered by AI.</span>"
    "    </div>"
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar — learner profile form
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### \U0001f464 Learner Profile")

    preset_key = st.selectbox("Load a preset profile", list(PRESETS.keys()))
    preset = PRESETS[preset_key]

    st.session_state.auto_mode = st.toggle(
        "\u26a1 Auto-mode",
        value=st.session_state.auto_mode,
        help="Automatically get recommendations when a profile is selected",
    )

    st.markdown("---")

    name = st.text_input("Name", value=preset["name"] if preset else "")
    goal = st.text_area(
        "\U0001f3af Learning goal",
        value=preset["goal"] if preset else "",
        height=80,
        placeholder="e.g. Learn ML deployment\u2026",
    )
    learning_style = st.selectbox(
        "\U0001f4d0 Learning style",
        ["visual", "reading", "hands-on"],
        index=(
            ["visual", "reading", "hands-on"].index(preset["learning_style"])
            if preset
            else 0
        ),
        help="visual \u2192 videos \u00b7 reading \u2192 slides/lectures \u00b7 hands-on \u2192 interactive",
    )
    difficulty = st.selectbox(
        "\U0001f4ca Preferred difficulty",
        ["Beginner", "Intermediate", "Advanced"],
        index=(
            ["Beginner", "Intermediate", "Advanced"].index(
                preset["preferred_difficulty"],
            )
            if preset
            else 1
        ),
    )
    time_per_day = st.slider(
        "\u23f0 Time per day (min)",
        15,
        120,
        value=preset["time_per_day"] if preset else 60,
        step=5,
    )
    interest_tags = st.multiselect(
        "\U0001f3f7\ufe0f Interest tags",
        ALL_TAGS,
        default=preset["interest_tags"] if preset else [],
    )
    viewed_ids = st.multiselect(
        "\U0001f441\ufe0f Already viewed IDs",
        list(range(1, 11)),
        default=preset["viewed_content_ids"] if preset else [],
        help="Content you've already completed",
    )

    st.markdown("---")
    manual_btn = st.button(
        "\U0001f680 Get Recommendations",
        use_container_width=True,
        type="primary",
    )


# ---------------------------------------------------------------------------
# Detect auto-mode trigger
# ---------------------------------------------------------------------------
auto_triggered = (
    st.session_state.auto_mode
    and preset is not None
    and preset_key != st.session_state.last_preset
)
if auto_triggered:
    st.session_state.last_preset = preset_key

should_run = manual_btn or auto_triggered


# ---------------------------------------------------------------------------
# Card renderer
# ---------------------------------------------------------------------------
def _render_card(rec: dict, *, show_score: bool = False) -> str:
    """Build a single recommendation card as safe HTML."""
    fmt_icon = FORMAT_ICONS.get(rec.get("format", ""), "\U0001f4c4")
    diff_icon = DIFF_COLORS.get(rec.get("difficulty", ""), "\u26aa")

    pills = (
        f'<span class="pill">{fmt_icon} {_safe(rec.get("format", ""))}</span>'
        f'<span class="pill">{diff_icon} {_safe(rec.get("difficulty", ""))}</span>'
        f'<span class="pill">\u23f1 {rec.get("duration_minutes", 0)} min</span>'
    )
    if show_score and rec.get("match_score") is not None:
        pct = int(rec["match_score"] * 100)
        pills += f'<span class="pill">\U0001f3af {pct}%</span>'

    tags_html = "".join(
        f'<span class="tag">{_safe(t)}</span>' for t in rec.get("tags", [])
    )
    explanation = _safe(rec.get("explanation", ""))

    return (
        '<div class="g-card">'
        '  <div style="display:flex;align-items:center">'
        f'    <span class="rank">{rec.get("rank", 0)}</span>'
        f'    <span class="rank-label">RANK #{rec.get("rank", 0)}</span>'
        "  </div>"
        f'  <div class="card-title">{_safe(rec.get("title", ""))}</div>'
        f"  <div>{pills}</div>"
        f'  <div style="margin-top:6px">{tags_html}</div>'
        f'  <div class="why-box"><b>\U0001f4a1 Why this?</b><br/>{explanation}</div>'
        "</div>"
    )


# ---------------------------------------------------------------------------
# Main flow — run pipeline & display results
# ---------------------------------------------------------------------------
if should_run:
    if not goal.strip():
        st.warning("\u26a0\ufe0f Please enter a learning goal.")
        st.stop()
    if not interest_tags:
        st.warning("\u26a0\ufe0f Please select at least one interest tag.")
        st.stop()

    payload = {
        "user_id": preset["user_id"] if preset else "custom",
        "name": name or "Learner",
        "goal": goal,
        "learning_style": learning_style,
        "preferred_difficulty": difficulty,
        "time_per_day": time_per_day,
        "viewed_content_ids": viewed_ids,
        "interest_tags": interest_tags,
    }

    # ── Toast progress ────────────────────────────────────────────────
    toast_box = st.empty()
    toasts: list[str] = []

    def _toast(icon: str, msg: str, cls: str = "info") -> None:
        ts = time.strftime("%H:%M:%S")
        toasts.append(
            f'<div class="toast {cls}">'
            f'<span class="ti">{icon}</span><span>{msg}</span>'
            f'<span class="tt">{ts}</span></div>',
        )
        toast_box.markdown("".join(toasts), unsafe_allow_html=True)

    _toast("\U0001f50d", "Analysing your profile\u2026")
    time.sleep(0.3)

    try:
        _toast("\U0001f916", "Finding the best content for you\u2026")
        profile = UserProfile(**payload)
        result = get_recommendations(profile)
        data = result.model_dump()
        st.session_state.api_result = data
    except Exception as exc:
        _toast("\u274c", f"Error: {_safe(str(exc))}", "err")
        st.stop()

    # Pipeline step toasts
    _FRIENDLY_NAMES: dict[str, str] = {
        "Embed content catalogue": "Analysing content library\u2026",
        "Embed user profile": "Understanding your preferences\u2026",
        "Cosine similarity retrieval": "Recommending best matches\u2026",
        "LLM re-ranking": "Reasoning & re-ranking\u2026",
        "Rule-based ranking": "Ranking by relevance\u2026",
    }
    for step in data.get("pipeline_log", []):
        label = _FRIENDLY_NAMES.get(step["step"], step["step"])
        _toast("\u2705", label, "ok")
        time.sleep(0.15)

    recs = data.get("recommendations", [])
    _toast(
        "\U0001f389",
        f"Found <b>{len(recs)} personalised recommendations</b> for you!",
        "ok",
    )
    time.sleep(0.3)

    # ── Recommendation cards ──────────────────────────────────────────
    st.markdown("---")

    if recs:
        cols = st.columns(len(recs))
        for col, rec in zip(cols, recs):
            with col:
                st.markdown(
                    _render_card(rec, show_score=False),
                    unsafe_allow_html=True,
                )

    # ── Content browser ───────────────────────────────────────────────
    st.markdown("---")
    with st.expander("\U0001f4da Browse all available content", expanded=True):
        try:
            items = [item.model_dump() for item in get_all_content()]
            for item in items:
                fmt_icon = FORMAT_ICONS.get(item.get("format", ""), "\U0001f4c4")
                diff_icon = DIFF_COLORS.get(item.get("difficulty", ""), "\u26aa")
                tags_html = "".join(
                    f'<span class="tag">{_safe(t)}</span>'
                    for t in item.get("tags", [])
                )
                st.markdown(
                    f'<div class="c-item">'
                    f'<h4>{item["id"]}. {_safe(item["title"])}</h4>'
                    f'<div style="margin-bottom:5px">'
                    f'<span class="pill">{fmt_icon} {_safe(item["format"])}</span>'
                    f'<span class="pill">{diff_icon} {_safe(item["difficulty"])}</span>'
                    f'<span class="pill">\u23f1 {item["duration_minutes"]} min</span>'
                    f"</div>"
                    f'<p>{_safe(item["description"])}</p>'
                    f'<div style="margin-top:5px">{tags_html}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            st.caption("Start the FastAPI server to browse content.")
