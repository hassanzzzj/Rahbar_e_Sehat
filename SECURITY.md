# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Security Model

Rahbar-e-Sehat handles sensitive health data and is designed with security as a first-class requirement.

### Data Protection

- **Patient PII** is never logged alongside symptom/clinical data
- Tokenized session identifiers decouple identity from clinical content
- All data at rest is encrypted using storage-level encryption
- All data in transit uses TLS 1.2+ (no plaintext HTTP anywhere)
- Field-level encryption for sensitive database fields

### Access Control

- Role-Based Access Control (RBAC) on all services and databases
- All API endpoints require authentication tokens
- Rate limiting on all public endpoints
- Safety Escalation Agent is isolated from user input paths

### Input Validation

- All inputs validated at API boundary using strict Pydantic schemas
- Max length, character allowlist, and type validation on free-text fields
- LLM outputs validated against strict schemas before downstream use
- Parameterized queries only (no string-concatenated SQL)

### Safety Guarantees

- Safety Escalation Agent is deterministic business logic, not an LLM
- Emergency detection bypasses all downstream agents immediately
- 100% branch coverage required on safety agent tests
- Changes to safety rules treated with same rigor as database migrations

## Reporting a Vulnerability

**DO NOT create a public GitHub issue for security vulnerabilities.**

Please email: **security@rahbar-e-sehat.org**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a detailed response within 7 days.

## Security Contacts

- Security Team: security@rahbar-e-sehat.org
- Core Team: core@rahbar-e-sehat.org

## Compliance

Architecture aligns with:
- Pakistan's Personal Data Protection Bill framework
- HIPAA-inspired data handling practices (adaptable for institutional partnerships)

## Dependency Management

- All dependencies are pinned to specific versions
- Automated vulnerability scanning via `pip-audit` and `npm audit`
- Dependabot configured for automated security updates
- Container scanning with Trivy in CI pipeline
