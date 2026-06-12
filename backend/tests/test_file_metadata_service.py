import os
import pytest
from fastapi import HTTPException
from app.services.file_metadata_service import (
    upload_workspace_file,
    list_workspace_files,
    delete_workspace_file,
    get_workspace_file_bytes,
    cascade_delete_workspace_files,
)
from app.models.workspace import UploadedFileRecord

class MockWorkspaceRepository:
    def __init__(self, workspace_exists=True):
        self.workspace_exists = workspace_exists

    def get_workspace(self, workspace_id: str):
        if self.workspace_exists:
            from app.models.workspace import CompanyWorkspace
            return CompanyWorkspace(
                id=workspace_id,
                companyName="Test Workspace Co",
                createdAt="2026-06-11T00:00:00Z",
                metadata={}
            )
        return None

class MockFileMetadataRepository:
    def __init__(self, files=None, delete_success=True):
        self.files = files or {}
        self.delete_success = delete_success
        self.save_called = False
        self.delete_called = False

    def save_file_record(
        self,
        workspace_id: str,
        record_key: str,
        filename: str,
        content_type: str,
        file_size_bytes: int,
        storage_uri: str,
        **kwargs
    ):
        self.save_called = True
        file_id = f"file_{len(self.files) + 1}"
        file_record = {
            "id": file_id,
            "workspaceId": workspace_id,
            "recordKey": record_key,
            "fileName": filename,
            "fileType": content_type,
            "fileSizeBytes": file_size_bytes,
            "status": "active",
            "uploadedAt": "2026-06-11T00:00:00Z",
            "filePath": storage_uri,
        }
        self.files[file_id] = file_record
        return file_record

    def get_file_record(self, file_id: str):
        return self.files.get(file_id)

    def list_file_records(self, workspace_id: str):
        return [f for f in self.files.values() if f["workspaceId"] == workspace_id and f.get("status") != "deleted"]

    def delete_file_record(self, file_id: str) -> bool:
        self.delete_called = True
        if self.delete_success:
            if file_id in self.files:
                self.files[file_id]["status"] = "deleted"
            return True
        return False

class MockAuditEventRepository:
    def __init__(self):
        self.calls = []

    def append_event(self, workspace_id, event_type, description, **kwargs):
        self.calls.append({
            "workspace_id": workspace_id,
            "event_type": event_type,
            "description": description
        })
        return {"id": "audit_xyz"}

class MockSettings:
    def __init__(self, persistence_backend="database", object_storage_backend="local_file"):
        self.normalized_persistence_backend = persistence_backend
        self.normalized_object_storage_backend = object_storage_backend

@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    import app.storage.workspace_store as ws_store
    import app.storage.file_store as f_store
    
    temp_dir = str(tmp_path / "storage_db")
    os.makedirs(temp_dir, exist_ok=True)
    
    monkeypatch.setattr(ws_store, "STORAGE_DIR", temp_dir)
    monkeypatch.setattr(f_store, "STORAGE_DIR", temp_dir)
    
    monkeypatch.setattr(f_store.FileStore, "_files_file", os.path.join(temp_dir, "files.json"))
    monkeypatch.setattr(f_store.FileStore, "_upload_root", os.path.join(temp_dir, "uploads"))
    
    monkeypatch.setattr(ws_store.WorkspaceStore, "_workspaces_file", os.path.join(temp_dir, "workspaces.json"))
    monkeypatch.setattr(ws_store.WorkspaceStore, "_snapshots_file", os.path.join(temp_dir, "snapshots.json"))
    monkeypatch.setattr(ws_store.WorkspaceStore, "_runs_file", os.path.join(temp_dir, "runs.json"))
    monkeypatch.setattr(ws_store.WorkspaceStore, "_audits_file", os.path.join(temp_dir, "audits.json"))
    
    yield temp_dir

@pytest.mark.anyio
async def test_upload_workspace_file_database_mode(temp_storage):
    ws_repo = MockWorkspaceRepository()
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings("database")

    record = await upload_workspace_file(
        workspace_id="ws_123",
        record_key="balance-sheet",
        filename="bs.csv",
        file_bytes=b"my-file-bytes",
        content_type="text/csv",
        workspace_repo=ws_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings
    )

    assert isinstance(record, UploadedFileRecord)
    assert record.record_key == "balance-sheet"
    assert record.file_name == "bs.csv"
    assert record.file_size_bytes == 13
    assert file_repo.save_called
    assert len(audit_repo.calls) == 1
    assert audit_repo.calls[0]["event_type"] == "file.uploaded"
    assert os.path.exists(record.file_path)

@pytest.mark.anyio
async def test_upload_workspace_file_local_mode(temp_storage, monkeypatch):
    # Setup a dummy workspace in local store so workspace check passes (or we can mock get_workspace)
    # Actually, MockWorkspaceRepository doesn't write to WorkspaceStore, it just returns workspace.
    ws_repo = MockWorkspaceRepository()
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings("local")

    # Mock WorkspaceStore.get_workspace to make sure FileStore can work
    from app.storage.workspace_store import WorkspaceStore
    monkeypatch.setattr(WorkspaceStore, "get_workspace", lambda cls, wid: ws_repo.get_workspace(wid))
    from app.core.config import settings as global_settings
    monkeypatch.setattr(global_settings, "PERSISTENCE_BACKEND", "local")

    record = await upload_workspace_file(
        workspace_id="ws_local",
        record_key="pl-statement",
        filename="pl.csv",
        file_bytes=b"revenue,100",
        content_type="text/csv",
        workspace_repo=ws_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings
    )

    assert isinstance(record, UploadedFileRecord)
    assert record.record_key == "pl-statement"
    assert record.file_name == "pl.csv"
    assert not file_repo.save_called
    assert len(audit_repo.calls) == 0  # local mode does not audit file upload via service (it bypasses audit_repo)

@pytest.mark.anyio
async def test_upload_workspace_missing():
    ws_repo = MockWorkspaceRepository(workspace_exists=False)
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    with pytest.raises(HTTPException) as exc_info:
        await upload_workspace_file(
            workspace_id="ws_missing",
            record_key="balance-sheet",
            filename="bs.csv",
            file_bytes=b"bytes",
            content_type="text/csv",
            workspace_repo=ws_repo,
            file_repo=file_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Workspace not found"

@pytest.mark.anyio
async def test_upload_invalid_params():
    ws_repo = MockWorkspaceRepository()
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    # Empty record key
    with pytest.raises(HTTPException) as exc_info:
        await upload_workspace_file(
            workspace_id="ws_123",
            record_key="",
            filename="bs.csv",
            file_bytes=b"bytes",
            content_type="text/csv",
            workspace_repo=ws_repo,
            file_repo=file_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "recordKey is required"

    # Empty filename
    with pytest.raises(HTTPException) as exc_info:
        await upload_workspace_file(
            workspace_id="ws_123",
            record_key="balance-sheet",
            filename="",
            file_bytes=b"bytes",
            content_type="text/csv",
            workspace_repo=ws_repo,
            file_repo=file_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "file is required"

@pytest.mark.anyio
async def test_list_workspace_files_database(temp_storage):
    ws_repo = MockWorkspaceRepository()
    settings = MockSettings("database")
    
    file_repo = MockFileMetadataRepository(files={
        "file_1": {
            "id": "file_1",
            "workspaceId": "ws_123",
            "recordKey": "balance-sheet",
            "fileName": "bs.csv",
            "fileType": "text/csv",
            "fileSizeBytes": 100,
            "status": "active",
            "uploadedAt": "2026-06-11T00:00:00Z",
            "filePath": "some/path/1",
        },
        "file_2": {
            "id": "file_2",
            "workspaceId": "ws_123",
            "recordKey": "pl-statement",
            "fileName": "pl.csv",
            "fileType": "text/csv",
            "fileSizeBytes": 200,
            "status": "active",
            "uploadedAt": "2026-06-11T00:00:00Z",
            "filePath": "some/path/2",
        }
    })

    files = await list_workspace_files(
        workspace_id="ws_123",
        workspace_repo=ws_repo,
        file_repo=file_repo,
        settings=settings
    )

    assert len(files) == 2
    assert isinstance(files[0], UploadedFileRecord)
    assert files[0].id == "file_1"
    assert files[1].id == "file_2"

@pytest.mark.anyio
async def test_delete_workspace_file_database(temp_storage):
    ws_repo = MockWorkspaceRepository()
    settings = MockSettings("database")
    audit_repo = MockAuditEventRepository()
    
    temp_file_path = os.path.join(temp_storage, "test_del.csv")
    with open(temp_file_path, "wb") as f:
        f.write(b"data")

    file_repo = MockFileMetadataRepository(files={
        "file_1": {
            "id": "file_1",
            "workspaceId": "ws_123",
            "recordKey": "balance-sheet",
            "fileName": "bs.csv",
            "fileType": "text/csv",
            "fileSizeBytes": 4,
            "status": "active",
            "uploadedAt": "2026-06-11T00:00:00Z",
            "filePath": temp_file_path,
        }
    })

    res = await delete_workspace_file(
        workspace_id="ws_123",
        file_id="file_1",
        workspace_repo=ws_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings
    )

    assert res["status"] == "success"
    assert file_repo.delete_called
    assert file_repo.get_file_record("file_1")["status"] == "deleted"
    assert not os.path.exists(temp_file_path)
    assert len(audit_repo.calls) == 1
    assert audit_repo.calls[0]["event_type"] == "file.deleted"

@pytest.mark.anyio
async def test_delete_workspace_file_not_found():
    ws_repo = MockWorkspaceRepository()
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings("database")

    with pytest.raises(HTTPException) as exc_info:
        await delete_workspace_file(
            workspace_id="ws_123",
            file_id="nonexistent",
            workspace_repo=ws_repo,
            file_repo=file_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "File not found in this workspace"

def test_get_workspace_file_bytes_database(temp_storage):
    settings = MockSettings("database")
    
    temp_file_path = os.path.join(temp_storage, "test_bytes.csv")
    with open(temp_file_path, "wb") as f:
        f.write(b"hello bytes")

    file_repo = MockFileMetadataRepository(files={
        "file_1": {
            "id": "file_1",
            "workspaceId": "ws_123",
            "recordKey": "balance-sheet",
            "fileName": "bs.csv",
            "fileType": "text/csv",
            "fileSizeBytes": 11,
            "status": "active",
            "uploadedAt": "2026-06-11T00:00:00Z",
            "filePath": temp_file_path,
        }
    })

    bytes_read = get_workspace_file_bytes(
        file_id="file_1",
        file_repo=file_repo,
        settings=settings
    )

    assert bytes_read == b"hello bytes"

def test_cascade_delete_workspace_files_database(temp_storage):
    settings = MockSettings("database")
    
    temp_file_path_1 = os.path.join(temp_storage, "test_cascade_1.csv")
    temp_file_path_2 = os.path.join(temp_storage, "test_cascade_2.csv")
    with open(temp_file_path_1, "wb") as f:
        f.write(b"data1")
    with open(temp_file_path_2, "wb") as f:
        f.write(b"data2")

    file_repo = MockFileMetadataRepository(files={
        "file_1": {
            "id": "file_1",
            "workspaceId": "ws_123",
            "filePath": temp_file_path_1,
        },
        "file_2": {
            "id": "file_2",
            "workspaceId": "ws_123",
            "filePath": temp_file_path_2,
        }
    })

    cascade_delete_workspace_files(
        workspace_id="ws_123",
        file_repo=file_repo,
        settings=settings
    )

    assert file_repo.delete_called
    assert not os.path.exists(temp_file_path_1)
    assert not os.path.exists(temp_file_path_2)
