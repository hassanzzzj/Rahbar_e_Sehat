# Threat Model

This is a living document. Review it whenever the architecture or data flow
changes.

## 1. Assets

| Asset | Sensitivity | Notes |
|---|---|---|
| Patient symptom text + audio | HIGH | Health data; not diagnostic, but sensitive |
| Phone numbers / WhatsApp IDs | HIGH | PII |
| Session tokens | MEDIUM | Linkable to PII via phone_hash mapping |
| Facility directory | LOW | Publicly derivable |
| Medicine stock dataset | MEDIUM | Operational, not personal |
| LLM prompts / RAG corpus | LOW | Not secret, but tamper-sensitive |
| Safety Escalation rules | HIGH-integrity | Tampering here endangers lives |

## 2. Adversaries

- **Casual abuser**: spamming the WhatsApp webhook.
- **Targeted attacker**: crafting prompt-injection payloads in symptom text.
- **Insider**: authorized operator attempting to re-identify patients.
- **Supply-chain adversary**: compromising dependencies or container images.

## 3. Threats and mitigations

### 3.1 Prompt injection via symptom text
- **Risk**: adversarial input tricks the Triage Reasoning Agent into producing
  unsafe recommendations.
- **Mitigations**:
  - Strict Pydantic schemas at every agent boundary (`extra="forbid"`).
  - Max length + character allowlist on free-text fields.
  - User input isolated in clearly delimited blocks inside prompts.
  - LLM output re-validated against schema before use; fail-safe fallback on
    schema mismatch.

### 3.2 Bypassing the Safety Escalation Agent
- **Risk**: attacker convinces the system to skip red-flag detection.
- **Mitigations**:
  - Safety agent is deterministic Python, executed unconditionally on the
    validated `ExtractedSymptoms` schema.
  - It is **entirely out-of-band** from LLM context — no LLM output can alter
    its rule set at runtime.
  - Rule file is versioned and reviewed like a migration.

### 3.3 PII leakage via logs
- **Risk**: raw phone numbers or names logged alongside symptom content.
- **Mitigations**:
  - Tokenized `session_token` + `phone_hash` used everywhere except the
    WhatsApp client adapter.
  - PII fields encrypted at rest using Fernet field-level encryption.
  - Structured logger redacts known sensitive field names.

### 3.4 WhatsApp webhook abuse / DoS
- **Mitigations**:
  - Rate-limit middleware on `/webhooks/whatsapp`.
  - Signature verification against Meta webhook secret.
  - Async processing to decouple request acceptance from agent pipeline.

### 3.5 Compromised dependencies / images
- **Mitigations**:
  - Pinned versions + `pip-audit` / `npm audit` in CI.
  - Multi-stage Docker builds, non-root runtime user, minimal base images.
  - Trivy container scanning in `security-scan.yml`.

### 3.6 Re-identification by insider
- **Mitigations**:
  - Phone numbers and clinical content stored in separate records linked
    only via one-way hash.
  - RBAC on admin endpoints; access logged in audit trail.

## 4. Out of scope

- Compromise of Alibaba Cloud's underlying infrastructure.
- Compromise of Meta's WhatsApp transport (we rely on E2E encryption there).
