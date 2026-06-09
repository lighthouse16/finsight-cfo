"""Tests for GET /api/market-watch/cross-border-funding-context."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FORBIDDEN_TERMS = [
    "approved", "rejected", "lender approved", "final offer",
    "guaranteed", "formal underwriting", "automated credit decision",
    "approval probability", "predicted default", "bank verified",
    "realtime", "live",
]


def assert_forbidden_terms_absent(text: str) -> None:
    lowered = text.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in lowered, f"Forbidden term '{term}' found in response"


def test_endpoint_returns_200():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    assert resp.status_code == 200


def test_response_top_level_fields():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    assert body["mode"] == "context_only"
    assert body["baseCurrency"] == "HKD"
    assert body["comparisonCurrency"] == "RMB"
    assert "hkdFundingReference" in body
    assert "rmbFundingReference" in body
    assert "spreadBps" in body
    assert "spreadBand" in body
    assert "fxRiskBand" in body
    assert "crossBorderReviewBand" in body
    assert "explanation" in body
    assert "components" in body
    assert "provenance" in body
    assert "source" in body
    assert "warnings" in body
    assert "disclaimer" in body


def test_reference_fields():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    for ref_key in ("hkdFundingReference", "rmbFundingReference"):
        ref = body[ref_key]
        assert "label" in ref
        assert "currency" in ref
        assert "value" in ref or ref["value"] is None
        assert "unit" in ref
        assert "displayValue" in ref
        assert "source" in ref


def test_spread_band_valid():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    assert body["spreadBand"] in (
        "hkd_advantage", "rmb_advantage", "balanced", "unavailable"
    )


def test_fx_risk_band_valid():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    assert body["fxRiskBand"] in (
        "low", "moderate", "elevated", "unavailable"
    )


def test_review_band_valid():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    assert body["crossBorderReviewBand"] in (
        "worth_reviewing", "monitor", "not_priority", "unavailable"
    )


def test_components_are_list():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    assert isinstance(body["components"], list)
    for comp in body["components"]:
        assert "label" in comp
        assert "signal" in comp
        assert "explanation" in comp


def test_safety_wording_present():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    text = str(body).lower()
    assert body["mode"] == "context_only"
    assert "planning support" in text or "financing decision" in text or "lending decision" in text
    assert "financing recommendation" in text or "lending decision" in text


def test_no_forbidden_wording():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    assert_forbidden_terms_absent(resp.text)


def test_warnings_present():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    assert len(body["warnings"]) > 0
    # Should mention fixture or provider-pending
    combined_warnings = " ".join(body["warnings"]).lower()
    assert "fixture" in combined_warnings or "provider" in combined_warnings


def test_disclaimer_content():
    resp = client.get("/api/market-watch/cross-border-funding-context")
    body = resp.json()
    d = body["disclaimer"].lower()
    assert "planning support" in d or "context" in d
