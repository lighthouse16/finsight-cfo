"""
Tests for AI Provider service — deterministic fallback, mode detection, and safety.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.services.advisory.ai_provider import (
    get_ai_mode,
    get_advisory_response,
    _get_deterministic_response,
    SAFETY_SYSTEM_PROMPT,
    AdvisoryResponse,
    AIMode,
)


class TestAiModeDetection:
    """Verify that get_ai_mode() correctly reads environment."""

    def test_deterministic_fallback_when_no_keys(self):
        """No LLM env vars → deterministic_fallback."""
        with patch.dict(os.environ, {}, clear=True):
            from app.core.config import get_settings
            # Force reload settings
            get_settings.cache_clear()
            mode = get_ai_mode()
            assert mode == "deterministic_fallback"

    def test_openai_when_key_set(self):
        """OPENAI_API_KEY set → openai mode."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}, clear=True):
            from app.core.config import get_settings
            get_settings.cache_clear()
            mode = get_ai_mode()
            assert mode == "openai"

    def test_azure_openai_when_key_and_provider_set(self):
        """AZURE_OPENAI_API_KEY + LLM_PROVIDER=azure_openai → azure_openai."""
        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "azure-key",
            "LLM_PROVIDER": "azure_openai",
        }, clear=True):
            from app.core.config import get_settings
            get_settings.cache_clear()
            mode = get_ai_mode()
            assert mode == "azure_openai"


class TestDeterministicFallback:
    """Verify deterministic fallback returns correct structure."""

    def test_fallback_response_has_required_fields(self):
        resp = _get_deterministic_response("how is the company doing?", None)
        assert isinstance(resp, AdvisoryResponse)
        assert resp.ai_mode == "deterministic_fallback"
        assert resp.answer and len(resp.answer) > 0
        assert resp.disclaimer and len(resp.disclaimer) > 0
        assert isinstance(resp.warnings, list)

    def test_fallback_with_workspace_data(self):
        ws_data = {
            "company_name": "TestCo Ltd",
            "financial_summary": {
                "revenue": "HKD 10M",
                "net_income": "HKD 2M",
                "ebitda": "HKD 3M",
                "cash_and_equivalents": "HKD 5M",
                "total_assets": "HKD 50M",
                "total_liabilities": "HKD 20M",
            },
            "ratios": {
                "current_ratio": 1.5,
                "debt_to_equity": 0.8,
            },
        }
        resp = _get_deterministic_response("financial health", ws_data)
        assert "TestCo Ltd" in resp.answer
        assert resp.ai_mode == "deterministic_fallback"
        assert len(resp.sources) > 0

    def test_fallback_without_workspace(self):
        resp = _get_deterministic_response("what is my funding readiness?", None)
        assert "deterministic fallback" in resp.answer.lower()
        assert resp.ai_mode == "deterministic_fallback"

    def test_funding_readiness_template(self):
        ws_data = {
            "company_name": "BorrowCo",
            "financial_summary": {
                "revenue": "HKD 100M",
                "ebitda": "HKD 20M",
                "cash_and_equivalents": "HKD 10M",
                "total_assets": "HKD 200M",
                "total_liabilities": "HKD 80M",
            },
        }
        resp = _get_deterministic_response("funding readiness for my company", ws_data)
        assert "Funding Readiness" in resp.answer

    def test_sources_populated_from_workspace_data(self):
        ws_data = {
            "company_name": "SourceCo",
            "financial_summary": {"revenue": "100"},
            "ratios": {"current_ratio": 1.2},
            "cdi_output": {"score": "A"},
            "pd_estimate": {"probability": 0.02},
            "stress_test": {"loss_given_default": "10%"},
            "valuation_summary": {"value": "HKD 500M"},
        }
        resp = _get_deterministic_response("how is everything?", ws_data)
        sources = {s.title for s in resp.sources}
        assert "Financial Summary" in sources
        assert "Financial Ratios" in sources
        assert "CDI Assessment" in sources
        assert "Probability of Default" in sources
        assert "Stress Test" in sources
        assert "Valuation Summary" in sources


class TestSafetySystemPrompt:
    """Verify the safety prompt contains all required constraints."""

    def test_no_loan_approval(self):
        assert "MUST NOT provide loan approval" in SAFETY_SYSTEM_PROMPT

    def test_no_underwriting(self):
        assert "underwriting decisions" in SAFETY_SYSTEM_PROMPT

    def test_no_guaranteed_funding(self):
        assert "guaranteed funding" in SAFETY_SYSTEM_PROMPT

    def test_rm_review_required(self):
        assert "Relationship Manager" in SAFETY_SYSTEM_PROMPT
        assert "BOCHK" in SAFETY_SYSTEM_PROMPT


class TestForbiddenClaims:
    """Verify fallback responses don't contain forbidden language."""

    FORBIDDEN_PHRASES = [
        "loan approved",
        "approved for",
        "guaranteed funding",
        "underwriting decision",
        "binding commitment",
    ]

    def test_fallback_has_no_forbidden_claims(self):
        resp = _get_deterministic_response("can I get a loan?", {
            "company_name": "TestCo",
            "financial_summary": {"revenue": "100"},
        })
        answer_lower = resp.answer.lower()
        for phrase in self.FORBIDDEN_PHRASES:
            assert phrase not in answer_lower, f"Found forbidden phrase: {phrase}"
