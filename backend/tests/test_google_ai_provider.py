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

from app.core.config import get_settings
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


def test_config_returns_none_when_key_missing(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")
    result = _get_google_ai_config()
    assert result is None


def test_config_returns_tuple_when_key_present(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")
    result = _get_google_ai_config()
    assert result is not None
    api_key, model, base_url = result
    assert api_key == "test-key-123"
    assert model == "gemini-1.5-flash"  # default
    assert "generativelanguage.googleapis.com" in base_url


def test_config_uses_custom_model(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_AI_MODEL", "gemini-1.5-pro")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")
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
        raise httpx.HTTPStatusError(
            "403 Forbidden",
            request=httpx.Request("POST", "http://example.com"),
            response=httpx.Response(403, text="quota exceeded"),
        )

    with patch.object(httpx.Client, "post", mock_post):
        text, err = _call_google_gemini("system prompt", "user prompt")

    assert text is None
    assert err is not None
    assert "403" in err


def test_call_google_gemini_no_config(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

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


def test_call_google_gemini_early_finish(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        payload = _mock_gemini_response(text="", finish_reason="MAX_TOKENS")
        return httpx.Response(200, json=payload)

    with patch.object(httpx.Client, "post", mock_post):
        text, err = _call_google_gemini("system prompt", "user prompt")

    assert text is None
    assert err is not None
    assert "MAX_TOKENS" in err


# ---------------------------------------------------------------------------
# get_advisory_response → AdvisoryResponse mapping
# ---------------------------------------------------------------------------


def test_advisory_response_maps_google_ai_success(monkeypatch: MonkeyPatch) -> None:
    """When LLM_PROVIDER=google_ai the full pipeline should return a well-formed
    AdvisoryResponse with ai_mode='google_ai'."""
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        payload = _mock_gemini_response(
            "Based on your financial data your application is approved for review."
        )
        return httpx.Response(200, json=payload)

    with patch.object(httpx.Client, "post", mock_post):
        resp = get_advisory_response(
            question="What is my credit status?",
            workspace_data={
                "metrics": {"profit_margin": 0.15},
                "documents": [{"title": "Balance Sheet 2024", "snippet": "..."}],
            },
        )

    assert resp.ai_mode == "google_ai"
    assert resp.answer is not None
    # Sanitisation should replace "approved"
    assert "conditionally eligible" in resp.answer
    assert resp.warnings is not None and len(resp.warnings) == 0
    assert resp.sources is not None
    assert resp.disclaimer is not None
    assert "informational purposes only" in resp.disclaimer


def test_advisory_response_fallback_on_google_ai_failure(
    monkeypatch: MonkeyPatch,
) -> None:
    """When the Gemini API fails, the system should fall back to a deterministic
    response with a warning."""
    monkeypatch.setenv("LLM_PROVIDER", "google_ai")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=None)

    with patch.object(httpx.Client, "post", mock_post):
        resp = get_advisory_response(
            question="What is my credit status?",
            workspace_data={"metrics": {"profit_margin": 0.15}},
        )

    # Should fall back to deterministic (still return a message)
    assert resp.answer is not None
    assert len(resp.answer) > 0
    # ai_mode should still be 'google_ai' to signal the provider was attempted
    assert resp.ai_mode == "google_ai"
    # Should have a warning about the failure
    assert resp.warnings is not None
    assert any("timed out" in w for w in resp.warnings)
