from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.services.audit_service import record_audit_event_best_effort

async def create_report(
    *,
    workspace_id: str,
    payload: Any,
    workspace_repo: Any,
    report_repo: Any,
    audit_repo: Any,
    settings: Any,
) -> Dict[str, Any]:
    """
    Orchestrates report creation, including workspace presence checks, repository saving,
    and best-effort audit logs.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        report = report_repo.save_report(
            workspace_id=workspace_id,
            report_type=payload.reportType,
            title=payload.title,
            report_payload=payload.reportPayload,
            storage_uri=payload.storageUri,
            metadata=payload.metadata,
        )
        await record_audit_event_best_effort(
            audit_repo=audit_repo,
            settings=settings,
            workspace_id=workspace_id,
            action="report.created",
            description=f"Report '{payload.title}' was created."
        )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def get_report(
    *,
    workspace_id: str,
    report_id: str,
    workspace_repo: Any,
    report_repo: Any,
) -> Dict[str, Any]:
    """
    Retrieves report by ID after workspace validation.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    report = report_repo.get_report(report_id)
    if not report or report.get("workspaceId") != workspace_id:
        raise HTTPException(status_code=404, detail="Report not found in this workspace")
    return report

async def list_reports(
    *,
    workspace_id: str,
    report_type: Optional[str] = None,
    workspace_repo: Any,
    report_repo: Any,
) -> List[Dict[str, Any]]:
    """
    Lists all reports in a workspace with optional report type filters.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    reports = report_repo.list_reports(workspace_id, report_type=report_type)
    return reports

async def update_report(
    *,
    workspace_id: str,
    report_id: str,
    payload: Any,
    workspace_repo: Any,
    report_repo: Any,
    audit_repo: Any,
    settings: Any,
) -> Dict[str, Any]:
    """
    Orchestrates report status updates, including verification checks and audits.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    report = report_repo.get_report(report_id)
    if not report or report.get("workspaceId") != workspace_id:
        raise HTTPException(status_code=404, detail="Report not found in this workspace")
    
    try:
        updated = report_repo.update_report_status(
            report_id=report_id,
            status=payload.status,
            storage_uri=payload.storageUri,
            metadata=payload.metadata,
        )
        await record_audit_event_best_effort(
            audit_repo=audit_repo,
            settings=settings,
            workspace_id=workspace_id,
            action="report.updated",
            description=f"Report '{report_id}' was updated to status '{payload.status}'."
        )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def delete_report(
    *,
    workspace_id: str,
    report_id: str,
    workspace_repo: Any,
    report_repo: Any,
    audit_repo: Any,
    settings: Any,
) -> Dict[str, str]:
    """
    Handles report deletion, verifying existence and emitting audit logs.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    report = report_repo.get_report(report_id)
    if not report or report.get("workspaceId") != workspace_id:
        raise HTTPException(status_code=404, detail="Report not found in this workspace")
    
    success = report_repo.delete_report(report_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete report")
    
    await record_audit_event_best_effort(
        audit_repo=audit_repo,
        settings=settings,
        workspace_id=workspace_id,
        action="report.deleted",
        description=f"Report '{report_id}' was deleted."
    )
    return {"status": "success", "message": "Report deleted successfully"}
