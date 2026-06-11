import pytest
from fastapi import HTTPException
from app.services.report_generation_job_service import generate_report_with_job

class MockJobRepository:
    def __init__(self):
        self.jobs = {}
        self.actions = []

    def create_job(self, job_type, workspace_id=None, payload=None, metadata=None):
        job_id = f"job_{len(self.jobs) + 1}"
        job = {
            "id": job_id,
            "workspaceId": workspace_id or "",
            "jobType": job_type,
            "status": "pending",
            "payload": payload or {},
            "metadata": metadata or {},
            "result": {},
            "errorMessage": "",
            "queuedAt": "2026-06-12T00:00:00Z",
            "startedAt": None,
            "completedAt": None,
        }
        self.jobs[job_id] = job
        self.actions.append(("create", job_id, "pending"))
        return job

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def list_jobs(self, workspace_id=None, status=None, limit=100):
        return list(self.jobs.values())

    def mark_job_started(self, job_id):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["startedAt"] = "2026-06-12T00:01:00Z"
        self.actions.append(("running", job_id, "running"))
        return self.jobs.get(job_id)

    def mark_job_completed(self, job_id, result_payload=None):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["result"] = result_payload or {}
            self.jobs[job_id]["completedAt"] = "2026-06-12T00:02:00Z"
        self.actions.append(("completed", job_id, "completed"))
        return self.jobs.get(job_id)

    def mark_job_failed(self, job_id, error_message):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["errorMessage"] = error_message
            self.jobs[job_id]["completedAt"] = "2026-06-12T00:02:00Z"
        self.actions.append(("failed", job_id, "failed"))
        return self.jobs.get(job_id)

    def update_job_status(self, job_id, status, error_message=None):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
        self.actions.append(("update", job_id, status))
        return self.jobs.get(job_id)

class MockReportRepository:
    def __init__(self, should_fail=False):
        self.reports = {}
        self.should_fail = should_fail
        self.save_called = False

    def save_report(self, workspace_id, report_type, title, report_payload, storage_uri=None, metadata=None):
        self.save_called = True
        if self.should_fail:
            raise RuntimeError("Database connection timed out during save")

        report_id = f"report_{len(self.reports) + 1}"
        report = {
            "id": report_id,
            "workspaceId": workspace_id,
            "report_type": report_type,
            "title": title,
            "report_payload": report_payload,
            "storage_uri": storage_uri,
            "metadata": metadata or {},
        }
        self.reports[report_id] = report
        return report

def test_generate_report_success():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()
    
    workspace_id = "ws_123"
    org_id = "org_567"
    report_payload = {"revenue": 100000, "expenses": 75000}
    metadata = {"title": "Q2 Financial Statement", "custom_tag": "internal"}
    storage_uri = "s3://reports/q2_financials.pdf"

    res = generate_report_with_job(
        job_repository=job_repo,
        report_repository=report_repo,
        workspace_id=workspace_id,
        organization_id=org_id,
        report_type="financial_health",
        report_payload=report_payload,
        metadata=metadata,
        storage_uri=storage_uri,
    )

    # 1. Assert result structure
    assert "job" in res
    assert "report" in res

    # 2. Assert job transitions and parameters
    job = res["job"]
    assert job["jobType"] == "report.generation"
    assert job["workspaceId"] == workspace_id
    assert job["status"] == "completed"
    assert job["metadata"]["organization_id"] == org_id
    assert job["metadata"]["custom_tag"] == "internal"
    
    # 3. Assert report details
    report = res["report"]
    assert report["id"].startswith("report_")
    assert report["workspaceId"] == workspace_id
    assert report["title"] == "Q2 Financial Statement"
    assert report["report_payload"] == report_payload
    assert report["storage_uri"] == storage_uri

    # 4. Assert correct transition sequence: pending -> running -> completed
    job_id = job["id"]
    expected_actions = [
        ("create", job_id, "pending"),
        ("running", job_id, "running"),
        ("completed", job_id, "completed"),
    ]
    assert job_repo.actions == expected_actions
    assert report_repo.save_called

    # 5. Assert job result contains report details
    assert job["result"]["report_id"] == report["id"]
    assert job["result"]["report_name"] == "Q2 Financial Statement"
    assert job["result"]["storage_uri"] == storage_uri

def test_generate_report_failure():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository(should_fail=True)

    workspace_id = "ws_123"
    report_payload = {"revenue": 100000}

    # Verify that the original database exception is re-raised
    with pytest.raises(RuntimeError) as exc_info:
        generate_report_with_job(
            job_repository=job_repo,
            report_repository=report_repo,
            workspace_id=workspace_id,
            organization_id=None,
            report_type="financial_health",
            report_payload=report_payload,
        )
    assert "Database connection timed out" in str(exc_info.value)

    # Verify that the job was created, marked running, and then failed
    assert len(job_repo.jobs) == 1
    job = list(job_repo.jobs.values())[0]
    assert job["status"] == "failed"
    assert "Database connection timed out" in job["errorMessage"]

    job_id = job["id"]
    expected_actions = [
        ("create", job_id, "pending"),
        ("running", job_id, "running"),
        ("failed", job_id, "failed"),
    ]
    assert job_repo.actions == expected_actions
    assert report_repo.save_called

def test_generate_report_rejects_file_bytes():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    workspace_id = "ws_123"
    payload_with_bytes = {"raw_file": b"pdf content"}

    with pytest.raises(HTTPException) as exc_info:
        generate_report_with_job(
            job_repository=job_repo,
            report_repository=report_repo,
            workspace_id=workspace_id,
            organization_id=None,
            report_type="financial_health",
            report_payload=payload_with_bytes,
        )
    assert exc_info.value.status_code == 422
    assert "File bytes are not allowed" in exc_info.value.detail
    assert len(job_repo.jobs) == 0
    assert not report_repo.save_called
