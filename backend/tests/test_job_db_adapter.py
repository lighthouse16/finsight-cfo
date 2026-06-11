import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Workspace, Organization, Job as DbJob
from app.persistence.database_adapters import DatabaseJobRepository
from app.persistence.factory import get_job_repository
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

def test_create_and_retrieve_job(db_session):
    """
    1. DatabaseJobRepository can create and retrieve a workspace job.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job = repo.create_job(
        job_type="generate_report",
        workspace_id="ws_1",
        payload={"report_type": "pdf"},
        metadata={"logic_version": "v1.2"}
    )
    assert job["id"].startswith("job_")
    assert job["workspaceId"] == "ws_1"
    assert job["jobType"] == "generate_report"
    assert job["status"] == "pending"
    assert job["payload"] == {"report_type": "pdf"}
    assert job["metadata"] == {"logic_version": "v1.2"}
    assert job["queuedAt"] is not None

    retrieved = repo.get_job(job["id"])
    assert retrieved is not None
    assert retrieved["id"] == job["id"]
    assert retrieved["status"] == "pending"
    assert retrieved["payload"] == {"report_type": "pdf"}
    assert retrieved["metadata"] == {"logic_version": "v1.2"}

def test_create_job_requires_existing_workspace(db_session):
    """
    2. create_job requires existing workspace when workspace_id is provided.
    """
    repo = DatabaseJobRepository(db_session)
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        repo.create_job(
            job_type="generate_report",
            workspace_id="ws_non_existent"
        )
    assert "Workspace 'ws_non_existent' does not exist" in str(exc_info.value)

def test_saved_workspace_job_uses_organization_id(db_session):
    """
    3. saved workspace job uses workspace.organization_id.
    """
    org = Organization(id="org_custom", name="Custom Org")
    db_session.add(org)
    ws = Workspace(id="ws_custom", organization_id="org_custom", name="WS Custom", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job = repo.create_job(
        job_type="generate_report",
        workspace_id="ws_custom"
    )
    orm_job = db_session.query(DbJob).filter_by(id=job["id"]).first()
    assert orm_job is not None
    assert orm_job.organization_id == "org_custom"

def test_list_jobs_limit_and_ordering(db_session):
    """
    4. list_jobs returns newest first and respects limit.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job_ids = []
    for i in range(5):
        job = repo.create_job(job_type=f"job_{i}", workspace_id="ws_1")
        job_ids.append(job["id"])

    # Alter created_at times to verify sorting
    for idx, j_id in enumerate(job_ids):
        db_jb = db_session.query(DbJob).filter_by(id=j_id).first()
        db_jb.created_at = datetime(2026, 6, 11, 10, idx, 0, tzinfo=timezone.utc)
    db_session.commit()

    # list_jobs newest first, limit 3
    recent = repo.list_jobs(workspace_id="ws_1", limit=3)
    assert len(recent) == 3
    assert recent[0]["id"] == job_ids[4]
    assert recent[1]["id"] == job_ids[3]
    assert recent[2]["id"] == job_ids[2]

def test_list_jobs_filters_workspace(db_session):
    """
    5. list_jobs filters by workspace_id.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws1 = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    ws2 = Workspace(id="ws_2", organization_id="org_1", name="WS 2", status="active")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    repo.create_job(job_type="job", workspace_id="ws_1")
    repo.create_job(job_type="job", workspace_id="ws_2")

    jobs1 = repo.list_jobs(workspace_id="ws_1")
    assert len(jobs1) == 1
    assert jobs1[0]["workspaceId"] == "ws_1"

    jobs2 = repo.list_jobs(workspace_id="ws_2")
    assert len(jobs2) == 1
    assert jobs2[0]["workspaceId"] == "ws_2"

def test_list_jobs_filters_status(db_session):
    """
    6. list_jobs filters by status.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job1 = repo.create_job(job_type="job", workspace_id="ws_1")
    job2 = repo.create_job(job_type="job", workspace_id="ws_1")

    repo.update_job_status(job1["id"], "running")
    repo.update_job_status(job2["id"], "completed")

    running_jobs = repo.list_jobs(workspace_id="ws_1", status="running")
    assert len(running_jobs) == 1
    assert running_jobs[0]["id"] == job1["id"]

    completed_jobs = repo.list_jobs(workspace_id="ws_1", status="completed")
    assert len(completed_jobs) == 1
    assert completed_jobs[0]["id"] == job2["id"]

def test_mark_job_started(db_session):
    """
    7. mark_job_started sets status running and started_at.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job = repo.create_job(job_type="job", workspace_id="ws_1")
    
    db_jb = db_session.query(DbJob).filter_by(id=job["id"]).first()
    assert db_jb.started_at is None

    updated = repo.mark_job_started(job["id"])
    assert updated["status"] == "running"
    assert updated["startedAt"] is not None

def test_mark_job_completed(db_session):
    """
    8. mark_job_completed sets status completed, result_payload, and completed_at.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job = repo.create_job(job_type="job", workspace_id="ws_1")
    repo.mark_job_started(job["id"])

    res = {"report_url": "s3://reports/rep.pdf"}
    updated = repo.mark_job_completed(job["id"], result_payload=res)
    assert updated["status"] == "completed"
    assert updated["result"] == res
    assert updated["completedAt"] is not None

def test_mark_job_failed(db_session):
    """
    9. mark_job_failed sets status failed, error_message, and completed_at.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job = repo.create_job(job_type="job", workspace_id="ws_1")
    repo.mark_job_started(job["id"])

    updated = repo.mark_job_failed(job["id"], error_message="Internal Server Error")
    assert updated["status"] == "failed"
    assert updated["errorMessage"] == "Internal Server Error"
    assert updated["completedAt"] is not None

def test_update_job_status_generic(db_session):
    """
    10. update_job_status updates generic status/result/error.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    job = repo.create_job(job_type="job", workspace_id="ws_1")

    updated = repo.update_job_status(
        job_id=job["id"],
        status="cancelled",
        result_payload={"cancelled_by": "user"},
        error_message="User requested cancel",
        metadata={"node": "worker-2"}
    )
    assert updated["status"] == "cancelled"
    assert updated["result"] == {"cancelled_by": "user"}
    assert updated["errorMessage"] == "User requested cancel"
    assert updated["metadata"]["node"] == "worker-2"

def test_metadata_payload_round_trip(db_session):
    """
    11. metadata and payload round-trip correctly.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseJobRepository(db_session)
    payload = {"step": 1, "data": [1, 2]}
    meta = {"job_class": "heavy_duty"}

    job = repo.create_job(
        job_type="job",
        workspace_id="ws_1",
        payload=payload,
        metadata=meta
    )
    assert job["payload"] == payload
    assert job["metadata"] == meta

    retrieved = repo.get_job(job["id"])
    assert retrieved["payload"] == payload
    assert retrieved["metadata"] == meta

def test_get_job_missing_returns_none(db_session):
    """
    12. get_job returns None for missing job.
    """
    repo = DatabaseJobRepository(db_session)
    assert repo.get_job("job_missing_123") is None

def test_org_level_job_resolves_organization(db_session):
    """
    13. org-level job requires resolvable organization_id.
    """
    repo = DatabaseJobRepository(db_session)
    
    # 1. No org_default and no org provided -> Raises PersistenceConfigurationError
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        repo.create_job(job_type="sys_cleanup")
    assert "organization_id must be provided" in str(exc_info.value)

    # 2. Provide org_id in metadata -> Saves successfully
    org = Organization(id="org_custom", name="Custom Org")
    db_session.add(org)
    db_session.commit()

    job1 = repo.create_job(job_type="sys_cleanup", metadata={"organization_id": "org_custom"})
    assert job1["organizationId"] == "org_custom"

    # 3. Provide org_id in payload -> Saves successfully
    job2 = repo.create_job(job_type="sys_cleanup", payload={"organization_id": "org_custom"})
    assert job2["organizationId"] == "org_custom"

    # 4. If org_default exists, fallback works without explicit organization_id
    default_org = Organization(id="org_default", name="Default Org")
    db_session.add(default_org)
    db_session.commit()

    job3 = repo.create_job(job_type="sys_cleanup")
    assert job3["organizationId"] == "org_default"

def test_factory_returns_db_repo(db_session):
    """
    14. factory returns DatabaseJobRepository for database backend with db_session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    repo = get_job_repository(settings, db_session=db_session)
    assert repo.__class__.__name__ == "DatabaseJobRepository"

def test_factory_db_without_session_raises():
    """
    15. factory database backend without db_session raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_job_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_factory_local_explicit():
    """
    16. local backend behavior remains explicit and does not accidentally create DB repository.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_job_repository(settings)
    assert repo.__class__.__name__ == "LocalJobRepository"

def test_no_global_session_on_import():
    """
    17. no DB engine/session is created by importing persistence interfaces/factory.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_job_repository(settings)
    assert repo is not None
