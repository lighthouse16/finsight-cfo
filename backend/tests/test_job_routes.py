import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db import models  # Register models on Base
from app.main import app
from app.routes.workspaces import get_db_session_optional, set_active_db_session
from app.core.config import settings

@pytest.fixture
def db_session():
    from sqlalchemy.pool import StaticPool
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

def test_local_mode_jobs_endpoint_throws_501(monkeypatch):
    """
    Local mode does not initialize DB engine/session, and returns a clean 501.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")

    from app.db import session as db_session_mod
    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    try:
        # Create workspace in local JSON first to satisfy workspace existence checks
        from app.storage.workspace_store import WorkspaceStore
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore.create_workspace("ws_local_123", "Local Corp")

        res_list = client.get("/api/workspaces/ws_local_123/jobs")
        assert res_list.status_code == 501
        assert "Background jobs are not supported" in res_list.json()["detail"]

        res_get = client.get("/api/workspaces/ws_local_123/jobs/job_any")
        assert res_get.status_code == 501
        assert "Background jobs are not supported" in res_get.json()["detail"]

        res_post = client.post(
            "/api/workspaces/ws_local_123/jobs/report-generation",
            json={
                "reportType": "financial_health",
                "reportPayload": {"revenue": 10000},
                "metadata": {"title": "Q3 Reports"}
            }
        )
        assert res_post.status_code == 501
        assert "Background jobs are not supported" in res_post.json()["detail"]

        res_tick = client.post("/api/workspaces/ws_local_123/jobs/report-worker/tick")
        assert res_tick.status_code == 200
        assert res_tick.json() == {
            "enabled": False,
            "scanned": 0,
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "jobIds": [],
            "errors": [],
            "skippedReason": "REPORT_WORKER_ENABLED flag is False",
        }

        # Ensure no DB engine/session was initialized
        assert db_session_mod._engine is None
        assert db_session_mod.SessionLocal is None
    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local
        from app.storage.workspace_store import WorkspaceStore
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])

def test_database_mode_job_routes(db_session, monkeypatch):
    """
    In database mode:
    1. GET workspace jobs returns jobs for that workspace, filtering by status / jobType.
    2. Excludes jobs from other workspaces.
    3. GET job by ID returns job payload (with safe camelCase and sanitized values).
    4. Missing job returns 404.
    5. Job in wrong workspace returns 404.
    6. Verify endpoints are read-only and do not trigger report worker or change job status.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session
    client = TestClient(app)

    try:
        from app.db.models import Organization, Workspace as DbWorkspace, Job as DbJob

        # Setup Organizations
        org = Organization(id="org_test", name="Test Org")
        db_session.add(org)
        
        # Setup Workspaces
        ws1 = DbWorkspace(id="ws_1", organization_id="org_test", name="Workspace One", status="active")
        ws2 = DbWorkspace(id="ws_2", organization_id="org_test", name="Workspace Two", status="active")
        db_session.add(ws1)
        db_session.add(ws2)
        db_session.commit()

        # Add jobs
        job1 = DbJob(
            id="job_ws1_pending_report",
            workspace_id="ws_1",
            organization_id="org_test",
            task_name="report.generation",
            status="pending",
            arguments={"report_type": "financial_health", "report_payload": {"revenue": 1000, "file_data": "json safe string"}},
            job_metadata={"title": "Q3 Health"},
            result_payload={}
        )
        job2 = DbJob(
            id="job_ws1_running_analysis",
            workspace_id="ws_1",
            organization_id="org_test",
            task_name="analysis.run",
            status="running",
            arguments={"run_type": "valuation"},
            job_metadata={"title": "Valuation Oct"},
            result_payload={"valuation_score": 9.5, "binary_file": "another safe string"}
        )
        job3 = DbJob(
            id="job_ws2_pending_report",
            workspace_id="ws_2",
            organization_id="org_test",
            task_name="report.generation",
            status="pending",
            arguments={"report_type": "valuation_summary"},
            job_metadata={"title": "Valuation Summary"},
            result_payload={}
        )
        db_session.add(job1)
        db_session.add(job2)
        db_session.add(job3)
        db_session.commit()

        # --- Test 1: GET workspaces/ws_1/jobs lists ws_1 jobs only ---
        list_res = client.get("/api/workspaces/ws_1/jobs")
        assert list_res.status_code == 200
        jobs_list = list_res.json()
        assert len(jobs_list) == 2
        ids = [j["id"] for j in jobs_list]
        assert "job_ws1_pending_report" in ids
        assert "job_ws1_running_analysis" in ids
        assert "job_ws2_pending_report" not in ids

        # --- Test 2: Filter by status ---
        filter_status = client.get("/api/workspaces/ws_1/jobs?status=pending")
        assert filter_status.status_code == 200
        pending_list = filter_status.json()
        assert len(pending_list) == 1
        assert pending_list[0]["id"] == "job_ws1_pending_report"

        # --- Test 3: Filter by jobType (camelCase query parameter) ---
        filter_type = client.get("/api/workspaces/ws_1/jobs?jobType=analysis.run")
        assert filter_type.status_code == 200
        type_list = filter_type.json()
        assert len(type_list) == 1
        assert type_list[0]["id"] == "job_ws1_running_analysis"

        # --- Test 4: Retrieve individual job by ID ---
        get_res = client.get("/api/workspaces/ws_1/jobs/job_ws1_pending_report")
        assert get_res.status_code == 200
        job_data = get_res.json()
        assert job_data["id"] == "job_ws1_pending_report"
        assert job_data["workspaceId"] == "ws_1"
        assert job_data["jobType"] == "report.generation"
        assert job_data["status"] == "pending"
        
        # Verify fields are mapped correctly
        assert job_data["inputPayload"]["report_payload"]["file_data"] == "json safe string"
        assert "organizationId" in job_data
        assert job_data["organizationId"] == "org_test"

        # Check running analysis job too
        get_res_2 = client.get("/api/workspaces/ws_1/jobs/job_ws1_running_analysis")
        assert get_res_2.status_code == 200
        job_data_2 = get_res_2.json()
        assert job_data_2["resultPayload"]["binary_file"] == "another safe string"

        # --- Test 5: Missing job returns 404 ---
        get_missing = client.get("/api/workspaces/ws_1/jobs/job_missing")
        assert get_missing.status_code == 404
        assert "Job not found" in get_missing.json()["detail"]

        # --- Test 6: Job in wrong workspace returns 404 ---
        get_wrong_ws = client.get("/api/workspaces/ws_2/jobs/job_ws1_pending_report")
        assert get_wrong_ws.status_code == 404
        assert "Job not found in this workspace" in get_wrong_ws.json()["detail"]

        # --- Test 7: GET requests are read-only and do not mutate job status ---
        db_job_before = db_session.query(DbJob).filter_by(id="job_ws1_pending_report").first()
        assert db_job_before.status == "pending"
        
        client.get("/api/workspaces/ws_1/jobs/job_ws1_pending_report")
        
        db_job_after = db_session.query(DbJob).filter_by(id="job_ws1_pending_report").first()
        assert db_job_after.status == "pending"

    finally:
        app.dependency_overrides.clear()

def test_sanitize_payload():
    from app.routes.jobs import sanitize_payload
    payload = {
        "bytes_field": b"hello bytes",
        "nested": {
            "bytearray_field": bytearray(b"hello bytearray"),
            "string_field": "safe string"
        },
        "list_field": [b"bytes in list", 42]
    }
    sanitized = sanitize_payload(payload)
    assert sanitized == {
        "bytes_field": "<binary data>",
        "nested": {
            "bytearray_field": "<binary data>",
            "string_field": "safe string"
        },
        "list_field": ["<binary data>", 42]
    }

def test_job_routes_metadata_exposure(db_session, monkeypatch):
    """
    Assert that job status route response exposes progress metadata and attempts count,
    and that routes remain read-only (they do not mutate attempts or progress).
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session
    client = TestClient(app)

    try:
        from app.db.models import Organization, Workspace as DbWorkspace, Job as DbJob

        # Setup Organizations
        org = Organization(id="org_test", name="Test Org")
        db_session.add(org)
        
        # Setup Workspaces
        ws1 = DbWorkspace(id="ws_1", organization_id="org_test", name="Workspace One", status="active")
        db_session.add(ws1)
        db_session.commit()

        # Add job with attempts and progress metadata
        job_metadata = {
            "attempts": 2,
            "max_attempts": 3,
            "progress": {
                "percent": 50,
                "stage": "generating",
                "message": "Generating chunks"
            }
        }
        job1 = DbJob(
            id="job_ws1_report",
            workspace_id="ws_1",
            organization_id="org_test",
            task_name="report.generation",
            status="failed",
            attempts=2,
            arguments={"report_type": "financial_health"},
            job_metadata=job_metadata,
            result_payload={}
        )
        db_session.add(job1)
        db_session.commit()

        # GET the job
        res = client.get("/api/workspaces/ws_1/jobs/job_ws1_report")
        assert res.status_code == 200
        data = res.json()
        
        # Check attempts and progress metadata are exposed
        assert data["metadata"]["attempts"] == 2
        assert data["metadata"]["progress"]["percent"] == 50
        assert data["metadata"]["progress"]["stage"] == "generating"
        assert data["metadata"]["progress"]["message"] == "Generating chunks"

        # Check route operations are read-only and do not mutate attempts/progress
        db_job = db_session.query(DbJob).filter_by(id="job_ws1_report").first()
        assert db_job.attempts == 2
        assert db_job.job_metadata["attempts"] == 2

    finally:
        app.dependency_overrides.clear()


def test_create_report_generation_job_route(db_session, monkeypatch):
    """
    In database mode:
    1. POST workspace report-generation job creates pending job and returns 201.
    2. Input payload matches request input.
    3. Metadata contains source="api" and max_attempts.
    4. Created job can be retrieved via GET endpoint.
    5. Does not call worker or persist reports.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session
    client = TestClient(app)

    try:
        from app.db.models import Organization, Workspace as DbWorkspace, Report as DbReport
        
        # Setup Organization
        org = Organization(id="org_test", name="Test Org")
        db_session.add(org)
        
        # Setup Workspace
        ws1 = DbWorkspace(id="ws_1", organization_id="org_test", name="Workspace One", status="active")
        db_session.add(ws1)
        db_session.commit()

        # Check report count before
        report_count_before = db_session.query(DbReport).count()
        assert report_count_before == 0

        # POST create report generation job
        post_data = {
            "reportType": "financial_health",
            "reportPayload": {"revenue": 120000, "expenses": 90000},
            "metadata": {"title": "Q4 Monthly Report"},
            "storageUri": "s3://my-bucket/reports/q4.pdf",
            "maxAttempts": 5
        }
        res = client.post("/api/workspaces/ws_1/jobs/report-generation", json=post_data)
        assert res.status_code == 201
        
        job_data = res.json()
        assert job_data["id"] is not None
        assert job_data["status"] == "pending"
        assert job_data["jobType"] == "report.generation"
        assert job_data["inputPayload"]["report_type"] == "financial_health"
        assert job_data["inputPayload"]["report_payload"] == {"revenue": 120000, "expenses": 90000}
        assert job_data["inputPayload"]["storage_uri"] == "s3://my-bucket/reports/q4.pdf"
        assert job_data["metadata"]["source"] == "api"
        assert job_data["metadata"]["max_attempts"] == 5
        assert job_data["metadata"]["title"] == "Q4 Monthly Report"

        # Check that no report record was created
        report_count_after = db_session.query(DbReport).count()
        assert report_count_after == 0

        # Retrieve individual job by ID
        get_res = client.get(f"/api/workspaces/ws_1/jobs/{job_data['id']}")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["id"] == job_data["id"]
        assert get_data["status"] == "pending"

        # List jobs
        list_res = client.get("/api/workspaces/ws_1/jobs")
        assert list_res.status_code == 200
        jobs_list = list_res.json()
        assert len(jobs_list) == 1
        assert jobs_list[0]["id"] == job_data["id"]

    finally:
        app.dependency_overrides.clear()


def test_trigger_report_worker_tick_route(db_session, monkeypatch):
    """
    In database mode:
    1. POST worker tick processes only pending report jobs in the requested workspace.
    2. Respects feature flag and existing max jobs per tick.
    3. Moves matching jobs to completed while leaving other jobs untouched.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")
    monkeypatch.setattr(settings, "REPORT_WORKER_ENABLED", True)
    monkeypatch.setattr(settings, "REPORT_WORKER_MAX_JOBS_PER_TICK", 1)

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session
    client = TestClient(app)

    try:
        from app.db.models import Organization, Workspace as DbWorkspace, Job as DbJob, Report as DbReport

        org = Organization(id="org_tick", name="Tick Org")
        db_session.add(org)
        db_session.add(DbWorkspace(id="ws_1", organization_id="org_tick", name="Workspace One", status="active"))
        db_session.add(DbWorkspace(id="ws_2", organization_id="org_tick", name="Workspace Two", status="active"))
        db_session.commit()

        db_session.add(DbJob(
            id="job_ws1_a",
            workspace_id="ws_1",
            organization_id="org_tick",
            task_name="report.generation",
            status="pending",
            arguments={"report_type": "financial_health", "report_payload": {"revenue": 1000}},
            job_metadata={"title": "WS1 Report A"},
            result_payload={},
        ))
        db_session.add(DbJob(
            id="job_ws1_b",
            workspace_id="ws_1",
            organization_id="org_tick",
            task_name="report.generation",
            status="pending",
            arguments={"report_type": "financial_health", "report_payload": {"revenue": 2000}},
            job_metadata={"title": "WS1 Report B"},
            result_payload={},
        ))
        db_session.add(DbJob(
            id="job_ws2_a",
            workspace_id="ws_2",
            organization_id="org_tick",
            task_name="report.generation",
            status="pending",
            arguments={"report_type": "financial_health", "report_payload": {"revenue": 3000}},
            job_metadata={"title": "WS2 Report A"},
            result_payload={},
        ))
        db_session.add(DbJob(
            id="job_ws1_analysis",
            workspace_id="ws_1",
            organization_id="org_tick",
            task_name="analysis.run",
            status="pending",
            arguments={"run_type": "valuation"},
            job_metadata={"title": "Analysis"},
            result_payload={},
        ))
        db_session.commit()

        res = client.post("/api/workspaces/ws_1/jobs/report-worker/tick")
        assert res.status_code == 200
        data = res.json()

        assert data["enabled"] is True
        assert data["scanned"] == 2
        assert data["processed"] == 1
        assert data["succeeded"] == 1
        assert data["failed"] == 0
        assert len(data["jobIds"]) == 1
        assert data["errors"] == []

        processed_job_id = data["jobIds"][0]
        processed_job = db_session.query(DbJob).filter_by(id=processed_job_id).first()
        assert processed_job.workspace_id == "ws_1"
        assert processed_job.status == "completed"

        remaining_ws1_job = db_session.query(DbJob).filter_by(id="job_ws1_a" if processed_job_id == "job_ws1_b" else "job_ws1_b").first()
        assert remaining_ws1_job.status == "pending"

        ws2_job = db_session.query(DbJob).filter_by(id="job_ws2_a").first()
        assert ws2_job.status == "pending"

        analysis_job = db_session.query(DbJob).filter_by(id="job_ws1_analysis").first()
        assert analysis_job.status == "pending"

        reports = db_session.query(DbReport).all()
        assert len(reports) == 1
        assert reports[0].workspace_id == "ws_1"

    finally:
        app.dependency_overrides.clear()


def test_trigger_report_worker_tick_route_returns_disabled_summary(db_session, monkeypatch):
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")
    monkeypatch.setattr(settings, "REPORT_WORKER_ENABLED", False)

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session
    client = TestClient(app)

    try:
        from app.db.models import Organization, Workspace as DbWorkspace, Job as DbJob

        org = Organization(id="org_tick_disabled", name="Tick Disabled Org")
        db_session.add(org)
        db_session.add(DbWorkspace(id="ws_disabled", organization_id="org_tick_disabled", name="Workspace Disabled", status="active"))
        db_session.add(DbJob(
            id="job_disabled",
            workspace_id="ws_disabled",
            organization_id="org_tick_disabled",
            task_name="report.generation",
            status="pending",
            arguments={"report_type": "financial_health"},
            job_metadata={"title": "Disabled Report"},
            result_payload={},
        ))
        db_session.commit()

        res = client.post("/api/workspaces/ws_disabled/jobs/report-worker/tick")
        assert res.status_code == 200
        assert res.json() == {
            "enabled": False,
            "scanned": 0,
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "jobIds": [],
            "errors": [],
            "skippedReason": "REPORT_WORKER_ENABLED flag is False",
        }

        job = db_session.query(DbJob).filter_by(id="job_disabled").first()
        assert job.status == "pending"

    finally:
        app.dependency_overrides.clear()


def test_create_request_model_rejects_bytes():
    from app.models.job import ReportGenerationJobCreateRequest
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc:
        ReportGenerationJobCreateRequest(
            reportType="financial_health",
            reportPayload={"pdf": b"binary PDF data"}
        )
    assert exc.value.status_code == 422

    with pytest.raises(HTTPException) as exc:
        ReportGenerationJobCreateRequest(
            reportType="financial_health",
            metadata={"file": bytearray(b"binary data")}
        )
    assert exc.value.status_code == 422



