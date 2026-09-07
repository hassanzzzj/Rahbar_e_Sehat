"""
State schema for the Supervisor Agent workflow.
Defines the data structure that flows through the LangGraph pipeline.
"""

from enum import Enum
from typing import Optional, TypedDict

from app.agents.facility_matching_agent import FacilityMatchOutput
from app.agents.medicine_availability_agent import MedicineCheckOutput
from app.models.schemas import (
    ExtractedSymptoms,
    SafetyCheckResult,
    TriageClassification,
)


class WorkflowStatus(str, Enum):
    """Status of the triage workflow."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    EMERGENCY = "EMERGENCY"
    ERROR = "ERROR"


class TriageState(TypedDict, total=False):
    """
    State that flows through the LangGraph triage pipeline.
    Uses total=False to allow partial state during pipeline execution.
    """

    # Input fields (from API request)
    patient_message: str
    phone_number: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    session_id: str

    # Agent 1 output: Symptom Intake
    symptoms: Optional[ExtractedSymptoms]
    follow_up_question: Optional[str]
    needs_follow_up: bool

    # Agent 2 output: Safety Escalation
    safety_check: Optional[SafetyCheckResult]

    # Agent 3 output: Triage Reasoning
    classification: Optional[TriageClassification]

    # Agent 4 output: Facility Matching
    facility_match: Optional[FacilityMatchOutput]

    # Agent 5 output: Medicine Availability
    medicine_check: Optional[MedicineCheckOutput]

    # Workflow metadata
    status: WorkflowStatus
    error_message: Optional[str]
