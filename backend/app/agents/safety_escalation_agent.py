"""
Safety Escalation Agent - Deterministic Rule Engine

This is the system's core safety mechanism. It is implemented as a rule-based
engine, NOT an LLM call. It checks structured symptom data against a curated
set of red-flag combinations and bypasses all downstream agents if triggered.

IMPORTANT: This file is treated as clinical logic. Any changes require the same
rigor as a database migration (versioned, reviewed, tested with 100% branch coverage).

Red-flag rules are based on established clinical protocols:
- FAST (Face, Arms, Speech, Time) for stroke detection
- Chest pain + associated symptoms for cardiac events
- Severe bleeding protocols
- Pregnancy complications
- Pediatric emergency indicators
- Respiratory distress indicators
"""

import re
from typing import List, Optional

from app.models.schemas import (
    AgeGroup,
    ExtractedSymptoms,
    SafetyCheckResult,
    SymptomSeverity,
)


class SafetyEscalationAgent:
    """
    Deterministic safety escalation agent that checks for emergency conditions.

    This agent runs independently of the LLM layer and can short-circuit the
    entire pipeline if a red flag is detected. It guarantees that model
    unpredictability can never delay a critical case.
    """

    # Red-flag symptom combinations (normalized to lowercase for matching)
    CARDIAC_RED_FLAGS = {
        "chest_pain_with_radiation": {
            "primary": ["chest pain", "seene mein dard", "chest pressure"],
            "associated": ["arm pain", "jaw pain", "back pain", "left arm", "right arm"],
            "description": "Chest pain with radiation (possible cardiac event)",
        },
        "chest_pain_with_sob": {
            "primary": ["chest pain", "seene mein dard", "chest tightness"],
            "associated": ["shortness of breath", "breathing difficulty", "saans nahi aa rahi"],
            "description": "Chest pain with shortness of breath",
        },
        "chest_pain_with_sweating": {
            "primary": ["chest pain", "seene mein dard"],
            "associated": ["sweating", "cold sweat", "pasina"],
            "description": "Chest pain with cold sweating",
        },
    }

    STROKE_RED_FLAGS = {
        "facial_droop": {
            "symptoms": ["facial droop", "face drooping", "munh tedha", "face asymmetry"],
            "description": "Facial droop (FAST - Face)",
        },
        "arm_weakness": {
            "symptoms": ["arm weakness", "arm numbness", "baazu mein kamzori", "cannot raise arm"],
            "description": "Arm weakness (FAST - Arms)",
        },
        "speech_difficulty": {
            "symptoms": [
                "speech difficulty",
                "slurred speech",
                "zaban larkharana",
                "cannot speak clearly",
            ],
            "description": "Speech difficulty (FAST - Speech)",
        },
    }

    BLEEDING_RED_FLAGS = [
        "severe bleeding",
        "uncontrolled bleeding",
        "ziada khoon behna",
        "bleeding not stopping",
    ]

    RESPIRATORY_RED_FLAGS = {
        "severe_sob": {
            "symptoms": [
                "severe shortness of breath",
                "cannot breathe",
                "saans bilkul nahi aa rahi",
                "gasping for air",
            ],
            "description": "Severe respiratory distress",
        },
        "sob_with_chest_pain": {
            "primary": ["shortness of breath", "saans nahi aa rahi"],
            "associated": ["chest pain", "seene mein dard"],
            "description": "Shortness of breath with chest pain",
        },
    }

    PREGNANCY_RED_FLAGS = [
        "severe abdominal pain",
        "heavy bleeding",
        "pet mein shadeed dard",
        "bleeding during pregnancy",
        "contractions before term",
        "seizures during pregnancy",
        "pregnancy seizure",
        "seizure",
        "eclampsia",
    ]

    PEDIATRIC_RED_FLAGS = {
        "infant_fever": {
            "symptoms": ["high fever", "tez bukhar", "fever"],
            "age_group": AgeGroup.INFANT,
            "min_severity": SymptomSeverity.MODERATE,
            "description": "High fever in infant",
        },
        "child_lethargy": {
            "symptoms": ["extreme lethargy", "not responding", "bacha respond nahi kar raha"],
            "age_group": [AgeGroup.INFANT, AgeGroup.CHILD],
            "min_severity": SymptomSeverity.MODERATE,
            "description": "Extreme lethargy in child",
        },
        "child_seizure": {
            "symptoms": ["seizure", "fit", "doray", "convulsions"],
            "age_group": [AgeGroup.INFANT, AgeGroup.CHILD],
            "min_severity": SymptomSeverity.MILD,
            "description": "Seizure in child",
        },
    }

    NEUROLOGICAL_RED_FLAGS = [
        "sudden severe headache",
        "worst headache of life",
        "zindagi ka sab se shadeed sir dard",
        "loss of consciousness",
        "behoshi",
        "confusion",
        "sudden confusion",
    ]

    def __init__(self) -> None:
        """Initialize the safety escalation agent."""
        pass

    # ------------------------------------------------------------------
    # Text normalisation helpers
    # ------------------------------------------------------------------

    # Synonym map: key (canonical form) → list of alternate spellings
    # Roman Urdu has no standard spelling, so this covers the most common
    # phonetic variations seen in clinical field usage.
    _SYNONYMS: dict[str, list[str]] = {
        # Cardiac
        "chest pain":        ["cheest pain", "cheest dard", "seene mein dard", "seenay mein dard",
                              "seenay main dard", "seena dard", "sena dard", "chhati mein dard",
                              "chhati ka dard", "seene ka dard", "chest pressure", "chest tightness",
                              "seena takleef"],
        "arm pain":          ["baazu mein dard", "baazoo mein dard", "hath mein dard",
                              "arm numbness", "baazu soonn"],
        "left arm":          ["baazu baain", "baain baazu"],
        "right arm":         ["baazu seedha", "seedha baazu"],
        "jaw pain":          ["jabra dard", "jabbra dard"],
        "sweating":          ["pasina", "pasinay", "thanda pasina", "cold sweat"],
        # Stroke / neuro
        "facial droop":      ["munh tedha", "mun tedha", "chehra tedha", "face drooping",
                              "face asymmetry", "face tedha"],
        "arm weakness":      ["baazu kamzori", "baazoo kamzori", "baazu mein kamzori",
                              "cannot raise arm", "haath uthana mushkil"],
        "speech difficulty": ["zaban larkharana", "zubaan larkharana", "baat karna mushkil",
                              "slurred speech", "cannot speak clearly", "bolne mein takleef"],
        # Respiratory — IMPORTANT: map variants to the EXACT phrases used in
        # RESPIRATORY_RED_FLAGS so that normalization does not destroy existing matches.
        #   severe_sob rule checks: "severe shortness of breath", "cannot breathe",
        #                           "saans bilkul nahi aa rahi", "gasping for air"
        #   sob_with_chest_pain primary: "shortness of breath", "saans nahi aa rahi"
        "cannot breathe":            ["nahi saans aa rahi", "saans nahi aati", "dam ghut raha",
                                      "bilkul saans nahi", "saans rukk gayi", "saans nahi aa sakta"],
        "saans bilkul nahi aa rahi": ["saans bilkul nahi ata", "saans aa nahi rahi",
                                      "saans bilkul band", "dam ghutna shadeed"],
        "gasping for air":           ["haanpna", "haanp raha", "haanp rahi"],
        "severe shortness of breath": ["bohat mushkil saans", "shadeed saans ki takleef",
                                        "extreme breathing difficulty"],
        "shortness of breath":       ["saans nahi aa rahi", "saans nahi ata", "saans aane mein takleef",
                                       "breathing difficulty", "saans phoolna", "saans ki takleef",
                                       "saans ki mushkil"],
        # Bleeding
        "severe bleeding":   ["ziada khoon behna", "ziyada khoon", "khoon band nahi ho raha",
                              "bleeding not stopping", "uncontrolled bleeding"],
        # Neurological
        "loss of consciousness": ["behoshi", "behosh ho gaya", "behosh ho gayi", "hosh kho gaya"],
        "sudden severe headache": ["zindagi ka sab se shadeed sir dard", "sar mein bohat shadeed dard",
                                    "worst headache of life", "sar phat raha hai"],
        "confusion":         ["ghabrahat", "ulajhn", "kuch samajh nahi aa raha", "sudden confusion"],
        "seizure":           ["doray", "dora parna", "fit aana", "jhatke aana", "convulsions",
                              "mirgi"],
        # Pregnancy
        "bleeding during pregnancy": ["hamal mein khoon", "hamla mein khoon"],
        "severe abdominal pain":      ["pet mein shadeed dard", "pait mein bohat dard",
                                        "tond mein dard"],
        # Pediatric
        "not responding":    ["bacha respond nahi kar raha", "bacha hosh mein nahi",
                              "bacha uth nahi raha"],
        "high fever":        ["tez bukhar", "bohat zyada bukhar", "thand aur bukhar"],
    }

    # Pre-compile synonym replacement patterns for performance
    _SYNONYM_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\b" + re.escape(alt) + r"\b", re.IGNORECASE), canonical)
        for canonical, alts in _SYNONYMS.items()
        for alt in alts
    ]

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """
        Normalize a symptom text string for safer matching.

        Steps:
          1. Lowercase.
          2. Collapse redundant whitespace.
          3. Apply synonym substitution for Roman Urdu spelling variants.

        This ensures that common misspellings and phonetic variants of
        Urdu medical terms (e.g. "seenay main dard" vs "seene mein dard")
        are mapped to the canonical form before red-flag matching.
        """
        normalized = text.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        for pattern, canonical in cls._SYNONYM_PATTERNS:
            normalized = pattern.sub(canonical, normalized)
        return normalized

    def check_safety(self, symptoms: ExtractedSymptoms) -> SafetyCheckResult:
        """
        Check symptoms against red-flag rules.

        Args:
            symptoms: Structured symptom data from intake agent

        Returns:
            SafetyCheckResult with emergency status and triggered flags
        """
        red_flags: List[str] = []

        # Check cardiac red flags
        cardiac_flags = self._check_cardiac_red_flags(symptoms)
        red_flags.extend(cardiac_flags)

        # Check stroke red flags (FAST protocol)
        stroke_flags = self._check_stroke_red_flags(symptoms)
        red_flags.extend(stroke_flags)

        # Check bleeding red flags
        bleeding_flags = self._check_bleeding_red_flags(symptoms)
        red_flags.extend(bleeding_flags)

        # Check respiratory red flags
        respiratory_flags = self._check_respiratory_red_flags(symptoms)
        red_flags.extend(respiratory_flags)

        # Check pregnancy red flags
        pregnancy_flags = self._check_pregnancy_red_flags(symptoms)
        red_flags.extend(pregnancy_flags)

        # Check pediatric red flags
        pediatric_flags = self._check_pediatric_red_flags(symptoms)
        red_flags.extend(pediatric_flags)

        # Check neurological red flags
        neurological_flags = self._check_neurological_red_flags(symptoms)
        red_flags.extend(neurological_flags)

        # Determine if emergency
        is_emergency = len(red_flags) > 0

        # Generate immediate action if emergency
        immediate_action: Optional[str] = None
        emergency_type: Optional[str] = None

        if is_emergency:
            emergency_type = self._classify_emergency_type(red_flags)
            immediate_action = self._generate_immediate_action(emergency_type)

        return SafetyCheckResult(
            is_emergency=is_emergency,
            red_flags_triggered=red_flags,
            emergency_type=emergency_type,
            immediate_action_required=immediate_action,
        )

    def _check_cardiac_red_flags(self, symptoms: ExtractedSymptoms) -> List[str]:
        """Check for cardiac emergency red flags."""
        triggered: List[str] = []
        primary_lower = self._normalize_text(symptoms.primary_symptom)
        associated_lower = [self._normalize_text(s) for s in symptoms.associated_symptoms]

        for rule_name, rule in self.CARDIAC_RED_FLAGS.items():
            primary_match = any(p in primary_lower for p in rule["primary"])
            associated_match = any(a in " ".join(associated_lower) for a in rule["associated"])

            if primary_match and associated_match:
                triggered.append(rule["description"])

        return triggered

    def _check_stroke_red_flags(self, symptoms: ExtractedSymptoms) -> List[str]:
        """Check for stroke red flags using FAST protocol."""
        triggered: List[str] = []
        all_symptoms = [self._normalize_text(symptoms.primary_symptom)] + [
            self._normalize_text(s) for s in symptoms.associated_symptoms
        ]

        fast_count = 0

        for rule_name, rule in self.STROKE_RED_FLAGS.items():
            if any(s in " ".join(all_symptoms) for s in rule["symptoms"]):
                triggered.append(rule["description"])
                fast_count += 1

        # If 2+ FAST criteria met, high suspicion of stroke
        if fast_count >= 2:
            triggered.append("Multiple FAST criteria met - high stroke suspicion")

        return triggered

    def _check_bleeding_red_flags(self, symptoms: ExtractedSymptoms) -> List[str]:
        """Check for severe bleeding red flags."""
        triggered: List[str] = []
        all_symptoms = [self._normalize_text(symptoms.primary_symptom)] + [
            self._normalize_text(s) for s in symptoms.associated_symptoms
        ]
        all_symptoms_text = " ".join(all_symptoms)

        if any(flag in all_symptoms_text for flag in self.BLEEDING_RED_FLAGS):
            triggered.append("Severe/uncontrolled bleeding detected")

        return triggered

    def _check_respiratory_red_flags(self, symptoms: ExtractedSymptoms) -> List[str]:
        """Check for respiratory distress red flags."""
        triggered: List[str] = []
        primary_lower = self._normalize_text(symptoms.primary_symptom)
        associated_lower = [self._normalize_text(s) for s in symptoms.associated_symptoms]

        # Check severe SOB
        if any(s in primary_lower for s in self.RESPIRATORY_RED_FLAGS["severe_sob"]["symptoms"]):
            triggered.append(self.RESPIRATORY_RED_FLAGS["severe_sob"]["description"])

        # Check SOB with chest pain
        sob_rule = self.RESPIRATORY_RED_FLAGS["sob_with_chest_pain"]
        primary_match = any(p in primary_lower for p in sob_rule["primary"])
        associated_match = any(a in " ".join(associated_lower) for a in sob_rule["associated"])

        if primary_match and associated_match:
            triggered.append(sob_rule["description"])

        return triggered

    def _check_pregnancy_red_flags(self, symptoms: ExtractedSymptoms) -> List[str]:
        """Check for pregnancy-related red flags."""
        triggered: List[str] = []

        if not symptoms.is_pregnant:
            return triggered

        all_symptoms = [self._normalize_text(symptoms.primary_symptom)] + [
            self._normalize_text(s) for s in symptoms.associated_symptoms
        ]
        all_symptoms_text = " ".join(all_symptoms)

        if any(flag in all_symptoms_text for flag in self.PREGNANCY_RED_FLAGS):
            triggered.append("Pregnancy complication requiring emergency care")

        return triggered

    # Severity ordering for threshold comparisons
    _SEVERITY_ORDER = {
        SymptomSeverity.MILD: 1,
        SymptomSeverity.MODERATE: 2,
        SymptomSeverity.SEVERE: 3,
    }

    def _check_pediatric_red_flags(self, symptoms: ExtractedSymptoms) -> List[str]:
        """Check for pediatric emergency red flags."""
        triggered: List[str] = []
        all_symptoms = [self._normalize_text(symptoms.primary_symptom)] + [
            self._normalize_text(s) for s in symptoms.associated_symptoms
        ]
        all_symptoms_text = " ".join(all_symptoms)

        for rule_name, rule in self.PEDIATRIC_RED_FLAGS.items():
            age_match = symptoms.age_group in (
                rule["age_group"]
                if isinstance(rule["age_group"], list)
                else [rule["age_group"]]
            )

            min_severity = rule.get("min_severity", SymptomSeverity.MILD)
            severity_met = (
                self._SEVERITY_ORDER.get(symptoms.severity, 0)
                >= self._SEVERITY_ORDER.get(min_severity, 0)
            )

            if (
                age_match
                and severity_met
                and any(s in all_symptoms_text for s in rule["symptoms"])
            ):
                triggered.append(rule["description"])

        return triggered

    def _check_neurological_red_flags(self, symptoms: ExtractedSymptoms) -> List[str]:
        """Check for neurological emergency red flags."""
        triggered: List[str] = []
        all_symptoms = [self._normalize_text(symptoms.primary_symptom)] + [
            self._normalize_text(s) for s in symptoms.associated_symptoms
        ]
        all_symptoms_text = " ".join(all_symptoms)

        if any(flag in all_symptoms_text for flag in self.NEUROLOGICAL_RED_FLAGS):
            triggered.append("Neurological emergency indicator")

        return triggered

    def _classify_emergency_type(self, red_flags: List[str]) -> str:
        """Classify the type of emergency based on triggered flags."""
        flags_text = " ".join(red_flags).lower()

        if "cardiac" in flags_text or "chest pain" in flags_text:
            return "CARDIAC_EMERGENCY"
        if "stroke" in flags_text or "fast" in flags_text:
            return "STROKE_EMERGENCY"
        if "bleeding" in flags_text:
            return "HEMORRHAGE_EMERGENCY"
        if "respiratory" in flags_text or "breathing" in flags_text:
            return "RESPIRATORY_EMERGENCY"
        if "pregnancy" in flags_text:
            return "OBSTETRIC_EMERGENCY"
        if "pediatric" in flags_text or "child" in flags_text or "infant" in flags_text:
            return "PEDIATRIC_EMERGENCY"
        if "neurological" in flags_text:
            return "NEUROLOGICAL_EMERGENCY"

        return "UNSPECIFIED_EMERGENCY"

    def _generate_immediate_action(self, emergency_type: str) -> str:
        """Generate immediate action recommendation based on emergency type."""
        actions = {
            "CARDIAC_EMERGENCY": "Call emergency services immediately. Go to nearest emergency facility. Do not drive yourself.",
            "STROKE_EMERGENCY": "Call emergency services immediately. Time is critical for stroke treatment.",
            "HEMORRHAGE_EMERGENCY": "Apply direct pressure to bleeding site. Call emergency services or go to nearest emergency facility immediately.",
            "RESPIRATORY_EMERGENCY": "Call emergency services immediately. Sit upright to ease breathing. Do not lie flat.",
            "OBSTETRIC_EMERGENCY": "Go to nearest hospital with maternity services immediately. Call emergency services if needed.",
            "PEDIATRIC_EMERGENCY": "Take child to nearest emergency facility immediately. Call emergency services if child is unresponsive.",
            "NEUROLOGICAL_EMERGENCY": "Call emergency services immediately. Do not give food or drink. Note time symptoms started.",
            "UNSPECIFIED_EMERGENCY": "Go to nearest emergency facility immediately or call emergency services.",
        }

        return actions.get(emergency_type, actions["UNSPECIFIED_EMERGENCY"])
