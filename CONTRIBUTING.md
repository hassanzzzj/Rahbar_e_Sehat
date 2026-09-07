# Contributing to Rahbar-e-Sehat

Thank you for your interest in contributing to Rahbar-e-Sehat! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct (`CODE_OF_CONDUCT.md`).

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write or update tests
5. Ensure all tests pass: `make test`
6. Commit your changes with a clear message
7. Push to your fork and submit a pull request

## Branch Naming

Use descriptive branch names with prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `security/` - Security improvements
- `docs/` - Documentation updates
- `test/` - Test additions
- `refactor/` - Code refactoring

Example: `feature/add-urdu-speech-support`

## Coding Standards

### Python (Backend)

- Follow PEP 8 with ruff formatting
- Type-annotate all code (mypy-clean)
- Use docstrings explaining *why*, not *what*
- Keep functions small and single-purpose
- Use early returns and guard clauses
- No magic numbers/strings (use named constants/enums)

### TypeScript (Frontend)

- Use TypeScript (not plain JavaScript)
- Functional components with hooks only
- Follow ESLint and Prettier configurations
- Semantic HTML5 tags only
- 8px grid system for all spacing
- 60-30-10 color palette (no neon gradients)

### Testing Requirements

- **Unit tests** for all agent logic
- **100% branch coverage** on Safety Escalation Agent
- **Integration tests** for full pipeline paths
- **Contract tests** for external API calls (mocked)
- Run tests before committing: `make test`

### Security Requirements

- Never log PII alongside clinical data
- Validate all inputs at API boundary
- Use parameterized queries (no string concatenation)
- Never commit secrets or credentials
- Sanitize user input before LLM prompts

## Pull Request Process

1. Ensure your code passes all CI checks:
   - Linting (ruff, eslint)
   - Type checking (mypy, TypeScript)
   - Unit tests
   - Integration tests
   - Coverage threshold (80%+)

2. Update documentation if needed

3. Fill out the PR template completely

4. Request review from appropriate code owners (see `.github/CODEOWNERS`)

5. Address review feedback

6. Squash and merge (maintainer will do this)

## Critical Files Requiring Extra Review

Changes to these files require security team review:

- `backend/app/core/security.py`
- `backend/app/agents/safety_escalation_agent.py`
- `backend/app/core/rate_limit.py`

## Commit Messages

Use clear, descriptive commit messages:

```
feat: add Urdu speech-to-text integration

Implement ASR support for Urdu voice notes using Alibaba Cloud
Speech Interaction service. Includes error handling and fallback
to text-only mode when speech service is unavailable.

Closes #42
```

Prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Refactoring
- `security:` - Security improvements
- `chore:` - Maintenance tasks

## Questions?

Open an issue with the `question` label or reach out to the core team.

Thank you for contributing!
