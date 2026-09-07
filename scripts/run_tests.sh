#!/usr/bin/env bash
# Run the full backend test suite (unit + integration + contract) with coverage.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "[test] Running pytest with coverage..."
python -m pytest \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=80 \
  "$@"

echo "[test] HTML coverage report: backend/htmlcov/index.html"
