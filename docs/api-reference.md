# API Reference

The backend mounts its routes under the configured API prefix, which defaults
to `/api/v1`. Most operational routes return a `{ "success", "data",
"error" }` envelope. Session creation and session lookup return their
response schemas directly. Framework-level request validation responses
may use FastAPI's default format.

The prototype installs rate-limit middleware, but the registered route set
does not enforce bearer-token authentication or admin RBAC. Creating a
session token does not mean the other routes validate it.

## Health

### `GET /healthz`

Liveness endpoint. Returns an envelope with `data.status` set to `healthy`.

### `GET /readyz`

Returns `data.status: ready` and fixed `ok` values for database,
vector-store, and LLM checks. These checks are placeholders; they do not
probe those dependencies.

## Triage

### `POST /triage`

Runs symptom intake, rule-based safety escalation, and, unless an emergency
is detected, triage reasoning, facility matching, and medicine availability
in sequence.

**Request body:**

```json
{
  "patient_message": "string, 1-2000 characters",
  "phone_number": "optional, 10-15 digits with optional leading +",
  "location_lat": 33.68,
  "location_lng": 73.04
}
```

`phone_number`, `location_lat`, and `location_lng` are optional. Unknown
request fields are rejected. The server generates a session ID for each
triage request.

**Response `data` fields:**

```json
{
  "session_id": "uuid",
  "is_emergency": false,
  "urgency": "EMERGENCY | URGENT | ROUTINE | SELF_CARE | null",
  "recommended_facility": null,
  "medicine_status": null,
  "patient_message_urdu": "string",
  "audio_url": "optional data:audio/mpeg;base64,...",
  "reasoning_trace": "optional string"
}
```

The actual response schema does not expose a `red_flags_triggered` field or
a separate medicines-available list. Emergency responses have no triage
classification urgency. `audio_url`, when present, is a base64 data URL, not
a hosted object URL.

### `GET /triage/{session_id}`

Returns the requested ID and `status: completed` as a placeholder; it does
not retrieve a persisted triage result.

## Facilities

### `POST /facilities/search`

Searches the bundled facility dataset by required `latitude` and `longitude`,
with optional filters:

- `facility_type`: `BHU | RHC | THQ | DHQ | TERTIARY | EMERGENCY`
- `max_distance_km`: number from 0.1 to 500; defaults to 50

The response data contains `facilities`, `total_count`, and
`search_radius_km`. Results are sorted by distance.

### `GET /facilities/{facility_id}`

Returns details for one matching facility. The current response does not
include live medicine stock.

## Speech

### `POST /transcribe`

Accepts multipart form data with a required audio `file` and optional
`language` field (ISO 639-1, defaults to `ur`). Transcription uses Groq
Whisper and returns `data.text` in the response envelope.

## Sessions

### `POST /session/create`

Creates an anonymous session ID and signed JWT, with an expiry. Session
metadata is stored in process memory and the response is not wrapped in the
standard API envelope.

### `GET /session/{session_id}`

Returns the in-memory session status directly. Unknown IDs return
`status: unknown`.

## Admin

### `GET /admin/stats`

Returns placeholder zero-valued statistics; collection is not implemented.

### `GET /admin/sessions`

Returns an empty placeholder list. Session listing and PII redaction are
not implemented. This route is not RBAC-protected in the current code.

## WhatsApp

### `POST /webhooks/whatsapp` — Planned, not implemented

There is no registered WhatsApp webhook route in the current application.
WhatsApp Business API integration is a production roadmap item, not a
working endpoint.
