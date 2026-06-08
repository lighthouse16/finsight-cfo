"""Tests for GET /api/market-watch/funding-channel-ranking."""

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
    resp = client.get("/api/market-watch/funding-channel-ranking")
    assert resp.status_code == 200


def test_response_top_level_fields():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    assert body["mode"] == "context_only"
    assert "companyContext" in body
    assert "rankingBand" in body
    assert "channels" in body
    assert "topChannelKey" in body
    assert "explanation" in body
    assert "components" in body
    assert "provenance" in body
    assert "source" in body
    assert "warnings" in body
    assert "disclaimer" in body


def test_exactly_five_candidate_channels():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    assert len(body["channels"]) == 5


def test_channel_item_fields():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    for ch in body["channels"]:
        assert "key" in ch
        assert "label" in ch
        assert "rank" in ch
        assert "fitBand" in ch
        assert "score" in ch
        assert "useCase" in ch, f"Channel {ch['key']} missing useCase"
        assert "rationale" in ch
        assert "supportingSignals" in ch, f"Channel {ch['key']} missing supportingSignals"
        assert isinstance(ch["supportingSignals"], list)
        assert "source" in ch, f"Channel {ch['key']} missing source"
        assert "constraints" in ch
        assert ch["fitBand"] in ("strong_fit", "moderate_fit", "watch_fit")


def test_safety_wording_present():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    text = str(body).lower()
    # Must contain safety phrases
    assert "candidate channel" in text or "context-only ranking" in text or "fit band" in text
    assert "subject to lender review" in text
    assert "production company records" in text


def test_no_forbidden_wording():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    assert_forbidden_terms_absent(resp.text)


def test_top_channel_is_receivables_or_wc():
    """Given the demo profile (DSO 52d, WC gap HKD 4.7M), expect either
    working_capital_line or receivables_financing as top channel."""
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    assert body["topChannelKey"] in ("working_capital_line", "receivables_financing")


def test_company_context_flags():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    ctx = body["companyContext"]
    assert ctx["companyName"] == "Harbour & Finch Trading Ltd."
    assert ctx["dsoWatch"] is True
    assert ctx["fxExposure"] is True
    assert ctx["importCostStress"] is True
    assert ctx["dscr"] is not None


def test_term_loan_has_constraint_about_review():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    term_loan = next(ch for ch in body["channels"] if ch["key"] == "term_loan")
    constraints_str = " ".join(term_loan["constraints"]).lower()
    assert "lender review" in constraints_str or "records" in constraints_str or "financials" in constraints_str


def test_fx_hedging_not_a_financing_channel():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    fx = next(ch for ch in body["channels"] if ch["key"] == "fx_hedging_context")
    constraints_str = " ".join(fx["constraints"]).lower()
    assert "not a financing channel" in constraints_str or "derivative" in constraints_str


def test_disclaimer_content():
    resp = client.get("/api/market-watch/funding-channel-ranking")
    body = resp.json()
    d = body["disclaimer"].lower()
    assert "context-only" in d
    assert "financing approval" in d or "underwriting" in d or "planning support" in d
