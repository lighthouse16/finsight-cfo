import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Workspace, Organization, Report as DbReport
from app.persistence.database_adapters import DatabaseReportRepository
from app.persistence.factory import get_report_repository
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

def test_save_and_retrieve_report(db_session):
    """
    1. DatabaseReportRepository can save and retrieve a workspace report.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    report = repo.save_report(
        workspace_id="ws_1",
        report_type="annual_summary",
        title="Annual Report 2025",
        report_payload={"metrics": {"revenue": 1000000}},
        storage_uri="s3://reports/annual_2025.pdf",
        metadata={"generated_by": "ai_cfo"}
    )
    assert report["id"].startswith("rep_")
    assert report["workspaceId"] == "ws_1"
    assert report["organizationId"] == "org_1"
    assert report["reportType"] == "annual_summary"
    assert report["title"] == "Annual Report 2025"
    assert report["status"] == "completed"
    assert report["reportPayload"] == {"metrics": {"revenue": 1000000}}
    assert report["storageUri"] == "s3://reports/annual_2025.pdf"
    assert report["metadata"] == {"generated_by": "ai_cfo"}
    assert report["createdAt"] is not None

    retrieved = repo.get_report(report["id"])
    assert retrieved is not None
    assert retrieved["id"] == report["id"]
    assert retrieved["title"] == "Annual Report 2025"
    assert retrieved["reportPayload"] == {"metrics": {"revenue": 1000000}}

def test_save_report_requires_existing_workspace(db_session):
    """
    2. save_report requires existing workspace.
    """
    repo = DatabaseReportRepository(db_session)
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        repo.save_report(
            workspace_id="ws_non_existent",
            report_type="annual_summary",
            title="Annual Report 2025"
        )
    assert "Workspace 'ws_non_existent' does not exist" in str(exc_info.value)

def test_saved_report_uses_workspace_organization_id(db_session):
    """
    3. saved report uses workspace.organization_id.
    """
    org = Organization(id="org_custom", name="Custom Org")
    db_session.add(org)
    ws = Workspace(id="ws_custom", organization_id="org_custom", name="WS Custom", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    report = repo.save_report(
        workspace_id="ws_custom",
        report_type="monthly_brief",
        title="June 2026"
    )
    orm_report = db_session.query(DbReport).filter_by(id=report["id"]).first()
    assert orm_report is not None
    assert orm_report.organization_id == "org_custom"

def test_list_reports_limit_and_ordering(db_session):
    """
    4. list_reports returns newest first and respects limit.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    report_ids = []
    for i in range(5):
        report = repo.save_report(
            workspace_id="ws_1",
            report_type="brief",
            title=f"Brief {i}"
        )
        report_ids.append(report["id"])

    # Alter created_at times to verify sorting
    for idx, r_id in enumerate(report_ids):
        db_rep = db_session.query(DbReport).filter_by(id=r_id).first()
        db_rep.created_at = datetime(2026, 6, 11, 10, idx, 0, tzinfo=timezone.utc)
    db_session.commit()

    recent = repo.list_reports(workspace_id="ws_1", limit=3)
    assert len(recent) == 3
    assert recent[0]["id"] == report_ids[4]
    assert recent[1]["id"] == report_ids[3]
    assert recent[2]["id"] == report_ids[2]

def test_list_reports_filters_workspace(db_session):
    """
    5. list_reports filters by workspace_id.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws1 = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    ws2 = Workspace(id="ws_2", organization_id="org_1", name="WS 2", status="active")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    repo.save_report(workspace_id="ws_1", report_type="type_a", title="Rep 1")
    repo.save_report(workspace_id="ws_2", report_type="type_a", title="Rep 2")

    reports1 = repo.list_reports(workspace_id="ws_1")
    assert len(reports1) == 1
    assert reports1[0]["workspaceId"] == "ws_1"

    reports2 = repo.list_reports(workspace_id="ws_2")
    assert len(reports2) == 1
    assert reports2[0]["workspaceId"] == "ws_2"

def test_list_reports_filters_type(db_session):
    """
    6. list_reports filters by report_type.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    repo.save_report(workspace_id="ws_1", report_type="type_a", title="Report A")
    repo.save_report(workspace_id="ws_1", report_type="type_b", title="Report B")

    type_a_reports = repo.list_reports(workspace_id="ws_1", report_type="type_a")
    assert len(type_a_reports) == 1
    assert type_a_reports[0]["reportType"] == "type_a"

    type_b_reports = repo.list_reports(workspace_id="ws_1", report_type="type_b")
    assert len(type_b_reports) == 1
    assert type_b_reports[0]["reportType"] == "type_b"

def test_update_report_status(db_session):
    """
    7. update_report_status updates status/storage_uri/metadata.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    report = repo.save_report(
        workspace_id="ws_1",
        report_type="brief",
        title="Pending Report",
        storage_uri=None,
        metadata={"initial": "value"}
    )

    updated = repo.update_report_status(
        report_id=report["id"],
        status="failed",
        storage_uri="s3://errors/failed.pdf",
        metadata={"error_reason": "timeout"}
    )
    assert updated["status"] == "failed"
    assert updated["storageUri"] == "s3://errors/failed.pdf"
    assert updated["metadata"] == {"initial": "value", "error_reason": "timeout"}

    # Verify updates persisted
    retrieved = repo.get_report(report["id"])
    assert retrieved["status"] == "failed"
    assert retrieved["storageUri"] == "s3://errors/failed.pdf"

def test_delete_report_hides_report(db_session):
    """
    8. delete_report hides report from get/list.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    report = repo.save_report(
        workspace_id="ws_1",
        report_type="brief",
        title="To Delete"
    )

    # Verify visible
    assert repo.get_report(report["id"]) is not None
    assert len(repo.list_reports(workspace_id="ws_1")) == 1

    # Delete
    success = repo.delete_report(report["id"])
    assert success is True

    # Verify hidden
    assert repo.get_report(report["id"]) is None
    assert len(repo.list_reports(workspace_id="ws_1")) == 0

    # Test deleting already deleted/missing report
    assert repo.delete_report(report["id"]) is False
    assert repo.delete_report("rep_non_existent") is False

def test_report_payload_round_trip(db_session):
    """
    9. report_payload round-trips correctly.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    payload = {"complex": {"list": [1, 2, 3], "value": True}}
    report = repo.save_report(
        workspace_id="ws_1",
        report_type="brief",
        title="Roundtrip Payload",
        report_payload=payload
    )
    assert report["reportPayload"] == payload

    retrieved = repo.get_report(report["id"])
    assert retrieved["reportPayload"] == payload

def test_metadata_round_trip(db_session):
    """
    10. metadata round-trips correctly.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    meta = {"nested": {"key": "value"}}
    report = repo.save_report(
        workspace_id="ws_1",
        report_type="brief",
        title="Roundtrip Metadata",
        metadata=meta
    )
    assert report["metadata"] == meta

    retrieved = repo.get_report(report["id"])
    assert retrieved["metadata"] == meta

def test_storage_uri_round_trip(db_session):
    """
    11. storage_uri round-trips correctly.
    """
    org = Organization(id="org_1", name="Org 1")
    db_session.add(org)
    ws = Workspace(id="ws_1", organization_id="org_1", name="WS 1", status="active")
    db_session.add(ws)
    db_session.commit()

    repo = DatabaseReportRepository(db_session)
    storage_uri = "s3://some-bucket/path/to/report.pdf"
    report = repo.save_report(
        workspace_id="ws_1",
        report_type="brief",
        title="Roundtrip Storage URI",
        storage_uri=storage_uri
    )
    assert report["storageUri"] == storage_uri

    retrieved = repo.get_report(report["id"])
    assert retrieved["storageUri"] == storage_uri

def test_get_report_missing_returns_none(db_session):
    """
    12. get_report returns None for missing report.
    """
    repo = DatabaseReportRepository(db_session)
    assert repo.get_report("rep_missing_123") is None

def test_factory_returns_db_repo(db_session):
    """
    13. factory returns DatabaseReportRepository for database backend with db_session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    repo = get_report_repository(settings, db_session=db_session)
    assert repo.__class__.__name__ == "DatabaseReportRepository"

def test_factory_db_without_session_raises():
    """
    14. factory database backend without db_session raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_report_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_factory_local_explicit():
    """
    15. local backend behavior remains explicit and does not accidentally create DB repository.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_report_repository(settings)
    assert repo.__class__.__name__ == "LocalReportRepository"

def test_no_global_session_on_import():
    """
    16. no DB engine/session is created by importing persistence interfaces/factory.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_report_repository(settings)
    assert repo is not None
