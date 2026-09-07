"""
Shared test fixtures and mocked external clients.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from app.agents.safety_escalation_agent import SafetyEscalationAgent
from app.models.schemas import (
    AgeGroup,
    ExtractedSymptoms,
    SymptomSeverity,
)


@pytest.fixture
def safety_agent() -> SafetyEscalationAgent:
    """Provide a SafetyEscalationAgent instance for testing."""
    return SafetyEscalationAgent()


@pytest.fixture
def baseline_symptoms() -> ExtractedSymptoms:
    """
    Baseline symptoms with no emergency indicators.
    Used as a starting point for tests that add specific symptoms.
    """
    return ExtractedSymptoms(
        primary_symptom="mild headache",
        secondary_symptoms=[],
        duration_hours=24.0,
        severity=SymptomSeverity.MILD,
        age_group=AgeGroup.ADULT,
        is_pregnant=False,
        pre_existing_conditions=[],
        associated_symptoms=[],
    )


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Mock LLM client for contract tests."""
    mock = MagicMock()
    mock.generate_response = AsyncMock(return_value={"text": "Mock response"})
    return mock
