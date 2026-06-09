"""Tests for GET /api/market-watch/red-flags-macro-summary."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FORBIDDEN_TERMS = [
    "approved", "rejected", "lender approved", "final offer",
    "guaranteed", "formal underwriting", "automated credit decision",
    "approval probability", "predicted default", "bank verified",
    "realtime",
]

# "live" is checked excluding legitimate provider name "ChinaData.live"
def assert_forbidden_terms_absent(text: str) -> None:
    import re
    lowered = text.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in lowered, f"Forbidden term '{term}' found in response"
    # Check "live" with context: exclude ChinaData.live
    live_indices = [m.start() for m in re.finditer(r"\blive\b", lowered)]
    for idx in live_indices:
        # Exclude if preceded by "chinadata." or within a longer provider context
        snippet_before = lowered[max(0, idx - 20):idx]
        if "chinadata." in snippet_before:
            continue
        raise AssertionError(f"Forbidden term 'live' found in response (non-provider context)")
    # Check other bounded terms
    for term in ["arbitrage profit", "risk-free"]:
        escaped = re.escape(term)
        matches = re.findall(rf"\b{escaped}\b", lowered)
        assert len(matches) == 0, f"Forbidden term '{term}' found in response"


def test_endpoint_returns_200():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    assert resp.status_code == 200


def test_response_top_level_fields():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    assert body["mode"] == "context_only"
    assert "summaryBand" in body
    assert "headline" in body
    assert "redFlags" in body
    assert "mitigants" in body
    assert "components" in body
    assert "provenance" in body
    assert "source" in body
    assert "warnings" in body
    assert "disclaimer" in body


def test_summary_band_valid():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    assert body["summaryBand"] in (
        "clear", "watch", "elevated", "stressed", "unavailable"
    )


def test_red_flag_item_fields():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    for flag in body["redFlags"]:
        assert "flagKey" in flag
        assert "label" in flag
        assert flag["severity"] in (
            "low", "moderate", "elevated", "stressed", "unavailable"
        )
        assert flag["category"] in (
            "rates", "fx", "sector", "funding", "cross_border", "timing", "liquidity"
        )
        assert "signal" in flag
        assert "rationale" in flag
        assert "suggestedReviewAction" in flag
        assert "supportingSignals" in flag
        assert "source" in flag


def test_mitigant_item_fields():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    for mitigant in body["mitigants"]:
        assert "label" in mitigant
        assert "rationale" in mitigant
        assert "source" in mitigant


def test_component_fields():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    for comp in body["components"]:
        assert "label" in comp
        assert "signal" in comp
        assert "explanation" in comp


def test_provenance_and_source():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    assert body["provenance"]["source"] == "market_watch_red_flags_macro_summary_v1"
    assert body["source"]["source"] == "market_watch_red_flags_macro_summary_v1"


def test_elevated_red_flags_drive_elevated_summary():
    """With fixture data, at least some flags should be > low, driving watch/elevated summary."""
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    # Fixture has moderate flags and summaryBand="watch"
    assert body["summaryBand"] in ("watch", "elevated", "stressed")


def test_safety_wording_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    text = str(body).lower()
    assert body["mode"] == "context_only"
    assert "context-only" in text or "planning support" in text
    assert "red flag" in text or "red-flag" in text
    assert "macro watch" in text or "macro" in text


def test_no_forbidden_wording():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    assert_forbidden_terms_absent(resp.text)


def test_warnings_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    assert len(body["warnings"]) > 0
    combined = " ".join(body["warnings"]).lower()
    assert "fixture" in combined or "provider" in combined


def test_disclaimer_content():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    d = body["disclaimer"].lower()
    assert "planning support" in d or "credit decision" in d


def test_rates_red_flag_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    keys = [f["flagKey"] for f in body["redFlags"]]
    assert "rates_red_flag" in keys


def test_fx_red_flag_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    keys = [f["flagKey"] for f in body["redFlags"]]
    assert "fx_red_flag" in keys


def test_sector_red_flag_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    keys = [f["flagKey"] for f in body["redFlags"]]
    assert "sector_red_flag" in keys


def test_funding_red_flag_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    keys = [f["flagKey"] for f in body["redFlags"]]
    assert "funding_red_flag" in keys


def test_cross_border_red_flag_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    keys = [f["flagKey"] for f in body["redFlags"]]
    assert "cross_border_red_flag" in keys


def test_timing_red_flag_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    keys = [f["flagKey"] for f in body["redFlags"]]
    assert "timing_red_flag" in keys


def test_liquidity_red_flag_present():
    resp = client.get("/api/market-watch/red-flags-macro-summary")
    body = resp.json()
    keys = [f["flagKey"] for f in body["redFlags"]]
    assert "liquidity_red_flag" in keys
