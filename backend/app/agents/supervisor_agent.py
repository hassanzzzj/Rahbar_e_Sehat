"""
Supervisor Agent for orchestrating the multi-agent triage pipeline.
Uses LangGraph to coordinate all 5 agents in a directed workflow.
"""

from typing import Any, Dict, Optional, Protocol
import base64

from langgraph.graph import END, StateGraph

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
from app.agents.graph import TriageState, WorkflowStatus
from app.agents.intake_agent import ConversationState, SymptomIntakeAgent
from app.agents.triage_reasoning_agent import TriageInput, TriageReasoningAgent
from app.core.exceptions import SupervisorError
from app.core.logging import get_logger
from app.integrations.speech_client import SpeechClient
from app.models.schemas import (
    ExtractedSymptoms,
    SafetyCheckResult,
    TriageClassification,
    TriageResponse,
)

logger = get_logger(__name__)


class SupervisorAgent:
    """
    Orchestrates the multi-agent triage pipeline using LangGraph.
    Coordinates all 5 agents and manages workflow state transitions.
    """

    def __init__(
        self,
        symptom_intake: SymptomIntakeAgent,
        safety_escalation: SafetyEscalationAgent,
        triage_reasoning: TriageReasoningAgent,
        facility_matching: FacilityMatchingAgent,
        medicine_availability: MedicineAvailabilityAgent,
        speech_client: Optional[SpeechClient] = None,
    ) -> None:
        """
        Initialize the Supervisor Agent with all downstream agents.

        Args:
            symptom_intake: Agent 1 - extracts symptoms from patient message
            safety_escalation: Agent 2 - checks for emergency red flags
            triage_reasoning: Agent 3 - classifies urgency with RAG grounding
            facility_matching: Agent 4 - finds nearest appropriate facility
            medicine_availability: Agent 5 - checks medicine stock at facility
            speech_client: Optional speech client for Urdu TTS synthesis
        """
        self._symptom_intake = symptom_intake
        self._safety_escalation = safety_escalation
        self._triage_reasoning = triage_reasoning
        self._facility_matching = facility_matching
        self._medicine_availability = medicine_availability
        self._speech_client = speech_client

        # Build the LangGraph workflow
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build the LangGraph StateGraph with all nodes and edges."""
        workflow = StateGraph(TriageState)

        # Add nodes for each agent
        workflow.add_node("run_symptom_intake", self._symptom_intake_node)
        workflow.add_node("run_safety_check", self._safety_check_node)
        workflow.add_node("run_triage_reasoning", self._triage_reasoning_node)
        workflow.add_node("run_facility_matching", self._facility_matching_node)
        workflow.add_node("run_medicine_availability", self._medicine_availability_node)
        workflow.add_node("build_emergency_response", self._emergency_response_node)
        workflow.add_node("build_final_response", self._final_response_node)

        # Define edges
        workflow.set_entry_point("run_symptom_intake")
        workflow.add_edge("run_symptom_intake", "run_safety_check")

        # Conditional edge after safety check: emergency or continue?
        workflow.add_conditional_edges(
            "run_safety_check",
            self._route_after_safety_check,
            {
                "emergency": "build_emergency_response",
                "continue": "run_triage_reasoning",
            },
        )

        # Linear flow for non-emergency cases
        workflow.add_edge("run_triage_reasoning", "run_facility_matching")
        workflow.add_edge("run_facility_matching", "run_medicine_availability")
        workflow.add_edge("run_medicine_availability", "build_final_response")

        # Terminal nodes
        workflow.add_edge("build_emergency_response", END)
        workflow.add_edge("build_final_response", END)

        return workflow.compile()

    async def _symptom_intake_node(self, state: TriageState) -> Dict[str, Any]:
        """Node 1: Extract symptoms from patient message."""
        logger.info("supervisor.symptom_intake_start")

        try:
            conversation = ConversationState(
                patient_message=state["patient_message"],
                history=[],
                language="ur",
            )

            result = await self._symptom_intake.extract_symptoms(conversation)

            return {
                "symptoms": result.symptoms,
                "follow_up_question": result.follow_up_question,
                "needs_follow_up": result.needs_follow_up,
            }

        except Exception as e:
            logger.error("supervisor.symptom_intake_failed", error=str(e))
            raise SupervisorError(
                message=f"Symptom intake failed: {str(e)}",
                details={"node": "symptom_intake"},
            ) from e

    async def _safety_check_node(self, state: TriageState) -> Dict[str, Any]:
        """Node 2: Check for emergency red flags (synchronous)."""
        logger.info("supervisor.safety_check_start")

        try:
            symptoms = state["symptoms"]
            if symptoms is None:
                raise SupervisorError(
                    message="Symptoms not found in state",
                    details={"node": "safety_check"},
                )

            # SafetyEscalationAgent.check_safety is synchronous
            result = self._safety_escalation.check_safety(symptoms)

            return {
                "safety_check": result,
            }

        except SupervisorError:
            raise
        except Exception as e:
            logger.error("supervisor.safety_check_failed", error=str(e))
            raise SupervisorError(
                message=f"Safety check failed: {str(e)}",
                details={"node": "safety_check"},
            ) from e

    def _route_after_safety_check(self, state: TriageState) -> str:
        """Conditional router: emergency short-circuit or continue pipeline."""
        safety_check = state.get("safety_check")

        if safety_check and safety_check.is_emergency:
            logger.warning(
                "supervisor.emergency_detected",
                emergency_type=safety_check.emergency_type,
            )
            return "emergency"

        return "continue"

    async def _triage_reasoning_node(self, state: TriageState) -> Dict[str, Any]:
        """Node 3: Classify urgency with RAG-grounded LLM."""
        logger.info("supervisor.triage_reasoning_start")

        try:
            symptoms = state["symptoms"]
            safety_check = state["safety_check"]

            if symptoms is None or safety_check is None:
                raise SupervisorError(
                    message="Missing required state for triage",
                    details={"node": "triage_reasoning"},
                )

            triage_input = TriageInput(
                symptoms=symptoms,
                safety_check=safety_check,
            )

            result = await self._triage_reasoning.classify(triage_input)

            return {
                "classification": result.classification,
            }

        except SupervisorError:
            raise
        except Exception as e:
            logger.error("supervisor.triage_reasoning_failed", error=str(e))
            raise SupervisorError(
                message=f"Triage reasoning failed: {str(e)}",
                details={"node": "triage_reasoning"},
            ) from e

    async def _facility_matching_node(self, state: TriageState) -> Dict[str, Any]:
        """Node 4: Find nearest appropriate facility."""
        logger.info("supervisor.facility_matching_start")

        try:
            symptoms = state["symptoms"]
            safety_check = state["safety_check"]
            classification = state["classification"]

            if symptoms is None or safety_check is None or classification is None:
                raise SupervisorError(
                    message="Missing required state for facility matching",
                    details={"node": "facility_matching"},
                )

            facility_input = FacilityMatchInput(
                classification=classification,
                safety_check=safety_check,
                symptoms=symptoms,
                latitude=state.get("latitude"),
                longitude=state.get("longitude"),
            )

            result = await self._facility_matching.match(facility_input)

            return {
                "facility_match": result,
            }

        except SupervisorError:
            raise
        except Exception as e:
            logger.error("supervisor.facility_matching_failed", error=str(e))
            raise SupervisorError(
                message=f"Facility matching failed: {str(e)}",
                details={"node": "facility_matching"},
            ) from e

    async def _medicine_availability_node(self, state: TriageState) -> Dict[str, Any]:
        """Node 5: Check medicine availability at recommended facility."""
        logger.info("supervisor.medicine_availability_start")

        try:
            symptoms = state["symptoms"]
            classification = state["classification"]
            facility_match = state["facility_match"]

            if symptoms is None or classification is None or facility_match is None:
                raise SupervisorError(
                    message="Missing required state for medicine check",
                    details={"node": "medicine_availability"},
                )

            # Skip if no facility was recommended
            if facility_match.recommended is None:
                logger.warning("supervisor.no_facility_for_medicine_check")
                return {"medicine_check": None}

            medicine_input = MedicineCheckInput(
                facility_id=facility_match.recommended.facility_id,
                symptoms=symptoms,
                classification=classification,
            )

            result = await self._medicine_availability.check(medicine_input)

            return {
                "medicine_check": result,
            }

        except SupervisorError:
            raise
        except Exception as e:
            logger.error("supervisor.medicine_availability_failed", error=str(e))
            raise SupervisorError(
                message=f"Medicine availability check failed: {str(e)}",
                details={"node": "medicine_availability"},
            ) from e

    async def _emergency_response_node(self, state: TriageState) -> Dict[str, Any]:
        """Build emergency response when safety check detects emergency."""
        logger.warning("supervisor.building_emergency_response")

        safety_check = state["safety_check"]
        symptoms = state["symptoms"]

        return {
            "status": WorkflowStatus.EMERGENCY,
            "error_message": None,
        }

    async def _final_response_node(self, state: TriageState) -> Dict[str, Any]:
        """Build final response after successful pipeline completion."""
        logger.info("supervisor.building_final_response")

        return {
            "status": WorkflowStatus.COMPLETED,
            "error_message": None,
        }

    async def run(
        self,
        patient_message: str,
        session_id: str,
        phone_number: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> TriageState:
        """
        Execute the complete triage workflow.

        Args:
            patient_message: Free-form patient message (Urdu/English)
            session_id: Unique session identifier
            phone_number: Optional patient phone number
            latitude: Optional patient latitude
            longitude: Optional patient longitude

        Returns:
            TriageState with all agent outputs populated

        Raises:
            SupervisorError: If any agent fails during execution
        """
        logger.info("supervisor.workflow_start", session_id=session_id)

        initial_state: TriageState = {
            "patient_message": patient_message,
            "session_id": session_id,
            "phone_number": phone_number,
            "latitude": latitude,
            "longitude": longitude,
            "status": WorkflowStatus.IN_PROGRESS,
            "needs_follow_up": False,
            "error_message": None,
        }

        try:
            final_state = await self._graph.ainvoke(initial_state)
            logger.info(
                "supervisor.workflow_complete",
                session_id=session_id,
                status=final_state.get("status"),
            )
            return final_state

        except SupervisorError:
            raise
        except Exception as e:
            logger.error(
                "supervisor.workflow_failed",
                session_id=session_id,
                error=str(e),
            )
            raise SupervisorError(
                message=f"Workflow execution failed: {str(e)}",
                details={"session_id": session_id},
            ) from e

    async def build_triage_response(self, state: TriageState) -> TriageResponse:
        """
        Convert workflow state to API response format.

        Args:
            state: Final workflow state after execution

        Returns:
            TriageResponse ready for API output
        """
        symptoms = state.get("symptoms")
        safety_check = state.get("safety_check")
        classification = state.get("classification")
        facility_match = state.get("facility_match")
        medicine_check = state.get("medicine_check")

        # Build facility info if available
        recommended_facility = None
        if facility_match and facility_match.recommended:
            recommended_facility = facility_match.recommended

        # Build medicine status if available
        medicine_status = None
        if medicine_check:
            medicine_status = medicine_check.availability

        # Determine urgency (None for emergencies)
        urgency = None
        if classification and not (safety_check and safety_check.is_emergency):
            urgency = classification.urgency

        # Build patient message (use primary symptom as fallback)
        patient_message_urdu = ""
        if symptoms:
            patient_message_urdu = symptoms.primary_symptom

        # Synthesise Urdu audio response if TTS is configured and message exists
        audio_url: Optional[str] = None
        if self._speech_client and patient_message_urdu:
            try:
                audio_bytes = await self._speech_client.synthesize_speech(
                    patient_message_urdu, language="ur"
                )
                if audio_bytes:
                    b64 = base64.b64encode(audio_bytes).decode("utf-8")
                    audio_url = f"data:audio/mpeg;base64,{b64}"
                    logger.info("supervisor.tts_synthesized", bytes=len(audio_bytes))
            except Exception as tts_err:
                logger.warning("supervisor.tts_failed", error=str(tts_err))

        return TriageResponse(
            session_id=state.get("session_id", ""),
            is_emergency=safety_check.is_emergency if safety_check else False,
            urgency=urgency,
            recommended_facility=recommended_facility,
            medicine_status=medicine_status,
            patient_message_urdu=patient_message_urdu,
            audio_url=audio_url,
            reasoning_trace=classification.reasoning_trace if classification else None,
        )
