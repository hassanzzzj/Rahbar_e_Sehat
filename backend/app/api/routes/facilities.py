"""Facility search API routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from app.agents.facility_matching_agent import InMemoryFacilityStore, haversine_km
from app.config import get_settings
from app.models.schemas import APIResponse, FacilityInfo, FacilitySearchRequest, FacilityType

router = APIRouter()

_facility_store: Optional[InMemoryFacilityStore] = None


def get_facility_store() -> InMemoryFacilityStore:
    """Get or create the global facility store."""
    global _facility_store
    if _facility_store is None:
        _facility_store = InMemoryFacilityStore()
        _facility_store.load_from_file(get_settings().facility_data_path)
    return _facility_store


@router.post("/facilities/search", response_model=APIResponse)
async def search_facilities(request: FacilitySearchRequest) -> APIResponse:
    """
    Search for nearby healthcare facilities based on location and requirements.

    Returns facilities sorted by distance, filtered by type if specified.
    """
    store = get_facility_store()
    facilities = await store.get_facilities()

    results: List[tuple[float, Dict[str, Any]]] = []
    for fac in facilities:
        fac_lat = fac.get("latitude")
        fac_lng = fac.get("longitude")
        if fac_lat is None or fac_lng is None:
            continue

        if request.facility_type and fac.get("facility_type") != request.facility_type.value:
            continue

        distance = haversine_km(request.latitude, request.longitude, fac_lat, fac_lng)
        if distance > request.max_distance_km:
            continue

        results.append((distance, fac))

    results.sort(key=lambda x: x[0])

    facility_list = []
    for distance, fac in results:
        facility_list.append({
            "facility_id": fac.get("facility_id", fac.get("id", "")),
            "name": fac.get("name", ""),
            "facility_type": fac.get("facility_type", ""),
            "address": fac.get("address", ""),
            "distance_km": round(distance, 2),
            "services_available": fac.get("services", []),
            "emergency_capable": fac.get("emergency_capable", False),
            "phone_number": fac.get("phone_number"),
        })

    return APIResponse(
        success=True,
        data={
            "facilities": facility_list,
            "total_count": len(facility_list),
            "search_radius_km": request.max_distance_km,
        },
        error=None,
    )


@router.get("/facilities/{facility_id}", response_model=APIResponse)
async def get_facility(facility_id: str) -> APIResponse:
    """Get details of a specific facility."""
    store = get_facility_store()
    facilities = await store.get_facilities()

    for fac in facilities:
        if fac.get("facility_id") == facility_id or fac.get("id") == facility_id:
            services_raw = fac.get("services", [])
            if isinstance(services_raw, str):
                import json
                try:
                    services_raw = json.loads(services_raw)
                except (json.JSONDecodeError, TypeError):
                    services_raw = []

            return APIResponse(
                success=True,
                data={
                    "facility_id": fac.get("facility_id", fac.get("id", "")),
                    "name": fac.get("name", ""),
                    "facility_type": fac.get("facility_type", ""),
                    "address": fac.get("address", ""),
                    "distance_km": 0.0,
                    "services_available": services_raw,
                    "emergency_capable": fac.get("emergency_capable", False),
                    "phone_number": fac.get("phone_number"),
                },
                error=None,
            )

    return APIResponse(
        success=False,
        data=None,
        error={"code": "NOT_FOUND", "message": f"Facility '{facility_id}' not found"},
    )
