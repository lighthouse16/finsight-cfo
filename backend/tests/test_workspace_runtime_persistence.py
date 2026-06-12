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

def test_local_mode_crud_and_no_db_side_effects(monkeypatch):
    """
    Local mode tests:
    1. Workspace routes still work using local persistence.
    2. No DB engine/session is created in local mode for workspace list/create/get/delete.
    3. Response shape is unchanged.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")

    from app.db import session as db_session_mod
    from app.storage.workspace_store import WorkspaceStore

    # Reset global engine to verify it is not initialized during local operations
    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    try:
        # 1. Create Workspace
        response = client.post("/api/workspaces", data={"companyName": "Local Temp Co"})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["companyName"] == "Local Temp Co"
        workspace_id = data["id"]

        # 2. List Workspaces
        response = client.get("/api/workspaces")
        assert response.status_code == 200
        lst = response.json()
        assert any(w["id"] == workspace_id for w in lst)

        # 3. Get Workspace
        response = client.get(f"/api/workspaces/{workspace_id}")
        assert response.status_code == 200
        assert response.json()["id"] == workspace_id

        # 4. Delete Workspace
        response = client.delete(f"/api/workspaces/{workspace_id}")
        assert response.status_code == 200

        # Assert no DB engine/sessionmaker was initialized
        assert db_session_mod._engine is None
        assert db_session_mod.SessionLocal is None

        # Clean up WorkspaceStore file leakage
        WorkspaceStore.delete_workspace(workspace_id)
    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local


def test_database_mode_crud(db_session, monkeypatch):
    """
    Database mode tests:
    1. Workspace routes can create/list/get/delete using DB repository.
    2. Database mode requires DB session dependency.
    3. Workspace data is persisted in in-memory SQLite.
    4. Deleted workspace is hidden from get/list.
    5. Response shape matches local mode.
    6. No WorkspaceStore write occurs in database mode.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    from app.db.models import Organization
    from app.storage.workspace_store import WorkspaceStore

    # Add default organization required by foreign keys
    org = Organization(id="org_default", name="Default Organization")
    db_session.add(org)
    db_session.commit()

    # Setup FastAPI dependency override
    from app.routes.workspaces import set_active_db_session
    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session

    client = TestClient(app)
    try:
        # 1. Create Workspace
        response = client.post(
            "/api/workspaces",
            data={
                "companyName": "DB Temp Co",
                "currency": "HKD",
                "reportingPeriod": "FY2026"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["companyName"] == "DB Temp Co"
        assert data["metadata"] == {"currency": "HKD", "reportingPeriod": "FY2026"}
        workspace_id = data["id"]

        # 2. List Workspaces (contains our created workspace)
        response = client.get("/api/workspaces")
        assert response.status_code == 200
        lst = response.json()
        assert len(lst) == 1
        assert lst[0]["id"] == workspace_id
        assert lst[0]["companyName"] == "DB Temp Co"

        # 3. Get Workspace Details
        response = client.get(f"/api/workspaces/{workspace_id}")
        assert response.status_code == 200
        assert response.json()["id"] == workspace_id
        assert response.json()["companyName"] == "DB Temp Co"

        # 4. Assert zero writes to local WorkspaceStore
        assert WorkspaceStore.get_workspace(workspace_id) is None

        # 5. Delete Workspace
        response = client.delete(f"/api/workspaces/{workspace_id}")
        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": f"Workspace {workspace_id} deleted successfully"}

        # 6. Get workspace details after deletion returns 404
        response = client.get(f"/api/workspaces/{workspace_id}")
        assert response.status_code == 404

        # 7. List workspaces after deletion is empty
        response = client.get("/api/workspaces")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()
