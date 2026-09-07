# Architecture

This document describes the runtime architecture of Rahbar-e-Sehat. For the
motivational / clinical framing, see the project-level `README.md` and the
top-level Project Documentation.

## 1. Agent pipeline

The system is a **LangGraph state machine** with six specialized agents.
Control flow is strictly sequential with one conditional bypass:

```
Patient input (Urdu voice / text via WhatsApp)
  → Symptom Intake Agent          (schema-constrained extraction)
  → Safety Escalation Agent       (DETERMINISTIC rule engine — NOT an LLM)
      → IF red flag: bypass all downstream agents, return emergency directive
      → IF no red flag: continue
  → Triage Reasoning Agent        (LLM + RAG, structured output only)
  → Facility-Matching RAG Agent   (geo-indexed retrieval)
  → Medicine Availability Agent   (stock-check against facility dataset)
  → Supervisor Agent              (synthesizes final Urdu text + voice)
```

The Safety Escalation Agent is the system's **core trust guarantee**. It
runs on validated structured output from the Symptom Intake Agent, is
implemented as plain Python (no LLM call), and is 100% branch-covered by
unit tests. Changes to its rule file are treated with the same rigor as
database migrations.

## 2. Trust boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ Public boundary: WhatsApp webhook + web frontend            │
│   • Rate-limited, input-sanitized, schema-validated         │
│   • No raw PII logged alongside clinical content            │
└──────────────────┬──────────────────────────────────────────┘
                   │ authenticated HTTPS
┌──────────────────▼──────────────────────────────────────────┐
│ API layer (FastAPI)                                         │
│   • Token-based auth, RBAC                                  │
│   • Exception handlers return unified API envelope          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ Agent orchestration (LangGraph)                             │
│   • Safety Escalation Agent is out-of-band from LLM context │
│   • Each agent boundary enforces a Pydantic schema          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ Data layer                                                  │
│   • PolarDB / RDS (encrypted at rest)                       │
│   • FAISS vector store (clinical protocols)                 │
│   • OSS bucket (audio, logs)                                │
└─────────────────────────────────────────────────────────────┘
```

## 3. Deployment topology

- **Compute**: Alibaba Cloud ECS (stateless FastAPI services, horizontally
  scalable behind load balancer) and PAI-EAS (elastic model serving).
- **Storage**: OSS for audio objects and RAG corpora; PolarDB/RDS for
  structured records; FAISS (or managed vector store) for embeddings.
- **Delivery channel**: WhatsApp Business API for patient interaction.
- **CI/CD**: GitHub Actions run lint, type-check, unit/integration tests,
  dependency/container scanning, and deploy to Alibaba Cloud on merge to
  `main`.

## 4. Graceful degradation

If the LLM reasoning layer is unavailable, the system returns a **safe
default**: the nearest facility recommendation based on location alone.
The system must never fail into silence. Every external call has explicit
timeouts, bounded retries with exponential backoff, and a defined fallback.

## 5. Observability

- Structured, centralized logging with explicit levels (DEBUG/INFO/WARN/ERROR).
- Audit log of anonymized triage decisions for clinical review and drift
  detection.
- Health check endpoints: `/api/v1/healthz` (liveness), `/api/v1/readyz`
  (readiness including DB, vector store, LLM service).
