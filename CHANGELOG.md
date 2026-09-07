# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with multi-agent architecture
- Safety Escalation Agent with deterministic rule engine (100% branch coverage)
- Pydantic schemas for schema-constrained agent inputs/outputs
- FastAPI backend foundation with security, logging, and rate limiting
- Docker configuration for local development and production
- CI/CD pipeline with linting, testing, and security scanning
- Comprehensive test suite for safety agent

### Security
- Field-level encryption for PII
- Tokenized session identifiers
- Rate limiting middleware
- Input validation at API boundary
- RBAC framework

## [0.1.0] - 2026-01-15

### Added
- Project initialization
- Architecture design and documentation
- Repository setup with GitHub workflows

[Unreleased]: https://github.com/your-org/rahbar-e-sehat/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/rahbar-e-sehat/releases/tag/v0.1.0
