/**
 * Shared API types. Mirrors the backend's Pydantic schemas so the frontend
 * and backend agree on the unified API response envelope.
 */

export type TriageUrgency = "EMERGENCY" | "URGENT" | "ROUTINE" | "SELF_CARE";

export type FacilityType = "BHU" | "RHC" | "THQ" | "DHQ" | "TERTIARY" | "EMERGENCY";

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface APIResponse<T> {
  success: boolean;
  data: T | null;
  error: ErrorDetail | null;
}

export interface FacilityInfo {
  facility_id: string;
  name: string;
  facility_type: FacilityType;
  address: string;
  distance_km: number;
  services_available: string[];
  emergency_capable: boolean;
  phone_number?: string | null;
}

export interface MedicineAvailability {
  facility_id: string;
  medicines_checked: string[];
  medicines_available: string[];
  medicines_unavailable: string[];
  last_updated: string;
}

export interface TriageResponse {
  session_id: string;
  is_emergency: boolean;
  urgency?: TriageUrgency | null;
  recommended_facility?: FacilityInfo | null;
  medicine_status?: MedicineAvailability | null;
  patient_message_urdu: string;
  audio_url?: string | null;
  reasoning_trace?: string | null;
}

export interface SymptomIntakeRequest {
  patient_message: string;
  phone_number?: string;
  location_lat?: number;
  location_lng?: number;
}

export interface FacilitySearchRequest {
  latitude: number;
  longitude: number;
  facility_type?: FacilityType;
  max_distance_km?: number;
}

export interface FacilitySearchResult {
  facilities: FacilityInfo[];
  total_count: number;
  search_radius_km: number;
}

export interface AdminStats {
  total_sessions: number;
  emergency_cases: number;
  average_response_time_ms: number;
  active_agents: number;
}

export interface AdminSessionList {
  sessions: unknown[];
  total: number;
}

export interface SessionCreateResponse {
  session_id: string;
  token: string;
  expires_at: string;
}

export interface SessionStatusResponse {
  session_id: string;
  status: string;
  created_at: string;
}

export interface TranscribeResponse {
  text: string;
}
