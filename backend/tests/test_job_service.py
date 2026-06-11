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
    increment_job_attempt,
    can_retry_job,
    mark_job_progress,
    prepare_job_retry,
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

    def update_job_status(self, job_id, status, result_payload=None, error_message=None, metadata=None):
        self.update_status_called = True
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            if error_message is not None:
                self.jobs[job_id]["errorMessage"] = error_message
            if result_payload is not None:
                self.jobs[job_id]["result"] = result_payload
            if metadata is not None:
                self.jobs[job_id]["metadata"] = {**(self.jobs[job_id].get("metadata") or {}), **metadata}
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

def test_increment_job_attempt():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    # Check default attempts
    assert created.get("metadata", {}).get("attempts", 0) == 0
    
    # First increment
    updated_1 = increment_job_attempt(job_id=job_id, job_repo=repo)
    assert updated_1.get("metadata", {}).get("attempts") == 1
    
    # Second increment
    updated_2 = increment_job_attempt(job_id=job_id, job_repo=repo)
    assert updated_2.get("metadata", {}).get("attempts") == 2

def test_can_retry_job_eligibility():
    # Helper to build a job dictionary
    def make_mock_job(status, attempts, max_attempts=None):
        meta = {"attempts": attempts}
        if max_attempts is not None:
            meta["max_attempts"] = max_attempts
        return {
            "status": status,
            "metadata": meta
        }

    # 1. Completed jobs are never retried
    assert not can_retry_job(make_mock_job("completed", 1, 3))
    
    # 2. Cancelled jobs are never retried
    assert not can_retry_job(make_mock_job("cancelled", 1, 3))
    
    # 3. Running jobs are never retried
    assert not can_retry_job(make_mock_job("running", 1, 3))
    
    # 4. Pending jobs are never retried
    assert not can_retry_job(make_mock_job("pending", 0, 3))

    # 5. Failed jobs with attempts < max_attempts are retryable
    assert can_retry_job(make_mock_job("failed", 1, 3)) # attempts=1, max=3 -> True
    assert can_retry_job(make_mock_job("failed", 2, 3)) # attempts=2, max=3 -> True
    
    # Default max_attempts is 3
    assert can_retry_job(make_mock_job("failed", 2))    # attempts=2, max=3 -> True

    # 6. Failed jobs with attempts >= max_attempts are not retryable
    assert not can_retry_job(make_mock_job("failed", 3, 3)) # attempts=3, max=3 -> False
    assert not can_retry_job(make_mock_job("failed", 4, 3)) # attempts=4, max=3 -> False
    assert not can_retry_job(make_mock_job("failed", 3))    # attempts=3, max=3 -> False

def test_mark_job_progress_success():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    updated = mark_job_progress(
        job_id=job_id,
        percent=45,
        stage="generating_excel",
        message="Creating columns",
        job_repo=repo
    )
    
    progress = updated.get("metadata", {}).get("progress", {})
    assert progress["percent"] == 45
    assert progress["stage"] == "generating_excel"
    assert progress["message"] == "Creating columns"

def test_mark_job_progress_invalid_bounds():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    # Negative percent
    with pytest.raises(HTTPException) as exc:
        mark_job_progress(job_id=job_id, percent=-10, stage="stage", message="msg", job_repo=repo)
    assert exc.value.status_code == 400
    assert "integer between 0 and 100" in exc.value.detail
    
    # > 100 percent
    with pytest.raises(HTTPException) as exc:
        mark_job_progress(job_id=job_id, percent=101, stage="stage", message="msg", job_repo=repo)
    assert exc.value.status_code == 400
    assert "integer between 0 and 100" in exc.value.detail

    # Invalid stage type
    with pytest.raises(HTTPException) as exc:
        mark_job_progress(job_id=job_id, percent=50, stage=123, message="msg", job_repo=repo)
    assert exc.value.status_code == 400
    assert "Progress stage must be a string" in exc.value.detail

    # Invalid message type
    with pytest.raises(HTTPException) as exc:
        mark_job_progress(job_id=job_id, percent=50, stage="stage", message=None, job_repo=repo)
    assert exc.value.status_code == 400
    assert "Progress message must be a string" in exc.value.detail

def test_mark_job_progress_rejects_raw_bytes():
    repo = MockJobRepository()
    created = repo.create_job("report", "ws_1")
    job_id = created["id"]
    
    with pytest.raises(HTTPException) as exc:
        mark_job_progress(job_id=job_id, percent=50, stage="stage", message=b"binary content", job_repo=repo)
    assert exc.value.status_code == 422
    assert "File bytes are not allowed" in exc.value.detail

def test_prepare_job_retry_success():
    repo = MockJobRepository()
    # Create a failed job with attempts < max_attempts
    created = repo.create_job("report", "ws_1", metadata={"attempts": 1, "max_attempts": 3})
    job_id = created["id"]
    repo.update_job_status(job_id=job_id, status="failed", error_message="Internal Error")
    
    # Verify retry preparation
    updated = prepare_job_retry(job_id=job_id, job_repo=repo)
    assert updated["status"] == "pending"
    assert updated["errorMessage"] == ""
    assert updated["result"] == {}

def test_prepare_job_retry_failed_ineligible():
    repo = MockJobRepository()
    # Create a completed job (ineligible)
    created1 = repo.create_job("report", "ws_1", metadata={"attempts": 1, "max_attempts": 3})
    job_id1 = created1["id"]
    repo.update_job_status(job_id=job_id1, status="completed")
    
    with pytest.raises(HTTPException) as exc:
        prepare_job_retry(job_id=job_id1, job_repo=repo)
    assert exc.value.status_code == 400
    assert "not eligible for retry" in exc.value.detail

    # Create a failed job with max attempts reached
    created2 = repo.create_job("report", "ws_1", metadata={"attempts": 3, "max_attempts": 3})
    job_id2 = created2["id"]
    repo.update_job_status(job_id=job_id2, status="failed")
    
    with pytest.raises(HTTPException) as exc:
        prepare_job_retry(job_id=job_id2, job_repo=repo)
    assert exc.value.status_code == 400
    assert "not eligible for retry" in exc.value.detail

