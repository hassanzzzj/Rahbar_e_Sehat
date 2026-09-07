"""Test fixtures for the agent test suites."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest


class FakeLLMClient:
    """Deterministic LLM stand-in for unit tests.

    Accepts a callable (or list of callables) that returns the dict the
    real LLMClient would return: ``{"text": "...", "usage": {...}}``.
    Multiple callables let a test simulate a failure on the first attempt
    and success on the retry.
    """

    def __init__(
        self,
        responses: Any,
    ) -> None:
        if not isinstance(responses, list):
            responses = [responses]
        self._responses: List[Any] = list(responses)
        self._index = 0
        self.calls: List[Dict[str, Any]] = []

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )

        if self._index < len(self._responses):
            response = self._responses[self._index]
            self._index += 1
        else:
            response = self._responses[-1]

        if isinstance(response, Exception):
            raise response
        if callable(response):
            response = response()
        return response


class FakeRAGRetriever:
    """Deterministic RAG retriever stand-in for unit tests."""

    def __init__(self, protocols: Optional[List[Dict]] = None) -> None:
        self._protocols = protocols or []
        self.calls: List[Dict[str, Any]] = []

    async def retrieve_clinical_protocols(
        self, query: str, top_k: int = 3
    ) -> List[Dict]:
        self.calls.append({"query": query, "top_k": top_k})
        return self._protocols[:top_k]


def llm_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Helper: wrap a dict as the LLM client's expected return value."""
    import json

    return {"text": json.dumps(payload), "usage": {}}


def llm_text(text: str) -> Dict[str, Any]:
    """Helper: raw-text LLM response (used for malformed-output tests)."""
    return {"text": text, "usage": {}}


@pytest.fixture
def fake_llm():
    """Fixture providing a fresh FakeLLMClient factory."""
    return FakeLLMClient


@pytest.fixture
def fake_retriever():
    """Fixture providing a fresh FakeRAGRetriever factory."""
    return FakeRAGRetriever
