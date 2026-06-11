import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.models.workspace import CompanyWorkspace
from app.services.audit_service import record_audit_event_best_effort
from app.services.file_metadata_service import cascade_delete_workspace_files

async def create_workspace(
    *,
    company_name: str,
    currency: Optional[str],
    reporting_period: Optional[str],
    workspace_repo: Any,
    audit_repo: Any,
    settings: Any,
) -> CompanyWorkspace:
    """
    Creates a new workspace, records the action in audit logs, and returns the workspace details.
    """
    company_name = company_name.strip()
    if not company_name:
        raise HTTPException(status_code=422, detail="CompanyName is required")
    workspace_id = f"workspace_{uuid.uuid4().hex[:12]}"
    metadata = {}
    if currency:
        metadata["currency"] = currency
    if reporting_period:
        metadata["reportingPeriod"] = reporting_period
    workspace = workspace_repo.create_workspace(workspace_id, company_name, metadata=metadata)
    await record_audit_event_best_effort(
        audit_repo=audit_repo,
        settings=settings,
        workspace_id=workspace_id,
        action="workspace.created",
        description=f"Workspace '{company_name}' was created."
    )
    return workspace

def list_workspaces(
    *,
    workspace_repo: Any,
) -> List[CompanyWorkspace]:
    """
    Lists all available workspaces.
    """
    return workspace_repo.list_workspaces()

def get_workspace(
    *,
    workspace_id: str,
    workspace_repo: Any,
) -> CompanyWorkspace:
    """
    Retrieves a workspace by its ID. Raises 404 if not found.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

async def delete_workspace(
    *,
    workspace_id: str,
    workspace_repo: Any,
    file_repo: Any,
    audit_repo: Any,
    settings: Any,
) -> Dict[str, str]:
    """
    Deletes a workspace, cascade-deletes physical files, and logs the deletion.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # 1. Cascade physical files and file metadata
    cascade_delete_workspace_files(
        workspace_id=workspace_id,
        file_repo=file_repo,
        settings=settings,
    )
    
    # 2. Cascade workspace metadata, snapshots, runs, audits
    success = workspace_repo.delete_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete workspace")
        
    await record_audit_event_best_effort(
        audit_repo=audit_repo,
        settings=settings,
        workspace_id=workspace_id,
        action="workspace.deleted",
        description=f"Workspace '{workspace_id}' was deleted."
    )
        
    return {"status": "success", "message": f"Workspace {workspace_id} deleted successfully"}
