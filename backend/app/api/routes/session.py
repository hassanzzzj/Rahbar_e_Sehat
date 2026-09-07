"""Session API routes — anonymous JWT session tokens for patient triage."""

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt

from fastapi import APIRouter

from app.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import SessionCreateResponse, SessionStatusResponse

logger = get_logger(__name__)

router = APIRouter()

_sessions: dict[str, dict] = {}


@router.post("/session/create", response_model=SessionCreateResponse)
async def create_session() -> SessionCreateResponse:
    """Generate an anonymous JWT session token (no login required)."""
    settings = get_settings()
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.jwt_expiration_hours)

    payload = {
        "sub": session_id,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    _sessions[session_id] = {
        "session_id": session_id,
        "status": "active",
        "created_at": now,
    }

    logger.info("session.created", session_id=session_id)

    return SessionCreateResponse(
        session_id=session_id,
        token=token,
        expires_at=expires_at,
    )


@router.get("/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str) -> SessionStatusResponse:
    """Return the status of a session."""
    session = _sessions.get(session_id)
    if session is None:
        return SessionStatusResponse(
            session_id=session_id,
            status="unknown",
            created_at=datetime.now(timezone.utc),
        )

    return SessionStatusResponse(
        session_id=session["session_id"],
        status=session["status"],
        created_at=session["created_at"],
    )
