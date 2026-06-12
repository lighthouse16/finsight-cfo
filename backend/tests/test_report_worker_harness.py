import sys
import pytest
from app.services.report_worker_harness import run_report_worker_tick

class DummySettings:
    def __init__(self, enabled=False, max_jobs=1):
        self.REPORT_WORKER_ENABLED = enabled
        self.REPORT_WORKER_MAX_JOBS_PER_TICK = max_jobs

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

    def list_jobs(self, status=None):
        res = list(self.jobs.values())
        if status:
            res = [j for j in res if j["status"] == status]
        return res

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

# 1. Disabled flag does not scan/process jobs.
def test_disabled_flag_does_not_scan_or_process():
    settings = DummySettings(enabled=False)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_repo.create_job_with_status("job_1", "report.generation", "pending")

    res = run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert res["enabled"] is False
    assert res["scanned"] == 0
    assert res["processed"] == 0
    assert res["succeeded"] == 0
    assert res["failed"] == 0
    assert res["jobIds"] == []
    assert res["errors"] == []
    assert res["skippedReason"] == "REPORT_WORKER_ENABLED flag is False"
    assert not report_repo.save_called
    assert job_repo.jobs["job_1"]["status"] == "pending"

# 2. Enabled flag processes one pending report.generation job.
def test_enabled_flag_processes_pending_report_generation():
    settings = DummySettings(enabled=True, max_jobs=1)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    payload = {
        "report_type": "financial_health",
        "report_payload": {"revenue": 100000}
    }
    job_repo.create_job_with_status("job_1", "report.generation", "pending", payload=payload)

    res = run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert res["enabled"] is True
    assert res["scanned"] == 1
    assert res["processed"] == 1
    assert res["succeeded"] == 1
    assert res["failed"] == 0
    assert res["jobIds"] == ["job_1"]
    assert res["errors"] == []

    assert report_repo.save_called
    assert job_repo.jobs["job_1"]["status"] == "completed"

# 3. Respects max jobs per tick.
def test_respects_max_jobs_per_tick():
    settings = DummySettings(enabled=True, max_jobs=2)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    payload = {"report_type": "financial_health"}
    job_repo.create_job_with_status("job_1", "report.generation", "pending", payload=payload)
    job_repo.create_job_with_status("job_2", "report.generation", "pending", payload=payload)
    job_repo.create_job_with_status("job_3", "report.generation", "pending", payload=payload)

    res = run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert res["processed"] == 2
    assert res["succeeded"] == 2
    assert len(res["jobIds"]) == 2
    assert job_repo.jobs["job_1"]["status"] == "completed"
    assert job_repo.jobs["job_2"]["status"] == "completed"
    assert job_repo.jobs["job_3"]["status"] == "pending"

# 4. Skips non-report job types.
def test_skips_non_report_job_types():
    settings = DummySettings(enabled=True, max_jobs=5)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    payload = {"report_type": "financial_health"}
    job_repo.create_job_with_status("job_1", "analysis_run", "pending", payload=payload)
    job_repo.create_job_with_status("job_2", "report.generation", "pending", payload=payload)

    res = run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert res["scanned"] == 1  # Only job_2 is report.generation
    assert res["processed"] == 1
    assert res["jobIds"] == ["job_2"]
    assert job_repo.jobs["job_1"]["status"] == "pending"
    assert job_repo.jobs["job_2"]["status"] == "completed"

# 5 & 12. Skips non-pending, completed, failed, cancelled jobs.
@pytest.mark.parametrize("status", ["running", "completed", "failed", "cancelled"])
def test_skips_non_pending_statuses(status):
    settings = DummySettings(enabled=True, max_jobs=5)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    payload = {"report_type": "financial_health"}
    job_repo.create_job_with_status("job_1", "report.generation", status, payload=payload)

    res = run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert res["scanned"] == 0  # Since status was not pending, it is not scanned/processed
    assert res["processed"] == 0
    assert job_repo.jobs["job_1"]["status"] == status

# 7. Failed job is counted as failed and summary includes error.
def test_failed_job_summarized_properly():
    settings = DummySettings(enabled=True, max_jobs=1)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository(should_fail=True)

    payload = {"report_type": "financial_health"}
    job_repo.create_job_with_status("job_1", "report.generation", "pending", payload=payload)

    res = run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert res["processed"] == 1
    assert res["succeeded"] == 0
    assert res["failed"] == 1
    assert len(res["errors"]) == 1
    assert res["errors"][0]["job_id"] == "job_1"
    assert "Database connection timed out" in res["errors"][0]["error"]
    assert job_repo.jobs["job_1"]["status"] == "failed"

# 8. Does not spawn threads/background tasks.
def test_does_not_spawn_threads_or_processes(monkeypatch):
    import threading
    import multiprocessing
    
    thread_spawned = False
    orig_thread = threading.Thread
    def dummy_thread(*args, **kwargs):
        nonlocal thread_spawned
        thread_spawned = True
        return orig_thread(*args, **kwargs)
    monkeypatch.setattr(threading, "Thread", dummy_thread)

    settings = DummySettings(enabled=True, max_jobs=1)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()
    payload = {"report_type": "financial_health"}
    job_repo.create_job_with_status("job_1", "report.generation", "pending", payload=payload)

    run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert not thread_spawned

# 9. Does not import/use Redis/Celery/RQ.
def test_no_redis_celery_rq_imports():
    for name in ["redis", "celery", "rq"]:
        assert name not in sys.modules

# 10. Does not create DB sessions.
def test_no_db_sessions_created(monkeypatch):
    from app.db import session as db_session_mod
    orig_session_local = db_session_mod.SessionLocal
    
    session_created = False
    def dummy_session():
        nonlocal session_created
        session_created = True
        return orig_session_local()
        
    monkeypatch.setattr(db_session_mod, "SessionLocal", dummy_session)

    settings = DummySettings(enabled=True, max_jobs=1)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()
    payload = {"report_type": "financial_health"}
    job_repo.create_job_with_status("job_1", "report.generation", "pending", payload=payload)

    run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert not session_created

# 11. Does not mutate jobs when disabled.
def test_does_not_mutate_jobs_when_disabled():
    settings = DummySettings(enabled=False)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    job_repo.create_job_with_status("job_1", "report.generation", "pending")

    run_report_worker_tick(settings=settings, job_repository=job_repo, report_repository=report_repo)
    assert job_repo.jobs["job_1"]["status"] == "pending"
    assert len(job_repo.actions) == 0  # No actions (mutations) performed


def test_workspace_scoped_tick_only_processes_matching_workspace():
    settings = DummySettings(enabled=True, max_jobs=5)
    job_repo = MockJobRepository()
    report_repo = MockReportRepository()

    payload = {"report_type": "financial_health"}
    job_repo.create_job_with_status("job_ws_1", "report.generation", "pending", workspace_id="ws_1", payload=payload)
    job_repo.create_job_with_status("job_ws_2", "report.generation", "pending", workspace_id="ws_2", payload=payload)

    res = run_report_worker_tick(
        settings=settings,
        job_repository=job_repo,
        report_repository=report_repo,
        workspace_id="ws_1",
    )

    assert res["enabled"] is True
    assert res["scanned"] == 1
    assert res["processed"] == 1
    assert res["succeeded"] == 1
    assert res["failed"] == 0
    assert res["jobIds"] == ["job_ws_1"]
    assert job_repo.jobs["job_ws_1"]["status"] == "completed"
    assert job_repo.jobs["job_ws_2"]["status"] == "pending"

