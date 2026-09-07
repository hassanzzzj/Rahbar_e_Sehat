"""
Comprehensive unit tests for the Triage Reasoning Agent.

Covers:
- JSON parsing and normalization
- LLM-based triage classification (happy path, retry, fallback)
- Deterministic fallback logic
- RAG integration
- Schema validation
"""

from __future__ import annotations

import json

import pytest

from app.agents.triage_reasoning_agent import (
    TriageInput,
    TriageReasoningAgent,
)
from app.core.exceptions import LLMServiceError, TriageError
from app.models.schemas import (
    AgeGroup,
    ExtractedSymptoms,
    FacilityType,
    SafetyCheckResult,
    SymptomSeverity,
    TriageUrgency,
)
from tests.unit.conftest import FakeLLMClient, FakeRAGRetriever, llm_json, llm_text


# ============================================================================
# Helpers
# ============================================================================


def _make_symptoms(**overrides) -> ExtractedSymptoms:
    """Create an ExtractedSymptoms instance with sensible defaults."""
    defaults = {
        "primary_symptom": "chest pain",
        "secondary_symptoms": ["shortness of breath"],
        "associated_symptoms": ["sweating"],
        "severity": SymptomSeverity.MODERATE,
        "duration_hours": 2.0,
        "age_group": AgeGroup.ADULT,
        "is_pregnant": False,
        "pre_existing_conditions": [],
    }
    defaults.update(overrides)
    return ExtractedSymptoms(**defaults)


def _make_safety(**overrides) -> SafetyCheckResult:
    """Create a SafetyCheckResult with sensible defaults."""
    defaults = {
        "is_emergency": False,
        "red_flags_triggered": [],
    }
    defaults.update(overrides)
    return SafetyCheckResult(**defaults)


def _make_triage_input(symptoms=None, safety=None) -> TriageInput:
    """Create a TriageInput from optional symptoms and safety check."""
    return TriageInput(
        symptoms=symptoms or _make_symptoms(),
        safety_check=safety or _make_safety(),
    )


def _valid_triage_response(**overrides) -> dict:
    """Return a valid triage classification dict."""
    defaults = {
        "urgency": "URGENT",
        "confidence_score": 0.85,
        "reasoning_trace": "Based on chest pain protocol, patient requires urgent evaluation.",
        "recommended_care_tier": "THQ",
        "source_documents": ["emergency_triage.md"],
    }
    defaults.update(overrides)
    return defaults


SAMPLE_PROTOCOLS = [
    {
        "content": "Chest pain with radiation to left arm — EMERGENCY. Refer to tertiary hospital.",
        "score": 0.92,
        "source": "emergency_triage.md",
        "protocol_type": "emergency",
    },
    {
        "content": "Moderate chest pain — URGENT. Refer to THQ for ECG and cardiac enzymes.",
        "score": 0.78,
        "source": "common_symptoms_triage.md",
        "protocol_type": "general",
    },
]


# ============================================================================
# TestTriageParsing
# ============================================================================


class TestTriageParsing:
    """Tests for the LLM response parser."""

    def _agent(self) -> TriageReasoningAgent:
        return TriageReasoningAgent(FakeLLMClient([]), FakeRAGRetriever())

    def test_parse_valid_json(self):
        data = self._agent()._parse_llm_response(
            json.dumps(_valid_triage_response()), ["emergency_triage.md"]
        )
        assert data["urgency"] == "URGENT"
        assert data["confidence_score"] == 0.85

    def test_parse_with_markdown_code_fence(self):
        raw = "```json\n" + json.dumps(_valid_triage_response()) + "\n```"
        data = self._agent()._parse_llm_response(raw, [])
        assert data["urgency"] == "URGENT"

    def test_parse_extracts_json_from_surrounding_text(self):
        raw = (
            "Here is the classification:\n"
            + json.dumps(_valid_triage_response())
            + "\nDone."
        )
        data = self._agent()._parse_llm_response(raw, [])
        assert data["urgency"] == "URGENT"

    def test_parse_normalizes_lowercase_urgency(self):
        resp = _valid_triage_response(urgency="urgent")
        data = self._agent()._parse_llm_response(json.dumps(resp), [])
        assert data["urgency"] == "URGENT"

    def test_parse_normalizes_lowercase_care_tier(self):
        resp = _valid_triage_response(recommended_care_tier="thq")
        data = self._agent()._parse_llm_response(json.dumps(resp), [])
        assert data["recommended_care_tier"] == "THQ"

    def test_parse_normalizes_string_confidence_score(self):
        resp = _valid_triage_response(confidence_score="0.9")
        data = self._agent()._parse_llm_response(json.dumps(resp), [])
        assert data["confidence_score"] == 0.9

    def test_parse_clamps_confidence_score(self):
        resp = _valid_triage_response(confidence_score=1.5)
        data = self._agent()._parse_llm_response(json.dumps(resp), [])
        assert data["confidence_score"] == 1.0

    def test_parse_populates_empty_source_documents(self):
        resp = _valid_triage_response(source_documents=[])
        data = self._agent()._parse_llm_response(
            json.dumps(resp), ["protocol_a.md"]
        )
        assert data["source_documents"] == ["protocol_a.md"]

    def test_parse_normalizes_string_source_documents(self):
        resp = _valid_triage_response(source_documents="single.md")
        data = self._agent()._parse_llm_response(json.dumps(resp), [])
        assert data["source_documents"] == ["single.md"]

    def test_parse_rejects_empty_response(self):
        with pytest.raises(TriageError, match="Empty LLM response"):
            self._agent()._parse_llm_response("", [])

    def test_parse_rejects_no_json_object(self):
        with pytest.raises(TriageError, match="No JSON object"):
            self._agent()._parse_llm_response("just some text without json", [])

    def test_parse_rejects_malformed_json(self):
        with pytest.raises(TriageError, match="Malformed JSON"):
            self._agent()._parse_llm_response('{"urgency": "URGENT",}', [])

    def test_parse_rejects_json_array(self):
        with pytest.raises(TriageError, match="not an object"):
            self._agent()._parse_llm_response("[1, 2, 3]", [])

    def test_parse_rejects_invalid_urgency(self):
        resp = _valid_triage_response(urgency="CRITICAL")
        with pytest.raises(TriageError, match="schema validation"):
            data = self._agent()._parse_llm_response(json.dumps(resp), [])
            # Validate to trigger schema error
            self._agent()._validate_extraction(data)


# ============================================================================
# TestTriageClassification
# ============================================================================


class TestTriageClassification:
    """Tests for the full classify() method."""

    @pytest.mark.asyncio
    async def test_happy_path_emergency(self):
        symptoms = _make_symptoms(severity=SymptomSeverity.SEVERE)
        safety = _make_safety(is_emergency=True, red_flags_triggered=["chest pain"])
        resp = _valid_triage_response(urgency="EMERGENCY", recommended_care_tier="EMERGENCY")

        llm = FakeLLMClient([llm_json(resp)])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(TriageInput(symptoms, safety))

        assert result.classification.urgency == TriageUrgency.EMERGENCY
        assert result.classification.recommended_care_tier == FacilityType.EMERGENCY
        assert result.reasoning_source == "llm"
        assert result.llm_attempts == 1
        assert result.retrieved_protocol_count == 2

    @pytest.mark.asyncio
    async def test_happy_path_routine(self):
        symptoms = _make_symptoms(
            primary_symptom="mild headache",
            severity=SymptomSeverity.MILD,
        )
        resp = _valid_triage_response(
            urgency="ROUTINE",
            recommended_care_tier="BHU",
            confidence_score=0.7,
        )

        llm = FakeLLMClient([llm_json(resp)])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(_make_triage_input(symptoms))

        assert result.classification.urgency == TriageUrgency.ROUTINE
        assert result.reasoning_source == "llm"

    @pytest.mark.asyncio
    async def test_retry_on_first_parse_failure(self):
        resp = _valid_triage_response()
        llm = FakeLLMClient([llm_text("not valid json"), llm_json(resp)])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(_make_triage_input())

        assert result.classification.urgency == TriageUrgency.URGENT
        assert result.reasoning_source == "retry"
        assert result.llm_attempts == 2

    @pytest.mark.asyncio
    async def test_fallback_after_both_llm_attempts_fail(self):
        llm = FakeLLMClient([llm_text("garbage"), llm_text("more garbage")])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(_make_triage_input())

        assert result.classification.urgency == TriageUrgency.URGENT
        assert result.reasoning_source == "fallback"
        assert result.llm_attempts == 2

    @pytest.mark.asyncio
    async def test_fallback_after_llm_service_error(self):
        llm = FakeLLMClient([
            LLMServiceError("LLM unavailable"),
            LLMServiceError("still unavailable"),
        ])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(_make_triage_input())

        assert result.classification.urgency == TriageUrgency.URGENT
        assert result.reasoning_source == "fallback"

    @pytest.mark.asyncio
    async def test_empty_llm_text_triggers_retry(self):
        resp = _valid_triage_response()
        llm = FakeLLMClient([llm_text(""), llm_json(resp)])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(_make_triage_input())

        assert result.reasoning_source == "retry"
        assert result.llm_attempts == 2

    @pytest.mark.asyncio
    async def test_retriever_called_with_symptom_query(self):
        resp = _valid_triage_response()
        llm = FakeLLMClient([llm_json(resp)])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        symptoms = _make_symptoms(
            primary_symptom="chest pain",
            secondary_symptoms=["dizziness"],
            associated_symptoms=["nausea"],
        )
        await agent.classify(_make_triage_input(symptoms))

        assert len(retriever.calls) == 1
        query = retriever.calls[0]["query"]
        assert "chest pain" in query
        assert "dizziness" in query

    @pytest.mark.asyncio
    async def test_empty_retrieval_still_works(self):
        resp = _valid_triage_response()
        llm = FakeLLMClient([llm_json(resp)])
        retriever = FakeRAGRetriever([])  # No protocols
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(_make_triage_input())

        assert result.classification.urgency == TriageUrgency.URGENT
        assert result.retrieved_protocol_count == 0

    @pytest.mark.asyncio
    async def test_llm_prompt_contains_patient_data_tags(self):
        resp = _valid_triage_response()
        llm = FakeLLMClient([llm_json(resp)])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        await agent.classify(_make_triage_input())

        prompt = llm.calls[0]["prompt"]
        assert "<patient_data>" in prompt
        assert "</patient_data>" in prompt
        assert "<clinical_protocols>" in prompt

    @pytest.mark.asyncio
    async def test_self_care_classification(self):
        symptoms = _make_symptoms(
            primary_symptom="mild cold",
            severity=SymptomSeverity.MILD,
        )
        resp = _valid_triage_response(
            urgency="SELF_CARE",
            recommended_care_tier="BHU",
            confidence_score=0.9,
        )

        llm = FakeLLMClient([llm_json(resp)])
        retriever = FakeRAGRetriever(SAMPLE_PROTOCOLS)
        agent = TriageReasoningAgent(llm, retriever)

        result = await agent.classify(_make_triage_input(symptoms))

        assert result.classification.urgency == TriageUrgency.SELF_CARE


# ============================================================================
# TestDeterministicFallback
# ============================================================================


class TestDeterministicFallback:
    """Tests for the rule-based deterministic fallback."""

    def test_emergency_flag_triggers_emergency(self):
        symptoms = _make_symptoms()
        safety = _make_safety(is_emergency=True)

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "EMERGENCY"
        assert result["recommended_care_tier"] == "EMERGENCY"

    def test_severe_symptoms_trigger_urgent(self):
        symptoms = _make_symptoms(severity=SymptomSeverity.SEVERE)
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "URGENT"
        assert result["recommended_care_tier"] == "THQ"

    def test_infant_gets_urgent(self):
        symptoms = _make_symptoms(age_group=AgeGroup.INFANT)
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "URGENT"

    def test_elderly_gets_urgent(self):
        symptoms = _make_symptoms(age_group=AgeGroup.ELDERLY)
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "URGENT"

    def test_pregnant_gets_urgent(self):
        symptoms = _make_symptoms(is_pregnant=True)
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "URGENT"

    def test_mild_adult_no_flags_gets_routine(self):
        symptoms = _make_symptoms(
            severity=SymptomSeverity.MILD,
            age_group=AgeGroup.ADULT,
            is_pregnant=False,
        )
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "ROUTINE"
        assert result["recommended_care_tier"] == "BHU"

    def test_moderate_adult_defaults_urgent(self):
        """Moderate severity without clear rules defaults to URGENT (never under-triage)."""
        symptoms = _make_symptoms(
            severity=SymptomSeverity.MODERATE,
            age_group=AgeGroup.ADULT,
            is_pregnant=False,
        )
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "URGENT"

    def test_confidence_score_is_half(self):
        symptoms = _make_symptoms()
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["confidence_score"] == 0.5

    def test_reasoning_trace_mentions_fallback(self):
        symptoms = _make_symptoms()
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert "fallback" in result["reasoning_trace"].lower()
        assert "under-triage" in result["reasoning_trace"].lower()

    def test_source_documents_preserved(self):
        symptoms = _make_symptoms()
        safety = _make_safety()
        docs = ["protocol_a.md", "protocol_b.md"]

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, docs)

        assert result["source_documents"] == docs

    def test_fallback_passes_schema_validation(self):
        """The fallback output must validate against TriageClassification."""
        symptoms = _make_symptoms()
        safety = _make_safety()

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])
        from app.models.schemas import TriageClassification
        classification = TriageClassification.model_validate(result)
        assert classification.urgency is not None

    def test_emergency_overrides_severe(self):
        """If safety check says emergency, it wins over severity alone."""
        symptoms = _make_symptoms(severity=SymptomSeverity.SEVERE)
        safety = _make_safety(is_emergency=True)

        result = TriageReasoningAgent._deterministic_fallback(symptoms, safety, [])

        assert result["urgency"] == "EMERGENCY"
