"""Admin and monitoring API routes (protected endpoints)."""

from fastapi import APIRouter, Depends

from app.models.schemas import APIResponse

router = APIRouter()


@router.get("/admin/stats", response_model=APIResponse)
async def get_system_stats() -> APIResponse:
    """Get system statistics and monitoring data."""
    # TODO: Implement stats collection
    return APIResponse(
        success=True,
        data={
            "total_sessions": 0,
            "emergency_cases": 0,
            "average_response_time_ms": 0,
            "active_agents": 6,
        },
        error=None,
    )


@router.get("/admin/sessions", response_model=APIResponse)
async def list_recent_sessions(limit: int = 50) -> APIResponse:
    """List recent triage sessions (anonymized)."""
    # TODO: Implement session listing with PII redaction
    return APIResponse(
        success=True,
        data={"sessions": [], "total": 0},
        error=None,
    )
