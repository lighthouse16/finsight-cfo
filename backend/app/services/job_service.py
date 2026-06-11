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
