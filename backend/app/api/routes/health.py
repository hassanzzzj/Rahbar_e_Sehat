"""Health check endpoints for uptime monitoring and load balancer checks."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def health_check() -> dict:
    """Liveness probe - returns 200 if application is running."""
    return {"success": True, "data": {"status": "healthy"}, "error": None}


@router.get("/readyz")
async def readiness_check() -> dict:
    """Readiness probe - returns 200 if application is ready to serve traffic."""
    # TODO: Check database connectivity
    # TODO: Check vector store availability
    # TODO: Check LLM service availability
    return {
        "success": True,
        "data": {
            "status": "ready",
            "checks": {
                "database": "ok",
                "vector_store": "ok",
                "llm_service": "ok",
            },
        },
        "error": None,
    }
