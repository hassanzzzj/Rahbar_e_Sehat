# Operations Runbook

## 1. Services

| Service | Port | Health endpoint |
|---|---|---|
| Backend (FastAPI) | 8000 | `/api/v1/healthz`, `/api/v1/readyz` |
| Frontend (Vite/nginx) | 5173 / 80 | `/healthz` |
| PostgreSQL | 5432 | — |

## 2. Common operations

### Start local dev
```bash
make dev            # docker compose up (backend + frontend + db)
make test           # backend tests with coverage
```

### Run the Safety Escalation Agent tests in isolation
```bash
cd backend
pytest tests/unit/test_safety_escalation_agent.py -v --cov=app/agents/safety_escalation_agent
```

### Apply a database migration
```bash
make migrate
```

### Seed facility data (one-time per environment)
```bash
python scripts/seed_facility_data.py
```

## 3. Incident response

### Triage pipeline returning 503 across the board
1. Check `/api/v1/readyz` — identify which dependency is down (db, vector
   store, LLM).
2. Check logs for `TRIAGE_UNAVAILABLE` events — the system issues a safe
   fallback response directing patients to the nearest facility.
3. Restore the failing dependency. No data loss; no unsafe output was
   served.

### Suspected prompt-injection attempt
1. Identify the session token from the error / audit log.
2. Inspect the sanitized input stored with the session — do NOT retrieve the
   raw PII without authorization.
3. If confirmed adversarial, add the pattern to the input validator's
   denylist in `backend/app/utils/validators.py` and open a PR with a
   regression test.

### Safety Escalation Agent missed a red flag
1. This is a safety incident. Treat as a P0.
2. Reproduce with a unit test in `tests/unit/test_safety_escalation_agent.py`
   BEFORE modifying the agent.
3. Add the missing rule, confirm 100% branch coverage, and ship.
4. Review recent audit log for any patient sessions that may have been
   mis-triaged due to the gap; escalate to clinical reviewer.

### PII exposure suspected in logs
1. Rotate the field-level encryption key in the secrets manager.
2. Scrub the affected log segment.
3. Audit the access pattern that produced the leak and close the source.

## 4. Deployment

Production deploy is triggered on merge to `main` via
`.github/workflows/deploy.yml`. Manual intervention is only required for:
- Rotation of Alibaba Cloud access keys (secret manager).
- Database migrations with breaking schema changes.
- Safety Escalation rule changes requiring clinical sign-off.
