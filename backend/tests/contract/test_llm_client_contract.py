"""
Contract test: LLM client interactions with mocked Groq (OpenAI-compatible) responses.
Verifies correct request/response handling without hitting live APIs.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.core.exceptions import LLMServiceError
from app.integrations.llm_client import LLMClient


class TestLLMClientContract:
    """Contract tests for LLMClient (Groq, OpenAI-compatible API)."""

    @pytest.fixture
    def client(self) -> LLMClient:
        """Provide an LLMClient with test config."""
        with patch("app.integrations.llm_client.get_settings") as mock_settings:
            settings = MagicMock()
            settings.groq_api_key = "test-key-123"
            settings.groq_api_base = "https://api.groq.com/openai/v1"
            settings.groq_model_name = "llama-3.3-70b-versatile"
            mock_settings.return_value = settings
            c = LLMClient()
            return c

    @pytest.mark.asyncio
    async def test_generate_response_success(self, client: LLMClient):
        """LLM client should parse OpenAI-format response correctly."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-abc",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Assalam-o-Alaikum. Main aap ki madad kar sakta hoon.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 25,
                "completion_tokens": 15,
                "total_tokens": 40,
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.generate_response(
                prompt="Hello",
                system_prompt="You are a helpful assistant.",
                max_tokens=512,
                temperature=0.2,
            )

        assert result["text"] == "Assalam-o-Alaikum. Main aap ki madad kar sakta hoon."
        assert result["usage"]["total_tokens"] == 40

        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.groq.com/openai/v1/chat/completions"
        payload = call_args[1]["json"]
        assert payload["model"] == "llama-3.3-70b-versatile"
        assert payload["max_tokens"] == 512
        assert payload["temperature"] == 0.2
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"

        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-key-123"

    @pytest.mark.asyncio
    async def test_generate_response_no_api_key(self, client: LLMClient):
        """When api_key is None, Authorization header should be omitted."""
        client.api_key = None

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}],
            "usage": {},
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.generate_response(prompt="test")

        assert result["text"] == "response"
        headers = mock_post.call_args[1]["headers"]
        assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_generate_response_http_error(self, client: LLMClient):
        """HTTP errors should raise LLMServiceError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500

        http_error = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=http_error
        ):
            with pytest.raises(LLMServiceError) as exc_info:
                await client.generate_response(prompt="test")

        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_response_request_error(self, client: LLMClient):
        """Connection failures should raise LLMServiceError."""
        request_error = httpx.ConnectError("Connection refused")

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=request_error
        ):
            with pytest.raises(LLMServiceError) as exc_info:
                await client.generate_response(prompt="test")

        assert "request failed" in str(exc_info.value)
