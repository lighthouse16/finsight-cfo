import pytest
from app.main import app
from app.core.config import settings

@pytest.mark.skipif(
    settings.normalized_persistence_backend == "database",
    reason="Workspace route contract guardrails for local mode default settings are skipped in database mode"
)
def test_workspace_route_contract_guardrails():
    """
    1. Assert local mode default setting remains 'local'.
    2. Assert core workspace route paths still exist.
    3. Assert expected HTTP methods are registered.
    4. Assert no duplicate route method/path pairs exist.
    5. Assert key groups (workspace CRUD, files, reports, analysis) exist.
    """
    # 1. Assert local mode default
    assert settings.PERSISTENCE_BACKEND == "local"

    # 2. Extract registered routes
    routes_map = {}
    for route in app.routes:
        path = route.path
        methods = getattr(route, "methods", None)
        if methods:
            if path not in routes_map:
                routes_map[path] = set()
            for method in methods:
                # 4. Assert no duplicate route method/path pairs
                assert method not in routes_map[path], f"Duplicate route method/path pair registered: {method} {path}"
                routes_map[path].add(method)

    # 3 & 5. Verify core workspace CRUD, files, reports, and analysis paths exist
    
    # Workspace CRUD group
    assert "/api/workspaces" in routes_map
    assert "POST" in routes_map["/api/workspaces"]
    assert "GET" in routes_map["/api/workspaces"]
    
    assert "/api/workspaces/{workspace_id}" in routes_map
    assert "DELETE" in routes_map["/api/workspaces/{workspace_id}"]
    assert "GET" in routes_map["/api/workspaces/{workspace_id}"]

    # Files group
    assert "/api/workspaces/{workspace_id}/files" in routes_map
    assert "POST" in routes_map["/api/workspaces/{workspace_id}/files"]
    assert "GET" in routes_map["/api/workspaces/{workspace_id}/files"]
    
    assert "/api/workspaces/{workspace_id}/files/{file_id}" in routes_map
    assert "DELETE" in routes_map["/api/workspaces/{workspace_id}/files/{file_id}"]

    # Analysis group
    assert "/api/workspaces/{workspace_id}/snapshot/build" in routes_map
    assert "POST" in routes_map["/api/workspaces/{workspace_id}/snapshot/build"]
    
    assert "/api/workspaces/{workspace_id}/analysis/financial-health/run" in routes_map
    assert "POST" in routes_map["/api/workspaces/{workspace_id}/analysis/financial-health/run"]

    # Reports group
    assert "/api/workspaces/{workspace_id}/reports" in routes_map
    assert "POST" in routes_map["/api/workspaces/{workspace_id}/reports"]
    assert "GET" in routes_map["/api/workspaces/{workspace_id}/reports"]
    
    assert "/api/workspaces/{workspace_id}/reports/{report_id}" in routes_map
    assert "GET" in routes_map["/api/workspaces/{workspace_id}/reports/{report_id}"]
    assert "PATCH" in routes_map["/api/workspaces/{workspace_id}/reports/{report_id}"]
    assert "DELETE" in routes_map["/api/workspaces/{workspace_id}/reports/{report_id}"]

@pytest.mark.skipif(
    settings.normalized_persistence_backend == "database",
    reason="DB session check for local mode is skipped in database mode"
)
def test_no_db_session_initialization_on_import():
    """
    6. Assert no DB engine/session is initialized merely by importing routes/app.
    """
    from app.db import session as db_session_mod
    # Verify that the internal engine and SessionLocal remain None by default in local mode
    assert db_session_mod._engine is None
    assert db_session_mod.SessionLocal is None
