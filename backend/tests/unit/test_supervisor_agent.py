"""
Unit tests for the Supervisor Agent.
Tests the LangGraph orchestration of the multi-agent triage pipeline.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.facility_matching_agent import (
    FacilityMatchInput,
    FacilityMatchOutput,
    FacilityMatchingAgent,
)
from app.agents.medicine_availability_agent import (
    MedicineAvailabilityAgent,
    MedicineCheckInput,
    MedicineCheckOutput,
)
from app.agents.safety_escalation_agent import SafetyEscalationAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.graph import TriageState, WorkflowStatus
from app.agents.intake_agent import ConversationState, IntakeResult
from app.agents.triage_reasoning_agent import TriageInput, TriageOutput
from app.core.exceptions import SupervisorError
from app.models.schemas import (
    AgeGroup,
    ExtractedSymptoms,
    FacilityInfo,
    FacilityType,
    MedicineAvailability,
    SafetyCheckResult,
    SymptomSeverity,
    TriageClassification,
    TriageUrgency,
)


# ---------------------------------------------------------------------------
# Mock Agents
# ---------------------------------------------------------------------------


class MockSymptomIntakeAgent:
    """Mock symptom intake agent for testing."""

    def __init__(self, result: Optional[IntakeResult] = None, error: Exception = None):
        self._result = result or self._default_result()
        self._error = error

    def _default_result(self) -> IntakeResult:
        symptoms = ExtractedSymptoms(
            primary_symptom="headache",
            severity=SymptomSeverity.MILD,
            age_group=AgeGroup.ADULT,
        )
        return IntakeResult(
            symptoms=symptoms,
            follow_up_question=None,
            raw_llm_response=None,
            llm_attempts=1,
            extraction_source="llm",
            needs_follow_up=False,
        )

    async def extract_symptoms(self, state: ConversationState) -> IntakeResult:
        if self._error:
            raise self._error
        return self._result


class MockTriageReasoningAgent:
    """Mock triage reasoning agent for testing."""

    def __init__(self, result: Optional[TriageOutput] = None, error: Exception = None):
        self._result = result or self._default_result()
        self._error = error

    def _default_result(self) -> TriageOutput:
        classification = TriageClassification(
            urgency=TriageUrgency.ROUTINE,
            confidence_score=0.85,
            reasoning_trace="Test reasoning trace",
            source_documents=["doc1.pdf"],
            recommended_care_tier=FacilityType.BHU,
        )
        return TriageOutput(
            classification=classification,
            retrieved_protocol_count=1,
            llm_attempts=1,
            reasoning_source="llm",
        )

    async def classify(self, triage_input: TriageInput) -> TriageOutput:
        if self._error:
            raise self._error
        return self._result


class MockFacilityMatchingAgent:
    """Mock facility matching agent for testing."""

    def __init__(
        self, result: Optional[FacilityMatchOutput] = None, error: Exception = None
    ):
        self._result = result or self._default_result()
        self._error = error

    def _default_result(self) -> FacilityMatchOutput:
        facility = FacilityInfo(
            facility_id="BHU-001",
            name="Test BHU",
            facility_type=FacilityType.BHU,
            address="Test Address",
            distance_km=2.5,
            services_available=["general_consultation"],
            emergency_capable=False,
            phone_number="+92-000-0000",
        )
        return FacilityMatchOutput(
            recommended=facility,
            alternatives=[],
            search_radius_km=50.0,
            total_candidates=1,
            match_reason="Nearest BHU",
        )

    async def match(self, input_data: FacilityMatchInput) -> FacilityMatchOutput:
        if self._error:
            raise self._error
        return self._result


class MockMedicineAvailabilityAgent:
    """Mock medicine availability agent for testing."""

    def __init__(
        self, result: Optional[MedicineCheckOutput] = None, error: Exception = None
    ):
        self._result = result or self._default_result()
        self._error = error

    def _default_result(self) -> MedicineCheckOutput:
        from datetime import datetime

        availability = MedicineAvailability(
            facility_id="BHU-001",
            medicines_checked=["Paracetamol 500mg"],
            medicines_available=["Paracetamol 500mg"],
            medicines_unavailable=[],
            last_updated=datetime.now(),
        )
        return MedicineCheckOutput(
            availability=availability,
            medicines_needed=["Paracetamol 500mg"],
            all_available=True,
            missing_critical=False,
        )

    async def check(self, input_data: MedicineCheckInput) -> MedicineCheckOutput:
        if self._error:
            raise self._error
        return self._result


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_symptom_intake():
    return MockSymptomIntakeAgent()


@pytest.fixture
def mock_safety_escalation():
    return SafetyEscalationAgent()


@pytest.fixture
def mock_triage_reasoning():
    return MockTriageReasoningAgent()


@pytest.fixture
def mock_facility_matching():
    return MockFacilityMatchingAgent()


@pytest.fixture
def mock_medicine_availability():
    return MockMedicineAvailabilityAgent()


@pytest.fixture
def supervisor(
    mock_symptom_intake,
    mock_safety_escalation,
    mock_triage_reasoning,
    mock_facility_matching,
    mock_medicine_availability,
):
    return SupervisorAgent(
        symptom_intake=mock_symptom_intake,
        safety_escalation=mock_safety_escalation,
        triage_reasoning=mock_triage_reasoning,
        facility_matching=mock_facility_matching,
        medicine_availability=mock_medicine_availability,
    )


# ---------------------------------------------------------------------------
# Happy Path Tests
# ---------------------------------------------------------------------------


class TestSupervisorHappyPath:
    """Tests for successful workflow execution."""

    async def test_complete_workflow_routine_case(self, supervisor):
        """Test complete workflow for a routine (non-emergency) case."""
        state = await supervisor.run(
            patient_message="I have a headache",
            session_id="test-session-123",
            latitude=31.5204,
            longitude=74.3587,
        )

        assert state["status"] == WorkflowStatus.COMPLETED
        assert state["session_id"] == "test-session-123"
        assert state["symptoms"] is not None
        assert state["safety_check"] is not None
        assert state["classification"] is not None
        assert state["facility_match"] is not None
        assert state["medicine_check"] is not None

    async def test_workflow_with_phone_number(self, supervisor):
        """Test workflow includes phone number in state."""
        state = await supervisor.run(
            patient_message="Fever and cough",
            session_id="test-session-456",
            phone_number="+923001234567",
        )

        assert state["phone_number"] == "+923001234567"
        assert state["status"] == WorkflowStatus.COMPLETED

    async def test_workflow_without_location(self, supervisor):
        """Test workflow works without latitude/longitude."""
        state = await supervisor.run(
            patient_message="Stomach pain",
            session_id="test-session-789",
        )

        assert state["latitude"] is None
        assert state["longitude"] is None
        assert state["status"] == WorkflowStatus.COMPLETED

    async def test_emergency_short_circuit(self):
        """Test that emergency cases skip triage and facility matching."""
        # Create symptoms that will trigger emergency
        emergency_symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.ELDERLY,
            associated_symptoms=["shortness of breath", "sweating"],
        )

        mock_intake = MockSymptomIntakeAgent(
            result=IntakeResult(
                symptoms=emergency_symptoms,
                follow_up_question=None,
                raw_llm_response=None,
                llm_attempts=1,
                extraction_source="llm",
                needs_follow_up=False,
            )
        )

        supervisor = SupervisorAgent(
            symptom_intake=mock_intake,
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=MockFacilityMatchingAgent(),
            medicine_availability=MockMedicineAvailabilityAgent(),
        )

        state = await supervisor.run(
            patient_message="Severe chest pain and difficulty breathing",
            session_id="emergency-session",
        )

        assert state["status"] == WorkflowStatus.EMERGENCY
        assert state["safety_check"].is_emergency is True
        # Triage and facility matching should not run in emergency path
        assert state.get("classification") is None
        assert state.get("facility_match") is None


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestSupervisorErrorHandling:
    """Tests for error handling and failure modes."""

    async def test_symptom_intake_failure_raises_supervisor_error(self):
        """Test that symptom intake failure raises SupervisorError."""
        mock_intake = MockSymptomIntakeAgent(
            error=RuntimeError("LLM unavailable")
        )

        supervisor = SupervisorAgent(
            symptom_intake=mock_intake,
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=MockFacilityMatchingAgent(),
            medicine_availability=MockMedicineAvailabilityAgent(),
        )

        with pytest.raises(SupervisorError) as exc_info:
            await supervisor.run(
                patient_message="Test message",
                session_id="error-session",
            )

        assert "Symptom intake failed" in str(exc_info.value)
        assert exc_info.value.details["node"] == "symptom_intake"

    async def test_triage_reasoning_failure_raises_supervisor_error(self):
        """Test that triage reasoning failure raises SupervisorError."""
        mock_triage = MockTriageReasoningAgent(
            error=RuntimeError("RAG retrieval failed")
        )

        supervisor = SupervisorAgent(
            symptom_intake=MockSymptomIntakeAgent(),
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=mock_triage,
            facility_matching=MockFacilityMatchingAgent(),
            medicine_availability=MockMedicineAvailabilityAgent(),
        )

        with pytest.raises(SupervisorError) as exc_info:
            await supervisor.run(
                patient_message="Test message",
                session_id="error-session",
            )

        assert "Triage reasoning failed" in str(exc_info.value)
        assert exc_info.value.details["node"] == "triage_reasoning"

    async def test_facility_matching_failure_raises_supervisor_error(self):
        """Test that facility matching failure raises SupervisorError."""
        mock_facility = MockFacilityMatchingAgent(
            error=RuntimeError("No facilities found")
        )

        supervisor = SupervisorAgent(
            symptom_intake=MockSymptomIntakeAgent(),
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=mock_facility,
            medicine_availability=MockMedicineAvailabilityAgent(),
        )

        with pytest.raises(SupervisorError) as exc_info:
            await supervisor.run(
                patient_message="Test message",
                session_id="error-session",
            )

        assert "Facility matching failed" in str(exc_info.value)
        assert exc_info.value.details["node"] == "facility_matching"

    async def test_medicine_availability_failure_raises_supervisor_error(self):
        """Test that medicine availability failure raises SupervisorError."""
        mock_medicine = MockMedicineAvailabilityAgent(
            error=RuntimeError("Inventory unavailable")
        )

        supervisor = SupervisorAgent(
            symptom_intake=MockSymptomIntakeAgent(),
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=MockFacilityMatchingAgent(),
            medicine_availability=mock_medicine,
        )

        with pytest.raises(SupervisorError) as exc_info:
            await supervisor.run(
                patient_message="Test message",
                session_id="error-session",
            )

        assert "Medicine availability check failed" in str(exc_info.value)
        assert exc_info.value.details["node"] == "medicine_availability"


# ---------------------------------------------------------------------------
# Response Building Tests
# ---------------------------------------------------------------------------


class TestSupervisorResponseBuilding:
    """Tests for building TriageResponse from workflow state."""

    async def test_build_triage_response_routine_case(self, supervisor):
        """Test response building for routine case."""
        state = await supervisor.run(
            patient_message="Headache",
            session_id="response-test",
        )

        response = await supervisor.build_triage_response(state)

        assert response.session_id == "response-test"
        assert response.is_emergency is False
        assert response.urgency == TriageUrgency.ROUTINE
        assert response.recommended_facility is not None
        assert response.recommended_facility.facility_id == "BHU-001"
        assert response.medicine_status is not None
        assert response.patient_message_urdu == "headache"
        assert response.reasoning_trace == "Test reasoning trace"

    async def test_build_triage_response_with_tts_audio(self):
        """Test that audio_url is populated when a speech client returns audio bytes.

        Regression test: build_triage_response previously called
        asyncio.get_event_loop().run_until_complete(...) from within an
        already-running event loop, which raised RuntimeError that was
        silently swallowed, leaving audio_url always None.
        """
        fake_speech_client = AsyncMock()
        fake_speech_client.synthesize_speech.return_value = b"fake-mp3-bytes"

        supervisor = SupervisorAgent(
            symptom_intake=MockSymptomIntakeAgent(),
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=MockFacilityMatchingAgent(),
            medicine_availability=MockMedicineAvailabilityAgent(),
            speech_client=fake_speech_client,
        )

        state = await supervisor.run(
            patient_message="Headache",
            session_id="tts-test",
        )

        response = await supervisor.build_triage_response(state)

        fake_speech_client.synthesize_speech.assert_called_once()
        assert response.audio_url is not None
        assert response.audio_url.startswith("data:audio/mpeg;base64,")

    async def test_build_triage_response_emergency_case(self):
        """Test response building for emergency case."""
        emergency_symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.ELDERLY,
            associated_symptoms=["shortness of breath"],
        )

        mock_intake = MockSymptomIntakeAgent(
            result=IntakeResult(
                symptoms=emergency_symptoms,
                follow_up_question=None,
                raw_llm_response=None,
                llm_attempts=1,
                extraction_source="llm",
                needs_follow_up=False,
            )
        )

        supervisor = SupervisorAgent(
            symptom_intake=mock_intake,
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=MockFacilityMatchingAgent(),
            medicine_availability=MockMedicineAvailabilityAgent(),
        )

        state = await supervisor.run(
            patient_message="Severe chest pain",
            session_id="emergency-response-test",
        )

        response = await supervisor.build_triage_response(state)

        assert response.session_id == "emergency-response-test"
        assert response.is_emergency is True
        assert response.urgency is None  # No urgency for emergencies
        assert response.recommended_facility is None
        assert response.medicine_status is None

    async def test_build_triage_response_no_facility(self):
        """Test response building when no facility is recommended."""
        mock_facility = MockFacilityMatchingAgent(
            result=FacilityMatchOutput(
                recommended=None,
                alternatives=[],
                search_radius_km=50.0,
                total_candidates=0,
                match_reason="No facilities in range",
            )
        )

        supervisor = SupervisorAgent(
            symptom_intake=MockSymptomIntakeAgent(),
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=mock_facility,
            medicine_availability=MockMedicineAvailabilityAgent(),
        )

        state = await supervisor.run(
            patient_message="Test",
            session_id="no-facility-test",
        )

        response = await supervisor.build_triage_response(state)

        assert response.recommended_facility is None
        # Medicine check should be skipped when no facility
        assert response.medicine_status is None


# ---------------------------------------------------------------------------
# State Flow Tests
# ---------------------------------------------------------------------------


class TestSupervisorStateFlow:
    """Tests for state propagation through the workflow."""

    async def test_symptoms_propagate_to_all_agents(self, supervisor):
        """Test that extracted symptoms are available in final state."""
        state = await supervisor.run(
            patient_message="Fever and cough",
            session_id="state-flow-test",
        )

        assert state["symptoms"] is not None
        assert state["symptoms"].primary_symptom == "headache"  # Mock default

    async def test_location_passed_to_facility_matching(self):
        """Test that lat/lng from request reach facility matching agent."""
        captured_input = None

        class CapturingFacilityAgent:
            async def match(self, input_data: FacilityMatchInput) -> FacilityMatchOutput:
                nonlocal captured_input
                captured_input = input_data
                return MockFacilityMatchingAgent()._default_result()

        supervisor = SupervisorAgent(
            symptom_intake=MockSymptomIntakeAgent(),
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=CapturingFacilityAgent(),
            medicine_availability=MockMedicineAvailabilityAgent(),
        )

        await supervisor.run(
            patient_message="Test",
            session_id="location-test",
            latitude=31.5204,
            longitude=74.3587,
        )

        assert captured_input is not None
        assert captured_input.latitude == 31.5204
        assert captured_input.longitude == 74.3587

    async def test_facility_id_passed_to_medicine_check(self):
        """Test that facility_id from matching reaches medicine check."""
        captured_input = None

        class CapturingMedicineAgent:
            async def check(self, input_data: MedicineCheckInput) -> MedicineCheckOutput:
                nonlocal captured_input
                captured_input = input_data
                return MockMedicineAvailabilityAgent()._default_result()

        supervisor = SupervisorAgent(
            symptom_intake=MockSymptomIntakeAgent(),
            safety_escalation=SafetyEscalationAgent(),
            triage_reasoning=MockTriageReasoningAgent(),
            facility_matching=MockFacilityMatchingAgent(),
            medicine_availability=CapturingMedicineAgent(),
        )

        await supervisor.run(
            patient_message="Test",
            session_id="facility-id-test",
        )

        assert captured_input is not None
        assert captured_input.facility_id == "BHU-001"


# ---------------------------------------------------------------------------
# Conditional Routing Tests
# ---------------------------------------------------------------------------


class TestSupervisorConditionalRouting:
    """Tests for conditional edge logic."""

    def test_route_after_safety_check_emergency(self, supervisor):
        """Test routing decision for emergency case."""
        state: TriageState = {
            "safety_check": SafetyCheckResult(
                is_emergency=True,
                red_flags_triggered=["CARDIAC_RED_FLAG"],
                emergency_type="CARDIAC_EMERGENCY",
                immediate_action_required="Call 1122",
            )
        }

        route = supervisor._route_after_safety_check(state)
        assert route == "emergency"

    def test_route_after_safety_check_non_emergency(self, supervisor):
        """Test routing decision for non-emergency case."""
        state: TriageState = {
            "safety_check": SafetyCheckResult(
                is_emergency=False,
                red_flags_triggered=[],
                emergency_type=None,
                immediate_action_required=None,
            )
        }

        route = supervisor._route_after_safety_check(state)
        assert route == "continue"

    def test_route_after_safety_check_missing_safety_check(self, supervisor):
        """Test routing when safety_check is missing (should continue)."""
        state: TriageState = {}

        route = supervisor._route_after_safety_check(state)
        assert route == "continue"
