import json
import math

from fastapi.testclient import TestClient

from app.main import app
from app.services.financials.demo_company import get_demo_financial_snapshot

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
]


def _clear_preview_context():
    client.delete("/api/data-room/demo-workspace-preview-context")


def _valid_preview_payload(company_name: str = "Preview Context Ltd.") -> dict:
    snapshot = get_demo_financial_snapshot().model_dump(by_alias=True)
    snapshot["companyId"] = "preview-company"
    snapshot["companyName"] = company_name
    snapshot["metadata"] = {
        "source": "data_room_snapshot_preview",
        "preview_only": True,
        "persistent": False,
    }
    return {
        "companyId": snapshot["companyId"],
        "companyName": snapshot["companyName"],
        "currency": snapshot["currency"],
        "reportingPeriod": snapshot["reportingPeriod"],
        "snapshotPreview": snapshot,
        "integrityChecks": [],
        "ratios": None,
        "warnings": ["Preview-only context seeded for endpoint verification."],
    }


def _assert_no_nan_or_infinity(value):
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_nan_or_infinity(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_nan_or_infinity(nested)
    elif isinstance(value, float):
        assert math.isfinite(value)


def test_preview_analysis_without_context_returns_404_not_demo_analysis():
    _clear_preview_context()

    response = client.get("/api/financials/preview-analysis")

    assert response.status_code == 404
    body = response.json()
    assert "No active workspace preview context" in body["detail"]
    assert "snapshot" not in body


def test_preview_analysis_uses_active_workspace_preview_context():
    _clear_preview_context()
    payload = _valid_preview_payload()

    activate_response = client.post(
        "/api/data-room/demo-workspace-preview-context",
        json=payload,
    )
    assert activate_response.status_code == 200

    response = client.get("/api/financials/preview-analysis")

    assert response.status_code == 200
    data = response.json()
    assert data["snapshot"]["companyName"] == "Preview Context Ltd."
    assert data["snapshot"]["metadata"]["mode"] == "preview"
    assert data["snapshot"]["metadata"]["source"] == "data_room_workspace_preview"
    assert data["snapshot"]["metadata"]["preview_only"] is True
    assert data["integrityChecks"]
    assert data["ratios"]
    assert any("Preview analysis mode" in warning for warning in data["warnings"])
    assert any("in-memory" in warning for warning in data["warnings"])
    assert any("Production analysis was not updated" in warning for warning in data["warnings"])
    _assert_no_nan_or_infinity(data)


def test_demo_analysis_still_works_and_is_not_mutated_by_preview_context():
    _clear_preview_context()
    baseline_response = client.get("/api/financials/demo-analysis")
    assert baseline_response.status_code == 200
    baseline = baseline_response.json()

    activate_response = client.post(
        "/api/data-room/demo-workspace-preview-context",
        json=_valid_preview_payload("Different Preview Ltd."),
    )
    assert activate_response.status_code == 200

    preview_response = client.get("/api/financials/preview-analysis")
    assert preview_response.status_code == 200
    assert preview_response.json()["snapshot"]["companyName"] == "Different Preview Ltd."

    demo_response = client.get("/api/financials/demo-analysis")
    assert demo_response.status_code == 200
    demo = demo_response.json()
    assert demo["snapshot"]["companyName"] == baseline["snapshot"]["companyName"]
    assert demo["snapshot"]["companyName"] != "Different Preview Ltd."
    assert demo["snapshot"] == baseline["snapshot"]


def test_preview_analysis_with_malformed_context_returns_safe_error():
    _clear_preview_context()
    payload = _valid_preview_payload()
    payload["snapshotPreview"] = {
        "companyId": "partial-preview",
        "companyName": "Partial Preview Ltd.",
        "metadata": {"source": "data_room_snapshot_preview"},
    }

    activate_response = client.post(
        "/api/data-room/demo-workspace-preview-context",
        json=payload,
    )
    assert activate_response.status_code == 200

    response = client.get("/api/financials/preview-analysis")

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["source"] == "data_room_workspace_preview"
    assert detail["previewOnly"] is True
    assert "incomplete or malformed" in detail["message"]
    assert detail["errors"]


def test_preview_financials_responses_avoid_forbidden_wording():
    _clear_preview_context()
    client.post(
        "/api/data-room/demo-workspace-preview-context",
        json=_valid_preview_payload(),
    )

    response_texts = [
        json.dumps(client.get("/api/financials/preview-analysis").json()).lower(),
        json.dumps(client.get("/api/financials/demo-analysis").json()).lower(),
    ]
    for response_text in response_texts:
        for term in FORBIDDEN_TERMS:
            assert term not in response_text
