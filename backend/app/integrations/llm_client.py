"""
LLM client adapter for Groq's free-tier, OpenAI-compatible chat completions API.
Provides async interface for LLM calls with retry logic and timeout handling.
"""

from typing import Any, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import LLMServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Adapter for Groq's LLM API (OpenAI-compatible chat completions)."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key: Optional[str] = settings.groq_api_key
        self.api_endpoint: str = settings.groq_api_base
        self.model_name: str = settings.groq_model_name
        self._client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generate a response from the Groq-hosted model.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            max_tokens: Maximum response tokens
            temperature: Response randomness (0.0-1.0)

        Returns:
            Dict with 'text' and 'usage' keys

        Raises:
            LLMServiceError: If LLM service is unavailable or returns errors
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self._client.post(
                f"{self.api_endpoint}/chat/completions",
                headers=headers,
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()

            data = response.json()
            return {
                "text": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
            }

        except httpx.HTTPStatusError as e:
            logger.error("llm.http_error", status=e.response.status_code, error=str(e))
            raise LLMServiceError(f"LLM API returned error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("llm.request_error", error=str(e))
            raise LLMServiceError(f"LLM API request failed: {str(e)}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
