"""
Tests for the Google AI (Gemini) provider integration.

Tests cover:
  - Config detection (GOOGLE_API_KEY set / unset)
  - Successful mock HTTP interactions with the Gemini generateContent API
  - Error handling (timeouts, HTTP errors, blocked content, early finish)
  - Sanitisation of forbidden banking terms in responses
  - Integration through `get_advisory_response` → AdvisoryResponse mapping
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pytest import MonkeyPatch

from app.core.config import get_settings, Settings
from app.services.advisory.ai_provider import (
    _FORBIDDEN_WORDS,
    _call_google_gemini,
    _get_google_ai_config,
    _sanitize_response,
    get_advisory_response,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Clear the lru_cache on get_settings before and after every test.

    This ensures tests that mutate env vars for Settings do not leak state.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_gemini_response(
    text: str = "This is a test response.",
    finish_reason: str = "STOP",
    block_reason: str | None = None,
) -> dict[str, Any]:
    """Build a minimal Gemini generateContent JSON response.

    When *block_reason* is set the response has no *candidates* key at all.
    When *text* is empty and *finish_reason* is not ``STOP`` the candidate
    will contain no *parts* (simulating an early-finish response from the API).
    """
    candidate: dict[str, Any] = {
        "finishReason": finish_reason,
        "safetyRatings": [],
    }

    if block_reason:
        return {
            "promptFeedback": {"blockReason": block_reason},
        }

    if text or finish_reason == "STOP":
        candidate["content"] = {
            "role": "model",
            "parts": [{"text": text}],
        }
    else:
        # Simulate an early-finish / blocked generation with no parts
        candidate["content"] = {"role": "model"}

    return {"candidates": [candidate]}


# ---------------------------------------------------------------------------
# _get_google_ai_config
# ---------------------------------------------------------------------------


def test_config_returns_none_when_key_missing() -> None:
    """Patch get_settings so GOOGLE_API_KEY is empty (overrides .env)."""
    settings = Settings(GOOGLE_API_KEY="", LLM_PROVIDER="google_ai")
    with patch("app.services.advisory.ai_provider.get_settings", return_value=settings):
        result = _get_google_ai_config()
        assert result is None


def test_config_returns_tuple_when_key_present() -> None:
    settings = Settings(GOOGLE_API_KEY="test-key-123", LLM_PROVIDER="google_ai",
                        GOOGLE_AI_MODEL="gemini-1.5-flash")
    with patch("app.services.advisory.ai_provider.get_settings", return_value=settings):
        result = _get_google_ai_config()
        assert result is not None
        api_key, model, base_url = result
        assert api_key == "test-key-123"
        assert model == "gemini-1.5-flash"  # default
        assert "generativelanguage.googleapis.com" in base_url


def test_config_uses_custom_model() -> None:
    settings = Settings(GOOGLE_API_KEY="test-key", LLM_PROVIDER="google_ai",
                        GOOGLE_AI_MODEL="gemini-1.5-pro")
    with patch("app.services.advisory.ai_provider.get_settings", return_value=settings):
        _key, model, _url = _get_google_ai_config()  # type: ignore[misc]
        assert model == "gemini-1.5-pro"


# ---------------------------------------------------------------------------
# _sanitize_response
# ---------------------------------------------------------------------------


def test_sanitize_replaces_forbidden_words() -> None:
    text = (
        "Your loan is approved. The rate is guaranteed. "
        "This is a final decision with no risk involved."
    )
    result = _sanitize_response(text)
    assert "approved" not in result
    assert "conditionally eligible" in result
    assert "guaranteed" not in result
    assert "estimated" in result
    assert "no risk" not in result
    assert "managed risk" in result
    assert "final decision" not in result
    assert "indicative assessment" in result


def test_sanitize_handles_empty_string() -> None:
    assert _sanitize_response("") == ""


def test_sanitize_passthrough_safe_text() -> None:
    safe = "This is a perfectly safe advisory statement with no forbidden terms."
    assert _sanitize_response(safe) == safe


# ---------------------------------------------------------------------------
# _call_google_gemini (real httpx mocking)
# ---------------------------------------------------------------------------


def test_call_google_gemini_success(monkeypatch: MonkeyPatch) -> None:
    """A successful Gemini call should return the parsed text (after sanitisation)."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        payload = _mock_gemini_response(
            "Your loan is approved for the requested amount."
        )
        return httpx.Response(200, json=payload)

    with patch.object(httpx.Client, "post", mock_post):
        text, err = _call_google_gemini("system prompt", "user prompt")

    assert err is None
    assert text is not None
    assert "conditionally eligible" in text


def test_call_google_gemini_timeout(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=None)

    with patch.object(httpx.Client, "post", mock_post):
        text, err = _call_google_gemini("system prompt", "user prompt")

    assert text is None
    assert err is not None
    assert "timed out" in err


def test_call_google_gemini_http_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "Access denied"}})

    with patch.object(httpx.Client, "post", mock_post):
        text, err = _call_google_gemini("system prompt", "user prompt")

    assert text is None
    assert err is not None
    assert "403" in err


def test_call_google_gemini_no_config() -> None:
    """Patch get_settings so GOOGLE_API_KEY is empty."""
    settings = Settings(GOOGLE_API_KEY="")
    with patch("app.services.advisory.ai_provider.get_settings", return_value=settings):
        text, err = _call_google_gemini("system prompt", "user prompt")
        assert text is None
        assert err is not None
        assert "not configured" in err


def test_call_google_gemini_blocked_prompt(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        payload = _mock_gemini_response(text="", block_reason="SAFETY")
        return httpx.Response(200, json=payload)

    with patch.object(httpx.Client, "post", mock_post):
        text, err = _call_google_gemini("system prompt", "user prompt")

    assert text is None
    assert err is not None
    assert "blocked" in err


def test_call_google_gemini_empty_early_finish(monkeypatch: MonkeyPatch) -> None:
    """When Gemini returns early finish with no parts, we treat it as no response."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        payload = _mock_gemini_response(text="", finish_reason="RECITATION")
        return httpx.Response(200, json=payload)

    with patch.object(httpx.Client, "post", mock_post):
        text, err = _call_google_gemini("system prompt", "user prompt")

    assert text is None
    assert err is not None
    assert "finished early" in err


def test_call_google_gemini_adapter_timeout(monkeypatch: MonkeyPatch) -> None:
    """When get_advisory_response receives a Gemini timeout."""

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=None)

    with patch.object(httpx.Client, "post", mock_post):
        response = get_advisory_response("user")

    assert response is not None
    assert "timed out" in response.warnings[0] or any("timed out" in w for w in response.warnings)


# ---------------------------------------------------------------------------
# get_advisory_response
# ---------------------------------------------------------------------------


def test_advisory_response_success(monkeypatch: MonkeyPatch) -> None:
    """get_advisory_response should return a mapped AdvisoryResponse on success."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        payload = _mock_gemini_response("This is a test response.")
        return httpx.Response(200, json=payload)

    with patch.object(httpx.Client, "post", mock_post):
        response = get_advisory_response("user")

    assert response is not None
    assert "test" in response.answer
    assert len(response.warnings) == 0


def test_advisory_response_no_config() -> None:
    """get_advisory_response should fall back gracefully when config is missing."""
    settings = Settings(GOOGLE_API_KEY="")
    with patch("app.services.advisory.ai_provider.get_settings", return_value=settings):
        response = get_advisory_response("user")

    assert response.warnings is not None
    assert any("LLM provider configured" in w for w in response.warnings)
