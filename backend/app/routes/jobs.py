from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.persistence.interfaces import WorkspaceRepository, JobRepository
from app.routes.workspaces import (
    get_db_session_optional,
    get_workspace_repository_dependency,
)
from app.services.job_service import (
    get_job as service_get_job,
    list_jobs as service_list_jobs,
    create_job as service_create_job,
)
from app.models.job import JobResponse, ReportGenerationJobCreateRequest

router = APIRouter()

def get_job_repository_dependency(
    db_session: Optional[Session] = Depends(get_db_session_optional)
) -> JobRepository:
    from app.core.config import settings
    from app.persistence.factory import get_job_repository
    return get_job_repository(settings, db_session=db_session)

def sanitize_payload(data: Any) -> Any:
    if isinstance(data, (bytes, bytearray)):
        return "<binary data>"
    if isinstance(data, dict):
        return {k: sanitize_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    return data

@router.get("/{workspace_id}/jobs", response_model=List[JobResponse])
async def list_workspace_jobs(
    workspace_id: str,
    status: Optional[str] = None,
    job_type: Optional[str] = Query(None, alias="jobType"),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    job_repo: JobRepository = Depends(get_job_repository_dependency),
):
    """
    List background jobs for a workspace with optional filters.
    """
    # 1. Validate workspace existence
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        # 2. Retrieve jobs
        jobs = service_list_jobs(workspace_id=workspace_id, status=status, job_repo=job_repo)
        
        # 3. Filter by jobType / job_type if provided
        if job_type:
            jobs = [
                j for j in jobs
                if j.get("jobType") == job_type or j.get("job_type") == job_type
            ]
        
        # 4. Sanitize and serialize response
        sanitized_jobs = [sanitize_payload(j) for j in jobs]
        return [JobResponse.from_dict(j) for j in sanitized_jobs]
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Background jobs are not supported under local persistence mode."
        )

@router.get("/{workspace_id}/jobs/{job_id}", response_model=JobResponse)
async def get_workspace_job(
    workspace_id: str,
    job_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    job_repo: JobRepository = Depends(get_job_repository_dependency),
):
    """
    Get one job by ID, validating workspace scope.
    """
    # 1. Validate workspace existence
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        # 2. Retrieve job by ID
        job = service_get_job(job_id=job_id, job_repo=job_repo)
        
        # 3. Validate workspace scope
        job_workspace_id = job.get("workspaceId") or job.get("workspace_id")
        if job_workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Job not found in this workspace")
            
        # 4. Sanitize and serialize response
        return JobResponse.from_dict(sanitize_payload(job))
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Background jobs are not supported under local persistence mode."
        )

@router.post("/{workspace_id}/jobs/report-generation", response_model=JobResponse, status_code=201)
async def create_report_generation_job(
    workspace_id: str,
    req: ReportGenerationJobCreateRequest,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    job_repo: JobRepository = Depends(get_job_repository_dependency),
):
    """
    Creates a pending report.generation job for the workspace.
    """
    # 1. Validate workspace existence
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        # 2. Build payload
        payload = {
            "workspace_id": workspace_id,
            "report_type": req.report_type,
            "report_payload": req.report_payload,
        }
        if req.storage_uri:
            payload["storage_uri"] = req.storage_uri

        # 3. Build metadata
        metadata = {
            "source": "api",
            **(req.metadata or {}),
        }
        if req.max_attempts is not None:
            metadata["max_attempts"] = req.max_attempts

        # 4. Call service layer
        job = service_create_job(
            job_type="report.generation",
            workspace_id=workspace_id,
            payload=payload,
            metadata=metadata,
            job_repo=job_repo,
        )

        # 5. Sanitize and serialize response
        return JobResponse.from_dict(sanitize_payload(job))
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Background jobs are not supported under local persistence mode."
        )

