# EduRecommender 

Personalised educational content recommendation engine using **Hybrid Search**
(embedding-based retrieval + LLM re-ranking).

This is a clean-code rewrite of the original EduRecommender project, applying
Python best practices: strict typing, enums, structured logging, modular
architecture, and comprehensive documentation.

---

## Features

- **Hybrid Search Architecture** — fast semantic retrieval (`sentence-transformers`)
  followed by intelligent LLM re-ranking (`Kimi-K2.5` via HuggingFace Router).
- **Strict Type Safety** — `Difficulty`, `LearningStyle`, `ContentFormat` enums
  replace raw strings; Pydantic models enforce validation constraints.
- **Provider-Agnostic Design** — swap embedding or LLM providers via `.env`
  without touching code.
- **Embedding Cache** — sub-15 ms latency on repeated queries.
- **Graceful Fallback** — rule-based re-ranking when no LLM API key is set.
- **FastAPI Backend** — RESTful endpoints with OpenAPI docs.

---

## Quick Start

### 1. Install

```bash
cd clean-code
pip install -r requirements.txt
```

### 2. Configure

Copy the example environment file and add your API key (optional):

```bash
cp .env.example .env
```

```env
# Enables LLM re-ranking (optional — rule-based fallback works without it)
HF_TOKEN=hf_...

# Embedding runs locally by default — no key needed
EMBEDDING_PROVIDER=local
```

### 3. Run the API

```bash
uvicorn api.main:app --reload --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive
API docs.

### 4. Test

```bash
python -m tests.test_api
```

---

## Project Structure

```
clean-code/
├── app/
│   ├── __init__.py          # Package metadata + __version__
│   ├── config.py            # Environment loader (single source of truth)
│   ├── schemas.py           # Enums + Pydantic models with validation
│   ├── data.py              # 10 content items + 3 user profiles
│   ├── embeddings.py        # Embedding generation + cosine retrieval
│   ├── llm_ranker.py        # LLM re-ranking with rule-based fallback
│   └── recommender.py       # Pipeline orchestrator with timing
├── api/
│   ├── __init__.py
│   └── main.py              # FastAPI endpoints
├── tests/
│   └── test_api.py          # Integration test
├── docs/
│   ├── architecture.md      # System architecture
│   └── Deep_Architecture.md # Detailed component diagrams
├── .devcontainer/
│   └── devcontainer.json    # Dev container config
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Path         | Description                           |
| ------ | ------------ | ------------------------------------- |
| GET    | `/health`    | Liveness probe                        |
| GET    | `/content`   | Full content catalogue                |
| GET    | `/users`     | Mock user profiles                    |
| POST   | `/recommend` | Top-3 personalised recommendations    |

### Example Request

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u1",
    "name": "Alice",
    "goal": "Learn to deploy ML models into production using Kubernetes",
    "learning_style": "visual",
    "preferred_difficulty": "Intermediate",
    "time_per_day": 60,
    "viewed_content_ids": [1],
    "interest_tags": ["ml", "deployment", "kubernetes"]
  }'
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the system overview and
[docs/Deep_Architecture.md](docs/Deep_Architecture.md) for sequence diagrams
and component interactions.

```
User Profile ──> Embed ──> Cosine Similarity ──> Top-5 ──> LLM Re-Rank ──> Top-3
                   │                                            │
              sentence-transformers                   Kimi-K2.5 / Rules
```

---

## Clean Code Improvements over Original

| Area               | Original                    | Clean Code Edition            |
| ------------------ | --------------------------- | ----------------------------- |
| Type safety        | Raw strings everywhere      | Enums (`Difficulty`, etc.)    |
| Validation         | None on Pydantic fields     | `gt=0`, `ge=1`, `le=1.0`     |
| Logging            | `print()` statements        | `logging.getLogger(__name__)` |
| Annotations        | Partial                     | Full `NDArray`, `list[...]`   |
| Documentation      | Minimal docstrings          | Module + function + attribute |
| Timing             | Repeated boilerplate        | Extracted `_timed()` helper   |
| Dependencies       | Unused `httpx`              | Trimmed to essentials         |
| Test structure     | Flat script                 | `tests/` package with `main()`|
| Future annotations | Missing                     | `from __future__ import annotations` |

---

## Configuration Reference

| Variable               | Default                          | Description                      |
| ---------------------- | -------------------------------- | -------------------------------- |
| `HF_TOKEN`             | —                                | HuggingFace token for LLM       |
| `OPENROUTER_API_KEY`   | —                                | Alternative LLM key              |
| `LLM_MODEL`            | `moonshotai/Kimi-K2.5:novita`    | Chat-completion model slug       |
| `LLM_BASE_URL`         | HuggingFace Router               | Chat-completion endpoint         |
| `EMBEDDING_PROVIDER`   | `local`                          | `local` or `api`                 |
| `EMBEDDING_MODEL_LOCAL`| `all-MiniLM-L6-v2`              | sentence-transformers model      |
| `EMBEDDING_MODEL_API`  | `text-embedding-ada-002`         | OpenAI-compatible model          |
| `EMBEDDING_API_KEY`    | —                                | API key for cloud embeddings     |

---

## License

MIT
