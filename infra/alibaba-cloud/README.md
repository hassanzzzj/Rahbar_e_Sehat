# Alibaba Cloud deployment notes

Rahbar-e-Sehat targets Alibaba Cloud for production. The resources below are
provisioned out-of-band (Terraform is a roadmap item); this file documents the
target topology for the deploy workflow in `.github/workflows/deploy.yml`.

## Compute

| Resource | Service | Purpose |
|---|---|---|
| Backend API cluster | ECS | Horizontally scalable FastAPI behind SLB |
| Model serving | PAI-EAS | Elastic Qwen inference |

## Data

| Resource | Service | Purpose |
|---|---|---|
| Relational DB | PolarDB / RDS | Sessions, facility directory, audit log |
| Vector store | Managed vector store / self-hosted FAISS | RAG corpus (clinical protocols) |
| Object storage | OSS | Audio inputs/outputs, logs |

## Networking

- **SLB** terminates TLS (TLS 1.2+) and routes to ECS instances.
- Internal service-to-service traffic stays on the VPC; encrypted via mTLS
  where supported.
- Public entrypoints: `/api/*`, `/webhooks/whatsapp`, and the static frontend.

## Secrets

- All credentials live in **Alibaba Cloud KMS / Secrets Manager**.
- Environment variables are injected at container start; no secrets in source
  control.

## CI/CD

`.github/workflows/deploy.yml` builds Docker images, pushes to Alibaba
Container Registry, and triggers a rolling deploy to ECS on merge to `main`.
Manual approval is required for changes touching:
- `backend/app/agents/safety_escalation_agent.py`
- `docs/threat-model.md`
- Any migration file under `backend/app/db/migrations/versions/`
