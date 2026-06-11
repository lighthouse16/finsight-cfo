from typing import Any, Dict
from fastapi import HTTPException
from app.services.job_service import (
    get_job,
    mark_job_running,
    mark_job_completed,
    mark_job_failed,
    _check_no_file_bytes,
)

def process_report_generation_job(
    *,
    job_repository: Any,
    report_repository: Any,
    job_id: str,
) -> Dict[str, Any]:
    """
    Processes exactly one report generation job from the job queue.
    Ensures that only pending report.generation jobs are processed,
    guards against raw file bytes, and coordinates job status transitions.
    """
    # 1. Load the job by ID
    job = get_job(job_id=job_id, job_repo=job_repository)

    # 2. Validate the job type
    job_type = job.get("jobType") or job.get("job_type")
    if job_type != "report.generation":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job type: '{job_type}'. Expected 'report.generation'."
        )

    # 3. Validate processable status (must be pending)
    status = job.get("status")
    if status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot process job {job_id} because it is in state '{status}'."
        )

    # 4. Extract inputs from payload and metadata
    payload = job.get("payload") or {}
    metadata = job.get("metadata") or {}

    # 5. Guard against raw file bytes in payload or metadata
    _check_no_file_bytes(payload)
    _check_no_file_bytes(metadata)

    # 6. Mark job running
    job = mark_job_running(job_id=job_id, job_repo=job_repository)

    workspace_id = job.get("workspaceId") or job.get("workspace_id")
    if not workspace_id:
        err_msg = "Missing workspace_id context in job record."
        mark_job_failed(job_id=job_id, error_message=err_msg, job_repo=job_repository)
        raise HTTPException(status_code=400, detail=err_msg)

    # Extract report generation input from job input_payload
    report_type = payload.get("report_type") or payload.get("reportType")
    if not report_type:
        err_msg = "Missing report_type in job payload."
        mark_job_failed(job_id=job_id, error_message=err_msg, job_repo=job_repository)
        raise HTTPException(status_code=400, detail=err_msg)

    report_payload = payload.get("report_payload")
    if report_payload is None:
        # If payload does not nest report_payload, fall back to treating the payload itself as report_payload
        report_payload = payload

    storage_uri = (
        payload.get("storage_uri")
        or payload.get("storageUri")
        or metadata.get("storage_uri")
        or metadata.get("storageUri")
    )
    title = metadata.get("title") or f"Report {report_type}"

    try:
        # 7. Call report repository to create the report
        report = report_repository.save_report(
            workspace_id=workspace_id,
            report_type=report_type,
            title=title,
            report_payload=report_payload,
            storage_uri=storage_uri,
            metadata=metadata,
        )
    except Exception as e:
        # 9. If report creation fails, mark job failed and re-raise
        mark_job_failed(job_id=job_id, error_message=str(e), job_repo=job_repository)
        raise e

    # 8. Mark job completed with result_payload containing report_id and report metadata
    result_payload = {
        "report_id": report["id"],
        "report_name": report.get("report_name") or report.get("title") or title,
        "storage_uri": report.get("storage_uri") or report.get("storageUri") or storage_uri,
    }
    updated_job = mark_job_completed(
        job_id=job_id,
        result_payload=result_payload,
        job_repo=job_repository,
    )

    # 10. Return a stable dict containing job status and report metadata
    return {
        "status": updated_job["status"],
        "report_id": report["id"],
        "report_name": result_payload["report_name"],
        "storage_uri": result_payload["storage_uri"],
    }
