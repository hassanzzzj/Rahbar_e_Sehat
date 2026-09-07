"""
FastAPI application entrypoint for Rahbar-e-Sehat.
Registers middleware, routes, and exception handlers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RahbarBaseException,
    RateLimitError,
    ValidationError,
)
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import create_rate_limit_middleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler — initialise singletons on startup, clean up on shutdown."""
    setup_logging()
    settings = get_settings()
    logger.info("application.starting", app_name="rahbar-e-sehat", env=settings.app_env)

    # ------------------------------------------------------------------
    # Import agent/integration modules here (deferred to avoid import
    # overhead before settings are resolved).
    # ------------------------------------------------------------------
    from app.agents.facility_matching_agent import FacilityMatchingAgent, InMemoryFacilityStore
    from app.agents.intake_agent import SymptomIntakeAgent
    from app.agents.medicine_availability_agent import InMemoryMedicineStore, MedicineAvailabilityAgent
    from app.agents.safety_escalation_agent import SafetyEscalationAgent
    from app.agents.supervisor_agent import SupervisorAgent
    from app.agents.triage_reasoning_agent import TriageReasoningAgent
    from app.integrations.llm_client import LLMClient
    from app.integrations.speech_client import SpeechClient
    from app.rag.retriever import RAGRetriever

    # LLM & speech clients (shared across all requests)
    llm_client = LLMClient()
    speech_client = SpeechClient()

    # RAG retriever (loads vector index once)
    retriever = RAGRetriever()

    # Facility data store (read JSON once at startup)
    facility_store = InMemoryFacilityStore()
    try:
        facility_store.load_from_file(settings.facility_data_path)
        logger.info("application.facility_store_loaded", path=settings.facility_data_path)
    except Exception as exc:
        logger.warning("application.facility_store_load_failed", error=str(exc))

    # Medicine data store (read JSON once at startup)
    medicine_store = InMemoryMedicineStore()
    try:
        medicine_store.load_from_file(settings.medicine_data_path)
        logger.info("application.medicine_store_loaded", path=settings.medicine_data_path)
    except Exception as exc:
        logger.warning("application.medicine_store_load_failed", error=str(exc))

    # Wire all agents into a single SupervisorAgent singleton
    supervisor = SupervisorAgent(
        symptom_intake=SymptomIntakeAgent(llm_client),
        safety_escalation=SafetyEscalationAgent(),
        triage_reasoning=TriageReasoningAgent(llm_client, retriever),
        facility_matching=FacilityMatchingAgent(facility_store),
        medicine_availability=MedicineAvailabilityAgent(medicine_store),
        speech_client=speech_client,
    )

    # Store singletons on app.state for injection into route handlers
    app.state.supervisor = supervisor
    app.state.llm_client = llm_client
    app.state.speech_client = speech_client
    app.state.facility_store = facility_store
    app.state.medicine_store = medicine_store

    logger.info("application.ready")
    yield

    # ------------------------------------------------------------------
    # Shutdown — close async clients gracefully
    # ------------------------------------------------------------------
    logger.info("application.shutdown")
    await llm_client.close()
    if speech_client:
        await speech_client.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Rahbar-e-Sehat API",
        description="Autonomous Multi-Agent Healthcare Triage & Referral System",
        version="0.1.0",
        docs_url=f"{settings.api_prefix}/docs" if settings.debug else None,
        redoc_url=f"{settings.api_prefix}/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware
    middleware_class, middleware_kwargs = create_rate_limit_middleware()
    app.add_middleware(middleware_class, **middleware_kwargs)

    # Exception handlers
    @app.exception_handler(RahbarBaseException)
    async def rahbar_exception_handler(request: Request, exc: RahbarBaseException) -> JSONResponse:
        """Handle all RahbarBaseException subclasses with unified response format."""
        logger.warning(
            "request.error",
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details if exc.details else None,
                },
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions with safe response."""
        logger.error(
            "request.unhandled_error",
            error=str(exc),
            path=request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                },
            },
        )

    # Register routes
    from app.api.routes import health, triage, facilities, admin, session, speech

    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(triage.router, prefix=settings.api_prefix, tags=["triage"])
    app.include_router(facilities.router, prefix=settings.api_prefix, tags=["facilities"])
    app.include_router(admin.router, prefix=settings.api_prefix, tags=["admin"])
    app.include_router(session.router, prefix=settings.api_prefix, tags=["session"])
    app.include_router(speech.router, prefix=settings.api_prefix, tags=["speech"])

    return app


app = create_app()
