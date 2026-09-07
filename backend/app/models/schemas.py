"""
Pydantic models for API request/response schemas.
Enforces strict input validation at the API boundary.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class TriageUrgency(str, Enum):
    """Triage urgency levels."""

    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"
    SELF_CARE = "SELF_CARE"


class FacilityType(str, Enum):
    """Healthcare facility types."""

    BHU = "BHU"  # Basic Health Unit
    RHC = "RHC"  # Rural Health Centre
    THQ = "THQ"  # Tehsil Headquarters Hospital
    DHQ = "DHQ"  # District Headquarters Hospital
    TERTIARY = "TERTIARY"
    EMERGENCY = "EMERGENCY"


class SymptomSeverity(str, Enum):
    """Symptom severity levels."""

    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"


class AgeGroup(str, Enum):
    """Patient age groups for triage considerations."""

    INFANT = "INFANT"  # 0-1 year
    CHILD = "CHILD"  # 2-12 years
    ADOLESCENT = "ADOLESCENT"  # 13-17 years
    ADULT = "ADULT"  # 18-64 years
    ELDERLY = "ELDERLY"  # 65+ years


# =============================================================================
# Request Schemas
# =============================================================================


class SymptomIntakeRequest(BaseModel):
    """Request schema for symptom intake from patient."""

    model_config = ConfigDict(extra="forbid")

    patient_message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Free-form patient message in Urdu or English",
    )
    phone_number: Optional[str] = Field(
        None,
        pattern=r"^\+?[0-9]{10,15}$",
        description="Patient phone number for session tracking",
    )
    location_lat: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Patient latitude for facility matching",
    )
    location_lng: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Patient longitude for facility matching",
    )


class FacilitySearchRequest(BaseModel):
    """Request schema for facility search."""

    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    facility_type: Optional[FacilityType] = None
    max_distance_km: float = Field(default=50.0, ge=0.1, le=500.0)


# =============================================================================
# Agent Output Schemas (Schema-Constrained)
# =============================================================================


class ExtractedSymptoms(BaseModel):
    """Structured symptom data extracted by Symptom Intake Agent."""

    model_config = ConfigDict(extra="forbid")

    primary_symptom: str = Field(..., min_length=1, max_length=200)
    secondary_symptoms: List[str] = Field(default_factory=list, max_length=10)
    duration_hours: Optional[float] = Field(None, ge=0, le=8760)
    severity: SymptomSeverity = Field(default=SymptomSeverity.MODERATE)
    age_group: AgeGroup = Field(default=AgeGroup.ADULT)
    is_pregnant: bool = Field(default=False)
    pre_existing_conditions: List[str] = Field(default_factory=list, max_length=10)
    associated_symptoms: List[str] = Field(default_factory=list, max_length=15)


class SafetyCheckResult(BaseModel):
    """Result from Safety Escalation Agent."""

    model_config = ConfigDict(extra="forbid")

    is_emergency: bool
    red_flags_triggered: List[str] = Field(default_factory=list)
    emergency_type: Optional[str] = None
    immediate_action_required: Optional[str] = None


class TriageClassification(BaseModel):
    """Result from Triage Reasoning Agent."""

    model_config = ConfigDict(extra="forbid")

    urgency: TriageUrgency
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning_trace: str = Field(..., min_length=1)
    source_documents: List[str] = Field(default_factory=list)
    recommended_care_tier: FacilityType


class FacilityInfo(BaseModel):
    """Facility information returned by Facility-Matching Agent."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str
    name: str
    facility_type: FacilityType
    address: str
    distance_km: float = Field(..., ge=0.0)
    services_available: List[str]
    emergency_capable: bool
    phone_number: Optional[str] = None


class MedicineAvailability(BaseModel):
    """Medicine availability status at a facility."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str
    medicines_checked: List[str]
    medicines_available: List[str]
    medicines_unavailable: List[str]
    last_updated: datetime


# =============================================================================
# Response Schemas (Unified API Format)
# =============================================================================


class ErrorDetail(BaseModel):
    """Error detail for API responses."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel):
    """Unified API response structure."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None


class TriageResponse(BaseModel):
    """Response schema for triage endpoint."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    is_emergency: bool
    urgency: Optional[TriageUrgency] = None
    recommended_facility: Optional[FacilityInfo] = None
    medicine_status: Optional[MedicineAvailability] = None
    patient_message_urdu: str
    audio_url: Optional[str] = None
    reasoning_trace: Optional[str] = None


class FacilityResponse(BaseModel):
    """Response schema for facility search."""

    model_config = ConfigDict(extra="forbid")

    facilities: List[FacilityInfo]
    total_count: int
    search_radius_km: float


# =============================================================================
# Session Schemas
# =============================================================================


class SessionCreateResponse(BaseModel):
    """Response for anonymous session creation."""

    session_id: str
    token: str
    expires_at: datetime


class SessionStatusResponse(BaseModel):
    """Response for session status lookup."""

    session_id: str
    status: str
    created_at: datetime


class TranscribeResponse(BaseModel):
    """Response for voice audio transcription."""

    text: str


