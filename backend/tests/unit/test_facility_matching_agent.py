"""Tests for the Facility Matching Agent."""

from __future__ import annotations

import math
from typing import Any, Dict, List

import pytest

from app.agents.facility_matching_agent import (
    CARE_TIER_RANK,
    EARTH_RADIUS_KM,
    FacilityMatchInput,
    FacilityMatchOutput,
    FacilityMatchingAgent,
    InMemoryFacilityStore,
    haversine_km,
)
from app.core.exceptions import FacilityMatchingError
from app.models.schemas import (
    AgeGroup,
    ExtractedSymptoms,
    FacilityInfo,
    FacilityType,
    SafetyCheckResult,
    SymptomSeverity,
    TriageClassification,
    TriageUrgency,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeFacilityStore:
    """Deterministic facility store for unit tests."""

    def __init__(self, facilities: List[Dict[str, Any]] | None = None) -> None:
        self._facilities = facilities or []
        self.calls = 0

    async def get_facilities(self) -> List[Dict[str, Any]]:
        self.calls += 1
        return list(self._facilities)


def _make_classification(
    urgency: TriageUrgency = TriageUrgency.ROUTINE,
    care_tier: FacilityType = FacilityType.BHU,
) -> TriageClassification:
    return TriageClassification(
        urgency=urgency,
        confidence_score=0.8,
        reasoning_trace="Test reasoning",
        recommended_care_tier=care_tier,
    )


def _make_safety(is_emergency: bool = False) -> SafetyCheckResult:
    return SafetyCheckResult(
        is_emergency=is_emergency,
        red_flags_triggered=["CARDIAC_RED_FLAG"] if is_emergency else [],
        emergency_type="CARDIAC_EMERGENCY" if is_emergency else None,
        immediate_action_required="Call 1122" if is_emergency else None,
    )


def _make_symptoms() -> ExtractedSymptoms:
    return ExtractedSymptoms(
        primary_symptom="headache",
        severity=SymptomSeverity.MILD,
        age_group=AgeGroup.ADULT,
    )


# Lahore coordinates for testing
LAHORE_LAT = 31.5204
LAHORE_LNG = 74.3587

# Sample facilities near Lahore
LAHORE_FACILITIES: List[Dict[str, Any]] = [
    {
        "facility_id": "BHU-001",
        "name": "Model Town BHU",
        "facility_type": "BHU",
        "address": "Model Town, Lahore",
        "latitude": 31.4832,
        "longitude": 74.3408,
        "services": ["general_consultation", "vaccination"],
        "emergency_capable": False,
        "phone_number": "+92-42-0001",
    },
    {
        "facility_id": "THQ-001",
        "name": "Shalimar THQ",
        "facility_type": "THQ",
        "address": "Shalimar, Lahore",
        "latitude": 31.5880,
        "longitude": 74.3873,
        "services": ["emergency", "surgery_minor", "lab", "pharmacy"],
        "emergency_capable": True,
        "phone_number": "+92-42-0003",
    },
    {
        "facility_id": "DHQ-001",
        "name": "DHQ Hospital Lahore",
        "facility_type": "DHQ",
        "address": "Ferozepur Road, Lahore",
        "latitude": 31.4500,
        "longitude": 74.3000,
        "services": ["emergency", "surgery", "icu", "pharmacy"],
        "emergency_capable": True,
        "phone_number": "+92-42-0004",
    },
    {
        "facility_id": "TER-001",
        "name": "Jinnah Hospital",
        "facility_type": "TERTIARY",
        "address": "Canal Bank Road, Lahore",
        "latitude": 31.6200,
        "longitude": 74.4500,
        "services": ["emergency", "cardiology", "neurology", "icu"],
        "emergency_capable": True,
        "phone_number": "+92-42-0005",
    },
]


# ---------------------------------------------------------------------------
# Haversine Distance Tests
# ---------------------------------------------------------------------------


class TestHaversineDistance:
    """Tests for the haversine_km function."""

    def test_same_point_returns_zero(self):
        assert haversine_km(31.5, 74.3, 31.5, 74.3) == pytest.approx(0.0, abs=0.01)

    def test_known_distance_lahore_islamabad(self):
        # Lahore to Islamabad ~270 km
        dist = haversine_km(31.5204, 74.3587, 33.6844, 73.0479)
        assert 240 < dist < 310

    def test_known_distance_lahore_karachi(self):
        # Lahore to Karachi ~1000 km
        dist = haversine_km(31.5204, 74.3587, 24.8600, 67.0100)
        assert 950 < dist < 1100

    def test_short_distance(self):
        # Two points within Lahore ~5 km
        dist = haversine_km(31.5204, 74.3587, 31.4832, 74.3408)
        assert 2 < dist < 8

    def test_antipodal_points(self):
        # Maximum distance ~half Earth circumference
        dist = haversine_km(0, 0, 0, 180)
        assert dist == pytest.approx(math.pi * EARTH_RADIUS_KM, rel=0.01)


# ---------------------------------------------------------------------------
# Facility Matching Agent Tests
# ---------------------------------------------------------------------------


class TestFacilityMatchingAgent:
    """Tests for the FacilityMatchingAgent."""

    async def test_routine_match_returns_nearest_bhu(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.BHU),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        assert result.recommended is not None
        assert result.recommended.facility_type == FacilityType.BHU
        assert result.recommended.facility_id == "BHU-001"
        assert result.match_reason != ""

    async def test_thq_match_excludes_bhu(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.THQ),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        assert result.recommended is not None
        assert result.recommended.facility_type in (FacilityType.THQ, FacilityType.DHQ, FacilityType.TERTIARY)
        assert CARE_TIER_RANK[result.recommended.facility_type] >= CARE_TIER_RANK[FacilityType.THQ]

    async def test_emergency_prefers_emergency_capable(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(
                urgency=TriageUrgency.EMERGENCY,
                care_tier=FacilityType.EMERGENCY,
            ),
            safety_check=_make_safety(is_emergency=True),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        assert result.recommended is not None
        assert result.recommended.emergency_capable is True
        assert "Emergency" in result.match_reason

    async def test_emergency_skips_non_emergency_facilities(self):
        # Only non-emergency facilities available
        non_emergency = [
            {
                "facility_id": "BHU-ONLY",
                "name": "Only BHU",
                "facility_type": "BHU",
                "address": "Somewhere",
                "latitude": 31.5,
                "longitude": 74.3,
                "services": ["general_consultation"],
                "emergency_capable": False,
                "phone_number": None,
            },
        ]
        store = FakeFacilityStore(non_emergency)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        with pytest.raises(FacilityMatchingError):
            await agent.match(FacilityMatchInput(
                classification=_make_classification(
                    urgency=TriageUrgency.EMERGENCY,
                    care_tier=FacilityType.EMERGENCY,
                ),
                safety_check=_make_safety(is_emergency=True),
                symptoms=_make_symptoms(),
                latitude=LAHORE_LAT,
                longitude=LAHORE_LNG,
            ))

    async def test_distance_filtering(self):
        # Facility 100km away should be excluded with 50km radius
        far_facility = [
            {
                "facility_id": "FAR-001",
                "name": "Far Hospital",
                "facility_type": "DHQ",
                "address": "Far Away",
                "latitude": 32.5,
                "longitude": 75.0,
                "services": ["emergency"],
                "emergency_capable": True,
                "phone_number": None,
            },
        ]
        store = FakeFacilityStore(far_facility)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        # Should fall back to searching all emergency facilities
        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.DHQ),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))
        # The far facility should appear in fallback since it's emergency-capable
        assert result.recommended is not None

    async def test_no_coordinates_uses_fallback(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.BHU),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=None,
            longitude=None,
        ))

        assert result.recommended is not None

    async def test_no_facilities_raises_error(self):
        store = FakeFacilityStore([])
        agent = FacilityMatchingAgent(store)

        with pytest.raises(FacilityMatchingError, match="No facilities available"):
            await agent.match(FacilityMatchInput(
                classification=_make_classification(),
                safety_check=_make_safety(),
                symptoms=_make_symptoms(),
                latitude=LAHORE_LAT,
                longitude=LAHORE_LNG,
            ))

    async def test_alternatives_returned(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0, max_results=5)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.BHU),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        # BHU matches first, then THQ, DHQ, TERTIARY as alternatives
        assert len(result.alternatives) >= 1
        assert result.total_candidates >= 2

    async def test_match_reason_contains_distance(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.BHU),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        assert "km" in result.match_reason

    async def test_search_radius_in_output(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=30.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.BHU),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        assert result.search_radius_km == 30.0

    async def test_facility_info_fields_populated(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.BHU),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        fac = result.recommended
        assert fac is not None
        assert fac.facility_id == "BHU-001"
        assert fac.name == "Model Town BHU"
        assert fac.facility_type == FacilityType.BHU
        assert fac.address != ""
        assert isinstance(fac.services_available, list)
        assert isinstance(fac.emergency_capable, bool)

    async def test_services_json_string_parsed(self):
        # Test when services is a JSON string instead of a list
        facilities = [
            {
                "facility_id": "TEST-001",
                "name": "Test Hospital",
                "facility_type": "THQ",
                "address": "Test Address",
                "latitude": 31.52,
                "longitude": 74.36,
                "services": '["emergency", "lab"]',
                "emergency_capable": True,
                "phone_number": None,
            },
        ]
        store = FakeFacilityStore(facilities)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        result = await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.THQ),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        assert result.recommended is not None
        assert "emergency" in result.recommended.services_available

    async def test_facility_store_called(self):
        store = FakeFacilityStore(LAHORE_FACILITIES)
        agent = FacilityMatchingAgent(store, max_distance_km=50.0)

        await agent.match(FacilityMatchInput(
            classification=_make_classification(care_tier=FacilityType.BHU),
            safety_check=_make_safety(is_emergency=False),
            symptoms=_make_symptoms(),
            latitude=LAHORE_LAT,
            longitude=LAHORE_LNG,
        ))

        assert store.calls == 1


# ---------------------------------------------------------------------------
# InMemoryFacilityStore Tests
# ---------------------------------------------------------------------------


class TestInMemoryFacilityStore:
    """Tests for the InMemoryFacilityStore."""

    async def test_load_from_list(self):
        store = InMemoryFacilityStore()
        store.load_from_list(LAHORE_FACILITIES)
        facilities = await store.get_facilities()
        assert len(facilities) == 4

    async def test_load_from_file(self, tmp_path):
        import json
        data_file = tmp_path / "facilities.json"
        data_file.write_text(json.dumps(LAHORE_FACILITIES))

        store = InMemoryFacilityStore()
        count = store.load_from_file(str(data_file))
        assert count == 4

        facilities = await store.get_facilities()
        assert len(facilities) == 4

    async def test_load_from_missing_file(self):
        store = InMemoryFacilityStore()
        count = store.load_from_file("/nonexistent/path/facilities.json")
        assert count == 0

    async def test_load_from_invalid_json(self, tmp_path):
        data_file = tmp_path / "bad.json"
        data_file.write_text('{"not": "a list"}')

        store = InMemoryFacilityStore()
        count = store.load_from_file(str(data_file))
        assert count == 0

    async def test_get_facilities_returns_copy(self):
        store = InMemoryFacilityStore()
        store.load_from_list(LAHORE_FACILITIES)
        facilities = await store.get_facilities()
        facilities.clear()
        # Original should be unchanged
        assert len(await store.get_facilities()) == 4

    async def test_empty_store(self):
        store = InMemoryFacilityStore()
        facilities = await store.get_facilities()
        assert facilities == []


# ---------------------------------------------------------------------------
# Care Tier Rank Tests
# ---------------------------------------------------------------------------


class TestCareTierRank:
    """Tests for the care tier hierarchy."""

    def test_bhu_lowest_rank(self):
        assert CARE_TIER_RANK[FacilityType.BHU] == min(CARE_TIER_RANK.values())

    def test_emergency_equals_tertiary(self):
        assert CARE_TIER_RANK[FacilityType.EMERGENCY] == CARE_TIER_RANK[FacilityType.TERTIARY]

    def test_rank_ordering(self):
        assert CARE_TIER_RANK[FacilityType.BHU] < CARE_TIER_RANK[FacilityType.RHC]
        assert CARE_TIER_RANK[FacilityType.RHC] < CARE_TIER_RANK[FacilityType.THQ]
        assert CARE_TIER_RANK[FacilityType.THQ] < CARE_TIER_RANK[FacilityType.DHQ]
        assert CARE_TIER_RANK[FacilityType.DHQ] <= CARE_TIER_RANK[FacilityType.TERTIARY]
