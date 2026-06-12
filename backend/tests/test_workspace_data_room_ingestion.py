import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.storage.workspace_store import WorkspaceStore
from app.storage.file_store import FileStore

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_storage_and_settings():
    # Store settings
    orig_mode = settings.APP_MODE
    orig_fallback = settings.ALLOW_DEMO_FALLBACK
    
    yield
    
    settings.APP_MODE = orig_mode
    settings.ALLOW_DEMO_FALLBACK = orig_fallback


def test_persistent_data_room_lifecycle():
    # 1. Create a workspace
    create_res = client.post("/api/workspaces", data={
        "companyName": "Data Room Ingestion Inc.",
        "currency": "HKD",
        "reportingPeriod": "FY2025"
    })
    assert create_res.status_code == 200
    ws = create_res.json()
    ws_id = ws["id"]
    
    # 2. Upload structured records (CSV)
    pl_content = b"metric,value\nRevenue,2500\nCOGS,(1000)\nOperating Expenses,500\nEBIT,1000\nDepreciation & Amortization,100\nEBITDA,1100\nInterest Expense,100\nEBT,900\nTaxes,150\nNet Income,750\n"
    files = {"file": ("pl.csv", pl_content, "text/csv")}
    data = {"recordKey": "pl-statement"}
    upload_res = client.post(f"/api/workspaces/{ws_id}/data-room/files", data=data, files=files)
    assert upload_res.status_code == 200
    uploaded_pl = upload_res.json()
    
    # Check upload metadata properties
    assert uploaded_pl["recordKey"] == "pl-statement"
    assert uploaded_pl["parserStatus"] == "parsed"
    assert uploaded_pl["recordCount"] > 0
    assert uploaded_pl["warnings"] == []
    
    # 3. Upload unsupported PDF (metadata stored but parserStatus == unsupported_without_ocr)
    pdf_content = b"%PDF-1.4\n"
    files = {"file": ("statements.pdf", pdf_content, "application/pdf")}
    data = {"recordKey": "balance-sheet"}
    upload_res = client.post(f"/api/workspaces/{ws_id}/data-room/files", data=data, files=files)
    assert upload_res.status_code == 200
    uploaded_pdf = upload_res.json()
    
    assert uploaded_pdf["recordKey"] == "balance-sheet"
    assert uploaded_pdf["parserStatus"] == "unsupported_without_ocr"
    assert uploaded_pdf["recordCount"] == 0
    assert len(uploaded_pdf["warnings"]) > 0
    
    # 4. List workspace files via GET /api/workspaces/{workspace_id}/data-room/files
    list_res = client.get(f"/api/workspaces/{ws_id}/data-room/files")
    assert list_res.status_code == 200
    files_list = list_res.json()
    assert len(files_list) == 2
    
    # 5. Safe error when running analysis before snapshot is built
    analysis_res = client.get(f"/api/workspaces/{ws_id}/financial-analysis")
    assert analysis_res.status_code == 404
    assert analysis_res.json()["detail"]["code"] == "ACTIVE_SNAPSHOT_NOT_FOUND"
    
    # 6. Upload remaining required sheets to build a snapshot successfully
    # Balance sheet (overwrite the PDF with structured CSV)
    bs_content = b"metric,value\nCash and Cash Equivalents,500\nAccounts Receivable,400\nInventory,300\nPrepaid,50\nCurrent Assets,1250\nfixed_assets,850\nTotal Assets,2100\nAccounts Payable,250\naccrued,50\nShort-Term Debt,150\nCurrent Portion of Long-Term Debt,50\nLong-Term Debt,500\nLease Liabilities,50\nCurrent Liabilities,500\nTotal Liabilities,1050\nEquity,1050\n"
    files = {"file": ("bs.csv", bs_content, "text/csv")}
    client.post(f"/api/workspaces/{ws_id}/data-room/files", data={"recordKey": "balance-sheet"}, files=files)
    
    # Cash flow statement
    cf_content = b"metric,value\nOperating Cash Flow,500\ncapex,150\nDebt Issued,100\nDebt Repaid,50\nDividends,50\nnet_change_cash,350\n"
    files = {"file": ("cf.csv", cf_content, "text/csv")}
    client.post(f"/api/workspaces/{ws_id}/data-room/files", data={"recordKey": "cash-flow"}, files=files)
    
    # Debt schedule
    debt_content = b"metric,value\nScheduled Interest,50\nScheduled Principal,100\n"
    files = {"file": ("debt.csv", debt_content, "text/csv")}
    client.post(f"/api/workspaces/{ws_id}/data-room/files", data={"recordKey": "debt-schedule"}, files=files)
    
    # Build active snapshot via data-room/snapshot alias
    build_res = client.post(f"/api/workspaces/{ws_id}/data-room/snapshot?currency=HKD&reportingPeriod=FY2025")
    assert build_res.status_code == 200
    build_data = build_res.json()
    assert build_data["status"] == "success"
    
    # 7. Run workspace financial analysis via new endpoint GET /api/workspaces/{workspace_id}/financial-analysis
    analysis_res = client.get(f"/api/workspaces/{ws_id}/financial-analysis")
    assert analysis_res.status_code == 200
    analysis_data = analysis_res.json()
    
    # Ensure all outcome categories run and shape matches
    assert "ratios" in analysis_data
    assert "integrityChecks" in analysis_data
    assert "projections" in analysis_data
    assert "valuation" in analysis_data
    assert "summary" in analysis_data
    
    # Check no NaN/Infinity in outputs
    def assert_no_nan_inf(val):
        import math
        if isinstance(val, float):
            assert math.isfinite(val)
        elif isinstance(val, dict):
            for v in val.values():
                assert_no_nan_inf(v)
        elif isinstance(val, list):
            for v in val:
                assert_no_nan_inf(v)
    assert_no_nan_inf(analysis_data)
    
    # Verify metadata source is tagged correctly
    assert analysis_data["snapshot"]["metadata"]["source"] == "workspace_persistent_snapshot"
    assert analysis_data["snapshot"]["metadata"]["persistent"] is True
    
    # 8. Verify demo endpoints are unchanged and still fallback correctly
    settings.APP_MODE = "development"
    settings.ALLOW_DEMO_FALLBACK = True
    
    demo_analysis_res = client.get("/api/financials/demo-analysis")
    assert demo_analysis_res.status_code == 200
    demo_data = demo_analysis_res.json()
    assert demo_data["snapshot"]["companyName"] == "Harbour & Finch Trading Ltd."
    assert demo_data["snapshot"]["metadata"]["source"] == "demo_sample"
    
    # Clean up
    client.delete(f"/api/workspaces/{ws_id}")
