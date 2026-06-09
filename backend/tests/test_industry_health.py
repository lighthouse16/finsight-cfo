from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FORBIDDEN_TERMS = [
    "approved",
    "rejected",
    "lender approved",
    "final offer",
    "guaranteed",
    "formal underwriting",
    "automated credit decision",
    "approval probability",
    "predicted default",
    "bank verified",
    "realtime",
    "live",
]


def assert_forbidden_terms_absent(text: str) -> None:
    lowered = text.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in lowered


def test_industry_health_default_context():
    response = client.get("/api/market-watch/industry-health")
    assert response.status_code == 200

    data = response.json()
    assert data["mode"] == "context_only"
    assert data["sectorName"] == "Trading & Distribution"
    assert data["industryHealthBand"] in {"resilient", "stable", "watch", "stressed", "unavailable"}
    assert data["demandSignal"] in {"expanding", "stable", "softening", "unavailable"}
    assert data["marginSignal"] in {"expanding", "stable", "compressing", "unavailable"}
    assert data["workingCapitalSignal"] in {"healthy", "watch", "stressed", "unavailable"}
    assert data["benchmarkSignal"] in {"favorable", "neutral", "cautious", "unavailable"}
    assert isinstance(data["components"], list)
    assert len(data["components"]) >= 4
    assert data["provenance"]["source"] == "industry_health_v1"
    assert data["source"]["source"] == "industry_health_v1"
    assert data["warnings"]
    assert "fixture" in " ".join(data["warnings"]).lower()
    assert data["disclaimer"]
    assert_forbidden_terms_absent(response.text)


def test_industry_health_electronics_context():
    response = client.get("/api/market-watch/industry-health?sector=electronics-import&geography=HK")
    assert response.status_code == 200

    data = response.json()
    assert data["sectorName"] == "Electronics Import"
    assert data["demandSignal"] == "expanding"
    assert data["industryHealthBand"] in {"resilient", "stable", "watch", "stressed"}
    assert {component["signal"] for component in data["components"]} == {
        "demandSignal",
        "marginSignal",
        "workingCapitalSignal",
        "benchmarkSignal",
    }
    assert_forbidden_terms_absent(response.text)


def test_industry_health_unknown_sector_uses_default_fixture_context():
    response = client.get("/api/market-watch/industry-health?sector=unknown-sector&geography=HK")
    assert response.status_code == 200

    data = response.json()
    assert data["sectorName"] == "Trading & Distribution"
    assert data["industryHealthBand"] in {"resilient", "stable", "watch", "stressed", "unavailable"}
    assert data["warnings"]
    assert "fixture" in " ".join(data["warnings"]).lower()
    assert_forbidden_terms_absent(response.text)
