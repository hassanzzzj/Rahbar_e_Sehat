"""
Unit tests for the voice transcription route.
Verifies POST /api/v1/transcribe behavior with a mocked speech client.
"""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.core.exceptions import SpeechServiceError
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI test client."""
    return TestClient(app)


class TestTranscribeRoute:
    """Tests for POST /api/v1/transcribe."""

    def test_transcribe_success(self, client: TestClient):
        """Should return transcribed text wrapped in the standard envelope."""
        mock_speech_client = AsyncMock()
        mock_speech_client.transcribe_audio.return_value = "mere sir mein dard hai"
        app.state.speech_client = mock_speech_client

        response = client.post(
            "/api/v1/transcribe",
            files={"file": ("recording.webm", b"fake-audio-bytes", "audio/webm")},
            data={"language": "ur"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["text"] == "mere sir mein dard hai"
        assert body["error"] is None
        mock_speech_client.transcribe_audio.assert_called_once()
        call_args = mock_speech_client.transcribe_audio.call_args
        assert call_args[1]["language"] == "ur"

    def test_transcribe_missing_speech_client(self, client: TestClient):
        """Should return a clean error envelope when speech client is unavailable."""
        app.state.speech_client = None

        response = client.post(
            "/api/v1/transcribe",
            files={"file": ("recording.webm", b"fake-audio-bytes", "audio/webm")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "SPEECH_SERVICE_UNAVAILABLE"

    def test_transcribe_speech_service_error(self, client: TestClient):
        """Should return a clean error envelope when transcription fails."""
        mock_speech_client = AsyncMock()
        mock_speech_client.transcribe_audio.side_effect = SpeechServiceError(
            "Whisper ASR returned HTTP 401: Invalid API key"
        )
        app.state.speech_client = mock_speech_client

        response = client.post(
            "/api/v1/transcribe",
            files={"file": ("recording.webm", b"fake-audio-bytes", "audio/webm")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is False
        assert body["data"] is None
        assert "Invalid API key" in body["error"]["message"]
