"""
Comprehensive unit tests for Safety Escalation Agent.

REQUIREMENT: 100% branch coverage - every red-flag rule must have both
positive (triggers emergency) and negative (does not trigger) test cases.

This file is critical for system safety. Any test failures here block deployment.
"""

import pytest

from app.agents.safety_escalation_agent import SafetyEscalationAgent
from app.models.schemas import (
    AgeGroup,
    ExtractedSymptoms,
    SafetyCheckResult,
    SymptomSeverity,
)


class TestSafetyEscalationAgent:
    """Test suite for SafetyEscalationAgent."""

    @pytest.fixture
    def agent(self) -> SafetyEscalationAgent:
        """Provide agent instance."""
        return SafetyEscalationAgent()

    @pytest.fixture
    def non_emergency_symptoms(self) -> ExtractedSymptoms:
        """Symptoms that should NOT trigger emergency."""
        return ExtractedSymptoms(
            primary_symptom="mild headache",
            secondary_symptoms=["fatigue"],
            duration_hours=12.0,
            severity=SymptomSeverity.MILD,
            age_group=AgeGroup.ADULT,
            is_pregnant=False,
            pre_existing_conditions=[],
            associated_symptoms=["slight nausea"],
        )

    # =========================================================================
    # BASELINE TESTS
    # =========================================================================

    def test_non_emergency_returns_no_emergency(
        self, agent: SafetyEscalationAgent, non_emergency_symptoms: ExtractedSymptoms
    ):
        """Non-emergency symptoms should not trigger emergency flag."""
        result = agent.check_safety(non_emergency_symptoms)

        assert isinstance(result, SafetyCheckResult)
        assert result.is_emergency is False
        assert len(result.red_flags_triggered) == 0
        assert result.emergency_type is None
        assert result.immediate_action_required is None

    def test_emergency_returns_correct_structure(self, agent: SafetyEscalationAgent):
        """Emergency case should return complete result structure."""
        symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            associated_symptoms=["shortness of breath"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert len(result.red_flags_triggered) > 0
        assert result.emergency_type is not None
        assert result.immediate_action_required is not None

    # =========================================================================
    # CARDIAC RED FLAG TESTS
    # =========================================================================

    def test_cardiac_chest_pain_with_arm_pain_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Chest pain with radiating arm pain should trigger cardiac emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            associated_symptoms=["left arm pain", "sweating"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("cardiac" in flag.lower() or "chest" in flag.lower() for flag in result.red_flags_triggered)
        assert result.emergency_type == "CARDIAC_EMERGENCY"

    def test_cardiac_chest_pain_with_jaw_pain_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Chest pain with jaw pain should trigger cardiac emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="seene mein dard",  # Urdu: chest pain
            associated_symptoms=["jaw pain"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "CARDIAC_EMERGENCY"

    def test_cardiac_chest_pain_with_sob_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Chest pain with shortness of breath should trigger cardiac emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="chest tightness",
            associated_symptoms=["shortness of breath"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "CARDIAC_EMERGENCY"

    def test_cardiac_chest_pain_with_sweating_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Chest pain with cold sweating should trigger cardiac emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            associated_symptoms=["cold sweat"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "CARDIAC_EMERGENCY"

    def test_chest_pain_alone_does_not_trigger_cardiac_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Chest pain without associated symptoms should NOT trigger cardiac emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="mild chest pain",
            associated_symptoms=[],
            severity=SymptomSeverity.MILD,
        )

        result = agent.check_safety(symptoms)

        # Should not trigger cardiac emergency (may trigger other flags)
        cardiac_flags = [f for f in result.red_flags_triggered if "cardiac" in f.lower() or "chest" in f.lower()]
        assert len(cardiac_flags) == 0

    def test_arm_pain_without_chest_pain_does_not_trigger_cardiac(
        self, agent: SafetyEscalationAgent
    ):
        """Arm pain without chest pain should NOT trigger cardiac emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="arm pain",
            associated_symptoms=["shoulder pain"],
            severity=SymptomSeverity.MODERATE,
        )

        result = agent.check_safety(symptoms)

        assert result.emergency_type != "CARDIAC_EMERGENCY"

    # =========================================================================
    # STROKE RED FLAG TESTS (FAST PROTOCOL)
    # =========================================================================

    def test_stroke_facial_droop_triggers_flag(self, agent: SafetyEscalationAgent):
        """Facial droop should trigger FAST stroke flag."""
        symptoms = ExtractedSymptoms(
            primary_symptom="face drooping",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("fast" in flag.lower() or "facial" in flag.lower() for flag in result.red_flags_triggered)

    def test_stroke_arm_weakness_triggers_flag(self, agent: SafetyEscalationAgent):
        """Arm weakness should trigger FAST stroke flag."""
        symptoms = ExtractedSymptoms(
            primary_symptom="arm weakness",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("fast" in flag.lower() or "arm" in flag.lower() for flag in result.red_flags_triggered)

    def test_stroke_speech_difficulty_triggers_flag(self, agent: SafetyEscalationAgent):
        """Speech difficulty should trigger FAST stroke flag."""
        symptoms = ExtractedSymptoms(
            primary_symptom="slurred speech",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("fast" in flag.lower() or "speech" in flag.lower() for flag in result.red_flags_triggered)

    def test_stroke_multiple_fast_criteria_triggers_high_suspicion(
        self, agent: SafetyEscalationAgent
    ):
        """Multiple FAST criteria should trigger high stroke suspicion."""
        symptoms = ExtractedSymptoms(
            primary_symptom="face drooping",
            associated_symptoms=["arm weakness", "slurred speech"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("multiple fast" in flag.lower() or "stroke suspicion" in flag.lower() for flag in result.red_flags_triggered)
        assert result.emergency_type == "STROKE_EMERGENCY"

    def test_stroke_urdu_symptoms_trigger_flag(self, agent: SafetyEscalationAgent):
        """Urdu stroke symptoms should trigger FAST flag."""
        symptoms = ExtractedSymptoms(
            primary_symptom="munh tedha",  # Urdu: facial droop
            associated_symptoms=["baazu mein kamzori"],  # Urdu: arm weakness
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "STROKE_EMERGENCY"

    def test_mild_arm_pain_does_not_trigger_stroke(self, agent: SafetyEscalationAgent):
        """Mild arm pain without other FAST criteria should not trigger stroke."""
        symptoms = ExtractedSymptoms(
            primary_symptom="mild arm soreness",
            associated_symptoms=[],
            severity=SymptomSeverity.MILD,
        )

        result = agent.check_safety(symptoms)

        stroke_flags = [f for f in result.red_flags_triggered if "stroke" in f.lower() or "fast" in f.lower()]
        # May have other flags, but not stroke-specific
        assert result.emergency_type != "STROKE_EMERGENCY" or len(stroke_flags) == 0

    # =========================================================================
    # BLEEDING RED FLAG TESTS
    # =========================================================================

    def test_severe_bleeding_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Severe bleeding should trigger hemorrhage emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="severe bleeding",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("bleeding" in flag.lower() for flag in result.red_flags_triggered)
        assert result.emergency_type == "HEMORRHAGE_EMERGENCY"

    def test_uncontrolled_bleeding_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Uncontrolled bleeding should trigger hemorrhage emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="bleeding not stopping",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "HEMORRHAGE_EMERGENCY"

    def test_urdu_bleeding_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Urdu bleeding description should trigger hemorrhage emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="ziada khoon behna",  # Urdu: excessive bleeding
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "HEMORRHAGE_EMERGENCY"

    def test_mild_bleeding_does_not_trigger_emergency(self, agent: SafetyEscalationAgent):
        """Mild bleeding (e.g., small cut) should not trigger hemorrhage emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="small cut on finger",
            associated_symptoms=["minor bleeding"],
            severity=SymptomSeverity.MILD,
        )

        result = agent.check_safety(symptoms)

        # Should not trigger hemorrhage emergency
        assert result.emergency_type != "HEMORRHAGE_EMERGENCY"

    # =========================================================================
    # RESPIRATORY RED FLAG TESTS
    # =========================================================================

    def test_severe_sob_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Severe shortness of breath should trigger respiratory emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="cannot breathe",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("respiratory" in flag.lower() or "breathing" in flag.lower() for flag in result.red_flags_triggered)
        assert result.emergency_type == "RESPIRATORY_EMERGENCY"

    def test_sob_with_chest_pain_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Shortness of breath with chest pain should trigger respiratory emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="shortness of breath",
            associated_symptoms=["chest pain"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        # May trigger both cardiac and respiratory
        assert result.emergency_type in ["RESPIRATORY_EMERGENCY", "CARDIAC_EMERGENCY"]

    def test_urdu_respiratory_distress_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Urdu respiratory distress should trigger emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="saans bilkul nahi aa rahi",  # Urdu: cannot breathe at all
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "RESPIRATORY_EMERGENCY"

    def test_mild_sob_does_not_trigger_emergency(self, agent: SafetyEscalationAgent):
        """Mild shortness of breath should not trigger respiratory emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="mild shortness of breath after walking",
            associated_symptoms=[],
            severity=SymptomSeverity.MILD,
        )

        result = agent.check_safety(symptoms)

        assert result.emergency_type != "RESPIRATORY_EMERGENCY"

    # =========================================================================
    # PREGNANCY RED FLAG TESTS
    # =========================================================================

    def test_pregnancy_severe_abdominal_pain_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Severe abdominal pain in pregnancy should trigger obstetric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="severe abdominal pain",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
            is_pregnant=True,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("pregnancy" in flag.lower() or "obstetric" in flag.lower() for flag in result.red_flags_triggered)
        assert result.emergency_type == "OBSTETRIC_EMERGENCY"

    def test_pregnancy_heavy_bleeding_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Heavy bleeding in pregnancy should trigger obstetric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="heavy bleeding",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
            is_pregnant=True,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "OBSTETRIC_EMERGENCY"

    def test_pregnancy_seizure_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Seizure during pregnancy should trigger obstetric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="seizure",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
            is_pregnant=True,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "OBSTETRIC_EMERGENCY"

    def test_pregnancy_mild_discomfort_does_not_trigger_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Mild discomfort in pregnancy should not trigger obstetric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="mild backache",
            associated_symptoms=["fatigue"],
            severity=SymptomSeverity.MILD,
            is_pregnant=True,
        )

        result = agent.check_safety(symptoms)

        assert result.emergency_type != "OBSTETRIC_EMERGENCY"

    def test_abdominal_pain_without_pregnancy_does_not_trigger_obstetric(
        self, agent: SafetyEscalationAgent
    ):
        """Severe abdominal pain without pregnancy should not trigger obstetric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="severe abdominal pain",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
            is_pregnant=False,
        )

        result = agent.check_safety(symptoms)

        assert result.emergency_type != "OBSTETRIC_EMERGENCY"

    # =========================================================================
    # PEDIATRIC RED FLAG TESTS
    # =========================================================================

    def test_infant_high_fever_triggers_emergency(self, agent: SafetyEscalationAgent):
        """High fever in infant should trigger pediatric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="high fever",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.INFANT,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("pediatric" in flag.lower() or "infant" in flag.lower() for flag in result.red_flags_triggered)
        assert result.emergency_type == "PEDIATRIC_EMERGENCY"

    def test_child_lethargy_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Extreme lethargy in child should trigger pediatric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="not responding",
            associated_symptoms=["extreme lethargy"],
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.CHILD,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "PEDIATRIC_EMERGENCY"

    def test_child_seizure_triggers_emergency(self, agent: SafetyEscalationAgent):
        """Seizure in child should trigger pediatric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="seizure",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.CHILD,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "PEDIATRIC_EMERGENCY"

    def test_infant_mild_fever_does_not_trigger_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Mild fever in infant should not trigger pediatric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="mild fever",
            associated_symptoms=[],
            severity=SymptomSeverity.MILD,
            age_group=AgeGroup.INFANT,
        )

        result = agent.check_safety(symptoms)

        # May trigger other flags but not pediatric emergency for mild fever
        pediatric_flags = [f for f in result.red_flags_triggered if "pediatric" in f.lower() or "infant" in f.lower()]
        assert len(pediatric_flags) == 0 or result.emergency_type != "PEDIATRIC_EMERGENCY"

    def test_adult_fever_does_not_trigger_pediatric_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """High fever in adult should not trigger pediatric emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="high fever",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
            age_group=AgeGroup.ADULT,
        )

        result = agent.check_safety(symptoms)

        assert result.emergency_type != "PEDIATRIC_EMERGENCY"

    # =========================================================================
    # NEUROLOGICAL RED FLAG TESTS
    # =========================================================================

    def test_sudden_severe_headache_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Sudden severe headache should trigger neurological emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="sudden severe headache",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert any("neurological" in flag.lower() for flag in result.red_flags_triggered)
        assert result.emergency_type == "NEUROLOGICAL_EMERGENCY"

    def test_loss_of_consciousness_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Loss of consciousness should trigger neurological emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="loss of consciousness",
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "NEUROLOGICAL_EMERGENCY"

    def test_urdu_loss_of_consciousness_triggers_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Urdu loss of consciousness should trigger neurological emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="behoshi",  # Urdu: unconsciousness
            associated_symptoms=[],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "NEUROLOGICAL_EMERGENCY"

    def test_mild_headache_does_not_trigger_neurological_emergency(
        self, agent: SafetyEscalationAgent
    ):
        """Mild headache should not trigger neurological emergency."""
        symptoms = ExtractedSymptoms(
            primary_symptom="mild headache",
            associated_symptoms=[],
            severity=SymptomSeverity.MILD,
        )

        result = agent.check_safety(symptoms)

        assert result.emergency_type != "NEUROLOGICAL_EMERGENCY"

    # =========================================================================
    # IMMEDIATE ACTION GENERATION TESTS
    # =========================================================================

    def test_cardiac_emergency_generates_correct_action(
        self, agent: SafetyEscalationAgent
    ):
        """Cardiac emergency should generate appropriate immediate action."""
        symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            associated_symptoms=["arm pain"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert "call emergency" in result.immediate_action_required.lower() or "emergency services" in result.immediate_action_required.lower()
        assert "emergency facility" in result.immediate_action_required.lower()

    def test_stroke_emergency_generates_correct_action(
        self, agent: SafetyEscalationAgent
    ):
        """Stroke emergency should generate appropriate immediate action."""
        symptoms = ExtractedSymptoms(
            primary_symptom="face drooping",
            associated_symptoms=["arm weakness", "slurred speech"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert "call emergency" in result.immediate_action_required.lower() or "emergency services" in result.immediate_action_required.lower()
        assert "time" in result.immediate_action_required.lower() or "critical" in result.immediate_action_required.lower()

    # =========================================================================
    # EDGE CASE TESTS
    # =========================================================================

    def test_empty_associated_symptoms_does_not_crash(
        self, agent: SafetyEscalationAgent
    ):
        """Agent should handle empty associated symptoms gracefully."""
        symptoms = ExtractedSymptoms(
            primary_symptom="headache",
            associated_symptoms=[],
            severity=SymptomSeverity.MILD,
        )

        result = agent.check_safety(symptoms)

        assert isinstance(result, SafetyCheckResult)

    def test_case_insensitive_matching(self, agent: SafetyEscalationAgent):
        """Agent should match symptoms case-insensitively."""
        symptoms_upper = ExtractedSymptoms(
            primary_symptom="CHEST PAIN",
            associated_symptoms=["SHORTNESS OF BREATH"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms_upper)

        assert result.is_emergency is True

    def test_multiple_emergencies_simultaneously(self, agent: SafetyEscalationAgent):
        """Agent should handle multiple emergency conditions at once."""
        symptoms = ExtractedSymptoms(
            primary_symptom="chest pain",
            associated_symptoms=["shortness of breath", "face drooping"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert len(result.red_flags_triggered) > 1

    def test_urdu_primary_symptom_with_english_associated(
        self, agent: SafetyEscalationAgent
    ):
        """Agent should handle mixed Urdu/English symptoms."""
        symptoms = ExtractedSymptoms(
            primary_symptom="seene mein dard",  # Urdu: chest pain
            associated_symptoms=["arm pain"],
            severity=SymptomSeverity.SEVERE,
        )

        result = agent.check_safety(symptoms)

        assert result.is_emergency is True
        assert result.emergency_type == "CARDIAC_EMERGENCY"
