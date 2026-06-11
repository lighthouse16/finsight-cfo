import pytest
from typing import Any, Dict, Optional
from app.services.audit_service import record_audit_event_best_effort

class MockAuditEventRepository:
    def __init__(self, should_raise=False):
        self.should_raise = should_raise
        self.calls = []

    def append_event(
        self,
        workspace_id: Optional[str],
        event_type: str,
        description: str,
        actor_user_id: Optional[str] = None,
        event_payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self.should_raise:
            raise RuntimeError("Database error")
        self.calls.append({
            "workspace_id": workspace_id,
            "event_type": event_type,
            "description": description,
            "actor_user_id": actor_user_id,
            "event_payload": event_payload,
            "metadata": metadata
        })
        return {"id": "test_id"}

class MockSettings:
    def __init__(self, persistence_backend="database"):
        self.normalized_persistence_backend = persistence_backend

@pytest.mark.anyio
async def test_audit_helper_appends_event_database_mode():
    repo = MockAuditEventRepository()
    settings = MockSettings("database")
    
    await record_audit_event_best_effort(
        audit_repo=repo,
        settings=settings,
        workspace_id="ws_123",
        action="workspace.created",
        description="Workspace created",
        actor_user_id="user_abc",
        organization_id="org_xyz",
        metadata={"key": "val"}
    )
    
    assert len(repo.calls) == 1
    call = repo.calls[0]
    assert call["workspace_id"] == "ws_123"
    assert call["event_type"] == "workspace.created"
    assert call["description"] == "Workspace created"
    assert call["actor_user_id"] == "user_abc"
    assert call["event_payload"] == {"key": "val"}
    assert call["metadata"] == {"organization_id": "org_xyz"}

@pytest.mark.anyio
async def test_audit_helper_ignored_in_local_mode():
    repo = MockAuditEventRepository()
    settings = MockSettings("local")
    
    await record_audit_event_best_effort(
        audit_repo=repo,
        settings=settings,
        workspace_id="ws_123",
        action="workspace.created",
        description="Workspace created"
    )
    
    assert len(repo.calls) == 0

@pytest.mark.anyio
async def test_audit_helper_swallows_exceptions():
    repo = MockAuditEventRepository(should_raise=True)
    settings = MockSettings("database")
    
    # This should not raise
    await record_audit_event_best_effort(
        audit_repo=repo,
        settings=settings,
        workspace_id="ws_123",
        action="workspace.created",
        description="Workspace created"
    )
    
    assert len(repo.calls) == 0

@pytest.mark.anyio
async def test_audit_helper_handles_missing_fields():
    repo = MockAuditEventRepository()
    settings = MockSettings("database")
    
    await record_audit_event_best_effort(
        audit_repo=repo,
        settings=settings,
        workspace_id="ws_123",
        action="workspace.created"
    )
    
    assert len(repo.calls) == 1
    call = repo.calls[0]
    assert call["workspace_id"] == "ws_123"
    assert call["event_type"] == "workspace.created"
    assert call["description"] is None
    assert call["actor_user_id"] is None
    assert call["event_payload"] is None
    assert call["metadata"] is None
