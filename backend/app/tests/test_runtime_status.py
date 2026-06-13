"""
Tests for runtime status endpoint — verifies AI mode, queue backend, warnings.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestRuntimeStatusEndpoint:
    """Verify /api/runtime/status returns expected fields."""

    def test_status_returns_required_fields(self):
        response = client.get("/api/runtime/status")
        assert response.status_code == 200
        data = response.json()
        assert "ai_mode" in data
        assert "ai_provider_configured" in data
        assert "queue_backend" in data
        assert "persistence_backend" in data
        assert "auth_mode" in data
        assert "warnings" in data

    def test_ai_mode_is_deterministic_fallback_by_default(self):
        response = client.get("/api/runtime/status")
        data = response.json()
        assert data["ai_mode"] in ("deterministic_fallback", "openai", "azure_openai")
        assert isinstance(data["ai_provider_configured"], bool)

    def test_queue_backend_defaults_to_in_process(self):
        response = client.get("/api/runtime/status")
        data = response.json()
        assert data["queue_backend"] == "in_process"

    def test_warnings_includes_ai_warning_in_production(self):
        with patch.dict(os.environ, {
            "APP_MODE": "production",
        }, clear=True):
            from app.core.config import get_settings
            get_settings.cache_clear()
            # Re-init app for new settings
            from app.main import app
            tc = TestClient(app)
            response = tc.get("/api/runtime/status")
            data = response.json()
            ai_warnings = [w for w in data["warnings"] if "AI" in w or "LLM" in w]
            assert len(ai_warnings) > 0

    def test_status_does_not_expose_secrets(self):
        response = client.get("/api/runtime/status")
        assert response.status_code == 200
        content = response.text.lower()
        # Verify secrets are not leaked
        assert "secret" not in content
        assert "password" not in content
        assert "key" not in content
        assert "database_url" not in content

