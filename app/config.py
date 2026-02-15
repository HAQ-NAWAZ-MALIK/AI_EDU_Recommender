"""
Configuration — single source of truth for all tuneable settings.

All values are loaded from environment variables (or a `.env` file at the
project root).  Swap the LLM or embedding provider by changing `.env` alone;
no code edits required.

Attributes
----------
LLM_API_KEY : str
    Bearer token for the chat-completion endpoint.
LLM_MODEL : str
    Model slug sent in the ``model`` field of the request payload.
LLM_BASE_URL : str
    Full URL of the chat-completions endpoint.
EMBEDDING_PROVIDER : ``"local"`` | ``"api"``
    Which embedding backend to use.
EMBEDDING_MODEL_LOCAL : str
    HuggingFace model id for ``sentence-transformers``.
EMBEDDING_MODEL_API : str
    Model id for an OpenAI-compatible embedding endpoint.
EMBEDDING_API_BASE_URL : str
    URL of the ``/embeddings`` endpoint (only used when provider is ``api``).
EMBEDDING_API_KEY : str
    Bearer token for the embedding API.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from project root
# ---------------------------------------------------------------------------
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


# ---------------------------------------------------------------------------
# LLM settings
# ---------------------------------------------------------------------------
LLM_API_KEY: str = os.getenv("HF_TOKEN") or os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "moonshotai/Kimi-K2.5:novita")
LLM_BASE_URL: str = os.getenv(
    "LLM_BASE_URL",
    "https://router.huggingface.co/v1/chat/completions",
)

# ---------------------------------------------------------------------------
# Embedding settings
# ---------------------------------------------------------------------------
EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")
EMBEDDING_MODEL_LOCAL: str = os.getenv("EMBEDDING_MODEL_LOCAL", "all-MiniLM-L6-v2")
EMBEDDING_MODEL_API: str = os.getenv("EMBEDDING_MODEL_API", "text-embedding-ada-002")
EMBEDDING_API_BASE_URL: str = os.getenv(
    "EMBEDDING_API_BASE_URL",
    "https://api.openai.com/v1/embeddings",
)
EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
