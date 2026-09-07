.PHONY: help dev prod build test lint format clean logs down restart

# Default target
help:
	@echo "Rahbar-e-Sehat - Healthcare Triage System"
	@echo ""
	@echo "Available commands:"
	@echo "  make dev          - Start development environment"
	@echo "  make prod         - Start production environment"
	@echo "  make build        - Build all Docker images"
	@echo "  make test         - Run all tests with coverage"
	@echo "  make lint         - Run linting and type checking"
	@echo "  make format       - Format all code"
	@echo "  make clean        - Remove all containers and volumes"
	@echo "  make logs         - View logs from all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make migrate      - Run database migrations"
	@echo "  make seed         - Seed facility data"
	@echo ""

# Development environment
dev:
	docker-compose up -d --build

# Production environment
prod:
	docker-compose -f docker-compose.prod.yml up -d --build

# Build images
build:
	docker-compose build

# Run tests
test:
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run linting
lint:
	cd backend && ruff check app/ tests/
	cd backend && mypy app/
	cd frontend && npm run lint

# Format code
format:
	cd backend && ruff format app/ tests/
	cd backend && ruff check --fix app/ tests/
	cd frontend && npm run format

# Clean up
clean:
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans

# View logs
logs:
	docker-compose logs -f

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# Database migrations
migrate:
	cd backend && alembic upgrade head

# Seed data
seed:
	cd backend && python ../scripts/seed_facility_data.py

# Shell into backend
shell-backend:
	docker-compose exec backend bash

# Shell into database
shell-db:
	docker-compose exec db psql -U postgres -d rahbar_sehat
