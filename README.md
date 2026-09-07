# Rahbar-e-Sehat (رہبرِ صحت)

**Autonomous Multi-Agent Healthcare Triage & Referral System**

*Har Bemaar Ka Sahi Rasta — Every Patient's Right Path*

---

## Overview

Rahbar-e-Sehat is an autonomous multi-agent AI system that solves patient misrouting in Pakistan's healthcare system. Rather than attempting diagnosis, the system helps patients understand the urgency of their condition and directs them to the correct tier of care (Basic Health Unit, Rural Health Centre, District/Tehsil Headquarters Hospital, or emergency facility).

The system is built as a coordinated network of specialized AI agents, orchestrated through a state-machine architecture (LangGraph), delivered over WhatsApp for zero-install accessibility, and grounded in real clinical protocols and facility data through Retrieval-Augmented Generation (RAG).

## Architecture

```
Patient Input (Urdu Voice/Text via WhatsApp)
        │
        ▼
┌───────────────────────┐
│ 1. Symptom Intake      │  Extracts structured symptom data
│    Agent               │  via schema-constrained parsing
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 2. Safety Escalation   │  Deterministic rule engine —
│    Agent (Rule-Based,  │  runs independently of the LLM
│    Non-LLM)            │  layer; can short-circuit the
└───────┬───────┬───────┘  entire pipeline
        │       │
  RED FLAG   No red flag
        │       │
        ▼       ▼
 ┌────────────┐ ┌────────────────────────┐
 │ EMERGENCY  │ │ 3. Triage Reasoning     │
 │ OUTPUT     │ │    Agent (LLM +         │
 │ (Immediate)│ │    Structured Output)   │
 └────────────┘ └───────────┬─────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
   ┌─────────────────────┐      ┌─────────────────────┐
   │ 4. Facility-Matching │      │ 5. Medicine          │
   │    RAG Agent         │      │    Availability Agent│
   └───────────┬─────────┘      └───────────┬─────────┘
               └──────────────┬─────────────┘
                               ▼
                  ┌─────────────────────────┐
                  │ 6. Supervisor Agent      │
                  │    (Response Synthesis,  │
                  │    Urdu Text + Voice)    │
                  └─────────────────────────┘
```

## Technology Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| LLM Reasoning | Qwen-Max / Qwen-Plus (Alibaba Model Studio) |
| Speech (ASR/TTS) | Alibaba Intelligent Speech Interaction (Urdu) |
| Vector Retrieval | FAISS |
| Database | PolarDB / PostgreSQL |
| Backend API | FastAPI (Python) |
| Frontend | React (TypeScript) |
| Containerization | Docker |
| Compute Hosting | Alibaba Cloud ECS / PAI-EAS |
| Delivery Channel | WhatsApp Business API |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Alibaba Cloud account with Model Studio access

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/your-org/rahbar-e-sehat.git
cd rahbar-e-sehat
```

2. Copy environment template:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Start development environment:
```bash
make dev
# Or manually: docker-compose up -d --build
```

4. Run tests:
```bash
make test
```

5. View logs:
```bash
make logs
```

### Manual Setup (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pytest tests/ -v

# Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

See `.env.example` for all required environment variables. Key variables:

- `SECRET_KEY` - Application secret key (32+ characters)
- `DATABASE_URL` - PostgreSQL connection string
- `QWEN_API_KEY` - Alibaba Cloud Model Studio API key
- `WHATSAPP_API_TOKEN` - WhatsApp Business API token
- `ENCRYPTION_KEY` - Field-level encryption key (32 bytes)

## Project Structure

```
rahbar-e-sehat/
├── backend/              # FastAPI backend with agent pipeline
│   ├── app/
│   │   ├── agents/      # LangGraph agents (intake, safety, triage, etc.)
│   │   ├── api/         # API routes and dependencies
│   │   ├── core/        # Security, logging, rate limiting
│   │   ├── models/      # Pydantic schemas and DB models
│   │   ├── rag/         # RAG retrieval and embeddings
│   │   └── integrations/ # External service clients
│   └── tests/
├── frontend/            # React patient-facing app + admin dashboard
├── infra/               # Infrastructure configs (Alibaba Cloud, nginx)
├── docs/                # Architecture, API reference, threat model
└── scripts/             # Setup and utility scripts
```

## Testing

```bash
# Run all tests with coverage
make test

# Run specific test suites
cd backend
pytest tests/unit/ -v                              # Unit tests
pytest tests/integration/ -v                        # Integration tests
pytest tests/unit/test_safety_escalation_agent.py   # Safety agent tests

# Coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Deployment

### Production Deployment

```bash
# Build and start production environment
make prod
# Or: docker-compose -f docker-compose.prod.yml up -d --build
```

### Alibaba Cloud Deployment

See `docs/architecture.md` and `infra/alibaba-cloud/` for detailed deployment instructions.

## Security

This system handles sensitive health data. See `SECURITY.md` for:

- Security model overview
- Data protection measures
- Responsible disclosure process

**Never commit `.env` files, API keys, or credentials to version control.**

## Contributing

See `CONTRIBUTING.md` for coding standards, branch naming, and PR process.

Key requirements:
- All changes via reviewed pull requests (no direct pushes to main)
- Tests required for all new functionality
- 100% branch coverage on Safety Escalation Agent
- Security review for changes to `app/core/security.py` and `app/agents/safety_escalation_agent.py`

## License

See `LICENSE` file for details.

## Acknowledgments

- **Track:** Healthcare (MedTech & Diagnostics)
- **Event:** Alibaba Cloud AI Hackathon Pakistan 2026
- **Hosted by:** Alkhidmat Foundation & Bano Qabil

---

*Built with care for Pakistan's healthcare system.*
