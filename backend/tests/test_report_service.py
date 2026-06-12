import pytest
from fastapi import HTTPException
from app.services.report_service import (
    create_report,
    get_report,
    list_reports,
    update_report,
    delete_report,
)

class MockWorkspaceRepository:
    def __init__(self, workspace_exists=True):
        self.workspace_exists = workspace_exists

    def get_workspace(self, workspace_id: str):
        if self.workspace_exists:
            return {"id": workspace_id, "name": "Test Workspace"}
        return None

class MockReportRepository:
    def __init__(self, reports=None, delete_success=True):
        self.reports = reports or {}
        self.delete_success = delete_success
        self.save_called = False
        self.update_called = False
        self.delete_called = False

    def save_report(self, workspace_id, report_type, title, report_payload, storage_uri, metadata):
        self.save_called = True
        report_id = f"report_{len(self.reports) + 1}"
        report = {
            "id": report_id,
            "workspaceId": workspace_id,
            "reportType": report_type,
            "title": title,
            "reportPayload": report_payload,
            "storageUri": storage_uri,
            "metadata": metadata,
            "status": "pending"
        }
        self.reports[report_id] = report
        return report

    def get_report(self, report_id: str):
        return self.reports.get(report_id)

    def list_reports(self, workspace_id: str, report_type=None):
        res = []
        for r in self.reports.values():
            if r["workspaceId"] == workspace_id:
                if not report_type or r["reportType"] == report_type:
                    res.append(r)
        return res

    def update_report_status(self, report_id, status, storage_uri, metadata):
        self.update_called = True
        if report_id in self.reports:
            self.reports[report_id]["status"] = status
            if storage_uri:
                self.reports[report_id]["storageUri"] = storage_uri
            if metadata:
                self.reports[report_id]["metadata"] = metadata
            return self.reports[report_id]
        raise RuntimeError("Report not found")

    def delete_report(self, report_id: str) -> bool:
        self.delete_called = True
        if self.delete_success:
            if report_id in self.reports:
                del self.reports[report_id]
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
        return {"id": "audit_abc"}

class MockSettings:
    def __init__(self, persistence_backend="database"):
        self.normalized_persistence_backend = persistence_backend

class DummyPayload:
    def __init__(self, reportType="valuation", title="Val Report", reportPayload=None, storageUri="s3://pdf", metadata=None, status="completed"):
        self.reportType = reportType
        self.title = title
        self.reportPayload = reportPayload or {}
        self.storageUri = storageUri
        self.metadata = metadata or {}
        self.status = status

@pytest.mark.anyio
async def test_create_report_success():
    ws_repo = MockWorkspaceRepository(workspace_exists=True)
    rep_repo = MockReportRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings("database")
    payload = DummyPayload()

    report = await create_report(
        workspace_id="ws_123",
        payload=payload,
        workspace_repo=ws_repo,
        report_repo=rep_repo,
        audit_repo=audit_repo,
        settings=settings
    )

    assert rep_repo.save_called
    assert report["workspaceId"] == "ws_123"
    assert report["title"] == "Val Report"
    assert len(audit_repo.calls) == 1
    assert audit_repo.calls[0]["event_type"] == "report.created"

@pytest.mark.anyio
async def test_create_report_workspace_missing():
    ws_repo = MockWorkspaceRepository(workspace_exists=False)
    rep_repo = MockReportRepository()
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()
    payload = DummyPayload()

    with pytest.raises(HTTPException) as exc_info:
        await create_report(
            workspace_id="ws_123",
            payload=payload,
            workspace_repo=ws_repo,
            report_repo=rep_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Workspace not found"

@pytest.mark.anyio
async def test_get_report_success():
    ws_repo = MockWorkspaceRepository()
    rep_repo = MockReportRepository(reports={
        "rep_1": {"id": "rep_1", "workspaceId": "ws_123", "title": "Report 1"}
    })

    report = await get_report(
        workspace_id="ws_123",
        report_id="rep_1",
        workspace_repo=ws_repo,
        report_repo=rep_repo
    )
    assert report["id"] == "rep_1"
    assert report["title"] == "Report 1"

@pytest.mark.anyio
async def test_get_report_missing_or_mismatch():
    ws_repo = MockWorkspaceRepository()
    rep_repo = MockReportRepository(reports={
        "rep_1": {"id": "rep_1", "workspaceId": "ws_other", "title": "Report 1"}
    })

    with pytest.raises(HTTPException) as exc_info:
        await get_report(
            workspace_id="ws_123",
            report_id="rep_1",
            workspace_repo=ws_repo,
            report_repo=rep_repo
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Report not found in this workspace"

@pytest.mark.anyio
async def test_list_reports():
    ws_repo = MockWorkspaceRepository()
    rep_repo = MockReportRepository(reports={
        "rep_1": {"id": "rep_1", "workspaceId": "ws_123", "reportType": "valuation"},
        "rep_2": {"id": "rep_2", "workspaceId": "ws_123", "reportType": "health"},
        "rep_3": {"id": "rep_3", "workspaceId": "ws_other", "reportType": "valuation"}
    })

    reports = await list_reports(
        workspace_id="ws_123",
        report_type="valuation",
        workspace_repo=ws_repo,
        report_repo=rep_repo
    )
    assert len(reports) == 1
    assert reports[0]["id"] == "rep_1"

@pytest.mark.anyio
async def test_update_report_success():
    ws_repo = MockWorkspaceRepository()
    rep_repo = MockReportRepository(reports={
        "rep_1": {"id": "rep_1", "workspaceId": "ws_123", "status": "pending", "storageUri": "s3://old"}
    })
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()
    payload = DummyPayload(status="completed", storageUri="s3://new")

    updated = await update_report(
        workspace_id="ws_123",
        report_id="rep_1",
        payload=payload,
        workspace_repo=ws_repo,
        report_repo=rep_repo,
        audit_repo=audit_repo,
        settings=settings
    )
    assert rep_repo.update_called
    assert updated["status"] == "completed"
    assert updated["storageUri"] == "s3://new"
    assert len(audit_repo.calls) == 1
    assert audit_repo.calls[0]["event_type"] == "report.updated"

@pytest.mark.anyio
async def test_delete_report_success():
    ws_repo = MockWorkspaceRepository()
    rep_repo = MockReportRepository(reports={
        "rep_1": {"id": "rep_1", "workspaceId": "ws_123"}
    })
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    res = await delete_report(
        workspace_id="ws_123",
        report_id="rep_1",
        workspace_repo=ws_repo,
        report_repo=rep_repo,
        audit_repo=audit_repo,
        settings=settings
    )
    assert rep_repo.delete_called
    assert res["status"] == "success"
    assert "rep_1" not in rep_repo.reports
    assert len(audit_repo.calls) == 1
    assert audit_repo.calls[0]["event_type"] == "report.deleted"

@pytest.mark.anyio
async def test_delete_report_failure():
    ws_repo = MockWorkspaceRepository()
    rep_repo = MockReportRepository(reports={
        "rep_1": {"id": "rep_1", "workspaceId": "ws_123"}
    }, delete_success=False)
    audit_repo = MockAuditEventRepository()
    settings = MockSettings()

    with pytest.raises(HTTPException) as exc_info:
        await delete_report(
            workspace_id="ws_123",
            report_id="rep_1",
            workspace_repo=ws_repo,
            report_repo=rep_repo,
            audit_repo=audit_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Failed to delete report"
