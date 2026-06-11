import pytest
from fastapi import HTTPException
from app.services.report_worker_service import process_report_generation_job

class MockJobRepository:
    def __init__(self):
        self.jobs = {}
        self.actions = []

    def create_job_with_status(self, job_id, job_type, status, workspace_id="ws_123", payload=None, metadata=None):
        job = {
            "id": job_id,
            "workspaceId": workspace_id,
            "jobType": job_type,
            "status": status,
            "payload": payload or {},
            "metadata": metadata or {},
            "result": {},
            "errorMessage": "",
            "queuedAt": "2026-06-12T00:00:00Z",
            "startedAt": None,
            "completedAt": None,
        }
        self.jobs[job_id] = job
        return job

    def get_job(self, job_id):
        return self.jobs.get(job_id)

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

    def update_job_status(self, job_id, status, result_payload=None, error_message=None, metadata=None):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            if error_message is not None:
                self.jobs[job_id]["errorMessage"] = error_message
            if result_payload is not None:
                self.jobs[job_id]["result"] = result_payload
            if metadata is not None:
                self.jobs[job_id]["metadata"] = {**(self.jobs[job_id].get("metadata") or {}), **metadata}
        self.actions.append(("update_status", job_id, status))
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

def test_process_pending_report_generation_job_success():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_id = "job_123"
    payload = {
        "report_type": "financial_health",
        "report_payload": {"revenue": 100000, "expenses": 75000},
        "storage_uri": "s3://reports/financial_health.pdf"
    }
    metadata = {"title": "Monthly Financial Health Report", "organization_id": "org_abc"}
    
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="pending",
        workspace_id="ws_123",
        payload=payload,
        metadata=metadata
    )

    res = process_report_generation_job(
        job_repository=job_repo,
        report_repository=report_repo,
        job_id=job_id
    )

    # 1. Assert result structure
    assert res["status"] == "completed"
    assert res["report_id"].startswith("report_")
    assert res["report_name"] == "Monthly Financial Health Report"
    assert res["storage_uri"] == "s3://reports/financial_health.pdf"

    # 2. Assert status sequence transitions
    assert job_repo.actions == [
        ("update_status", job_id, "pending"),
        ("update_status", job_id, "pending"),
        ("running", job_id, "running"),
        ("update_status", job_id, "running"),
        ("update_status", job_id, "running"),
        ("completed", job_id, "completed")
    ]
    assert report_repo.save_called

    # 3. Assert job result in repo
    job = job_repo.get_job(job_id)
    assert job["status"] == "completed"
    assert job["result"]["report_id"] == res["report_id"]
    assert job["result"]["report_name"] == "Monthly Financial Health Report"
    assert job["result"]["storage_uri"] == "s3://reports/financial_health.pdf"

def test_process_report_generation_job_failure():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository(should_fail=True)

    job_id = "job_123"
    payload = {
        "report_type": "financial_health",
        "report_payload": {"revenue": 100000}
    }
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="pending",
        workspace_id="ws_123",
        payload=payload
    )

    # Verify that original runtime error is re-raised
    with pytest.raises(RuntimeError) as exc_info:
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id=job_id
        )
    assert "Database connection timed out" in str(exc_info.value)

    # Verify that status sequence marked running then failed
    assert job_repo.actions == [
        ("update_status", job_id, "pending"),
        ("update_status", job_id, "pending"),
        ("running", job_id, "running"),
        ("update_status", job_id, "running"),
        ("update_status", job_id, "running"),
        ("failed", job_id, "failed")
    ]
    job = job_repo.get_job(job_id)
    assert job["status"] == "failed"
    assert "Database connection timed out" in job["errorMessage"]

def test_process_job_completed_rejected():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_id = "job_123"
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="completed"
    )

    with pytest.raises(HTTPException) as exc_info:
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id=job_id
        )
    assert exc_info.value.status_code == 400
    assert "Cannot process job" in exc_info.value.detail
    assert not report_repo.save_called

def test_process_job_failed_rejected():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_id = "job_123"
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="failed"
    )

    with pytest.raises(HTTPException) as exc_info:
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id=job_id
        )
    assert exc_info.value.status_code == 400
    assert "Cannot process job" in exc_info.value.detail
    assert not report_repo.save_called

def test_process_job_cancelled_rejected():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_id = "job_123"
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="cancelled"
    )

    with pytest.raises(HTTPException) as exc_info:
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id=job_id
        )
    assert exc_info.value.status_code == 400
    assert "Cannot process job" in exc_info.value.detail
    assert not report_repo.save_called

def test_process_job_invalid_type_rejected():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_id = "job_123"
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="analysis_run",
        status="pending"
    )

    with pytest.raises(HTTPException) as exc_info:
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id=job_id
        )
    assert exc_info.value.status_code == 400
    assert "Invalid job type" in exc_info.value.detail
    assert not report_repo.save_called

def test_process_job_missing_raises_404():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    with pytest.raises(HTTPException) as exc_info:
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id="missing_job_id"
        )
    assert exc_info.value.status_code == 404
    assert "Job not found" in exc_info.value.detail

def test_process_job_rejects_file_bytes():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_id = "job_123"
    payload = {
        "report_type": "financial_health",
        "report_payload": {"raw_pdf_bytes": b"binary data"}
    }
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="pending",
        payload=payload
    )

    with pytest.raises(HTTPException) as exc_info:
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id=job_id
        )
    assert exc_info.value.status_code == 422
    assert "File bytes are not allowed" in exc_info.value.detail
    assert not report_repo.save_called

def test_process_job_does_not_spawn_workers_or_threads(monkeypatch):
    # Ensure no threading or process pooling is imported or run
    import threading
    import multiprocessing
    
    # We can mock threading.Thread to detect if one is created
    thread_spawned = False
    original_thread = threading.Thread
    def dummy_thread(*args, **kwargs):
        nonlocal thread_spawned
        thread_spawned = True
        return original_thread(*args, **kwargs)
    monkeypatch.setattr(threading, "Thread", dummy_thread)

    job_repo = MockJobRepository()
    report_repo = MockReportRepository()
    job_id = "job_123"
    payload = {
        "report_type": "financial_health",
        "report_payload": {"revenue": 100000}
    }
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="pending",
        payload=payload
    )

    process_report_generation_job(
        job_repository=job_repo,
        report_repository=report_repo,
        job_id=job_id
    )

    assert not thread_spawned, "Service spawned a thread!"

def test_report_worker_records_attempts_and_progress_success():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_id = "job_123"
    payload = {
        "report_type": "financial_health",
        "report_payload": {"revenue": 100000}
    }
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="pending",
        workspace_id="ws_123",
        payload=payload
    )

    res = process_report_generation_job(
        job_repository=job_repo,
        report_repository=report_repo,
        job_id=job_id
    )

    # Verify attempts incremented
    job = job_repo.get_job(job_id)
    assert job["metadata"]["attempts"] == 1

    # Verify progress milestones recorded
    progress = job["metadata"]["progress"]
    assert progress["percent"] == 100
    assert progress["stage"] == "completed"
    assert progress["message"] == "Report generated successfully"

def test_report_worker_records_attempts_and_progress_failure():
    job_repo = MockJobRepository()
    report_repo = MockReportRepository(should_fail=True)

    job_id = "job_123"
    payload = {
        "report_type": "financial_health",
        "report_payload": {"revenue": 100000}
    }
    job_repo.create_job_with_status(
        job_id=job_id,
        job_type="report.generation",
        status="pending",
        workspace_id="ws_123",
        payload=payload
    )

    with pytest.raises(RuntimeError):
        process_report_generation_job(
            job_repository=job_repo,
            report_repository=report_repo,
            job_id=job_id
        )

    # Verify attempts incremented
    job = job_repo.get_job(job_id)
    assert job["metadata"]["attempts"] == 1

    # Verify progress milestone failed state recorded
    progress = job["metadata"]["progress"]
    assert progress["percent"] == 50
    assert progress["stage"] == "failed"
    assert "Database connection timed out" in progress["message"]
