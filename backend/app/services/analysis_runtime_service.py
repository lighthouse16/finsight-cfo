import inspect
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.models.workspace import AnalysisRun
from app.storage.workspace_store import WorkspaceStore
from app.services.audit_service import record_audit_event_best_effort

def _db_save_run(run_dto: Any, run_repo: Any, workspace_id: str, settings: Any) -> dict:
    meta = {
        "run_id": run_dto.id,
        "snapshot_id": run_dto.snapshot_id,
        "source_trace": run_dto.source_trace,
        "logic_version": run_dto.logic_version,
        "duration_ms": run_dto.duration_ms
    }
    summary = {
        "warnings": run_dto.warnings,
        "errors": run_dto.errors
    }
    res = run_repo.save_run(
        workspace_id=workspace_id,
        run_type=run_dto.run_type,
        status=run_dto.status,
        input_payload=run_dto.inputs,
        output_payload=run_dto.results,
        summary=summary,
        error_message="; ".join(run_dto.errors) if run_dto.errors else None,
        metadata=meta
    )
    try:
        from app.persistence.factory import get_audit_event_repository
        import asyncio
        audit_repo = get_audit_event_repository(settings, db_session=run_repo.session)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(record_audit_event_best_effort(
                audit_repo=audit_repo,
                settings=settings,
                workspace_id=workspace_id,
                action="analysis.run.created",
                description=f"Analysis run of type '{run_dto.run_type}' was saved."
            ))
        else:
            asyncio.run(record_audit_event_best_effort(
                audit_repo=audit_repo,
                settings=settings,
                workspace_id=workspace_id,
                action="analysis.run.created",
                description=f"Analysis run of type '{run_dto.run_type}' was saved."
            ))
    except Exception:
        pass
    return res

async def run_analysis_stage(
    *,
    workspace_id: str,
    snapshot_id: Optional[str],
    execution_fn: Any,
    run_repo: Any,
    workspace_repo: Any,
    settings: Any,
) -> Any:
    """
    Validates workspace and executes an analysis run.
    Saves the run metadata to the DB repository (in DB mode) or returns the run object directly (in local mode).
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if inspect.iscoroutinefunction(execution_fn):
        run_dto = await execution_fn(workspace_id, snapshot_id)
    else:
        run_dto = execution_fn(workspace_id, snapshot_id)
        
    if settings.normalized_persistence_backend == "database":
        res_dict = _db_save_run(run_dto, run_repo, workspace_id, settings)
        return AnalysisRun.model_validate(res_dict)
    else:
        return run_dto

def get_latest_analysis_stage(
    *,
    workspace_id: str,
    run_type: str,
    workspace_repo: Any,
    run_repo: Any,
    settings: Any,
) -> Any:
    """
    Fetches the latest analysis run of a specific stage for a workspace.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    display_type = "workflow" if run_type == "workflow_run" else run_type.replace("_", " ")
    error_msg = f"No {display_type} runs found for this workspace"
    
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == run_type), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail=error_msg)
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, run_type)
        if not run:
            raise HTTPException(status_code=404, detail=error_msg)
        return run

def list_workspace_runs(
    *,
    workspace_id: str,
    run_type: Optional[str] = None,
    workspace_repo: Any,
    run_repo: Any,
    settings: Any,
) -> List[Any]:
    """
    Lists all runs for a workspace, optionally filtered by run type.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        if run_type:
            runs = [r for r in runs if r.get("runType") == run_type]
        return [AnalysisRun.model_validate(r) for r in runs]
    else:
        return WorkspaceStore.list_runs(workspace_id, run_type=run_type)

def get_workspace_run_latest_generic(
    *,
    workspace_id: str,
    run_type: str,
    workspace_repo: Any,
    run_repo: Any,
    settings: Any,
) -> Any:
    """
    Fetches the latest analysis run of a specific type (generic endpoint).
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    error_msg = f"No run found of type {run_type} for this workspace"
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == run_type), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail=error_msg)
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, run_type)
        if not run:
            raise HTTPException(status_code=404, detail=error_msg)
        return run

def get_workspace_run_by_id(
    *,
    workspace_id: str,
    run_id: str,
    workspace_repo: Any,
    run_repo: Any,
    settings: Any,
) -> Any:
    """
    Fetches a specific analysis run by ID.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if settings.normalized_persistence_backend == "database":
        run = run_repo.get_run(run_id)
        if not run or run.get("workspaceId") != workspace_id:
            raise HTTPException(status_code=404, detail="Run not found in this workspace")
        return AnalysisRun.model_validate(run)
    else:
        run = WorkspaceStore.get_run(run_id)
        if not run or run.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Run not found in this workspace")
        return run
