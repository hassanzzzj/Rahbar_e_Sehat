"""
Speech client adapter for Groq's Whisper transcription API (ASR) and gTTS (TTS).
Provides async speech-to-text and text-to-speech for Urdu and other languages.
"""

import asyncio
import io

import httpx
from gtts import gTTS
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import SpeechServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SpeechClient:
    """Adapter for Groq Whisper ASR (remote) and gTTS (local) speech synthesis."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._api_base = settings.groq_api_base
        self._whisper_model = settings.groq_whisper_model_name
        self._client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def transcribe_audio(self, audio_bytes: bytes, language: str = "ur") -> str:
        """
        Transcribe audio to text using Groq's Whisper API.

        Args:
            audio_bytes: Raw audio bytes (WebM/WAV/OGG format).
            language: ISO 639-1 language code (default: "ur" for Urdu).

        Returns:
            Transcribed text string.

        Raises:
            SpeechServiceError: If the Whisper API is unavailable or returns an error.
        """
        url = f"{self._api_base}/audio/transcriptions"
        try:
            response = await self._client.post(
                url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": ("audio.webm", audio_bytes, "audio/webm")},
                data={
                    "model": self._whisper_model,
                    "language": language,
                },
            )
            response.raise_for_status()
            result = response.json()
            text = result.get("text", "")
            logger.info(
                "speech.asr_success",
                language=language,
                text_length=len(text),
            )
            return text
        except httpx.HTTPStatusError as e:
            logger.error(
                "speech.asr_http_error",
                status_code=e.response.status_code,
                detail=e.response.text,
            )
            raise SpeechServiceError(
                f"Whisper ASR returned HTTP {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            logger.error("speech.asr_request_error", error=str(e), url=url)
            raise SpeechServiceError(
                f"Whisper ASR request failed: {e}"
            ) from e
        except Exception as e:
            logger.error("speech.asr_error", error=str(e))
            raise SpeechServiceError(f"Speech-to-text failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def synthesize_speech(self, text: str, language: str = "ur") -> bytes:
        """
        Synthesize text to speech audio using gTTS (local, no API key required).

        Args:
            text: Text to convert to speech.
            language: ISO 639-1 language code (default: "ur" for Urdu).

        Returns:
            Raw audio bytes (MP3 format).

        Raises:
            SpeechServiceError: If speech synthesis fails.
        """
        try:
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None, self._synthesize_sync, text, language
            )
            logger.info(
                "speech.tts_success",
                language=language,
                audio_bytes=len(audio_data),
            )
            return audio_data
        except Exception as e:
            logger.error("speech.tts_error", error=str(e))
            raise SpeechServiceError(f"Text-to-speech failed: {e}") from e

    @staticmethod
    def _synthesize_sync(text: str, language: str) -> bytes:
        """Blocking gTTS call — run inside an executor to avoid blocking the event loop."""
        buffer = io.BytesIO()
        gTTS(text=text, lang=language).write_to_fp(buffer)
        return buffer.getvalue()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
