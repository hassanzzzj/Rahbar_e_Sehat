"""
Facility Matching Agent — deterministic geo-distance + capability matching.

Matches a patient to the nearest appropriate healthcare facility based on:
- Patient location (Haversine distance)
- Triage-recommended care tier
- Emergency capability requirements
- Maximum search radius

No LLM dependency — pure deterministic logic.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from app.core.exceptions import FacilityMatchingError
from app.core.logging import get_logger
from app.models.schemas import (
    ExtractedSymptoms,
    FacilityInfo,
    FacilityType,
    SafetyCheckResult,
    TriageClassification,
)

logger = get_logger(__name__)

EARTH_RADIUS_KM = 6371.0

# Care tier hierarchy — higher-tier facilities can handle lower-tier recommendations
CARE_TIER_RANK: Dict[FacilityType, int] = {
    FacilityType.BHU: 1,
    FacilityType.RHC: 2,
    FacilityType.THQ: 3,
    FacilityType.DHQ: 4,
    FacilityType.TERTIARY: 5,
    FacilityType.EMERGENCY: 5,
}


class FacilityStoreProtocol(Protocol):
    """Protocol for facility data retrieval."""

    async def get_facilities(self) -> List[Dict[str, Any]]:
        """Return all facility records."""
        ...


@dataclass
class FacilityMatchInput:
    """Input for the Facility Matching Agent."""

    classification: TriageClassification
    safety_check: SafetyCheckResult
    symptoms: ExtractedSymptoms
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class FacilityMatchOutput:
    """Output from the Facility Matching Agent."""

    recommended: Optional[FacilityInfo] = None
    alternatives: List[FacilityInfo] = field(default_factory=list)
    search_radius_km: float = 0.0
    total_candidates: int = 0
    match_reason: str = ""


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Haversine distance between two coordinates in kilometres."""
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


class FacilityMatchingAgent:
    """Deterministic facility matching using geo-distance and capability rules."""

    DEFAULT_MAX_DISTANCE_KM = 50.0
    DEFAULT_MAX_RESULTS = 5
    LAHORE_FALLBACK_COORDS = (31.5204, 74.3587)

    def __init__(
        self,
        facility_store: FacilityStoreProtocol,
        max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> None:
        self._store = facility_store
        self._max_distance_km = max_distance_km
        self._max_results = max_results

    async def match(self, input_data: FacilityMatchInput) -> FacilityMatchOutput:
        """Match a patient to the best available facility."""
        lat = input_data.latitude
        lng = input_data.longitude

        if lat is None or lng is None:
            logger.warning("facility_matching.no_location_provided")
            lat, lng = self.LAHORE_FALLBACK_COORDS

        facilities = await self._store.get_facilities()
        if not facilities:
            logger.error("facility_matching.no_facilities_loaded")
            raise FacilityMatchingError("No facilities available for matching")

        required_tier = input_data.classification.recommended_care_tier
        is_emergency = input_data.safety_check.is_emergency

        candidates = self._compute_candidates(facilities, lat, lng, required_tier, is_emergency)

        if not candidates:
            logger.warning("facility_matching.no_candidates_in_radius", radius_km=self._max_distance_km)
            candidates = self._fallback_search(facilities, lat, lng)

        if not candidates:
            raise FacilityMatchingError(
                "No facility found within search radius",
                details={"radius_km": self._max_distance_km, "lat": lat, "lng": lng},
            )

        recommended = candidates[0]
        alternatives = candidates[1 : self._max_results]

        reason = self._build_reason(is_emergency, required_tier, recommended)

        return FacilityMatchOutput(
            recommended=recommended,
            alternatives=alternatives,
            search_radius_km=self._max_distance_km,
            total_candidates=len(candidates),
            match_reason=reason,
        )

    def _compute_candidates(
        self,
        facilities: List[Dict[str, Any]],
        lat: float,
        lng: float,
        required_tier: FacilityType,
        is_emergency: bool,
    ) -> List[FacilityInfo]:
        """Filter, score, and sort facilities into ranked candidates."""
        required_rank = CARE_TIER_RANK.get(required_tier, 1)
        results: List[tuple[float, FacilityInfo]] = []

        for fac in facilities:
            fac_lat = fac.get("latitude")
            fac_lng = fac.get("longitude")
            if fac_lat is None or fac_lng is None:
                continue

            distance = haversine_km(lat, lng, fac_lat, fac_lng)
            if distance > self._max_distance_km:
                continue

            fac_type_str = fac.get("facility_type", "BHU")
            try:
                fac_type = FacilityType(fac_type_str)
            except ValueError:
                continue

            fac_rank = CARE_TIER_RANK.get(fac_type, 1)

            if fac_rank < required_rank:
                continue

            emergency_capable = bool(fac.get("emergency_capable", False))
            if is_emergency and not emergency_capable:
                continue

            services_raw = fac.get("services", "[]")
            if isinstance(services_raw, str):
                try:
                    services = json.loads(services_raw)
                except (json.JSONDecodeError, TypeError):
                    services = []
            else:
                services = services_raw if isinstance(services_raw, list) else []

            info = FacilityInfo(
                facility_id=fac.get("facility_id", fac.get("id", "unknown")),
                name=fac.get("name", "Unknown Facility"),
                facility_type=fac_type,
                address=fac.get("address", ""),
                distance_km=round(distance, 2),
                services_available=services,
                emergency_capable=emergency_capable,
                phone_number=fac.get("phone_number"),
            )

            results.append((distance, info))

        results.sort(key=lambda x: x[0])
        return [info for _, info in results]

    def _fallback_search(
        self,
        facilities: List[Dict[str, Any]],
        lat: float,
        lng: float,
    ) -> List[FacilityInfo]:
        """Fall back to nearest emergency-capable facility regardless of distance."""
        results: List[tuple[float, FacilityInfo]] = []

        for fac in facilities:
            if not fac.get("emergency_capable", False):
                continue

            fac_lat = fac.get("latitude")
            fac_lng = fac.get("longitude")
            if fac_lat is None or fac_lng is None:
                continue

            distance = haversine_km(lat, lng, fac_lat, fac_lng)

            fac_type_str = fac.get("facility_type", "BHU")
            try:
                fac_type = FacilityType(fac_type_str)
            except ValueError:
                continue

            services_raw = fac.get("services", "[]")
            if isinstance(services_raw, str):
                try:
                    services = json.loads(services_raw)
                except (json.JSONDecodeError, TypeError):
                    services = []
            else:
                services = services_raw if isinstance(services_raw, list) else []

            info = FacilityInfo(
                facility_id=fac.get("facility_id", fac.get("id", "unknown")),
                name=fac.get("name", "Unknown Facility"),
                facility_type=fac_type,
                address=fac.get("address", ""),
                distance_km=round(distance, 2),
                services_available=services,
                emergency_capable=True,
                phone_number=fac.get("phone_number"),
            )
            results.append((distance, info))

        results.sort(key=lambda x: x[0])
        return [info for _, info in results]

    @staticmethod
    def _build_reason(
        is_emergency: bool,
        required_tier: FacilityType,
        recommended: FacilityInfo,
    ) -> str:
        """Build a human-readable match reason string."""
        parts = []
        if is_emergency:
            parts.append(f"Emergency: nearest emergency-capable facility ({recommended.name})")
        else:
            parts.append(
                f"Recommended tier {required_tier.value}: matched {recommended.facility_type.value} "
                f"({recommended.name})"
            )
        parts.append(f"Distance: {recommended.distance_km} km")
        return ". ".join(parts)


class InMemoryFacilityStore:
    """Loads facility data from a JSON file into memory."""

    def __init__(self, data_path: Optional[str] = None) -> None:
        self._facilities: List[Dict[str, Any]] = []
        if data_path:
            self.load_from_file(data_path)

    def load_from_file(self, path: str) -> int:
        """Load facilities from a JSON file. Returns count loaded."""
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("facility_store.file_not_found", path=path)
            return 0

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.error("facility_store.invalid_format", path=path)
            return 0

        self._facilities = data
        logger.info("facility_store.loaded", count=len(data), path=path)
        return len(data)

    def load_from_list(self, facilities: List[Dict[str, Any]]) -> None:
        """Load facilities directly from a list."""
        self._facilities = list(facilities)

    async def get_facilities(self) -> List[Dict[str, Any]]:
        """Return all loaded facility records."""
        return list(self._facilities)
