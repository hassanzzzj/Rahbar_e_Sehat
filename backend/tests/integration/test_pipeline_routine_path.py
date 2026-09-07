"""
Integration test: Routine triage path through the full pipeline.
Tests that non-emergency cases proceed through all agents correctly.
"""

import pytest

from app.agents.safety_escalation_agent import SafetyEscalationAgent
from app.models.schemas import AgeGroup, ExtractedSymptoms, SymptomSeverity


class TestRoutinePath:
    """Integration tests for standard triage path (non-emergency)."""

    def test_mild_symptoms_pass_safety_check(self):
        """Mild symptoms should pass safety escalation and proceed to triage."""
        agent = SafetyEscalationAgent()
        symptoms = ExtractedSymptoms(
            primary_symptom="mild headache",
            associated_symptoms=["fatigue"],
            severity=SymptomSeverity.MILD,
            age_group=AgeGroup.ADULT,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is False
        assert len(result.red_flags_triggered) == 0
        assert result.emergency_type is None
        assert result.immediate_action_required is None

    def test_moderate_symptoms_pass_safety_check(self):
        """Moderate symptoms should pass safety escalation and proceed to triage."""
        agent = SafetyEscalationAgent()
        symptoms = ExtractedSymptoms(
            primary_symptom="stomach pain",
            associated_symptoms=["nausea", "loss of appetite"],
            severity=SymptomSeverity.MODERATE,
            age_group=AgeGroup.ADULT,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is False
