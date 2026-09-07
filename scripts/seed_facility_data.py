#!/usr/bin/env python3
"""
Seed the facility directory database from a CSV.

Expected CSV columns:
  name, facility_type, address, latitude, longitude, emergency_capable, phone

Run locally against a running Postgres:
  python scripts/seed_facility_data.py --csv data/facilities.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Any

import sqlalchemy as sa

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from backend.app.models.db_models import Base, Facility  # type: ignore  # noqa: E402


REQUIRED_COLUMNS = {
    "name",
    "facility_type",
    "address",
    "latitude",
    "longitude",
    "emergency_capable",
}


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def seed(csv_path: Path, database_url: str) -> int:
    engine = sa.create_engine(database_url)
    Base.metadata.create_all(engine)
    inserted = 0

    with engine.begin() as conn, csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        for row in reader:
            record: dict[str, Any] = {
                "name": row["name"].strip(),
                "facility_type": row["facility_type"].strip().upper(),
                "address": row["address"].strip(),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "emergency_capable": _parse_bool(row["emergency_capable"]),
                "phone": (row.get("phone") or "").strip() or None,
            }
            conn.execute(sa.insert(Facility.__table__).values(**record))
            inserted += 1

    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed facility directory")
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="SQLAlchemy URL (defaults to DATABASE_URL env var)",
    )
    args = parser.parse_args()

    if not args.database_url:
        parser.error("--database-url or DATABASE_URL is required")

    count = seed(args.csv, args.database_url)
    print(f"Inserted {count} facilities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
