"""
Integration test: Malformed input handling.
Tests that the pipeline gracefully handles invalid or unexpected inputs.
"""

import pytest

from app.agents.safety_escalation_agent import SafetyEscalationAgent
from app.models.schemas import AgeGroup, ExtractedSymptoms, SymptomSeverity


class TestMalformedInput:
    """Integration tests for malformed input handling."""

    def test_empty_associated_symptoms_handled(self):
        """Pipeline should handle empty associated symptoms without crashing."""
        agent = SafetyEscalationAgent()
        symptoms = ExtractedSymptoms(
            primary_symptom="headache",
            associated_symptoms=[],
            severity=SymptomSeverity.MILD,
        )

        result = agent.check_safety(symptoms)
        assert isinstance(result.is_emergency, bool)

    def test_unrecognized_symptoms_pass_safety(self):
        """Unrecognized symptoms should pass safety check (no red flags)."""
        agent = SafetyEscalationAgent()
        symptoms = ExtractedSymptoms(
            primary_symptom="random unknown symptom",
            associated_symptoms=["another unknown symptom"],
            severity=SymptomSeverity.MODERATE,
        )

        result = agent.check_safety(symptoms)
        assert result.is_emergency is False
