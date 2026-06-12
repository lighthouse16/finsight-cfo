from typing import Any, Dict, Optional
from app.services.job_service import (
    create_job,
    mark_job_running,
    mark_job_completed,
    mark_job_failed,
)

def generate_report_with_job(
    *,
    job_repository: Any,
    report_repository: Any,
    workspace_id: str,
    organization_id: Optional[str],
    report_type: str,
    report_payload: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    storage_uri: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Synchronously orchestrates report generation wrapping it with a job execution record.
    1. Creates the job in 'pending' state.
    2. Marks the job as 'running'.
    3. Persists the report in the report repository.
    4. Marks the job as 'completed' (or 'failed' if an error occurs).
    """
    job_metadata = {**(metadata or {})}
    if organization_id:
        job_metadata["organization_id"] = organization_id

    # 1. Create the job in 'pending' state.
    job = create_job(
        job_type="report.generation",
        workspace_id=workspace_id,
        payload=report_payload,
        metadata=job_metadata,
        job_repo=job_repository,
    )

    # 2. Mark the job as 'running'.
    job = mark_job_running(job_id=job["id"], job_repo=job_repository)

    try:
        # 3. Create/persist the report.
        title = (metadata or {}).get("title") or f"Report {report_type}"
        report = report_repository.save_report(
            workspace_id=workspace_id,
            report_type=report_type,
            title=title,
            report_payload=report_payload,
            storage_uri=storage_uri,
            metadata=metadata,
        )
    except Exception as e:
        # 4a. Mark the job as 'failed' and re-raise.
        mark_job_failed(job_id=job["id"], error_message=str(e), job_repo=job_repository)
        raise e

    # 4b. Mark the job as 'completed' upon success.
    result_payload = {
        "report_id": report["id"],
        "report_name": report.get("report_name") or report.get("title"),
        "storage_uri": report.get("storage_uri"),
    }
    updated_job = mark_job_completed(
        job_id=job["id"],
        result_payload=result_payload,
        job_repo=job_repository,
    )

    return {
        "job": updated_job,
        "report": report,
    }
