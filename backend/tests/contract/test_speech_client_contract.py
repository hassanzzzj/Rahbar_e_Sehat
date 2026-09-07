"""
Contract test: Speech client interactions — Groq Whisper transcription (mocked HTTP)
and gTTS speech synthesis (mocked library calls). Verifies correct request/response
handling without hitting live services.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.core.exceptions import SpeechServiceError
from app.integrations.speech_client import SpeechClient


class TestSpeechClientContract:
    """Contract tests for SpeechClient (Groq Whisper ASR + gTTS)."""

    @pytest.fixture
    def client(self) -> SpeechClient:
        """Provide a SpeechClient with test config."""
        with patch("app.integrations.speech_client.get_settings") as mock_settings:
            settings = MagicMock()
            settings.groq_api_key = "test-groq-key"
            settings.groq_api_base = "https://api.groq.com/openai/v1"
            settings.groq_whisper_model_name = "whisper-large-v3"
            mock_settings.return_value = settings
            c = SpeechClient()
            # Disable retry for fast tests
            c.transcribe_audio.retry.stop = lambda *a, **k: True
            c.synthesize_speech.retry.stop = lambda *a, **k: True
            return c

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, client: SpeechClient):
        """Groq Whisper should return transcribed text from JSON response."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "mere sir mein dard hai"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.transcribe_audio(b"fake-audio-bytes", language="ur")

        assert result == "mere sir mein dard hai"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.groq.com/openai/v1/audio/transcriptions"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-groq-key"
        assert call_args[1]["data"]["language"] == "ur"
        assert call_args[1]["data"]["model"] == "whisper-large-v3"

    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_text(self, client: SpeechClient):
        """Groq Whisper should return empty string when text field is missing."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.transcribe_audio(b"silent-audio")

        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_audio_http_error(self, client: SpeechClient):
        """Groq Whisper HTTP error should raise SpeechServiceError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        http_error = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=http_error
        ):
            with pytest.raises(SpeechServiceError) as exc_info:
                await client.transcribe_audio(b"bad-audio")

        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_audio_request_error(self, client: SpeechClient):
        """Groq Whisper connection failure should raise SpeechServiceError."""
        request_error = httpx.ConnectError("Connection refused")

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=request_error
        ):
            with pytest.raises(SpeechServiceError) as exc_info:
                await client.transcribe_audio(b"audio")

        assert "request failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, client: SpeechClient):
        """gTTS should return raw MP3 bytes written via write_to_fp."""
        fake_audio = b"fake-mp3-audio-bytes"

        def fake_write_to_fp(fp):
            fp.write(fake_audio)

        mock_gtts_instance = MagicMock()
        mock_gtts_instance.write_to_fp.side_effect = fake_write_to_fp

        with patch(
            "app.integrations.speech_client.gTTS", return_value=mock_gtts_instance
        ) as mock_gtts_cls:
            result = await client.synthesize_speech("Assalam-o-Alaikum", language="ur")

        assert result == fake_audio
        mock_gtts_cls.assert_called_once_with(text="Assalam-o-Alaikum", lang="ur")

    @pytest.mark.asyncio
    async def test_synthesize_speech_failure_wrapped(self, client: SpeechClient):
        """gTTS failures should be wrapped in SpeechServiceError."""
        with patch(
            "app.integrations.speech_client.gTTS",
            side_effect=RuntimeError("network unreachable"),
        ):
            with pytest.raises(SpeechServiceError) as exc_info:
                await client.synthesize_speech("hello")

        assert "Text-to-speech failed" in str(exc_info.value)
