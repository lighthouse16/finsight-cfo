import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_runtime_status_does_not_expose_secrets():
    """Verify runtime status endpoint does not leak credentials or keys."""
    response = client.get("/api/runtime/status")
    assert response.status_code == 200
    data = response.json()
    
    # Assert expected public attributes exist
    assert "app_mode" in data
    assert "persistence_backend" in data
    assert "auth_mode" in data
    assert "ai_mode" in data
    
    # Assert sensitive keys are NOT present
    for key in data.keys():
        assert "secret" not in key.lower()
        assert "password" not in key.lower()
        assert "url" not in key.lower()
        assert "key" not in key.lower()
        assert "token" not in key.lower()
        
    # Verify content doesn't leak raw credentials
    content = response.text.lower()
    assert "sqlite://" not in content
    assert "postgresql://" not in content
    assert "redis://" not in content

def test_production_sample_reset_disabled():
    """Verify sample reset endpoint is disabled outside dev/demo modes."""
    with patch.object(settings, "APP_MODE", "production"):
        response = client.post("/api/workspaces/reset-sample")
        assert response.status_code == 403
        assert "disabled" in response.text.lower()

def test_advisor_ready_report_endpoint_disclaimers_citations():
    """Verify /api/advisory/report returns appropriate disclaimers and citations."""
    mock_repo = MagicMock()
    mock_repo.get_workspace.return_value = {"id": "smoke_ws", "name": "Smoke Workspace"}
    
    from app.routes.workspaces import get_workspace_repository_dependency
    app.dependency_overrides[get_workspace_repository_dependency] = lambda: mock_repo
    
    try:
        response = client.post(
            "/api/advisory/report",
            json={"objective": "Validate funding strategies"},
            headers={"x-workspace-id": "smoke_ws"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "payload" in data
        payload = data["payload"]
        
        # Check disclaimers
        assert "disclaimers" in payload
        disclaimers = [d.lower() for d in payload["disclaimers"]]
        assert any("not a formal credit approval" in d for d in disclaimers)
        
        # Check limitations
        assert "limitations" in payload
        assert len(payload["limitations"]) > 0
        
        # Check sections structure
        assert "sections" in payload
        assert len(payload["sections"]) > 0
    finally:
        del app.dependency_overrides[get_workspace_repository_dependency]

def test_ai_cfo_source_citations_workspace_scoped():
    """Verify that document retrieval for AI CFO RAG context is workspace-scoped."""
    from app.services.data_room.document_index import get_document_index
    index = get_document_index()
    
    # Use retrieval to assert workspace isolation
    ws_1_chunks = index.retrieve(workspace_id="ws_1", query="financial", top_k=5)
    ws_2_chunks = index.retrieve(workspace_id="ws_2", query="financial", top_k=5)
    
    # Assert chunks retrieved belong strictly to their respective workspace_ids
    for chunk in ws_1_chunks:
        assert getattr(chunk, "workspace_id", None) == "ws_1"
    for chunk in ws_2_chunks:
        assert getattr(chunk, "workspace_id", None) == "ws_2"

def test_stress_endpoint_invalid_parameters():
    """Verify stress test endpoint rejects invalid/out-of-bounds parameters."""
    # Out of bounds HIBOR shock (> 1000 bps)
    response = client.post(
        "/api/advisory/stress-tests",
        json={"hibor_shock_bps": 1200}
    )
    assert response.status_code == 422
    
    # Out of bounds DSO shock (> 180 days)
    response = client.post(
        "/api/advisory/stress-tests",
        json={"dso_days_shock": 200}
    )
    assert response.status_code == 422

def test_no_forbidden_approval_wording_in_outputs():
    """Ensure report and advisory responses contain no forbidden credit approval terminology."""
    forbidden_words = [
        "guaranteed approval",
        "approved loan",
        "guaranteed funding",
        "formal underwriting",
        "certified bank rating",
        "bank-grade approval",
        "govt guaranteed"
    ]
    
    # Mock compile and assert lack of forbidden words
    mock_repo = MagicMock()
    mock_repo.get_workspace.return_value = {"id": "smoke_ws", "name": "Smoke Workspace"}
    
    from app.routes.workspaces import get_workspace_repository_dependency
    app.dependency_overrides[get_workspace_repository_dependency] = lambda: mock_repo
    
    try:
        response = client.post(
            "/api/advisory/report",
            json={"objective": "General business review"},
            headers={"x-workspace-id": "smoke_ws"}
        )
        assert response.status_code == 200
        content = response.text.lower()
        for word in forbidden_words:
            assert word not in content, f"Forbidden word '{word}' found in report payload!"
    finally:
        del app.dependency_overrides[get_workspace_repository_dependency]
