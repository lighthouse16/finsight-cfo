import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Workspace, Organization
from app.models.workspace import CompanyWorkspace
from app.persistence.database_adapters import DatabaseWorkspaceRepository
from app.persistence.factory import get_workspace_repository, get_persistence_backend_name
from app.persistence.errors import PersistenceConfigurationError

@pytest.fixture
def db_session():
    # Setup SQLite in-memory database for testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

def test_db_workspace_repo_create_and_get(db_session):
    """
    1. DatabaseWorkspaceRepository can create and retrieve a workspace.
    """
    repo = DatabaseWorkspaceRepository(db_session)
    ws = repo.create_workspace("ws_123", "Acme Corp", {"industry": "SaaS"})
    assert ws.id == "ws_123"
    assert ws.company_name == "Acme Corp"
    assert ws.metadata == {"industry": "SaaS"}

    # Retrieve workspace and verify fields match
    retrieved = repo.get_workspace("ws_123")
    assert retrieved is not None
    assert retrieved.id == "ws_123"
    assert retrieved.company_name == "Acme Corp"
    assert retrieved.metadata == {"industry": "SaaS"}

def test_db_workspace_repo_list(db_session):
    """
    2. list_workspaces returns created workspaces.
    """
    repo = DatabaseWorkspaceRepository(db_session)
    repo.create_workspace("ws_1", "Company 1")
    repo.create_workspace("ws_2", "Company 2")

    workspaces = repo.list_workspaces()
    assert len(workspaces) == 2
    ids = {w.id for w in workspaces}
    assert ids == {"ws_1", "ws_2"}

def test_db_workspace_repo_delete(db_session):
    """
    3. delete_workspace hides workspace from list/get.
    """
    repo = DatabaseWorkspaceRepository(db_session)
    repo.create_workspace("ws_1", "Company 1")

    # Confirm visible
    assert repo.get_workspace("ws_1") is not None
    assert len(repo.list_workspaces()) == 1

    # Delete workspace
    success = repo.delete_workspace("ws_1")
    assert success is True

    # Confirm hidden from get and list
    assert repo.get_workspace("ws_1") is None
    assert len(repo.list_workspaces()) == 0

    # Deleting non-existent returns False
    assert repo.delete_workspace("non_existent") is False

def test_db_workspace_repo_get_active(db_session):
    """
    4. get_active_workspace returns newest non-deleted workspace.
    """
    repo = DatabaseWorkspaceRepository(db_session)
    assert repo.get_active_workspace() is None

    repo.create_workspace("ws_old", "Old Company")
    active = repo.get_active_workspace()
    assert active is not None
    assert active.id == "ws_old"

    repo.create_workspace("ws_new", "New Company")
    
    # Manually adjust created_at timestamps to ensure ordering
    old_ws = db_session.query(Workspace).filter_by(id="ws_old").first()
    new_ws = db_session.query(Workspace).filter_by(id="ws_new").first()
    old_ws.created_at = datetime(2026, 6, 10, 10, 0, 0, tzinfo=timezone.utc)
    new_ws.created_at = datetime(2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc)
    db_session.commit()

    # Active should now be ws_new
    active = repo.get_active_workspace()
    assert active is not None
    assert active.id == "ws_new"

    # Soft-delete ws_new, get_active should fall back to ws_old
    repo.delete_workspace("ws_new")
    active = repo.get_active_workspace()
    assert active is not None
    assert active.id == "ws_old"

def test_db_workspace_repo_metadata_round_trip(db_session):
    """
    5. metadata round-trips correctly.
    """
    repo = DatabaseWorkspaceRepository(db_session)
    complex_meta = {
        "tags": ["commercial", "v3"],
        "funding": {"round": "Series A", "amount": 5000000},
        "settings": {"active": True}
    }
    repo.create_workspace("ws_meta", "Meta Inc", complex_meta)

    retrieved = repo.get_workspace("ws_meta")
    assert retrieved is not None
    assert retrieved.metadata == complex_meta

def test_factory_local_by_default(monkeypatch):
    """
    6. factory returns LocalWorkspaceRepository by default.
    """
    monkeypatch.delenv("PERSISTENCE_BACKEND", raising=False)
    settings = Settings()
    repo = get_workspace_repository(settings)
    assert repo.__class__.__name__ == "LocalWorkspaceRepository"

def test_factory_database_with_session(db_session):
    """
    7. factory with PERSISTENCE_BACKEND="database" and db_session returns DatabaseWorkspaceRepository.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    repo = get_workspace_repository(settings, db_session=db_session)
    assert repo.__class__.__name__ == "DatabaseWorkspaceRepository"
    assert repo.session == db_session

def test_factory_database_without_session_raises():
    """
    8. factory with PERSISTENCE_BACKEND="database" and no db_session raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_workspace_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_factory_unknown_backend_raises():
    """
    9. unknown backend still raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="unsupported_backend")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_workspace_repository(settings)
    assert "Unknown persistence backend configured" in str(exc_info.value)
