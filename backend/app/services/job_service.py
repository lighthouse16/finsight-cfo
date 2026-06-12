from typing import Any, Dict, List, Optional
from fastapi import HTTPException

def _check_no_file_bytes(data: Any) -> None:
    """
    Recursively checks if the payload contains raw bytes or bytearray to prevent storing file bytes.
    """
    if isinstance(data, (bytes, bytearray)):
        raise HTTPException(status_code=422, detail="File bytes are not allowed in job payloads")
    if isinstance(data, dict):
        for v in data.values():
            _check_no_file_bytes(v)
    elif isinstance(data, list):
        for item in data:
            _check_no_file_bytes(item)

def create_job(
    *,
    job_type: str,
    workspace_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Creates/registers a new background job with a 'pending' status.
    Ensures that raw file bytes are not included in the payload.
    """
    if payload:
        _check_no_file_bytes(payload)
    if metadata:
        _check_no_file_bytes(metadata)

    return job_repo.create_job(
        job_type=job_type,
        workspace_id=workspace_id,
        payload=payload,
        metadata=metadata,
    )

def get_job(
    *,
    job_id: str,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Retrieves job execution details by ID. Raises 404 if not found.
    """
    job = job_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def list_jobs(
    *,
    workspace_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    job_repo: Any,
) -> List[Dict[str, Any]]:
    """
    Lists background jobs with optional workspace/status filtering.
    """
    return job_repo.list_jobs(
        workspace_id=workspace_id,
        status=status,
        limit=limit,
    )

def mark_job_running(
    *,
    job_id: str,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Transitions job status from 'pending' to 'running'.
    Raises 400 if the job is not in 'pending' status.
    """
    job = get_job(job_id=job_id, job_repo=job_repo)
    current_status = job.get("status")
    if current_status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition job {job_id} from state '{current_status}' to 'running'."
        )
    return job_repo.mark_job_started(job_id)

def mark_job_completed(
    *,
    job_id: str,
    result_payload: Optional[Dict[str, Any]] = None,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Transitions job status from 'running' to 'completed'.
    Raises 400 if the job is not in 'running' status.
    """
    if result_payload:
        _check_no_file_bytes(result_payload)

    job = get_job(job_id=job_id, job_repo=job_repo)
    current_status = job.get("status")
    if current_status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition job {job_id} from state '{current_status}' to 'completed'."
        )
    return job_repo.mark_job_completed(job_id, result_payload=result_payload)

def mark_job_failed(
    *,
    job_id: str,
    error_message: str,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Transitions job status from 'running' to 'failed'.
    Raises 400 if the job is not in 'running' status.
    """
    job = get_job(job_id=job_id, job_repo=job_repo)
    current_status = job.get("status")
    if current_status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition job {job_id} from state '{current_status}' to 'failed'."
        )
    return job_repo.mark_job_failed(job_id, error_message=error_message)

def cancel_job(
    *,
    job_id: str,
    reason: str,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Transitions job status from 'pending' or 'running' to 'cancelled'.
    Raises 400 if the job is already completed or failed.
    """
    job = get_job(job_id=job_id, job_repo=job_repo)
    current_status = job.get("status")
    if current_status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job {job_id} because it is already in state '{current_status}'."
        )
    return job_repo.update_job_status(
        job_id=job_id,
        status="cancelled",
        error_message=reason,
    )

def increment_job_attempt(
    *,
    job_id: str,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Increments the attempt count for the job.
    Updates the database column if DatabaseJobRepository,
    and updates/stores the count in metadata['attempts'] so it's returned in route responses.
    """
    job = get_job(job_id=job_id, job_repo=job_repo)
    metadata = job.get("metadata") or {}
    current_attempts = metadata.get("attempts", 0)
    new_attempts = current_attempts + 1
    metadata["attempts"] = new_attempts

    if hasattr(job_repo, "session") and job_repo.session:
        from app.db.models import Job as DbJob
        db_job = job_repo.session.query(DbJob).filter_by(id=job_id).first()
        if db_job:
            db_job.attempts = new_attempts
            db_job.job_metadata = {**(db_job.job_metadata or {}), **metadata}
            job_repo.session.commit()
            return job_repo._to_dict(db_job)

    return job_repo.update_job_status(job_id=job_id, status=job.get("status"), metadata=metadata)

def can_retry_job(job: Dict[str, Any]) -> bool:
    """
    Returns True if a failed job is eligible to be retried.
    Completed, running, and cancelled jobs are never retryable.
    Failed jobs are retryable only if attempts < max_attempts.
    """
    status = job.get("status")
    if status != "failed":
        return False
        
    metadata = job.get("metadata") or {}
    attempts = metadata.get("attempts", 0)
    max_attempts = metadata.get("max_attempts") or metadata.get("maxAttempts") or 3
    return attempts < max_attempts

def mark_job_progress(
    *,
    job_id: str,
    percent: int,
    stage: str,
    message: str,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Updates progress information (percent, stage, message) inside the job metadata.
    Enforces progress bounds and guards against raw file bytes.
    """
    _check_no_file_bytes(percent)
    _check_no_file_bytes(stage)
    _check_no_file_bytes(message)

    if not isinstance(percent, int) or not (0 <= percent <= 100):
        raise HTTPException(status_code=400, detail="Progress percent must be an integer between 0 and 100.")
    if not isinstance(stage, str):
        raise HTTPException(status_code=400, detail="Progress stage must be a string.")
    if not isinstance(message, str):
        raise HTTPException(status_code=400, detail="Progress message must be a string.")


    job = get_job(job_id=job_id, job_repo=job_repo)
    metadata = job.get("metadata") or {}
    
    metadata["progress"] = {
        "percent": percent,
        "stage": stage,
        "message": message,
    }

    if hasattr(job_repo, "session") and job_repo.session:
        from app.db.models import Job as DbJob
        db_job = job_repo.session.query(DbJob).filter_by(id=job_id).first()
        if db_job:
            db_job.job_metadata = {**(db_job.job_metadata or {}), **metadata}
            job_repo.session.commit()
            return job_repo._to_dict(db_job)

    return job_repo.update_job_status(job_id=job_id, status=job.get("status"), metadata=metadata)

def prepare_job_retry(
    *,
    job_id: str,
    job_repo: Any,
) -> Dict[str, Any]:
    """
    Moves a retry-eligible failed job back to the 'pending' state.
    """
    job = get_job(job_id=job_id, job_repo=job_repo)
    if not can_retry_job(job):
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not eligible for retry.")

    if hasattr(job_repo, "session") and job_repo.session:
        from app.db.models import Job as DbJob
        db_job = job_repo.session.query(DbJob).filter_by(id=job_id).first()
        if db_job:
            db_job.status = "pending"
            db_job.result_payload = {}
            db_job.error_log = None
            job_repo.session.commit()
            return job_repo._to_dict(db_job)

    return job_repo.update_job_status(
        job_id=job_id,
        status="pending",
        result_payload={},
        error_message="",
    )

