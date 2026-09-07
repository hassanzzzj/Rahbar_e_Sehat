"""
SQLAlchemy ORM models for database tables.
Defines schema for sessions, facilities, and audit logs.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Session(Base):
    """Patient triage session record."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    phone_hash: Mapped[str] = mapped_column(String(64), index=True)
    primary_symptom: Mapped[str] = mapped_column(String(500))
    urgency: Mapped[str] = mapped_column(String(20))
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    recommended_facility_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reasoning_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Facility(Base):
    """Healthcare facility directory record."""

    __tablename__ = "facilities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    facility_type: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(512))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    services: Mapped[str] = mapped_column(Text)  # JSON array of services
    emergency_capable: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class MedicineInventory(Base):
    """Medicine stock record for a facility."""

    __tablename__ = "medicine_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    facility_id: Mapped[str] = mapped_column(String(64), ForeignKey("facilities.id"), index=True)
    medicine_name: Mapped[str] = mapped_column(String(256), index=True)
    quantity_available: Mapped[int] = mapped_column(Integer, default=0, ge=0)
    unit: Mapped[str] = mapped_column(String(50), default="units")
    last_updated: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """Audit log for triage decisions (anonymized)."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_token: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(50))
    agent_name: Mapped[str] = mapped_column(String(50))
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
