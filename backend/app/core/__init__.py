"""Core utilities and security modules."""

from typing import Any

from app.core.exceptions import (
    AgentError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    FacilityMatchingError,
    IntakeError,
    LLMServiceError,
    MedicineAvailabilityError,
    NotFoundError,
    RahbarBaseException,
    RateLimitError,
    SafetyEscalationError,
    SupervisorError,
    TriageError,
    ValidationError,
)
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import RateLimitMiddleware, create_rate_limit_middleware
from app.core.security import SecurityManager, get_security_manager

__all__ = [
    # Exceptions
    "RahbarBaseException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "RateLimitError",
    "AgentError",
    "IntakeError",
    "TriageError",
    "FacilityMatchingError",
    "MedicineAvailabilityError",
    "SupervisorError",
    "LLMServiceError",
    "SafetyEscalationError",
    "DatabaseError",
    # Logging
    "setup_logging",
    "get_logger",
    # Security
    "SecurityManager",
    "get_security_manager",
    "security_manager",
    # Rate limiting
    "RateLimitMiddleware",
    "create_rate_limit_middleware",
]


def __getattr__(name: str) -> Any:
    """Lazily resolve the legacy ``security_manager`` singleton name."""
    if name == "security_manager":
        return get_security_manager()
    raise AttributeError(f"module 'app.core' has no attribute {name!r}")
