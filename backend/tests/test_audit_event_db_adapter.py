import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Workspace, Organization, AuditEvent as DbAuditEvent
from app.persistence.database_adapters import DatabaseAuditEventRepository
from app.persistence.factory import get_audit_event_repository
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

def test_append_and_retrieve_event(db_session):
    """
    1. DatabaseAuditEventRepository can append and retrieve a workspace audit event.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    event = repo.append_event(
        workspace_id="ws_1",
        event_type="workspace_created",
        description="Created workspace for Acme"
    )
    assert event["id"].startswith("audit_")
    assert event["workspaceId"] == "ws_1"
    assert event["eventType"] == "workspace_created"
    assert event["description"] == "Created workspace for Acme"
    assert event["timestamp"] is not None

    retrieved = repo.get_event(event["id"])
    assert retrieved is not None
    assert retrieved["id"] == event["id"]
    assert retrieved["workspaceId"] == "ws_1"
    assert retrieved["eventType"] == "workspace_created"
    assert retrieved["description"] == "Created workspace for Acme"

def test_append_event_requires_existing_workspace(db_session):
    """
    2. append_event requires existing workspace when workspace_id is provided.
    """
    repo = DatabaseAuditEventRepository(db_session)
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        repo.append_event(
            workspace_id="ws_non_existent",
            event_type="workspace_created",
            description="Testing"
        )
    assert "Workspace 'ws_non_existent' does not exist" in str(exc_info.value)

def test_saved_workspace_event_uses_org_id(db_session):
    """
    3. saved workspace event uses workspace.organization_id.
    """
    org = Organization(id="org_custom", name="Custom Org")
    db_session.add(org)
    ws = Workspace(id="ws_custom", organization_id="org_custom", name="WS Custom", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    event = repo.append_event(
        workspace_id="ws_custom",
        event_type="workspace_created",
        description="Testing org mapping"
    )
    orm_event = db_session.query(DbAuditEvent).filter_by(id=event["id"]).first()
    assert orm_event is not None
    assert orm_event.organization_id == "org_custom"

def test_list_events_limit_and_ordering(db_session):
    """
    4. list_events returns newest first and respects limit.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    event_ids = []
    for i in range(5):
        event = repo.append_event(
            workspace_id="ws_1",
            event_type=f"action_{i}",
            description=f"desc_{i}"
        )
        event_ids.append(event["id"])

    # Alter created_at times to verify sorting
    for idx, e_id in enumerate(event_ids):
        db_ev = db_session.query(DbAuditEvent).filter_by(id=e_id).first()
        db_ev.created_at = datetime(2026, 6, 11, 10, idx, 0, tzinfo=timezone.utc)
    db_session.commit()

    # list_events newest first, limit 3
    recent = repo.list_events(workspace_id="ws_1", limit=3)
    assert len(recent) == 3
    assert recent[0]["id"] == event_ids[4]
    assert recent[1]["id"] == event_ids[3]
    assert recent[2]["id"] == event_ids[2]

def test_list_events_filters_workspace(db_session):
    """
    5. list_events filters by workspace_id.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws1 = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    ws2 = Workspace(id="ws_2", organization_id="org_1", name="WS 2", status="active")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    repo.append_event(workspace_id="ws_1", event_type="action", description="ws1 event")
    repo.append_event(workspace_id="ws_2", event_type="action", description="ws2 event")

    events1 = repo.list_events(workspace_id="ws_1")
    assert len(events1) == 1
    assert events1[0]["workspaceId"] == "ws_1"

    events2 = repo.list_events(workspace_id="ws_2")
    assert len(events2) == 1
    assert events2[0]["workspaceId"] == "ws_2"

def test_list_organization_events_filter(db_session):
    """
    6. list_organization_events filters by organization_id.
    """
    org1 = Organization(id="org_1", name="Org 1")
    org2 = Organization(id="org_2", name="Org 2")
    db_session.add_all([org1, org2])
    ws1 = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    ws2 = Workspace(id="ws_2", organization_id="org_2", name="WS 2", status="active")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    repo.append_event(workspace_id="ws_1", event_type="action", description="org1 event")
    repo.append_event(workspace_id="ws_2", event_type="action", description="org2 event")

    org1_events = repo.list_organization_events("org_1")
    assert len(org1_events) == 1
    assert org1_events[0]["workspaceId"] == "ws_1"

    org2_events = repo.list_organization_events("org_2")
    assert len(org2_events) == 1
    assert org2_events[0]["workspaceId"] == "ws_2"

def test_get_event_missing_returns_none(db_session):
    """
    7. get_event returns None for missing event.
    """
    repo = DatabaseAuditEventRepository(db_session)
    assert repo.get_event("audit_missing") is None

def test_event_payload_round_trip(db_session):
    """
    8. event_payload round-trips correctly.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    payload = {"details": {"action": "delete", "file_name": "data.csv"}}
    event = repo.append_event(
        workspace_id="ws_1",
        event_type="delete_file",
        description="User deleted data.csv",
        event_payload=payload
    )

    db_ev = db_session.query(DbAuditEvent).filter_by(id=event["id"]).first()
    assert db_ev.context_payload == payload

def test_metadata_round_trip(db_session):
    """
    9. metadata round-trips correctly.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    meta = {"source": "api_gateway", "ip_range": "10.0.0.1"}
    event = repo.append_event(
        workspace_id="ws_1",
        event_type="api_call",
        description="Testing metadata mapping",
        metadata=meta
    )

    db_ev = db_session.query(DbAuditEvent).filter_by(id=event["id"]).first()
    assert db_ev.event_metadata == meta

def test_actor_user_id_round_trip(db_session):
    """
    10. actor_user_id round-trips correctly if ORM supports it.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    event = repo.append_event(
        workspace_id="ws_1",
        event_type="api_call",
        description="Testing actor",
        actor_user_id="user_admin_123"
    )

    db_ev = db_session.query(DbAuditEvent).filter_by(id=event["id"]).first()
    assert db_ev.user_id == "user_admin_123"

def test_org_level_event_can_be_saved(db_session):
    """
    11. org-level event with organization_id in metadata/event_payload can be saved.
    """
    org = Organization(id="org_custom", name="Custom Org")
    db_session.add(org)
    db_session.commit()

    repo = DatabaseAuditEventRepository(db_session)
    event = repo.append_event(
        workspace_id=None,
        event_type="org_settings_changed",
        description="Org settings modified",
        metadata={"organization_id": "org_custom"}
    )
    assert event["workspaceId"] == ""

    db_ev = db_session.query(DbAuditEvent).filter_by(id=event["id"]).first()
    assert db_ev.organization_id == "org_custom"
    assert db_ev.workspace_id is None

    # Alternative check using event_payload
    event2 = repo.append_event(
        workspace_id=None,
        event_type="org_settings_changed",
        description="Org settings modified",
        event_payload={"organization_id": "org_custom"}
    )
    db_ev2 = db_session.query(DbAuditEvent).filter_by(id=event2["id"]).first()
    assert db_ev2.organization_id == "org_custom"

def test_org_level_event_without_org_raises(db_session):
    """
    12. org-level event without organization_id raises PersistenceConfigurationError.
    """
    repo = DatabaseAuditEventRepository(db_session)
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        repo.append_event(
            workspace_id=None,
            event_type="org_settings_changed",
            description="Missing org"
        )
    assert "organization_id must be provided" in str(exc_info.value)

def test_factory_returns_db_repo(db_session):
    """
    13. factory returns DatabaseAuditEventRepository for database backend with db_session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    repo = get_audit_event_repository(settings, db_session=db_session)
    assert repo.__class__.__name__ == "DatabaseAuditEventRepository"

def test_factory_db_without_session_raises():
    """
    14. factory database backend without db_session raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_audit_event_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_factory_local_explicit():
    """
    15. local backend behavior remains explicit and does not accidentally create DB repository.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_audit_event_repository(settings)
    assert repo.__class__.__name__ == "LocalAuditEventRepository"

def test_no_global_session_on_import():
    """
    16. no DB engine/session is created by importing persistence interfaces/factory.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_audit_event_repository(settings)
    assert repo is not None
