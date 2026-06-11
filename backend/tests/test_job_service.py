import pytest
from fastapi import HTTPException
from app.services.job_service import (
    create_job,
    get_job,
    list_jobs,
    mark_job_running,
    mark_job_completed,
    mark_job_failed,
    cancel_job,
)

class MockJobRepository:
    def __init__(self, jobs=None):
        self.jobs = jobs or {}
        self.create_called = False
        self.mark_started_called = False
        self.mark_completed_called = False
        self.mark_failed_called = False
        self.update_status_called = False

    def create_job(self, job_type, workspace_id=None, payload=None, metadata=None):
        self.create_called = True
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
        return job

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def list_jobs(self, workspace_id=None, status=None, limit=100):
        res = list(self.jobs.values())
        if workspace_id:
            res = [j for j in res if j["workspaceId"] == workspace_id]
        if status:
            res = [j for j in res if j["status"] == status]
        return res[:limit]

    def mark_job_started(self, job_id):
        self.mark_started_called = True
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["startedAt"] = "2026-06-12T00:01:00Z"
        return self.jobs.get(job_id)

    def mark_job_completed(self, job_id, result_payload=None):
        self.mark_completed_called = True
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["result"] = result_payload or {}
            self.jobs[job_id]["completedAt"] = "2026-06-12T00:02:00Z"
        return self.jobs.get(job_id)

    def mark_job_failed(self, job_id, error_message):
        self.mark_failed_called = True
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["errorMessage"] = error_message
            self.jobs[job_id]["completedAt"] = "2026-06-12T00:02:00Z"
        return self.jobs.get(job_id)

    def update_job_status(self, job_id, status, error_message=None):
        self.update_status_called = True
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            if error_message:
                self.jobs[job_id]["errorMessage"] = error_message
        return self.jobs.get(job_id)

def test_create_job_passes_fields():
    repo = MockJobRepository()
    payload = {"param": 1}
    meta = {"source": "api"}
    job = create_job(
        job_type="generate_report",
        workspace_id="ws_123",
        payload=payload,
        metadata=meta,
        job_repo=repo,
    )
    assert job["jobType"] == "generate_report"
    assert job["workspaceId"] == "ws_123"
    assert job["payload"] == payload
    assert job["metadata"] == meta
    assert repo.create_called

def test_create_job_rejects_file_bytes():
    repo = MockJobRepository()
    payload_with_bytes = {"file_content": b"raw bytes data"}
    with pytest.raises(HTTPException) as exc_info:
        create_job(
            job_type="generate_report",
            workspace_id="ws_123",
            payload=payload_with_bytes,
            job_repo=repo,
        )
    assert exc_info.value.status_code == 422
    assert "File bytes are not allowed" in exc_info.value.detail

def test_get_job_success():
    repo = MockJobRepository()
    created = repo.create_job("generate_report", "ws_123")
    job_id = created["id"]
    job = get_job(job_id=job_id, job_repo=repo)
    assert job["id"] == job_id
    assert job["jobType"] == "generate_report"

def test_get_job_missing():
    repo = MockJobRepository()
    with pytest.raises(HTTPException) as exc_info:
        get_job(job_id="missing_id", job_repo=repo)
    assert exc_info.value.status_code == 404
    assert "Job not found" in exc_info.value.detail

def test_list_jobs():
    repo = MockJobRepository()
    repo.create_job("report", "ws_1")
    repo.create_job("analysis", "ws_2")
    repo.create_job("report", "ws_1")
    
    jobs = list_jobs(workspace_id="ws_1", job_repo=repo)
    assert len(jobs) == 2
    assert all(j["workspaceId"] == "ws_1" for j in jobs)

def test_mark_job_running_success():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    updated = mark_job_running(job_id=job_id, job_repo=repo)
    assert updated["status"] == "running"
    assert updated["startedAt"] is not None
    assert repo.mark_started_called

def test_mark_job_running_invalid_transition():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    # Transition to running first time (success)
    mark_job_running(job_id=job_id, job_repo=repo)
    
    # Second time should fail because status is no longer pending
    with pytest.raises(HTTPException) as exc_info:
        mark_job_running(job_id=job_id, job_repo=repo)
    assert exc_info.value.status_code == 400
    assert "Cannot transition job" in exc_info.value.detail

def test_mark_job_completed_success():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    mark_job_running(job_id=job_id, job_repo=repo)
    
    result = {"download_url": "s3://reports/pdf"}
    updated = mark_job_completed(job_id=job_id, result_payload=result, job_repo=repo)
    assert updated["status"] == "completed"
    assert updated["result"] == result
    assert updated["completedAt"] is not None
    assert repo.mark_completed_called

def test_mark_job_completed_invalid_transition():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    # Try to mark completed directly from pending without running
    with pytest.raises(HTTPException) as exc_info:
        mark_job_completed(job_id=job_id, result_payload={}, job_repo=repo)
    assert exc_info.value.status_code == 400
    assert "Cannot transition job" in exc_info.value.detail

def test_mark_job_failed_success():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    mark_job_running(job_id=job_id, job_repo=repo)
    
    updated = mark_job_failed(job_id=job_id, error_message="NullPointerException", job_repo=repo)
    assert updated["status"] == "failed"
    assert updated["errorMessage"] == "NullPointerException"
    assert updated["completedAt"] is not None
    assert repo.mark_failed_called

def test_cancel_job_pending():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    updated = cancel_job(job_id=job_id, reason="User clicked cancel", job_repo=repo)
    assert updated["status"] == "cancelled"
    assert updated["errorMessage"] == "User clicked cancel"
    assert repo.update_status_called

def test_cancel_job_completed_rejected():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    mark_job_running(job_id=job_id, job_repo=repo)
    mark_job_completed(job_id=job_id, job_repo=repo)
    
    with pytest.raises(HTTPException) as exc_info:
        cancel_job(job_id=job_id, reason="Cancel", job_repo=repo)
    assert exc_info.value.status_code == 400
    assert "Cannot cancel job" in exc_info.value.detail
