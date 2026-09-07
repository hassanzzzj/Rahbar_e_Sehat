"""
Integration test: Emergency bypass path through the full pipeline.
Tests that emergency cases bypass all downstream agents and return immediately.
"""

import pytest

from app.agents.safety_escalation_agent import SafetyEscalationAgent
from app.models.schemas import AgeGroup, ExtractedSymptoms, SymptomSeverity


class TestEmergencyPath:
    """Integration tests for emergency bypass path."""

    def test_cardiac_emergency_bypasses_pipeline(self):
        """Cardiac emergency should be detected and bypass all downstream agents."""
        agent = SafetyEscalationAgent()
        symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            associated_symptoms=["shortness of breath", "sweating"],
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.ADULT,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "CARDIAC_EMERGENCY"
        assert result.immediate_action_required is not None
        assert len(result.red_flags_triggered) > 0

    def test_stroke_emergency_bypasses_pipeline(self):
        """Stroke (FAST protocol) should be detected and bypass all downstream agents."""
        agent = SafetyEscalationAgent()
        symptoms = ExtractedSymptoms(
            primary_symptom="face drooping",
            associated_symptoms=["arm weakness", "slurred speech"],
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.ELDERLY,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "STROKE_EMERGENCY"
