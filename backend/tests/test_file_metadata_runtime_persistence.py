import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db import models  # Ensure models register on Base
from app.main import app
from app.routes.workspaces import get_db_session_optional
from app.core.config import settings

@pytest.fixture
def db_session():
    from sqlalchemy.pool import StaticPool
    # Setup SQLite in-memory database with StaticPool for TestClient compatibility
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

def test_file_metadata_local_mode_no_db_side_effects(monkeypatch):
    """
    Local mode tests:
    1. Workspace files endpoint accepts uploads.
    2. File lists can be retrieved and files deleted.
    3. No DB engine/session is created in local mode.
    4. Response shape is unchanged.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")

    from app.db import session as db_session_mod
    from app.storage.workspace_store import WorkspaceStore
    from app.storage.file_store import FileStore

    # Reset global engine to verify it is not initialized during local operations
    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    try:
        # Create a workspace first
        ws_res = client.post("/api/workspaces", data={"companyName": "Local File Co"})
        assert ws_res.status_code == 200
        workspace_id = ws_res.json()["id"]

        # 1. Upload a file
        file_content = b"pl-statement,revenue,100\n"
        upload_res = client.post(
            f"/api/workspaces/{workspace_id}/files",
            data={"recordKey": "pl-statement"},
            files={"file": ("pl.csv", io.BytesIO(file_content), "text/csv")}
        )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        assert "id" in upload_data
        assert upload_data["recordKey"] == "pl-statement"
        assert upload_data["fileName"] == "pl.csv"
        file_id = upload_data["id"]

        # 2. List files
        list_res = client.get(f"/api/workspaces/{workspace_id}/files")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert len(list_data) >= 1
        assert any(f["id"] == file_id for f in list_data)

        # 3. Delete file
        del_res = client.delete(f"/api/workspaces/{workspace_id}/files/{file_id}")
        assert del_res.status_code == 200

        # Assert no DB engine/sessionmaker was initialized
        assert db_session_mod._engine is None
        assert db_session_mod.SessionLocal is None

        # Clean up WorkspaceStore and FileStore local leaks
        FileStore.delete_workspace_files(workspace_id)
        WorkspaceStore.delete_workspace(workspace_id)
    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local


def test_file_metadata_database_mode(db_session, monkeypatch):
    """
    Database mode tests:
    1. Upload/save flow writes file metadata to DB repository.
    2. File bytes are NOT stored in the database.
    3. filePath pointer is stored.
    4. list file metadata reads from DB.
    5. delete file metadata hides from list/get.
    6. Database mode does NOT write metadata to files.json.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    from app.db.models import Organization, Workspace as DbWorkspace, WorkspaceFile
    from app.storage.file_store import FileStore

    # Add default organization required by foreign keys
    org = Organization(id="org_default", name="Default Organization")
    db_session.add(org)
    
    # Add workspace to DB
    workspace_id = "ws_db_test_files"
    ws = DbWorkspace(id=workspace_id, organization_id="org_default", name="DB File Co", status="active")
    db_session.add(ws)
    db_session.commit()

    # Setup FastAPI dependency override
    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session_optional] = override_get_db_session

    client = TestClient(app)
    try:
        # Clear legacy FileStore to make sure we don't accidentally write/read metadata from it
        orig_files_file = FileStore._files_file
        temp_files_json = os.path.join(os.path.dirname(orig_files_file), "temp_files_test.json")
        FileStore._files_file = temp_files_json

        # 1. Upload file
        file_content = b"balance-sheet-data,cash,5000\n"
        upload_res = client.post(
            f"/api/workspaces/{workspace_id}/files",
            data={"recordKey": "balance-sheet"},
            files={"file": ("bs.csv", io.BytesIO(file_content), "text/csv")}
        )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        assert "id" in upload_data
        assert upload_data["recordKey"] == "balance-sheet"
        assert upload_data["fileName"] == "bs.csv"
        file_id = upload_data["id"]
        file_path = upload_data["filePath"]

        # Assert file bytes are stored physically on disk
        assert os.path.exists(file_path)
        with open(file_path, "rb") as f:
            assert f.read() == file_content

        # Assert no metadata was written to local files.json
        assert not os.path.exists(temp_files_json) or os.path.getsize(temp_files_json) == 0

        # Assert metadata is stored in DB
        db_file = db_session.query(WorkspaceFile).filter_by(id=file_id).first()
        assert db_file is not None
        assert db_file.file_name == "bs.csv"
        assert db_file.record_key == "balance-sheet"
        # Verify no file bytes are in the database (models don't even have a blob column for it)
        with pytest.raises(AttributeError):
            _ = db_file.file_bytes

        # 2. List files
        list_res = client.get(f"/api/workspaces/{workspace_id}/files")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert len(list_data) == 1
        assert list_data[0]["id"] == file_id
        assert list_data[0]["recordKey"] == "balance-sheet"
        assert list_data[0]["fileName"] == "bs.csv"

        # 3. Delete file
        del_res = client.delete(f"/api/workspaces/{workspace_id}/files/{file_id}")
        assert del_res.status_code == 200

        # Assert DB record is soft-deleted or hidden
        db_file_after = db_session.query(WorkspaceFile).filter_by(id=file_id).first()
        assert db_file_after.status == "deleted"
        assert db_file_after.deleted_at is not None

        # Assert listing files is now empty
        list_res_after = client.get(f"/api/workspaces/{workspace_id}/files")
        assert list_res_after.status_code == 200
        assert list_res_after.json() == []

        # Cleanup physical test file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        if os.path.exists(temp_files_json):
            try:
                os.remove(temp_files_json)
            except Exception:
                pass
        FileStore._files_file = orig_files_file
    finally:
        app.dependency_overrides.clear()
