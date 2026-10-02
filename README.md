# Rahbar-e-Sehat (رہبرِ صحت)

**Autonomous Multi-Agent Healthcare Triage & Referral System**

*Har Bemaar Ka Sahi Rasta — Every Patient's Right Path*

---

## Overview

Rahbar-e-Sehat is an autonomous multi-agent AI system that solves patient misrouting in Pakistan's healthcare system. Rather than attempting diagnosis, the system helps patients understand the urgency of their condition and directs them to the correct tier of care (Basic Health Unit, Rural Health Centre, District/Tehsil Headquarters Hospital, or emergency facility).

The prototype is a web application with a FastAPI backend and a LangGraph triage workflow. It accepts typed symptoms and recorded voice (transcribed before triage), and uses a small pilot dataset of clinical protocols, facilities, and medicine inventory. It is a decision-support prototype, not a diagnostic service.

## Architecture

```
Patient Input (web: typed text or recorded voice)
        │
        ▼
│ Voice is transcribed by Groq Whisper before triage │
            │
            ▼
Symptom Intake (LLM + regex fallback)
        │
        ▼
Safety Escalation (rule-based)
       ├── Emergency → emergency-marked response (downstream stages skipped)
        └── No emergency
               │
               ▼
        Triage Reasoning (LLM + RAG)
               │
               ▼
        Facility Matching
               │
               ▼
        Medicine Availability
               │
               ▼
        Response (Urdu text + optional audio)
```

Facility matching and medicine availability run sequentially, and both are skipped for an emergency short-circuit.

## Current Prototype Stack

| Layer | Technology |
|---|---|
| LLM | Groq, `llama-3.3-70b-versatile`, through an OpenAI-compatible client |
| ASR | Groq `whisper-large-v3` |
| TTS | gTTS |
| Embeddings and vector search | sentence-transformers `paraphrase-multilingual-MiniLM-L12-v2` + FAISS |
| Agent orchestration | LangGraph |
| Backend API | FastAPI (Python) |
| Frontend | React + TypeScript web app with a voice recorder |
| Facility and medicine data | JSON files loaded into in-memory stores |
| Local containerization | Docker |

## Target Production Architecture (Roadmap)

These are proposed production targets, not integrations implemented by the current prototype:

- Qwen through Alibaba Model Studio for LLM reasoning.
- Alibaba Speech for speech services.
- PAI-EAS for model serving and ECS for application compute.
- PolarDB for structured production data.
- WhatsApp Business API as a patient delivery channel.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Network access and a Groq API key for hosted LLM and speech recognition calls

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/hassanzzzj/Rahbar_e_Sehat
cd Rahbar_e_Sehat
```

2. Configure the required environment variables for the backend (see below).
```bash
# Set GROQ_API_KEY and the required application/database/security settings.
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

The backend reads settings from its environment (and `.env` when present). Key variables:

- `SECRET_KEY` - Application secret key (32+ characters)
- `DATABASE_URL` - PostgreSQL connection string
- `GROQ_API_KEY` - Groq API key for LLM and Whisper requests
- `ENCRYPTION_KEY` - Field-level encryption key (32 bytes)
- `JWT_SECRET_KEY` - Secret used to sign anonymous session tokens

The Groq model defaults to `llama-3.3-70b-versatile`; the transcription model defaults to `whisper-large-v3`.

## Data

The bundled pilot/sample dataset contains 17 facilities in `backend/data/facilities.json`, 77 medicine records covering 13 facilities in `backend/data/medicines.json`, and five clinical protocol documents in `backend/data/protocols/`. This is sample data, not a live or comprehensive directory or inventory.

## Known Limitations

- Safety rules do not handle negation; when other conditions for a rule match, “no arm pain” can still satisfy its arm-pain phrase check.
- Medicine inventory is static sample data and is not synchronized with facilities.
- LLM, speech recognition, and speech synthesis depend on third-party services; network access is required for triage and voice workflows.
- There is no offline triage or transcription mode.
- The prototype has not undergone formal clinical validation.

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

### Production Deployment Roadmap

Alibaba Cloud ECS, PAI-EAS, PolarDB, Alibaba Speech, and WhatsApp Business API are roadmap targets. They are not presented as deployed integrations in this prototype; see `docs/architecture.md`.

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
