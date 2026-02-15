# Architecture Deep Dive — EduRecommender (Clean Code Edition)

Detailed internal structure, data flow, and component interactions.

---

## 1. System Context

The system is a Python application (FastAPI backend) orchestrating a local
embedding model and an external LLM for personalised content recommendations.

```mermaid
graph TD
    User((Learner))

    subgraph "Local Execution"
        App["EduRecommender<br/>(FastAPI)"]
        Emb["Embedding Model<br/>(all-MiniLM-L6-v2)"]
    end

    Cloud["Model Provider<br/>(HuggingFace / OpenRouter)"]

    User -->|1. Submit Profile| App
    App -->|2. Vectorise Data| Emb
    Emb -.->|3. Return Vectors| App
    App -->|4. Send Candidates| Cloud
    Cloud -.->|5. Return Ranked JSON| App
    App -->|6. JSON Response| User
```

---

## 2. Execution Flow (Sequence Diagram)

How a recommendation request flows through the pipeline.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant REC as Recommender
    participant DATA as Data Layer
    participant EMB as Embeddings
    participant LLM as LLM Provider

    C->>API: POST /recommend (profile JSON)
    API->>REC: get_recommendations(profile)

    rect rgb(20, 20, 30)
        note right of REC: Step 1 — Embed Content (cached)
        REC->>EMB: get_content_embeddings(items)
        EMB-->>REC: ndarray [10 x 384]

        note right of REC: Step 2 — Embed User
        REC->>EMB: get_user_embedding(profile)
        EMB-->>REC: ndarray [1 x 384]

        note right of REC: Step 3 — Retrieval
        REC->>REC: cosine_similarity -> top-5

        note right of REC: Step 4 — Re-Rank
        REC->>LLM: POST chat/completions (prompt + 5 candidates)
        LLM-->>REC: JSON array [3 recommendations]
    end

    REC-->>API: RecommendationResponse
    API-->>C: JSON (recommendations + pipeline_log)
```

---

## 3. Component Diagram

```mermaid
classDiagram
    direction TB

    class FastAPI {
        +health()
        +list_content()
        +list_users()
        +recommend(profile)
    }

    class Recommender {
        +get_recommendations(profile)
        -_get_cached_content_embeddings()
        -_timed(label, fn)
    }

    class DataLayer {
        +get_all_content()
        +get_all_users()
        +get_user_by_id(user_id)
    }

    class Embeddings {
        +get_content_embeddings(items)
        +get_user_embedding(profile)
        +retrieve_top_k(user_emb, content_embs, items, k, exclude_ids)
        -_embed_texts(texts)
        -_embed_locally(texts)
        -_embed_via_api(texts)
    }

    class LLMRanker {
        +rerank(profile, candidates)
        -_call_llm(system, user)
        -_parse_llm_response(raw, candidates)
        -_rule_based_rerank(profile, candidates)
        -_extract_json_array(raw)
    }

    class Config {
        +LLM_API_KEY
        +LLM_MODEL
        +LLM_BASE_URL
        +EMBEDDING_PROVIDER
        +EMBEDDING_MODEL_LOCAL
    }

    class Schemas {
        +Difficulty
        +LearningStyle
        +ContentFormat
        +PipelineStatus
        +ContentItem
        +UserProfile
        +Recommendation
        +PipelineStep
        +RecommendationResponse
    }

    FastAPI --> Recommender : calls
    FastAPI --> DataLayer : loads data
    Recommender --> Embeddings : steps 1-3
    Recommender --> LLMRanker : step 4
    Recommender --> DataLayer : get_all_content()
    LLMRanker ..> Config : reads API settings
    Embeddings ..> Config : reads provider settings
    Recommender ..> Schemas : returns typed models
```

---

## 4. Module Dependency Graph

```mermaid
graph LR
    subgraph Root
        API[api/main.py]
    end

    subgraph App
        REC[app/recommender.py]
        LLM[app/llm_ranker.py]
        EMB[app/embeddings.py]
        DATA[app/data.py]
        CONF[app/config.py]
        SCH[app/schemas.py]
    end

    API --> REC
    API --> DATA
    API --> SCH
    REC --> LLM
    REC --> EMB
    REC --> DATA
    REC --> SCH
    LLM --> CONF
    LLM --> SCH
    EMB --> CONF
    EMB --> SCH
    DATA --> SCH
```

---

## 5. Key Design Decisions

### 5.1 Hybrid Search

- **Retrieval** — `sentence-transformers` (fast, local, CPU-only) narrows the
  catalogue to 5 candidates.
- **Ranking** — LLM (`Kimi-K2.5`) reasons about multi-dimensional constraints
  to select the best 3.
- **Benefit** — balances millisecond retrieval speed with intelligent
  constraint satisfaction.

### 5.2 Caching

Content embeddings are cached in a module-level variable keyed by the hash
of content IDs.  Subsequent requests with the same catalogue skip the
embedding step entirely (< 5 ms).

### 5.3 Strict Enums

Raw strings (`"Beginner"`, `"visual"`, `"video"`) are replaced by
`Difficulty`, `LearningStyle`, and `ContentFormat` enums.  This prevents
typo-induced bugs, enables IDE autocompletion, and makes the API schema
self-documenting.

### 5.4 Graceful Degradation

The LLM ranker wraps all network calls in a try/except.  On any failure
(timeout, bad JSON, rate limit), the system transparently falls back to
deterministic rule-based scoring — ensuring the user always receives
recommendations.

### 5.5 Timing Instrumentation

A `_timed()` helper replaces repeated `time.perf_counter()` boilerplate.
Each pipeline step records its duration in milliseconds, exposed in the
`pipeline_log` field of every response.

---

## 6. Performance Characteristics

| Operation                       | Latency      | Notes                        |
| ------------------------------- | ------------ | ---------------------------- |
| Content embedding (first run)   | 50 - 200 ms  | 10 items, then cached        |
| Content embedding (cached)      | < 5 ms       | Hash-based cache hit         |
| User embedding                  | 5 - 20 ms    | Always computed              |
| Cosine similarity retrieval     | < 1 ms       | numpy dot product            |
| LLM re-ranking                  | 2 - 5 s      | Network round-trip           |
| Rule-based ranking              | < 1 ms       | Heuristic scoring            |
| Full pipeline (with LLM)        | 2.5 - 6 s    | Dominated by LLM call        |
| Full pipeline (rules only)      | 50 - 150 ms  | No network latency           |
