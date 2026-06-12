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


def test_readiness_template_contract():
    response = client.get("/api/data-room/readiness-template")

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


def test_demo_parse_preview_pl_csv():
    files = {
        "file": (
            "pl.csv",
            b"metric,value\nRevenue,1000\nCOGS,(400)\nEBITDA,250\nOther,10",
            "text/csv",
        )
    }
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "pl-statement"},
        files=files,
    )

    assert response.status_code == 200
    resp = response.json()
    assert resp["uploadedFile"]["status"] == "accepted_metadata"
    assert resp["preview"]["statementType"] == "profit_and_loss"
    records = {item["fieldKey"]: item for item in resp["preview"]["parsedRecords"]}
    assert records["revenue"]["normalizedValue"] == 1000
    assert records["cogs"]["normalizedValue"] == -400
    assert records["ebitda"]["confidence"] == "high"
    assert resp["preview"]["unsupportedFields"] == ["other"]
    assert "net_income" in resp["preview"]["missingExpectedFields"]


def test_demo_parse_preview_balance_sheet_csv_aliases():
    files = {
        "file": (
            "balance.csv",
            b"account,amount\nCash and Cash Equivalents,500\nAR,300\nLTD,1200",
            "text/csv",
        )
    }
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "balance-sheet"},
        files=files,
    )

    assert response.status_code == 200
    records = {item["fieldKey"]: item for item in response.json()["preview"]["parsedRecords"]}
    assert records["cash"]["normalizedValue"] == 500
    assert records["accounts_receivable"]["normalizedValue"] == 300
    assert records["long_term_debt"]["normalizedValue"] == 1200


def test_demo_parse_preview_receivables_aging_csv():
    files = {
        "file": (
            "aging.csv",
            b"field,value\n0-30 days,100\n31-60,80\n61-90,40\n90+,20",
            "text/csv",
        )
    }
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "receivables-aging"},
        files=files,
    )

    assert response.status_code == 200
    preview = response.json()["preview"]
    records = {item["fieldKey"]: item for item in preview["parsedRecords"]}
    assert records["current_0_30"]["normalizedValue"] == 100
    assert records["days_31_60"]["normalizedValue"] == 80
    assert records["days_61_90"]["normalizedValue"] == 40
    assert records["days_90_plus"]["normalizedValue"] == 20
    assert preview["missingExpectedFields"] == []


def test_demo_parse_preview_metadata_only_record_key():
    files = {"file": ("contract.csv", b"metric,value\nfoo,1", "text/csv")}
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "supplier-contracts"},
        files=files,
    )

    assert response.status_code == 200
    resp = response.json()
    assert resp["uploadedFile"]["status"] == "validation_warning"
    assert resp["preview"]["statementType"] == "metadata_only"
    assert resp["preview"]["parsedRecords"] == []
    assert "metadata-only" in resp["warnings"][0]


def test_demo_parse_preview_unsupported_file_type():
    files = {"file": ("pl.txt", b"metric,value\nRevenue,1000", "text/plain")}
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "pl-statement"},
        files=files,
    )

    assert response.status_code == 200
    resp = response.json()
    assert resp["uploadedFile"]["status"] == "validation_warning"
    assert resp["preview"]["parsedRecords"] == []
    assert "not supported for structured parsing preview" in resp["preview"]["warnings"][0]


def test_demo_parse_preview_malformed_csv_shape_is_safe():
    files = {"file": ("pl.csv", b"metric\nRevenue\nCOGS", "text/csv")}
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "pl-statement"},
        files=files,
    )

    assert response.status_code == 200
    resp = response.json()
    assert resp["uploadedFile"]["status"] == "validation_warning"
    assert resp["preview"]["parsedRecords"] == []
    assert "No value column found" in " ".join(resp["preview"]["warnings"])


def test_demo_parse_preview_non_finite_values_are_not_serialized():
    files = {"file": ("pl.csv", b"metric,value\nRevenue,NaN\nEBITDA,Infinity", "text/csv")}
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "pl-statement"},
        files=files,
    )

    assert response.status_code == 200
    text = response.text
    assert "NaN" not in text
    assert "Infinity" not in text
    records = response.json()["preview"]["parsedRecords"]
    assert all(item["normalizedValue"] is None for item in records)


def test_demo_parse_preview_avoids_forbidden_wording():
    files = {"file": ("pl.csv", b"metric,value\nRevenue,1000", "text/csv")}
    response = client.post(
        "/api/data-room/demo-parse-preview",
        data={"recordKey": "pl-statement"},
        files=files,
    )

    assert response.status_code == 200
    body = response.text.lower()
    forbidden = [
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
    for phrase in forbidden:
        assert phrase not in body


def _record(field_key: str, value: float):
    return {
        "fieldKey": field_key,
        "label": field_key.replace("_", " ").title(),
        "rawValue": str(value),
        "normalizedValue": value,
        "confidence": "high",
        "warnings": [],
    }


def _snapshot_preview_payload(include_aging: bool = True, total_assets: float = 1500):
    record_sets = [
        {
            "recordKey": "pl-statement",
            "warnings": [],
            "parsedRecords": [
                _record("revenue", 2000),
                _record("cogs", 900),
                _record("operating_expenses", 500),
                _record("ebit", 420),
                _record("depreciation_amortization", 80),
                _record("ebitda", 500),
                _record("interest_expense", 60),
                _record("ebt", 360),
                _record("taxes", 70),
                _record("net_income", 300),
            ],
        },
        {
            "recordKey": "balance-sheet",
            "warnings": [],
            "parsedRecords": [
                _record("cash", 200),
                _record("accounts_receivable", 300),
                _record("inventory", 250),
                _record("prepaid", 50),
                _record("current_assets", 800),
                _record("ppe_net", 700),
                _record("total_assets", total_assets),
                _record("accounts_payable", 180),
                _record("accrued", 70),
                _record("short_term_debt", 100),
                _record("current_portion_long_term_debt", 80),
                _record("long_term_debt", 420),
                _record("lease_liabilities", 40),
                _record("current_liabilities", 450),
                _record("total_liabilities", 800),
                _record("equity", 700),
            ],
        },
        {
            "recordKey": "cash-flow",
            "warnings": [],
            "parsedRecords": [
                _record("cfo", 360),
                _record("capex", 120),
                _record("debt_issued", 90),
                _record("debt_repaid", 80),
                _record("dividends", 40),
                _record("net_change_cash", 210),
            ],
        },
        {
            "recordKey": "debt-schedule",
            "warnings": [],
            "parsedRecords": [
                _record("scheduled_interest", 60),
                _record("scheduled_principal", 90),
            ],
        },
    ]
    if include_aging:
        record_sets.append(
            {
                "recordKey": "receivables-aging",
                "warnings": [],
                "parsedRecords": [
                    _record("current_0_30", 180),
                    _record("days_31_60", 70),
                    _record("days_61_90", 30),
                    _record("days_90_plus", 20),
                ],
            }
        )
    return {
        "companyId": "preview-company",
        "companyName": "Preview Company Ltd.",
        "currency": "HKD",
        "reportingPeriod": "FY2025",
        "recordSets": record_sets,
    }


def test_demo_snapshot_preview_full_payload_builds_snapshot_integrity_and_ratios():
    response = client.post(
        "/api/data-room/demo-snapshot-preview",
        json=_snapshot_preview_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["snapshotPreview"] is not None
    assert data["snapshotPreview"]["metadata"]["preview_only"] is True
    assert data["missingRequiredStatements"] == []
    assert data["integrityChecks"]
    assert any(check["checkName"] == "Balance Sheet Identity" for check in data["integrityChecks"])
    ratios = data["ratios"]
    assert ratios["currentRatio"]["value"] is not None
    assert ratios["quickRatio"]["value"] is not None
    assert ratios["interestCoverage"]["value"] is not None
    assert ratios["dscr"]["value"] is not None


def test_demo_snapshot_preview_missing_required_statement_warns_without_crash():
    payload = _snapshot_preview_payload()
    payload["recordSets"] = [item for item in payload["recordSets"] if item["recordKey"] != "cash-flow"]

    response = client.post("/api/data-room/demo-snapshot-preview", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["snapshotPreview"] is None
    assert data["ratios"] is None
    assert data["missingRequiredStatements"] == ["cash-flow"]
    assert "required statements are missing" in " ".join(data["warnings"])
    assert any(check["passed"] is False for check in data["integrityChecks"])


def test_demo_snapshot_preview_receivables_aging_is_optional():
    response = client.post(
        "/api/data-room/demo-snapshot-preview",
        json=_snapshot_preview_payload(include_aging=False),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["snapshotPreview"] is not None
    assert data["snapshotPreview"]["receivablesAging"] is None
    assert data["ratios"]["expectedCreditLossAr"]["value"] is None
    assert "Receivables aging was not provided" in " ".join(data["warnings"])


def test_demo_snapshot_preview_balance_sheet_identity_failure_returns_check():
    response = client.post(
        "/api/data-room/demo-snapshot-preview",
        json=_snapshot_preview_payload(total_assets=1600),
    )

    assert response.status_code == 200
    data = response.json()
    bs_check = next(
        check for check in data["integrityChecks"] if check["checkName"] == "Balance Sheet Identity"
    )
    assert bs_check["passed"] is False
    assert data["snapshotPreview"] is not None


def test_demo_snapshot_preview_no_persistence_claim_no_nan_and_no_unsafe_wording():
    response = client.post(
        "/api/data-room/demo-snapshot-preview",
        json=_snapshot_preview_payload(),
    )

    assert response.status_code == 200
    body = response.text
    lower_body = body.lower()
    assert ':nan' not in lower_body
    assert ':infinity' not in lower_body
    assert ':-infinity' not in lower_body
    assert "analysis was not updated" in lower_body
    assert "no file or snapshot was stored" in lower_body
    forbidden = [
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
    for phrase in forbidden:
        assert phrase not in lower_body
