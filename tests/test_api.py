"""
Integration test for the ``/recommend`` endpoint.

Usage
-----
1. Start the server:  ``uvicorn api.main:app --port 8000``
2. Run this script:   ``python -m tests.test_api``
"""

from __future__ import annotations

import json
import sys

import requests

ENDPOINT = "http://localhost:8000/recommend"

PAYLOAD = {
    "user_id": "u1",
    "name": "Alice",
    "goal": "Learn to deploy ML models into production using Kubernetes",
    "learning_style": "visual",
    "preferred_difficulty": "Intermediate",
    "time_per_day": 60,
    "viewed_content_ids": [1],
    "interest_tags": ["ml", "deployment", "kubernetes"],
}


def main() -> None:
    """Fire a single recommendation request and print the response."""
    print(f"POST {ENDPOINT}")
    try:
        resp = requests.post(ENDPOINT, json=PAYLOAD, timeout=120)
    except requests.ConnectionError:
        print("ERROR: Could not connect. Is the server running?")
        sys.exit(1)

    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    main()
