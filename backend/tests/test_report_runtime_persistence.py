import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db import models
from app.main import app
from app.routes.workspaces import get_db_session_optional, set_active_db_session
from app.core.config import settings

@pytest.fixture
def db_session():
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

def test_reports_local_mode_no_db_side_effects(monkeypatch):
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")

    from app.db import session as db_session_mod
    from app.storage.workspace_store import WorkspaceStore

    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    try:
        # Create workspace locally
        ws_res = client.post("/api/workspaces", data={"companyName": "Local Report Inc."})
        assert ws_res.status_code == 200
        ws_id = ws_res.json()["id"]

        # Ensure reports.json is clean
        from app.storage.workspace_store import STORAGE_DIR
        reports_json = os.path.join(STORAGE_DIR, "reports.json")
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass

        # 1. Create/Save report
        report_data = {
            "reportType": "quarterly_summary",
            "title": "Q1 2026",
            "reportPayload": {"revenue": 50000},
            "storageUri": "s3://local-reports/q1.pdf",
            "metadata": {"creator": "user123"}
        }
        res = client.post(f"/api/workspaces/{ws_id}/reports", json=report_data)
        assert res.status_code == 200
        saved_report = res.json()
        assert "id" in saved_report
        assert saved_report["reportType"] == "quarterly_summary"
        assert saved_report["title"] == "Q1 2026"
        assert saved_report["reportPayload"] == {"revenue": 50000}
        report_id = saved_report["id"]

        # 2. Get report
        res = client.get(f"/api/workspaces/{ws_id}/reports/{report_id}")
        assert res.status_code == 200
        assert res.json()["title"] == "Q1 2026"

        # 3. List reports
        res = client.get(f"/api/workspaces/{ws_id}/reports?type=quarterly_summary")
        assert res.status_code == 200
        reports_list = res.json()
        assert len(reports_list) == 1
        assert reports_list[0]["id"] == report_id

        # 4. Patch status
        patch_data = {
            "status": "archived",
            "storageUri": "s3://local-reports/q1_archived.pdf",
            "metadata": {"archived_by": "admin"}
        }
        res = client.patch(f"/api/workspaces/{ws_id}/reports/{report_id}", json=patch_data)
        assert res.status_code == 200
        updated = res.json()
        assert updated["status"] == "archived"
        assert updated["storageUri"] == "s3://local-reports/q1_archived.pdf"
        assert updated["metadata"]["archived_by"] == "admin"

        # 5. Delete report
        res = client.delete(f"/api/workspaces/{ws_id}/reports/{report_id}")
        assert res.status_code == 200
        assert res.json() == {"status": "success", "message": "Report deleted successfully"}

        # Verify not found anymore
        res = client.get(f"/api/workspaces/{ws_id}/reports/{report_id}")
        assert res.status_code == 404

        # Clean up files
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass
        WorkspaceStore.delete_workspace(ws_id)
        
        # Verify no database engine was initialized
        assert db_session_mod._engine is None
        assert db_session_mod.SessionLocal is None
    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])


def test_reports_database_mode(db_session, monkeypatch):
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    from app.db.models import Organization, Workspace as DbWorkspace, Report as DbReport
    from app.storage.workspace_store import WorkspaceStore

    # Override session dependency
    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session

    client = TestClient(app)
    try:
        # 1. Setup workspace/organization in DB
        org = Organization(id="org_custom", name="Custom Organization")
        db_session.add(org)
        
        ws_id = "ws_db_test_123"
        ws_db = DbWorkspace(id=ws_id, organization_id="org_custom", name="DB Workspace", status="active")
        db_session.add(ws_db)
        db_session.commit()

        # Clear reports.json local file to verify it is NOT written in DB mode
        from app.storage.workspace_store import STORAGE_DIR
        reports_json = os.path.join(STORAGE_DIR, "reports.json")
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass

        # 2. Save/Create report via route
        report_data = {
            "reportType": "audit_compliance",
            "title": "Audit 2026",
            "reportPayload": {"status": "compliant"},
            "storageUri": "s3://db-reports/audit.pdf",
            "metadata": {"auditor": "external"}
        }
        res = client.post(f"/api/workspaces/{ws_id}/reports", json=report_data)
        assert res.status_code == 200
        saved_report = res.json()
        assert "id" in saved_report
        assert saved_report["reportType"] == "audit_compliance"
        assert saved_report["title"] == "Audit 2026"
        assert saved_report["reportPayload"] == {"status": "compliant"}
        report_id = saved_report["id"]

        # Assert no reports.json file was created locally
        assert not os.path.exists(reports_json) or os.path.getsize(reports_json) == 0 or WorkspaceStore._read_json(reports_json) == []

        # Verify organizationId in the saved report matches org_custom
        assert saved_report["organizationId"] == "org_custom"

        # Verify DB contains the record directly
        db_report = db_session.query(DbReport).filter_by(id=report_id).first()
        assert db_report is not None
        assert db_report.report_name == "Audit 2026"
        assert db_report.organization_id == "org_custom"

        # 3. Get report via route
        res = client.get(f"/api/workspaces/{ws_id}/reports/{report_id}")
        assert res.status_code == 200
        assert res.json()["title"] == "Audit 2026"

        # 4. List reports via route
        res = client.get(f"/api/workspaces/{ws_id}/reports?type=audit_compliance")
        assert res.status_code == 200
        reports_list = res.json()
        assert len(reports_list) == 1
        assert reports_list[0]["id"] == report_id

        # 5. Patch report status
        patch_data = {
            "status": "revised",
            "storageUri": "s3://db-reports/audit_revised.pdf",
            "metadata": {"revision_reason": "typo"}
        }
        res = client.patch(f"/api/workspaces/{ws_id}/reports/{report_id}", json=patch_data)
        assert res.status_code == 200
        updated = res.json()
        assert updated["status"] == "revised"
        assert updated["storageUri"] == "s3://db-reports/audit_revised.pdf"
        assert updated["metadata"]["revision_reason"] == "typo"

        # Verify DB model matches
        db_session.refresh(db_report)
        assert db_report.status == "revised"
        assert db_report.storage_uri == "s3://db-reports/audit_revised.pdf"

        # 6. Delete report via route
        res = client.delete(f"/api/workspaces/{ws_id}/reports/{report_id}")
        assert res.status_code == 200

        # Verify hidden from route
        res = client.get(f"/api/workspaces/{ws_id}/reports/{report_id}")
        assert res.status_code == 404

        # Clean up files if any
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass
    finally:
        app.dependency_overrides.clear()
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
