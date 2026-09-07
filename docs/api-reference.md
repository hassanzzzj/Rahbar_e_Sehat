# API Reference

All endpoints return the unified envelope:

```json
{
  "success": true,
  "data": { /* endpoint-specific payload */ },
  "error": null
}
```

On failure:

```json
{
  "success": false,
  "data": null,
  "error": { "code": "STRING_ERROR_CODE", "message": "Human-readable message" }
}
```

Base URL: `https://<host>/api/v1`

## Health

### `GET /healthz`
Liveness check. Returns `{"status": "healthy"}`.

### `GET /readyz`
Readiness check including database, vector store, and LLM service.

## Triage

### `POST /triage`

Run the full agent pipeline on a patient message.

**Request body:**
```json
{
  "message": "string, max 1000 chars",
  "channel": "whatsapp | web | voice",
  "session_id": "optional — server-generated if omitted",
  "location": { "latitude": 33.68, "longitude": 73.04 }
}
```

**Response `data`:**
```json
{
  "session_id": "uuid",
  "is_emergency": false,
  "red_flags_triggered": [],
  "urgency": "EMERGENCY | URGENT | ROUTINE | SELF_CARE",
  "recommended_facility_type": "BHU | RHC | DHQ | THQ | TERTIARY | EMERGENCY",
  "recommended_facility": { /* Facility object, see below */ },
  "medicines_available": ["paracetamol", "..."],
  "justification": "RAG-grounded reasoning trace",
  "response_urdu": "اردو میں حتمی پیغام",
  "audio_url": "https://oss/.../response.mp3"
}
```

**Error codes:**
- `VALIDATION_ERROR` (400)
- `AUTH_REQUIRED` (401)
- `RATE_LIMITED` (429)
- `TRIAGE_UNAVAILABLE` (503) — safe fallback triggered

## Facilities

### `GET /facilities`
List facilities, optionally filtered.

Query parameters:
- `type` (optional): `BHU | RHC | DHQ | THQ | TERTIARY | EMERGENCY`
- `near=lat,lng` (optional)
- `radius_km` (optional, default 50)
- `limit` (optional, default 20, max 100)

**Response `data`:** array of `Facility` objects.

### `GET /facilities/{id}`
Single facility detail, including current medicine stock signals.

## WhatsApp webhook

### `POST /webhooks/whatsapp`
Verified webhook endpoint for WhatsApp Business API callbacks.
- Rate-limited.
- Input is sanitized before reaching any downstream agent.
- Returns `200 OK` immediately; processing is asynchronous.

## Admin (RBAC-protected)

### `GET /admin/sessions`
List anonymized triage sessions for clinical review.

### `GET /admin/audit`
Structured audit log of triage decisions.

## HTTP status codes

| Code | Meaning |
|------|---------|
| 400 | Validation failure |
| 401 | Authentication required |
| 403 | Insufficient privileges |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (safe fallback issued) |
