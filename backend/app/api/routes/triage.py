"""Triage API routes for patient symptom intake and triage processing."""

import uuid

from fastapi import APIRouter, Request

from app.agents.graph import WorkflowStatus
from app.agents.supervisor_agent import SupervisorAgent
from app.core.exceptions import SupervisorError
from app.core.logging import get_logger
from app.models.schemas import APIResponse, ErrorDetail, SymptomIntakeRequest

logger = get_logger(__name__)

router = APIRouter()


def _get_supervisor(request: Request) -> SupervisorAgent:
    """
    Retrieve the singleton SupervisorAgent from application state.

    The supervisor is initialised once at startup via the FastAPI lifespan
    handler and stored in ``app.state.supervisor``. This eliminates the
    per-request overhead of re-instantiating agents and re-reading JSON
    data files from disk.
    """
    return request.app.state.supervisor


@router.post("/triage")
async def process_triage(request: Request, body: SymptomIntakeRequest) -> APIResponse:
    """
    Process patient symptom intake through the multi-agent triage pipeline.

    This endpoint:
    1. Extracts structured symptoms from patient message
    2. Checks for emergency conditions (safety escalation)
    3. If not emergency, classifies urgency via triage reasoning
    4. Matches to nearest appropriate facility
    5. Checks medicine availability
    6. Returns comprehensive response in Urdu

    Returns unified APIResponse with TriageResponse data.
    """
    session_id = str(uuid.uuid4())
    logger.info("triage.request_start", session_id=session_id)

    try:
        supervisor = _get_supervisor(request)

        final_state = await supervisor.run(
            patient_message=body.patient_message,
            session_id=session_id,
            phone_number=body.phone_number,
            latitude=body.location_lat,
            longitude=body.location_lng,
        )

        triage_response = await supervisor.build_triage_response(final_state)

        logger.info(
            "triage.request_complete",
            session_id=session_id,
            is_emergency=triage_response.is_emergency,
            urgency=triage_response.urgency,
        )

        return APIResponse(
            success=True,
            data=triage_response.model_dump(),
            error=None,
        )

    except SupervisorError as e:
        logger.error(
            "triage.supervisor_error",
            session_id=session_id,
            error=str(e),
        )
        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code=e.error_code,
                message=e.message,
                details=e.details,
            ),
        )

    except Exception as e:
        logger.error(
            "triage.unexpected_error",
            session_id=session_id,
            error=str(e),
        )
        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="TRIAGE_ERROR",
                message="An unexpected error occurred during triage",
                details={"error": str(e)},
            ),
        )


@router.get("/triage/{session_id}")
async def get_triage_status(session_id: str) -> APIResponse:
    """Get the status of a triage session."""
    return APIResponse(
        success=True,
        data={"session_id": session_id, "status": "completed"},
        error=None,
    )
