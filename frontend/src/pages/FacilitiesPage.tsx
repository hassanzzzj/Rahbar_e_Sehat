import { useState } from "react";
import {
  MapPin,
  Navigation,
  Phone,
  Search,
  AlertTriangle,
  Building2,
  Clock,
  Stethoscope,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { SkeletonPage } from "@/components/common/SkeletonPage";
import { tokens } from "@/lib/design-tokens";
import { api, ApiClientError } from "@/lib/api-client";
import type { FacilityInfo, FacilitySearchResult } from "@/types/api";

/* ── Facility type badge colours ────────────────────────────── */
const FACILITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  EMERGENCY: { bg: "#FDF2F1", text: "#B52D24", border: "#F4C1BE" },
  TERTIARY:  { bg: "#FDF8EE", text: "#C47A18", border: "#F5DFA0" },
  DHQ:       { bg: "#EEF4F0", text: "#276142", border: "#B0D2BC" },
  THQ:       { bg: "#EEF4F0", text: "#357A53", border: "#B0D2BC" },
  RHC:       { bg: "#F9F8F6", text: "#4D4842", border: "#E5E1DA" },
  BHU:       { bg: "#F9F8F6", text: "#66605A", border: "#E5E1DA" },
};

function FacilityTypeBadge({ type }: { type: string }) {
  const c = FACILITY_COLORS[type] ?? FACILITY_COLORS.BHU;
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold border"
      style={{ backgroundColor: c.bg, color: c.text, borderColor: c.border }}
    >
      {type}
    </span>
  );
}

function FacilityCard({ f }: { f: FacilityInfo }) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-[#E5E1DA] bg-white p-5 transition-shadow duration-200 hover:shadow-[0_4px_12px_0_rgba(0,0,0,0.09)]">
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#EEF4F0]">
            <Building2 size={18} className="text-[#357A53]" aria-hidden="true" />
          </div>
          <div>
            <p className="font-semibold text-sm text-[#1A1815] leading-tight">{f.name}</p>
            <div className="mt-1 flex flex-wrap items-center gap-1.5">
              <FacilityTypeBadge type={f.facility_type} />
              {f.emergency_capable && (
                <span className="inline-flex items-center gap-0.5 rounded-full bg-[#FDF2F1] border border-[#F4C1BE] px-2 py-0.5 text-xs font-medium text-[#B52D24]">
                  <AlertTriangle size={10} aria-hidden="true" /> Emergency
                </span>
              )}
            </div>
          </div>
        </div>
        {/* Distance chip */}
        <div className="shrink-0 flex items-center gap-1 rounded-full bg-[#F2F0EC] border border-[#E5E1DA] px-2.5 py-1 text-xs font-semibold text-[#4D4842]">
          <MapPin size={11} aria-hidden="true" />
          {f.distance_km.toFixed(1)} km
        </div>
      </div>

      {/* Address */}
      <p className="flex items-start gap-1.5 text-xs text-[#66605A]">
        <MapPin size={13} className="shrink-0 mt-0.5 text-[#A8A098]" aria-hidden="true" />
        {f.address}
      </p>

      {/* Services */}
      {f.services_available.length > 0 && (
        <div className="flex items-start gap-1.5">
          <Stethoscope size={13} className="shrink-0 mt-0.5 text-[#A8A098]" aria-hidden="true" />
          <p className="text-xs text-[#66605A] leading-relaxed">
            {f.services_available.slice(0, 4).join(" · ")}
            {f.services_available.length > 4 && (
              <span className="text-[#A8A098]"> +{f.services_available.length - 4} more</span>
            )}
          </p>
        </div>
      )}

      {/* Phone */}
      {f.phone_number && (
        <a
          href={`tel:${f.phone_number}`}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-[#357A53] hover:text-[#276142] hover:underline w-fit"
        >
          <Phone size={13} aria-hidden="true" />
          {f.phone_number}
        </a>
      )}
    </div>
  );
}

/* ── Page ───────────────────────────────────────────────────── */
export default function FacilitiesPage() {
  const [lat, setLat] = useState(String(tokens.map.defaultCenter[0]));
  const [lng, setLng] = useState(String(tokens.map.defaultCenter[1]));
  const [facilities, setFacilities] = useState<FacilityInfo[] | null>(null);
  const [searchMeta, setSearchMeta] = useState<{ total: number; radius: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [locating, setLocating] = useState(false);
  const [locationUsed, setLocationUsed] = useState(false);

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser.");
      return;
    }
    setLocating(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLng(pos.coords.longitude.toFixed(6));
        setLocating(false);
        setLocationUsed(true);
      },
      () => {
        setError("Unable to get your location. Please enter coordinates manually.");
        setLocating(false);
      },
    );
  };

  const handleSearch = async () => {
    const parsedLat = parseFloat(lat);
    const parsedLng = parseFloat(lng);
    if (isNaN(parsedLat) || isNaN(parsedLng)) {
      setError("Please enter valid coordinates.");
      return;
    }
    setSearching(true);
    setError(null);
    setFacilities(null);
    setSearchMeta(null);
    try {
      const res = await api.post<FacilitySearchResult>("/facilities/search", {
        latitude: parsedLat,
        longitude: parsedLng,
        max_distance_km: 50,
      });
      if (res.data) {
        setFacilities(res.data.facilities);
        setSearchMeta({ total: res.data.total_count, radius: res.data.search_radius_km });
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Unable to search facilities.",
      );
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#F9F8F6]">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        {/* Header */}
        <div className="mb-6">
          <span className="label-uppercase text-[#357A53]">Directory</span>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#1A1815]">
            Nearby Healthcare Facilities
          </h1>
          <p className="mt-1 text-sm text-[#66605A]">
            Search for BHUs, RHCs, THQs, DHQs, and emergency centres near you.
          </p>
        </div>

        {/* Search card */}
        <Card variant="default" className="mb-6">
          {/* GPS as primary CTA */}
          <Button
            onClick={handleUseMyLocation}
            disabled={locating || searching}
            loading={locating}
            variant="primary"
            size="lg"
            className="w-full"
          >
            <Navigation size={18} aria-hidden="true" />
            {locating ? "Getting your location…" : locationUsed ? "Location found ✓ — Search again" : "Use my GPS location"}
          </Button>

          {locationUsed && (
            <p className="text-center text-xs text-[#357A53] font-medium">
              📍 {parseFloat(lat).toFixed(4)}, {parseFloat(lng).toFixed(4)}
            </p>
          )}

          {/* Divider */}
          <div className="flex items-center gap-2">
            <div className="flex-1 h-px bg-[#E5E1DA]" />
            <span className="text-xs text-[#A8A098] font-medium">or enter coordinates manually</span>
            <div className="flex-1 h-px bg-[#E5E1DA]" />
          </div>

          {/* Manual coordinates */}
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-36">
              <Input
                label="Latitude"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                disabled={searching}
                placeholder="31.5204"
              />
            </div>
            <div className="w-36">
              <Input
                label="Longitude"
                value={lng}
                onChange={(e) => setLng(e.target.value)}
                disabled={searching}
                placeholder="74.3587"
              />
            </div>
            <Button
              onClick={handleSearch}
              disabled={searching}
              loading={searching}
              variant="secondary"
              size="md"
            >
              <Search size={16} aria-hidden="true" />
              {searching ? "Searching…" : "Search"}
            </Button>
          </div>
        </Card>

        {/* Error */}
        {error && (
          <div
            role="alert"
            className="mb-4 flex items-center gap-2 rounded-xl border border-[#F4C1BE] bg-[#FDF2F1] px-4 py-3 text-sm text-[#B52D24] animate-slide-up"
          >
            <AlertTriangle size={15} className="shrink-0" aria-hidden="true" />
            {error}
          </div>
        )}

        {/* Loading */}
        {searching && !facilities && <SkeletonPage />}

        {/* Results summary */}
        {searchMeta && !searching && (
          <div className="mb-4 flex items-center gap-2">
            <Clock size={15} className="text-[#A8A098]" aria-hidden="true" />
            <p className="text-sm text-[#66605A]">
              Found{" "}
              <strong className="text-[#1A1815]">{searchMeta.total}</strong>{" "}
              {searchMeta.total === 1 ? "facility" : "facilities"} within{" "}
              <strong className="text-[#1A1815]">{searchMeta.radius} km</strong>
            </p>
          </div>
        )}

        {/* Empty state */}
        {facilities && facilities.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#D7E9DC] bg-white px-6 py-14 text-center">
            <MapPin size={32} className="text-[#B0D2BC]" aria-hidden="true" />
            <p className="mt-3 text-sm font-semibold text-[#4D4842]">No facilities found nearby</p>
            <p className="mt-1 text-xs text-[#A8A098]">
              Try a different location or increase the search radius.
            </p>
          </div>
        )}

        {/* Facility grid */}
        {facilities && facilities.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {facilities.map((f) => (
              <FacilityCard key={f.facility_id} f={f} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
