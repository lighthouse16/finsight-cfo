import pytest
from fastapi import HTTPException
from app.services.workspace_service import (
    create_workspace,
    list_workspaces,
    get_workspace,
    delete_workspace,
)
from app.models.workspace import CompanyWorkspace

class MockWorkspaceRepository:
    def __init__(self, workspaces=None, delete_success=True):
        self.workspaces = workspaces or {}
        self.delete_success = delete_success
        self.create_called = False
        self.delete_called = False

    def create_workspace(self, workspace_id: str, company_name: str, metadata: dict):
        self.create_called = True
        ws = CompanyWorkspace(
            id=workspace_id,
            companyName=company_name,
            createdAt="2026-06-11T00:00:00Z",
            metadata=metadata
        )
        self.workspaces[workspace_id] = ws
        return ws

    def list_workspaces(self):
        return list(self.workspaces.values())

    def get_workspace(self, workspace_id: str):
        return self.workspaces.get(workspace_id)

    def delete_workspace(self, workspace_id: str) -> bool:
        self.delete_called = True
        if self.delete_success:
            if workspace_id in self.workspaces:
                del self.workspaces[workspace_id]
            return True
        return False

class MockFileMetadataRepository:
    def __init__(self, files=None):
        self.files = files or []

    def list_file_records(self, workspace_id: str):
        return self.files

    def delete_file_record(self, file_id: str):
        return True

class MockAuditEventRepository:
    def __init__(self):
        self.calls = []

    def append_event(self, workspace_id, event_type, description, **kwargs):
        self.calls.append({
            "workspace_id": workspace_id,
            "event_type": event_type,
            "description": description
        })
        return {"id": "audit_123"}

class MockSettings:
    def __init__(self, persistence_backend="database", object_storage_backend="local_file"):
        self.normalized_persistence_backend = persistence_backend
        self.normalized_object_storage_backend = object_storage_backend

@pytest.mark.anyio
async def test_create_workspace_success():
    ws_repo = MockWorkspaceRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    res = await create_workspace(
        company_name="My Company",
        currency="USD",
        reporting_period="FY2026",
        workspace_repo=ws_repo,
        audit_repo=audit_repo,
        settings=settings
    )

    assert isinstance(res, CompanyWorkspace)
    assert res.company_name == "My Company"
    assert res.metadata.get("currency") == "USD"
    assert res.metadata.get("reportingPeriod") == "FY2026"
    assert ws_repo.create_called
    assert len(audit_repo.calls) == 1
    assert audit_repo.calls[0]["event_type"] == "workspace.created"

@pytest.mark.anyio
async def test_create_workspace_empty_name():
    ws_repo = MockWorkspaceRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    with pytest.raises(HTTPException) as exc_info:
        await create_workspace(
            company_name="  ",
            currency="USD",
            reporting_period="FY2026",
            workspace_repo=ws_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "CompanyName is required"

def test_list_workspaces():
    ws_repo = MockWorkspaceRepository(workspaces={
        "ws_1": CompanyWorkspace(id="ws_1", companyName="WS 1", createdAt="2026-06-11T00:00:00Z"),
        "ws_2": CompanyWorkspace(id="ws_2", companyName="WS 2", createdAt="2026-06-11T00:00:00Z")
    })

    res = list_workspaces(workspace_repo=ws_repo)
    assert len(res) == 2
    assert res[0].id == "ws_1"
    assert res[1].id == "ws_2"

def test_get_workspace_success():
    ws = CompanyWorkspace(id="ws_1", companyName="WS 1", createdAt="2026-06-11T00:00:00Z")
    ws_repo = MockWorkspaceRepository(workspaces={"ws_1": ws})

    res = get_workspace(workspace_id="ws_1", workspace_repo=ws_repo)
    assert res.id == "ws_1"
    assert res.company_name == "WS 1"

def test_get_workspace_missing():
    ws_repo = MockWorkspaceRepository()

    with pytest.raises(HTTPException) as exc_info:
        get_workspace(workspace_id="missing", workspace_repo=ws_repo)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Workspace not found"

@pytest.mark.anyio
async def test_delete_workspace_success():
    ws = CompanyWorkspace(id="ws_1", companyName="WS 1", createdAt="2026-06-11T00:00:00Z")
    ws_repo = MockWorkspaceRepository(workspaces={"ws_1": ws})
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    res = await delete_workspace(
        workspace_id="ws_1",
        workspace_repo=ws_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings
    )

    assert res["status"] == "success"
    assert ws_repo.delete_called
    assert "ws_1" not in ws_repo.workspaces
    assert len(audit_repo.calls) == 1
    assert audit_repo.calls[0]["event_type"] == "workspace.deleted"

@pytest.mark.anyio
async def test_delete_workspace_missing():
    ws_repo = MockWorkspaceRepository()
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    with pytest.raises(HTTPException) as exc_info:
        await delete_workspace(
            workspace_id="missing",
            workspace_repo=ws_repo,
            file_repo=file_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Workspace not found"

@pytest.mark.anyio
async def test_delete_workspace_failure():
    ws = CompanyWorkspace(id="ws_1", companyName="WS 1", createdAt="2026-06-11T00:00:00Z")
    ws_repo = MockWorkspaceRepository(workspaces={"ws_1": ws}, delete_success=False)
    file_repo = MockFileMetadataRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    with pytest.raises(HTTPException) as exc_info:
        await delete_workspace(
            workspace_id="ws_1",
            workspace_repo=ws_repo,
            file_repo=file_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to delete workspace"
