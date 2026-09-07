#!/usr/bin/env bash
# Bootstrap script for fresh development machines.
# Installs dependencies, sets up pre-commit hooks, and seeds local data.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[setup] Checking prerequisites..."
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
command -v node >/dev/null || { echo "node is required"; exit 1; }
command -v docker >/dev/null || { echo "docker is required"; exit 1; }

echo "[setup] Installing pre-commit hooks..."
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet pre-commit
pre-commit install

echo "[setup] Setting up backend virtual environment..."
python3 -m venv "$ROOT/backend/.venv"
# shellcheck disable=SC1091
source "$ROOT/backend/.venv/bin/activate"
pip install --quiet -r "$ROOT/backend/requirements.txt"
pip install --quiet -r "$ROOT/backend/requirements-dev.txt"

echo "[setup] Copying .env.example files..."
for f in "$ROOT/.env.example" "$ROOT/backend/.env.example" "$ROOT/frontend/.env.example"; do
  target="${f%.example}"
  if [ ! -f "$target" ]; then
    cp "$f" "$target"
    echo "  created $target"
  fi
done

echo "[setup] Installing frontend dependencies..."
(cd "$ROOT/frontend" && npm install --no-audit --no-fund)

echo "[setup] Done. Next steps:"
echo "  make dev      # start backend + frontend + db in Docker"
echo "  make test     # run backend tests with coverage"
