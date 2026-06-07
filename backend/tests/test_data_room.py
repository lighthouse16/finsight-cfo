from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_data_room_readiness_contract():
    response = client.get("/api/data-room/demo-readiness")

    assert response.status_code == 200
    data = response.json()

    assert set(data.keys()) == {"records", "dependencies", "summary"}
    assert len(data["records"]) == 9
    assert len(data["dependencies"]) == 5

    summary = data["summary"]
    assert summary["totalRequired"] == 6
    assert summary["connectedRequired"] == 3
    assert summary["missingRequired"] == 3
    assert summary["readinessPercentage"] == 50
    assert summary["dataMode"] == "demo_workspace"

    record = data["records"][0]
    assert record["id"] == "pl-statement"
    assert record["status"] == "demo_available"
    assert "valuation" in record["requiredFor"]


def test_demo_upload_metadata_supported_csv():
    # Minimal CSV content
    files = {"file": ("pl.csv", b"period,revenue\n2025,1000", "text/csv")}
    data = {"recordKey": "pl-statement"}
    response = client.post("/api/data-room/demo-upload-metadata", data=data, files=files)

    assert response.status_code == 200
    resp = response.json()
    assert resp["uploadedFile"]["recordKey"] == "pl-statement"
    assert resp["uploadedFile"]["fileName"] == "pl.csv"
    assert resp["uploadedFile"]["fileType"] == "text/csv"
    assert resp["uploadedFile"]["status"] == "accepted_metadata"
    assert resp["uploadedFile"]["validationMessages"]
    assert "Metadata received" in resp["uploadedFile"]["validationMessages"][0]
    assert resp["uploadedFile"]["disclaimer"] == (
        "This is a metadata-only upload stub. "
        "Company records require production ingestion before analysis updates."
    )
    assert resp["disclaimer"] == (
        "Metadata received. Analysis will update after production ingestion is connected."
    )
    # No wording about final offers, approvals, guarantees, etc.
    assert "approved" not in str(resp).lower()
    assert "rejected" not in str(resp).lower()
    assert "guaranteed" not in str(resp).lower()
    assert "formal underwriting" not in str(resp).lower()
    assert "automated credit decision" not in str(resp).lower()
    assert "approval probability" not in str(resp).lower()
    assert "predicted default" not in str(resp).lower()
    assert "bank verified" not in str(resp).lower()


def test_demo_upload_metadata_supported_pdf():
    files = {"file": ("balance.pdf", b"%PDF-1.4\n", "application/pdf")}
    data = {"recordKey": "balance-sheet"}
    response = client.post("/api/data-room/demo-upload-metadata", data=data, files=files)

    assert response.status_code == 200
    resp = response.json()
    assert resp["uploadedFile"]["recordKey"] == "balance-sheet"
    assert resp["uploadedFile"]["fileName"] == "balance.pdf"
    assert resp["uploadedFile"]["fileType"] == "application/pdf"
    assert resp["uploadedFile"]["status"] == "accepted_metadata"
    assert resp["uploadedFile"]["validationMessages"]
    assert "Metadata received" in resp["uploadedFile"]["validationMessages"][0]


def test_demo_upload_metadata_unsupported_type():
    files = {"file": ("document.txt", b"hello world", "text/plain")}
    data = {"recordKey": "pl-statement"}
    response = client.post("/api/data-room/demo-upload-metadata", data=data, files=files)

    assert response.status_code == 200
    resp = response.json()
    assert resp["uploadedFile"]["recordKey"] == "pl-statement"
    assert resp["uploadedFile"]["fileName"] == "document.txt"
    assert resp["uploadedFile"]["status"] == "unsupported_type"
    assert resp["uploadedFile"]["validationMessages"]
    assert "not in the supported list" in resp["uploadedFile"]["validationMessages"][0]
    assert "Analysis will not be updated" in resp["warnings"][0]


def test_demo_upload_metadata_invalid_record_key():
    files = {"file": ("test.csv", b"period,revenue\n2025,1000", "text/csv")}
    data = {"recordKey": "non-existent-key"}
    response = client.post("/api/data-room/demo-upload-metadata", data=data, files=files)

    assert response.status_code == 400
    assert "not part of the demo data room scope" in response.json()["detail"]


def test_demo_upload_metadata_missing_record_key():
    files = {"file": ("test.csv", b"period,revenue\n2025,1000", "text/csv")}
    data = {}
    response = client.post("/api/data-room/demo-upload-metadata", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    errors = body.get("detail", [])
    assert isinstance(errors, list)
    error_locs = [e.get("loc", [None, None]) for e in errors]
    assert any("recordKey" in loc for loc in error_locs)


def test_demo_upload_metadata_missing_file():
    data = {"recordKey": "pl-statement"}
    response = client.post("/api/data-room/demo-upload-metadata", data=data)

    assert response.status_code == 422
    body = response.json()
    errors = body.get("detail", [])
    assert isinstance(errors, list)
    error_locs = [e.get("loc", [None, None]) for e in errors]
    assert any("file" in loc for loc in error_locs)
