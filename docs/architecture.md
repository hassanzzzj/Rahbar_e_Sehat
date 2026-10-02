# Runtime Architecture

This document describes the implemented prototype. Production integrations
listed at the end are roadmap targets, not current runtime components.

## 1. Current pipeline

The backend uses a LangGraph state graph. Voice recorded in the React web app
is first sent to `/api/v1/transcribe`; its transcript can then be submitted
through the triage endpoint. Typed text goes directly to triage.

```
Symptom Intake (Groq LLM; deterministic regex fallback)
  → Safety Escalation (rule-based)
      → Emergency: return an emergency-marked response and stop
      → No emergency:
          Triage Reasoning (Groq LLM + protocol RAG)
            → Facility Matching
              → Medicine Availability
                → Final response (Urdu text + optional audio)
```

Facility matching and medicine availability execute sequentially. Safety
escalation checks structured symptom fields with deterministic phrase/rule
matching; it does not call an LLM. Triage reasoning retrieves clinical
protocol context and has a deterministic fallback when LLM output cannot be
used. The current `patient_message_urdu` value is the extracted primary
symptom, not a generated full guidance narrative. The response may include
gTTS audio encoded as a data URL; it is not an OSS-hosted audio link.

## 2. Current implementation

- **Frontend**: React + TypeScript web app with typed symptom input and a
  browser voice recorder.
- **API**: FastAPI routes under the configured API prefix, `/api/v1` by
  default. The application registers health, triage, facilities, admin,
  session, and speech routes. No WhatsApp webhook route is registered.
- **LLM and ASR**: Groq's OpenAI-compatible chat completions endpoint using
  `llama-3.3-70b-versatile`, and Groq transcription using `whisper-large-v3`.
- **TTS**: gTTS.
- **Retrieval**: sentence-transformers
  `paraphrase-multilingual-MiniLM-L12-v2` embeddings with an in-memory FAISS
  index for clinical protocol retrieval.
- **Facility and medicine stores**: JSON files loaded into in-memory stores
  at application startup. This triage path checks the bundled inventory; it
  does not query live facility systems.
- **Readiness endpoint**: `/api/v1/readyz` currently returns fixed `ok`
  check values; its database, vector-store, and LLM checks are TODOs, not live
  dependency probes.

## 3. Data

The pilot/sample data includes 17 facilities in
`backend/data/facilities.json`, 77 medicine records covering 13 facilities
in `backend/data/medicines.json`, and five clinical protocol documents in
`backend/data/protocols/`. These files are not a comprehensive or live
clinical, facility, or inventory source.

## 4. Known limitations

- Safety phrase matching does not account for negation. When a rule's other
  conditions match, “no arm pain” can still satisfy its arm-pain phrase
  check.
- Medicine inventory is static sample data.
- LLM, ASR, and TTS rely on third-party services; triage and voice workflows
  require network access and there is no offline triage/transcription mode.
- The prototype has not undergone formal clinical validation.
- Session state is held in process memory; admin statistics and session
  listing are placeholders, not a persistent clinical audit system.

## 5. Target Production Architecture (Roadmap)

The following are planned architecture targets and are not implemented
integrations in the current prototype:

- Qwen models through Alibaba Model Studio for LLM reasoning.
- Alibaba Speech services.
- PAI-EAS for model serving and Alibaba Cloud ECS for application hosting.
- PolarDB for production structured data.
- WhatsApp Business API for patient messaging.
