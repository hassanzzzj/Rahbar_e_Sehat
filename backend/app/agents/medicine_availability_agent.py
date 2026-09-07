"""
Medicine Availability Agent — deterministic medicine stock checking.

Checks whether the matched facility has the medicines likely needed
for the patient's condition. Medicine inference is rule-based (no LLM):
symptoms and conditions are mapped to standard treatment protocols.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set

from app.core.exceptions import MedicineAvailabilityError
from app.core.logging import get_logger
from app.models.schemas import (
    ExtractedSymptoms,
    MedicineAvailability,
    SymptomSeverity,
    TriageClassification,
    TriageUrgency,
)

logger = get_logger(__name__)

# Symptom/condition keyword to medicine name mapping
# Based on WHO Essential Medicines List and Pakistan National Formulary
SYMPTOM_MEDICINE_MAP: Dict[str, List[str]] = {
    # Fever / infections
    "fever": ["Paracetamol 500mg"],
    "high fever": ["Paracetamol 500mg", "Ceftriaxone 1g"],
    "typhoid": ["Ceftriaxone 1g", "Paracetamol 500mg"],
    "infection": ["Amoxicillin 500mg"],
    "urinary infection": ["Amoxicillin 500mg"],
    "ear infection": ["Amoxicillin 500mg"],
    "throat infection": ["Amoxicillin 500mg", "Paracetamol 500mg"],
    # Respiratory
    "cough": ["Amoxicillin 500mg"],
    "difficulty breathing": ["Salbutamol Inhaler"],
    "shortness of breath": ["Salbutamol Inhaler"],
    "breathing difficulty": ["Salbutamol Inhaler"],
    "asthma": ["Salbutamol Inhaler"],
    "wheezing": ["Salbutamol Inhaler"],
    "pneumonia": ["Ceftriaxone 1g", "Paracetamol 500mg"],
    # Cardiac
    "chest pain": ["Aspirin 75mg", "Clopidogrel 75mg", "Epinephrine 1mg"],
    "heart attack": ["Aspirin 75mg", "Clopidogrel 75mg", "Streptokinase"],
    "cardiac arrest": ["Epinephrine 1mg"],
    # Stroke
    "stroke": ["tPA (Alteplase)"],
    "weakness one side": ["Aspirin 75mg"],
    # Diabetes
    "diabetes": ["Insulin Regular", "Metformin 500mg"],
    "high blood sugar": ["Insulin Regular"],
    # Hypertension
    "high blood pressure": ["Amlodipine 5mg"],
    "hypertension": ["Amlodipine 5mg"],
    # Allergic / anaphylaxis
    "allergic reaction": ["Hydrocortisone 100mg", "Epinephrine 1mg"],
    "anaphylaxis": ["Epinephrine 1mg", "Hydrocortisone 100mg"],
    # GI
    "diarrhea": ["ORS Sachets"],
    "vomiting": ["ORS Sachets"],
    "dehydration": ["ORS Sachets"],
    "stomach pain": ["Paracetamol 500mg"],
    "abdominal pain": ["Paracetamol 500mg"],
    # Pain
    "pain": ["Paracetamol 500mg"],
    "headache": ["Paracetamol 500mg"],
    "body ache": ["Paracetamol 500mg"],
    "severe pain": ["Paracetamol 500mg", "Morphine 10mg"],
    # Trauma
    "injury": ["Paracetamol 500mg", "Ceftriaxone 1g"],
    "burn": ["Morphine 10mg", "Ceftriaxone 1g"],
    "fracture": ["Paracetamol 500mg", "Morphine 10mg"],
    # Bleeding
    "bleeding": ["Epinephrine 1mg"],
}

# Conditions from pre_existing_conditions to medicines
CONDITION_MEDICINE_MAP: Dict[str, List[str]] = {
    "diabetes": ["Insulin Regular", "Metformin 500mg"],
    "hypertension": ["Amlodipine 5mg"],
    "asthma": ["Salbutamol Inhaler"],
    "copd": ["Salbutamol Inhaler"],
    "heart disease": ["Aspirin 75mg", "Clopidogrel 75mg"],
    "kidney disease": ["Amlodipine 5mg"],
}


class MedicineStoreProtocol(Protocol):
    """Protocol for medicine inventory data retrieval."""

    async def get_inventory(self, facility_id: str) -> List[Dict[str, Any]]:
        """Return medicine inventory records for a facility."""
        ...


@dataclass
class MedicineCheckInput:
    """Input for the Medicine Availability Agent."""

    facility_id: str
    symptoms: ExtractedSymptoms
    classification: TriageClassification


@dataclass
class MedicineCheckOutput:
    """Output from the Medicine Availability Agent."""

    availability: MedicineAvailability
    medicines_needed: List[str] = field(default_factory=list)
    all_available: bool = False
    missing_critical: bool = False


class MedicineAvailabilityAgent:
    """Deterministic medicine stock checker."""

    def __init__(self, medicine_store: MedicineStoreProtocol) -> None:
        self._store = medicine_store

    async def check(self, input_data: MedicineCheckInput) -> MedicineCheckOutput:
        """Check medicine availability at the given facility."""
        medicines_needed = self._infer_medicines(input_data.symptoms, input_data.classification)

        if not medicines_needed:
            return MedicineCheckOutput(
                availability=MedicineAvailability(
                    facility_id=input_data.facility_id,
                    medicines_checked=[],
                    medicines_available=[],
                    medicines_unavailable=[],
                    last_updated=datetime.now(timezone.utc),
                ),
                medicines_needed=[],
                all_available=True,
                missing_critical=False,
            )

        inventory = await self._store.get_inventory(input_data.facility_id)
        stock = self._build_stock_map(inventory)

        available: List[str] = []
        unavailable: List[str] = []

        for medicine in medicines_needed:
            if stock.get(medicine, 0) > 0:
                available.append(medicine)
            else:
                unavailable.append(medicine)

        missing_critical = self._has_missing_critical(
            unavailable, input_data.classification.urgency
        )

        last_updated = self._get_latest_timestamp(inventory)

        result = MedicineCheckOutput(
            availability=MedicineAvailability(
                facility_id=input_data.facility_id,
                medicines_checked=medicines_needed,
                medicines_available=available,
                medicines_unavailable=unavailable,
                last_updated=last_updated,
            ),
            medicines_needed=medicines_needed,
            all_available=len(unavailable) == 0,
            missing_critical=missing_critical,
        )

        logger.info(
            "medicine_check.complete",
            facility_id=input_data.facility_id,
            checked=len(medicines_needed),
            available=len(available),
            unavailable=len(unavailable),
        )

        return result

    def _infer_medicines(
        self,
        symptoms: ExtractedSymptoms,
        classification: TriageClassification,
    ) -> List[str]:
        """Infer needed medicines from symptoms and classification using rule-based mapping."""
        needed: Set[str] = set()

        primary = symptoms.primary_symptom.lower()
        for keyword, meds in SYMPTOM_MEDICINE_MAP.items():
            if keyword in primary:
                needed.update(meds)

        all_symptoms = symptoms.secondary_symptoms + symptoms.associated_symptoms
        for symptom in all_symptoms:
            symptom_lower = symptom.lower()
            for keyword, meds in SYMPTOM_MEDICINE_MAP.items():
                if keyword in symptom_lower:
                    needed.update(meds)

        for condition in symptoms.pre_existing_conditions:
            condition_lower = condition.lower()
            for keyword, meds in CONDITION_MEDICINE_MAP.items():
                if keyword in condition_lower:
                    needed.update(meds)

        if symptoms.severity == SymptomSeverity.SEVERE:
            needed.add("Epinephrine 1mg")

        if classification.urgency in (TriageUrgency.EMERGENCY, TriageUrgency.URGENT):
            needed.add("Ceftriaxone 1g")

        if not needed:
            needed.add("Paracetamol 500mg")

        return sorted(needed)

    @staticmethod
    def _build_stock_map(inventory: List[Dict[str, Any]]) -> Dict[str, int]:
        """Build a medicine_name -> quantity map from inventory records."""
        stock: Dict[str, int] = {}
        for record in inventory:
            name = record.get("medicine_name", "")
            qty = record.get("quantity_available", 0)
            if name:
                stock[name] = stock.get(name, 0) + qty
        return stock

    @staticmethod
    def _has_missing_critical(unavailable: List[str], urgency: TriageUrgency) -> bool:
        """Check if any critical medicines are missing for the given urgency level."""
        if not unavailable:
            return False
        if urgency == TriageUrgency.EMERGENCY:
            critical = {"Epinephrine 1mg", "Morphine 10mg", "Streptokinase", "tPA (Alteplase)"}
            return bool(set(unavailable) & critical)
        if urgency == TriageUrgency.URGENT:
            important = {"Ceftriaxone 1g", "Epinephrine 1mg", "Insulin Regular", "Salbutamol Inhaler"}
            return bool(set(unavailable) & important)
        return False

    @staticmethod
    def _get_latest_timestamp(inventory: List[Dict[str, Any]]) -> datetime:
        """Get the most recent timestamp from inventory records."""
        latest = datetime.now(timezone.utc)
        for record in inventory:
            ts = record.get("last_updated")
            if isinstance(ts, datetime) and ts > latest:
                latest = ts
        return latest


class InMemoryMedicineStore:
    """Loads medicine inventory from a JSON file into memory."""

    def __init__(self, data_path: Optional[str] = None) -> None:
        self._inventory: Dict[str, List[Dict[str, Any]]] = {}
        if data_path:
            self.load_from_file(data_path)

    def load_from_file(self, path: str) -> int:
        """Load medicine inventory from a JSON file. Returns total records loaded."""
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("medicine_store.file_not_found", path=path)
            return 0

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.error("medicine_store.invalid_format", path=path)
            return 0

        self._inventory = {}
        for record in data:
            facility_id = record.get("facility_id", "")
            if facility_id:
                self._inventory.setdefault(facility_id, []).append(record)

        total = sum(len(v) for v in self._inventory.values())
        logger.info(
            "medicine_store.loaded",
            total_records=total,
            facilities=len(self._inventory),
            path=path,
        )
        return total

    def load_from_list(self, records: List[Dict[str, Any]]) -> None:
        """Load inventory directly from a list."""
        self._inventory = {}
        for record in records:
            facility_id = record.get("facility_id", "")
            if facility_id:
                self._inventory.setdefault(facility_id, []).append(record)

    async def get_inventory(self, facility_id: str) -> List[Dict[str, Any]]:
        """Return inventory records for a specific facility."""
        return list(self._inventory.get(facility_id, []))
