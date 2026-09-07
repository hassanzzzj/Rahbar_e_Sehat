"""
Unit tests for the anonymous session route.
Verifies POST /session/create and GET /session/{session_id} behavior.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


class TestSessionCreate:
    """Tests for POST /api/v1/session/create."""

    def test_create_session_returns_jwt_and_session_id(self, client: TestClient):
        """POST /session/create should return session_id, token, and expires_at."""
        response = client.post("/api/v1/session/create")
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "token" in data
        assert "expires_at" in data
        assert len(data["session_id"]) == 36  # UUID format
        assert len(data["token"]) > 20  # JWT is non-trivial length

    def test_create_session_token_is_valid_jwt(self, client: TestClient):
        """Returned token should decode with the configured secret."""
        from jose import jwt
        from app.config import get_settings

        response = client.post("/api/v1/session/create")
        data = response.json()

        settings = get_settings()
        decoded = jwt.decode(
            data["token"],
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert decoded["sub"] == data["session_id"]
        assert "iat" in decoded
        assert "exp" in decoded

    def test_create_session_unique_ids(self, client: TestClient):
        """Each call should generate a unique session_id."""
        r1 = client.post("/api/v1/session/create").json()
        r2 = client.post("/api/v1/session/create").json()
        assert r1["session_id"] != r2["session_id"]
        assert r1["token"] != r2["token"]


class TestSessionStatus:
    """Tests for GET /api/v1/session/{session_id}."""

    def test_get_session_status_after_create(self, client: TestClient):
        """GET should return 'active' status for a just-created session."""
        create_resp = client.post("/api/v1/session/create").json()
        session_id = create_resp["session_id"]

        status_resp = client.get(f"/api/v1/session/{session_id}")
        assert status_resp.status_code == 200

        data = status_resp.json()
        assert data["session_id"] == session_id
        assert data["status"] == "active"
        assert "created_at" in data

    def test_get_session_status_unknown_session(self, client: TestClient):
        """GET for unknown session_id should return 'unknown' status."""
        response = client.get("/api/v1/session/nonexistent-session-id")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == "nonexistent-session-id"
        assert data["status"] == "unknown"
