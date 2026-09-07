"""Speech API routes — audio transcription for voice-first symptom input."""

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.exceptions import SpeechServiceError
from app.core.logging import get_logger
from app.models.schemas import APIResponse, ErrorDetail, TranscribeResponse

logger = get_logger(__name__)

router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("ur"),
) -> APIResponse:
    """
    Transcribe a recorded audio clip to text via the Groq Whisper API.

    Accepts a multipart form with an audio ``file`` field and an optional
    ``language`` field (ISO 639-1 code, defaults to Urdu).
    """
    speech_client = request.app.state.speech_client
    if speech_client is None:
        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="SPEECH_SERVICE_UNAVAILABLE",
                message="Speech service is not configured.",
            ),
        )

    audio_bytes = await file.read()

    try:
        text = await speech_client.transcribe_audio(audio_bytes, language=language)
        return APIResponse(
            success=True,
            data=TranscribeResponse(text=text).model_dump(),
            error=None,
        )
    except SpeechServiceError as e:
        logger.error("transcribe.speech_service_error", error=str(e))
        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(code=e.error_code, message=e.message),
        )
