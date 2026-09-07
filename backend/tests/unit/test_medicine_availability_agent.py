"""Tests for the Medicine Availability Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from app.agents.medicine_availability_agent import (
    CONDITION_MEDICINE_MAP,
    InMemoryMedicineStore,
    MedicineAvailabilityAgent,
    MedicineCheckInput,
    MedicineCheckOutput,
    SYMPTOM_MEDICINE_MAP,
)
from app.models.schemas import (
    AgeGroup,
    ExtractedSymptoms,
    FacilityType,
    MedicineAvailability,
    SymptomSeverity,
    TriageClassification,
    TriageUrgency,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeMedicineStore:
    """Deterministic medicine store for unit tests."""

    def __init__(self, inventory: Dict[str, List[Dict[str, Any]]] | None = None) -> None:
        self._inventory = inventory or {}
        self.calls: List[str] = []

    async def get_inventory(self, facility_id: str) -> List[Dict[str, Any]]:
        self.calls.append(facility_id)
        return list(self._inventory.get(facility_id, []))


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


def _make_symptoms(
    primary: str = "headache",
    severity: SymptomSeverity = SymptomSeverity.MILD,
    secondary: List[str] | None = None,
    associated: List[str] | None = None,
    conditions: List[str] | None = None,
) -> ExtractedSymptoms:
    return ExtractedSymptoms(
        primary_symptom=primary,
        severity=severity,
        age_group=AgeGroup.ADULT,
        secondary_symptoms=secondary or [],
        associated_symptoms=associated or [],
        pre_existing_conditions=conditions or [],
    )


SAMPLE_INVENTORY: Dict[str, List[Dict[str, Any]]] = {
    "FAC-001": [
        {"facility_id": "FAC-001", "medicine_name": "Paracetamol 500mg", "quantity_available": 500, "unit": "tablets"},
        {"facility_id": "FAC-001", "medicine_name": "Amoxicillin 500mg", "quantity_available": 200, "unit": "capsules"},
        {"facility_id": "FAC-001", "medicine_name": "Ceftriaxone 1g", "quantity_available": 50, "unit": "vials"},
        {"facility_id": "FAC-001", "medicine_name": "ORS Sachets", "quantity_available": 300, "unit": "sachets"},
    ],
    "FAC-002": [
        {"facility_id": "FAC-002", "medicine_name": "Paracetamol 500mg", "quantity_available": 100, "unit": "tablets"},
    ],
    "FAC-EMPTY": [],
}


# ---------------------------------------------------------------------------
# Medicine Availability Agent Tests
# ---------------------------------------------------------------------------


class TestMedicineAvailabilityAgent:
    """Tests for the MedicineAvailabilityAgent."""

    async def test_all_medicines_available(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="headache"),
            classification=_make_classification(),
        ))

        assert result.all_available is True
        assert "Paracetamol 500mg" in result.availability.medicines_available
        assert result.availability.medicines_unavailable == []

    async def test_some_medicines_unavailable(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-002",
            symptoms=_make_symptoms(primary="fever"),
            classification=_make_classification(urgency=TriageUrgency.URGENT),
        ))

        # FAC-002 only has Paracetamol — Ceftriaxone (from URGENT urgency) should be unavailable
        assert not result.all_available
        assert "Paracetamol 500mg" in result.availability.medicines_available

    async def test_no_inventory_all_unavailable(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-EMPTY",
            symptoms=_make_symptoms(primary="headache"),
            classification=_make_classification(),
        ))

        assert not result.all_available
        assert result.availability.medicines_available == []
        assert len(result.availability.medicines_unavailable) > 0

    async def test_unknown_facility_returns_empty(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="NONEXISTENT",
            symptoms=_make_symptoms(primary="headache"),
            classification=_make_classification(),
        ))

        assert not result.all_available

    async def test_severe_adds_epinephrine(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="headache", severity=SymptomSeverity.SEVERE),
            classification=_make_classification(),
        ))

        assert "Epinephrine 1mg" in result.medicines_needed

    async def test_emergency_urgency_critical_check(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-002",
            symptoms=_make_symptoms(
                primary="chest pain",
                severity=SymptomSeverity.SEVERE,
            ),
            classification=_make_classification(
                urgency=TriageUrgency.EMERGENCY,
                care_tier=FacilityType.EMERGENCY,
            ),
        ))

        # Epinephrine should be needed but unavailable at FAC-002
        assert result.missing_critical is True

    async def test_pre_existing_condition_adds_medicines(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(
                primary="headache",
                conditions=["diabetes"],
            ),
            classification=_make_classification(),
        ))

        assert "Insulin Regular" in result.medicines_needed or "Metformin 500mg" in result.medicines_needed

    async def test_secondary_symptom_inference(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(
                primary="headache",
                secondary=["diarrhea"],
            ),
            classification=_make_classification(),
        ))

        assert "ORS Sachets" in result.medicines_needed

    async def test_associated_symptom_inference(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(
                primary="headache",
                associated=["vomiting"],
            ),
            classification=_make_classification(),
        ))

        assert "ORS Sachets" in result.medicines_needed

    async def test_minimal_check_when_no_keywords_match(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="xyz_unknown_condition"),
            classification=_make_classification(),
        ))

        # Should still check at least Paracetamol as fallback
        assert "Paracetamol 500mg" in result.medicines_needed

    async def test_medicines_checked_list_populated(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="fever"),
            classification=_make_classification(),
        ))

        assert len(result.availability.medicines_checked) > 0
        assert result.availability.facility_id == "FAC-001"

    async def test_facility_id_in_output(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(),
            classification=_make_classification(),
        ))

        assert result.availability.facility_id == "FAC-001"

    async def test_last_updated_is_datetime(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(),
            classification=_make_classification(),
        ))

        assert isinstance(result.availability.last_updated, datetime)

    async def test_urgent_adds_ceftriaxone(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="headache"),
            classification=_make_classification(urgency=TriageUrgency.URGENT),
        ))

        assert "Ceftriaxone 1g" in result.medicines_needed

    async def test_store_called_with_correct_facility(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        await agent.check(MedicineCheckInput(
            facility_id="FAC-002",
            symptoms=_make_symptoms(),
            classification=_make_classification(),
        ))

        assert "FAC-002" in store.calls

    async def test_no_critical_missing_when_all_available(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="headache"),
            classification=_make_classification(),
        ))

        assert result.missing_critical is False

    async def test_respiratory_symptoms(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="difficulty breathing"),
            classification=_make_classification(),
        ))

        assert "Salbutamol Inhaler" in result.medicines_needed

    async def test_cardiac_symptoms(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(primary="chest pain"),
            classification=_make_classification(),
        ))

        assert "Aspirin 75mg" in result.medicines_needed
        assert "Clopidogrel 75mg" in result.medicines_needed

    async def test_medicines_needed_sorted(self):
        store = FakeMedicineStore(SAMPLE_INVENTORY)
        agent = MedicineAvailabilityAgent(store)

        result = await agent.check(MedicineCheckInput(
            facility_id="FAC-001",
            symptoms=_make_symptoms(
                primary="chest pain",
                secondary=["fever"],
                conditions=["diabetes"],
            ),
            classification=_make_classification(),
        ))

        assert result.medicines_needed == sorted(result.medicines_needed)


# ---------------------------------------------------------------------------
# InMemoryMedicineStore Tests
# ---------------------------------------------------------------------------


class TestInMemoryMedicineStore:
    """Tests for the InMemoryMedicineStore."""

    async def test_load_from_list(self):
        store = InMemoryMedicineStore()
        records = SAMPLE_INVENTORY["FAC-001"]
        store.load_from_list(records)
        inventory = await store.get_inventory("FAC-001")
        assert len(inventory) == 4

    async def test_load_from_file(self, tmp_path):
        import json
        all_records = []
        for records in SAMPLE_INVENTORY.values():
            all_records.extend(records)

        data_file = tmp_path / "medicines.json"
        data_file.write_text(json.dumps(all_records))

        store = InMemoryMedicineStore()
        count = store.load_from_file(str(data_file))
        assert count > 0

    async def test_load_from_missing_file(self):
        store = InMemoryMedicineStore()
        count = store.load_from_file("/nonexistent/path/medicines.json")
        assert count == 0

    async def test_load_from_invalid_json(self, tmp_path):
        data_file = tmp_path / "bad.json"
        data_file.write_text('{"not": "a list"}')

        store = InMemoryMedicineStore()
        count = store.load_from_file(str(data_file))
        assert count == 0

    async def test_unknown_facility_returns_empty(self):
        store = InMemoryMedicineStore()
        store.load_from_list(SAMPLE_INVENTORY["FAC-001"])
        inventory = await store.get_inventory("NONEXISTENT")
        assert inventory == []

    async def test_get_inventory_returns_copy(self):
        store = InMemoryMedicineStore()
        store.load_from_list(SAMPLE_INVENTORY["FAC-001"])
        inventory = await store.get_inventory("FAC-001")
        inventory.clear()
        assert len(await store.get_inventory("FAC-001")) == 4


# ---------------------------------------------------------------------------
# Medicine Map Tests
# ---------------------------------------------------------------------------


class TestMedicineMap:
    """Tests for the symptom-to-medicine mapping."""

    def test_fever_maps_to_paracetamol(self):
        assert "Paracetamol 500mg" in SYMPTOM_MEDICINE_MAP["fever"]

    def test_chest_pain_maps_to_aspirin(self):
        assert "Aspirin 75mg" in SYMPTOM_MEDICINE_MAP["chest pain"]

    def test_diabetes_condition_maps_to_insulin(self):
        assert "Insulin Regular" in CONDITION_MEDICINE_MAP["diabetes"]

    def test_asthma_condition_maps_to_salbutamol(self):
        assert "Salbutamol Inhaler" in CONDITION_MEDICINE_MAP["asthma"]
