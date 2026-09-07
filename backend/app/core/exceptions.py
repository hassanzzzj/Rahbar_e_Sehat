"""
Custom exception classes and exception handlers for the application.
Provides structured error responses following the unified API format.
"""

from typing import Any, Dict, Optional


class RahbarBaseException(Exception):
    """Base exception for all Rahbar-e-Sehat application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RahbarBaseException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class AuthenticationError(RahbarBaseException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(RahbarBaseException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class NotFoundError(RahbarBaseException):
    """Raised when a resource is not found."""

    def __init__(self, message: str, resource_type: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type} if resource_type else {},
        )


class RateLimitError(RahbarBaseException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


class AgentError(RahbarBaseException):
    """Raised when an agent fails during processing."""

    def __init__(
        self,
        message: str,
        agent_name: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            status_code=500,
            details={"agent_name": agent_name, **(details or {})},
        )


class IntakeError(AgentError):
    """Raised when the Symptom Intake Agent cannot extract structured symptoms."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            agent_name="symptom_intake",
            details=details,
        )
        self.error_code = "INTAKE_ERROR"


class TriageError(AgentError):
    """Raised when the Triage Reasoning Agent cannot produce a valid classification."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            agent_name="triage_reasoning",
            details=details,
        )
        self.error_code = "TRIAGE_ERROR"


class FacilityMatchingError(AgentError):
    """Raised when the Facility Matching Agent cannot find a suitable facility."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            agent_name="facility_matching",
            details=details,
        )
        self.error_code = "FACILITY_MATCHING_ERROR"


class MedicineAvailabilityError(AgentError):
    """Raised when the Medicine Availability Agent cannot check medicine stock."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            agent_name="medicine_availability",
            details=details,
        )
        self.error_code = "MEDICINE_AVAILABILITY_ERROR"


class SupervisorError(AgentError):
    """Raised when the Supervisor Agent encounters a workflow orchestration error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            agent_name="supervisor",
            details=details,
        )
        self.error_code = "SUPERVISOR_ERROR"


class LLMServiceError(RahbarBaseException):
    """Raised when LLM service is unavailable or returns errors."""

    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(
            message=message,
            error_code="LLM_SERVICE_ERROR",
            status_code=503,
        )


class SpeechServiceError(RahbarBaseException):
    """Raised when speech service (ASR/TTS) is unavailable or returns errors."""

    def __init__(self, message: str = "Speech service unavailable"):
        super().__init__(
            message=message,
            error_code="SPEECH_SERVICE_ERROR",
            status_code=503,
        )


class SafetyEscalationError(RahbarBaseException):
    """Raised when safety escalation agent encounters an error."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="SAFETY_ESCALATION_ERROR",
            status_code=500,
        )


class DatabaseError(RahbarBaseException):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation} if operation else {},
        )
