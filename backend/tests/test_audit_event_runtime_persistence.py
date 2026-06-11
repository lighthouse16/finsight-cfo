import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db import models  # Register models on Base
from app.main import app
from app.routes.workspaces import get_db_session_optional, set_active_db_session
from app.core.config import settings
from app.storage.workspace_store import WorkspaceStore
from app.storage.file_store import FileStore

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

def test_audit_local_mode_no_db_side_effects(monkeypatch):
    """
    1. Local mode CRUD actions (workspace, file, report) write audit events.
    2. No DB engine/session is created in local mode.
    3. Response shape remains compatible.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")

    from app.db import session as db_session_mod

    # Reset global engine to verify it is not initialized during local operations
    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    try:
        # Clean local storage files
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])
        
        # Ensure audits.json and reports.json are clean
        from app.storage.workspace_store import STORAGE_DIR
        audits_json = os.path.join(STORAGE_DIR, "audits.json")
        reports_json = os.path.join(STORAGE_DIR, "reports.json")
        for fpath in [audits_json, reports_json]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

        # 1. Create Workspace (should trigger workspace.created)
        ws_res = client.post("/api/workspaces", data={"companyName": "Local Audit Co"})
        assert ws_res.status_code == 200
        ws_data = ws_res.json()
        assert "id" in ws_data
        ws_id = ws_data["id"]

        # 2. Upload File (should trigger file.uploaded / legacy file_uploaded)
        file_content = b"metric,value\nRevenue,100\n"
        upload_res = client.post(
            f"/api/workspaces/{ws_id}/files",
            data={"recordKey": "pl-statement"},
            files={"file": ("pl.csv", io.BytesIO(file_content), "text/csv")}
        )
        assert upload_res.status_code == 200
        file_id = upload_res.json()["id"]

        # 3. Create Report (should trigger report.created)
        report_payload = {
            "reportType": "audit_report",
            "title": "Local Audit Report",
            "reportPayload": {"score": 100},
            "storageUri": "s3://local/audit.pdf",
            "metadata": {"type": "test"}
        }
        report_res = client.post(f"/api/workspaces/{ws_id}/reports", json=report_payload)
        assert report_res.status_code == 200
        report_id = report_res.json()["id"]

        # 4. Patch Report (should trigger report.updated)
        patch_payload = {
            "status": "completed",
            "storageUri": "s3://local/audit_final.pdf",
            "metadata": {"revised": True}
        }
        patch_res = client.patch(f"/api/workspaces/{ws_id}/reports/{report_id}", json=patch_payload)
        assert patch_res.status_code == 200

        # Verify audits file exists and contains local logs
        assert os.path.exists(audits_json)
        local_audits = WorkspaceStore._read_json(audits_json)
        event_types = [a.get("eventType") for a in local_audits]
        
        # Verify the legacy logs are written
        assert "workspace_created" in event_types
        assert "file_uploaded" in event_types

        # Assert no DB engine/sessionmaker was initialized
        assert db_session_mod._engine is None
        assert db_session_mod.SessionLocal is None

        # Clean up files
        FileStore.delete_workspace_files(ws_id)
        WorkspaceStore.delete_workspace(ws_id)
        for fpath in [audits_json, reports_json]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass
    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])


def test_audit_database_mode(db_session, monkeypatch):
    """
    1. Database mode CRUD actions persist audit events to DB.
    2. Database mode does NOT write audit events to legacy local JSON store.
    3. Events contain workspace_id and action type.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    from app.db.models import Organization, Workspace as DbWorkspace, AuditEvent as DbAuditEvent
    from app.storage.workspace_store import STORAGE_DIR

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session

    client = TestClient(app)
    try:
        # Clear legacy JSON file paths
        audits_json = os.path.join(STORAGE_DIR, "audits.json")
        reports_json = os.path.join(STORAGE_DIR, "reports.json")
        for fpath in [audits_json, reports_json]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

        # 1. Setup workspace/organization in DB
        org = Organization(id="org_default", name="Default Org")
        db_session.add(org)
        
        ws_id = "ws_audit_db_test_123"
        ws_db = DbWorkspace(id=ws_id, organization_id="org_default", name="DB Audit Workspace", status="active")
        db_session.add(ws_db)
        db_session.commit()

        # 2. Upload file metadata via route (should log file.uploaded)
        file_content = b"balance-sheet-data,cash,5000\n"
        upload_res = client.post(
            f"/api/workspaces/{ws_id}/files",
            data={"recordKey": "balance-sheet"},
            files={"file": ("bs.csv", io.BytesIO(file_content), "text/csv")}
        )
        assert upload_res.status_code == 200
        file_id = upload_res.json()["id"]

        # 3. Create Report (should log report.created)
        report_payload = {
            "reportType": "audit_compliance",
            "title": "DB Compliance Report",
            "reportPayload": {"compliant": True},
            "storageUri": "s3://db/report.pdf",
            "metadata": {"auditor": "bot"}
        }
        report_res = client.post(f"/api/workspaces/{ws_id}/reports", json=report_payload)
        assert report_res.status_code == 200
        report_id = report_res.json()["id"]

        # 4. Patch Report (should log report.updated)
        patch_payload = {
            "status": "revised",
            "storageUri": "s3://db/report_revised.pdf",
            "metadata": {"revision": 2}
        }
        patch_res = client.patch(f"/api/workspaces/{ws_id}/reports/{report_id}", json=patch_payload)
        assert patch_res.status_code == 200

        # Assert no metadata was written to local audits.json
        assert not os.path.exists(audits_json) or os.path.getsize(audits_json) == 0 or WorkspaceStore._read_json(audits_json) == []

        # Verify DB contains the audit events
        db_audits = db_session.query(DbAuditEvent).filter_by(workspace_id=ws_id).all()
        assert len(db_audits) >= 3
        actions = [a.action for a in db_audits]
        assert "file.uploaded" in actions
        assert "report.created" in actions
        assert "report.updated" in actions

        # Assert no report metadata in local reports.json
        assert not os.path.exists(reports_json) or os.path.getsize(reports_json) == 0 or WorkspaceStore._read_json(reports_json) == []

        # 5. Delete file metadata via route (should log file.deleted)
        del_file_res = client.delete(f"/api/workspaces/{ws_id}/files/{file_id}")
        assert del_file_res.status_code == 200

        # Verify deleted audit exists in DB
        db_audits_after = db_session.query(DbAuditEvent).filter_by(workspace_id=ws_id, action="file.deleted").first()
        assert db_audits_after is not None

        # Clean up files
        FileStore.delete_workspace_files(ws_id)
        for fpath in [audits_json, reports_json]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass
    finally:
        app.dependency_overrides.clear()
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])
