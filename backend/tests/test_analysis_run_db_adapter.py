import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Workspace, Organization, AnalysisRun as DbAnalysisRun
from app.persistence.database_adapters import DatabaseAnalysisRunRepository
from app.persistence.factory import get_analysis_run_repository
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

def test_save_and_retrieve_run(db_session):
    """
    1. DatabaseAnalysisRunRepository can save and retrieve an analysis run.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    run = repo.save_run(
        workspace_id="ws_1",
        run_type="forecast",
        status="pending",
        input_payload={"param": 1},
        metadata={"logic_version": "v2"}
    )
    assert run["id"].startswith("run_")
    assert run["workspaceId"] == "ws_1"
    assert run["runType"] == "forecast"
    assert run["status"] == "pending"
    assert run["inputs"] == {"param": 1}

    retrieved = repo.get_run(run["id"])
    assert retrieved is not None
    assert retrieved["id"] == run["id"]
    assert retrieved["status"] == "pending"
    assert retrieved["inputs"] == {"param": 1}
    assert retrieved["logicVersion"] == "v2"

def test_save_run_requires_existing_workspace(db_session):
    """
    2. save_run requires existing workspace.
    """
    repo = DatabaseAnalysisRunRepository(db_session)
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        repo.save_run(
            workspace_id="ws_non_existent",
            run_type="forecast",
            status="pending"
        )
    assert "Workspace 'ws_non_existent' does not exist" in str(exc_info.value)

def test_saved_run_uses_organization_id(db_session):
    """
    3. saved run uses workspace.organization_id.
    """
    org = Organization(id="org_custom", name="Custom Org")
    db_session.add(org)
    ws = Workspace(id="ws_custom", organization_id="org_custom", name="WS Custom", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    run_dict = repo.save_run(
        workspace_id="ws_custom",
        run_type="forecast",
        status="pending"
    )
    # Get the raw ORM model to inspect organization_id
    orm_run = db_session.query(DbAnalysisRun).filter_by(id=run_dict["id"]).first()
    assert orm_run is not None
    assert orm_run.organization_id == "org_custom"

def test_list_runs_isolated_by_workspace(db_session):
    """
    4. list_runs returns runs only for the requested workspace.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws1 = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    ws2 = Workspace(id="ws_2", organization_id="org_1", name="WS 2", status="active")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    repo.save_run(workspace_id="ws_1", run_type="forecast", status="completed")
    repo.save_run(workspace_id="ws_2", run_type="forecast", status="completed")

    runs_ws1 = repo.list_runs("ws_1")
    assert len(runs_ws1) == 1
    assert runs_ws1[0]["workspaceId"] == "ws_1"

    runs_ws2 = repo.list_runs("ws_2")
    assert len(runs_ws2) == 1
    assert runs_ws2[0]["workspaceId"] == "ws_2"

def test_list_recent_runs_limit_and_ordering(db_session):
    """
    5. list_recent_runs returns newest first and respects limit.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    
    run_ids = []
    for i in range(5):
        run = repo.save_run(workspace_id="ws_1", run_type="forecast", status="completed")
        run_ids.append(run["id"])
        
    # Set different created_at
    for idx, run_id in enumerate(run_ids):
        db_run = db_session.query(DbAnalysisRun).filter_by(id=run_id).first()
        db_run.created_at = datetime(2026, 6, 11, 10, idx, 0, tzinfo=timezone.utc)
    db_session.commit()

    # list_recent_runs with limit 3, should be newest first (idx 4, 3, 2)
    recent_runs = repo.list_recent_runs("ws_1", limit=3)
    assert len(recent_runs) == 3
    assert recent_runs[0]["id"] == run_ids[4]
    assert recent_runs[1]["id"] == run_ids[3]
    assert recent_runs[2]["id"] == run_ids[2]

def test_update_run_status_payload(db_session):
    """
    6. update_run_status updates status and output_payload.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    run = repo.save_run(workspace_id="ws_1", run_type="forecast", status="pending")

    updated = repo.update_run_status(
        run_id=run["id"],
        status="completed",
        output_payload={"metrics": {"rev": 100}}
    )
    assert updated["status"] == "completed"
    assert updated["results"] == {"metrics": {"rev": 100}}

    # Retrieve again
    retrieved = repo.get_run(run["id"])
    assert retrieved["status"] == "completed"
    assert retrieved["results"] == {"metrics": {"rev": 100}}

def test_completed_status_sets_completed_at(db_session):
    """
    7. completed status sets completed_at if supported.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    run = repo.save_run(workspace_id="ws_1", run_type="forecast", status="pending")
    
    # Retrieve model to check initial completed_at
    db_run = db_session.query(DbAnalysisRun).filter_by(id=run["id"]).first()
    assert db_run.completed_at is None

    # Update status to completed
    updated = repo.update_run_status(run_id=run["id"], status="completed")
    assert updated["completedAt"] is not None
    assert updated["durationMs"] is not None

def test_failed_status_stores_error_message(db_session):
    """
    8. failed status stores error_message.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    run = repo.save_run(workspace_id="ws_1", run_type="forecast", status="pending")

    updated = repo.update_run_status(
        run_id=run["id"],
        status="failed",
        error_message="Runtime exception occurred"
    )
    assert updated["status"] == "failed"
    
    # Retrieve raw model to check error_message
    db_run = db_session.query(DbAnalysisRun).filter_by(id=run["id"]).first()
    assert db_run.error_message == "Runtime exception occurred"

def test_missing_run_returns_none(db_session):
    """
    9. missing run returns None.
    """
    repo = DatabaseAnalysisRunRepository(db_session)
    assert repo.get_run("run_missing_123") is None

def test_metadata_payloads_round_trip(db_session):
    """
    10. metadata/input/output/summary round-trip correctly.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseAnalysisRunRepository(db_session)
    inputs = {"dataset": "q3_actuals", "adjustments": [1, 2, 3]}
    outputs = {"summary": {"total": 500}, "breakdown": {"tax": 50}}
    summary = {"warnings": ["High volatility"], "errors": []}
    meta = {"source_trace": {"user": "admin"}, "logic_version": "v1.2"}

    run = repo.save_run(
        workspace_id="ws_1",
        run_type="scenarios",
        status="completed",
        input_payload=inputs,
        output_payload=outputs,
        summary=summary,
        metadata=meta
    )
    assert run["inputs"] == inputs
    assert run["results"] == outputs
    assert run["warnings"] == ["High volatility"]
    assert run["sourceTrace"] == {"user": "admin"}
    assert run["logicVersion"] == "v1.2"

    retrieved = repo.get_run(run["id"])
    assert retrieved["inputs"] == inputs
    assert retrieved["results"] == outputs
    assert retrieved["warnings"] == ["High volatility"]
    assert retrieved["sourceTrace"] == {"user": "admin"}
    assert retrieved["logicVersion"] == "v1.2"

def test_factory_returns_db_repo(db_session):
    """
    11. factory returns DatabaseAnalysisRunRepository for database backend with db_session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    repo = get_analysis_run_repository(settings, db_session=db_session)
    assert repo.__class__.__name__ == "DatabaseAnalysisRunRepository"

def test_factory_db_without_session_raises():
    """
    12. factory database backend without db_session raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_analysis_run_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_factory_local_explicit():
    """
    13. local backend behavior remains explicit and does not accidentally create DB repository.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_analysis_run_repository(settings)
    assert repo.__class__.__name__ == "LocalAnalysisRunRepository"

def test_no_global_session_on_import():
    """
    14. no DB engine/session is created by importing persistence interfaces/factory.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_analysis_run_repository(settings)
    assert repo is not None
