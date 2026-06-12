from typing import Any, Dict, List
from app.services.report_worker_service import process_report_generation_job

def run_report_worker_tick(
    *,
    settings: Any,
    job_repository: Any,
    report_repository: Any,
) -> Dict[str, Any]:
    """
    Executes a single tick of the feature-flagged report worker harness.
    Scans and processes pending report.generation jobs in-process.
    """
    if not getattr(settings, "REPORT_WORKER_ENABLED", False):
        return {
            "enabled": False,
            "processed": 0,
            "skipped_reason": "REPORT_WORKER_ENABLED flag is False",
        }

    # 1. List pending jobs
    try:
        all_pending = job_repository.list_jobs(status="pending")
    except NotImplementedError:
        return {
            "enabled": True,
            "scanned": 0,
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "jobIds": [],
            "errors": [{"error": "NotImplementedError: Background jobs are not supported under local persistence mode."}],
        }

    scanned_jobs = []
    processable_jobs = []

    for job in all_pending:
        jtype = job.get("jobType") or job.get("job_type")
        if jtype != "report.generation":
            continue

        scanned_jobs.append(job)

        # Confirm status is pending
        status = job.get("status")
        if status != "pending":
            continue

        # Check retry bounds
        metadata = job.get("metadata") or {}
        attempts = metadata.get("attempts", 0)
        max_attempts = metadata.get("max_attempts") or metadata.get("maxAttempts") or 3
        if attempts >= max_attempts:
            continue

        processable_jobs.append(job)

    # 2. Process up to REPORT_WORKER_MAX_JOBS_PER_TICK
    max_jobs = getattr(settings, "REPORT_WORKER_MAX_JOBS_PER_TICK", 1)
    jobs_to_process = processable_jobs[:max_jobs]

    succeeded_jobs = []
    failed_jobs = []
    errors_list = []
    processed_job_ids = []

    for job in jobs_to_process:
        job_id = job["id"]
        processed_job_ids.append(job_id)
        try:
            process_report_generation_job(
                job_repository=job_repository,
                report_repository=report_repository,
                job_id=job_id,
            )
            succeeded_jobs.append(job_id)
        except Exception as e:
            failed_jobs.append(job_id)
            errors_list.append({
                "job_id": job_id,
                "error": str(e)
            })

    result = {
        "enabled": True,
        "scanned": len(scanned_jobs),
        "processed": len(processed_job_ids),
        "succeeded": len(succeeded_jobs),
        "failed": len(failed_jobs),
        "jobIds": processed_job_ids,
    }
    if errors_list:
        result["errors"] = errors_list
    else:
        result["errors"] = []

    return result
