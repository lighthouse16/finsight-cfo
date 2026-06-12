import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.auth import require_admin, require_write_access, RequestContext
from app.persistence.interfaces import WorkspaceRepository, FileMetadataRepository, AnalysisRunRepository, ReportRepository, AuditEventRepository
from app.services.audit_service import record_audit_event_best_effort
from app.services.report_service import (
    create_report as service_create_report,
    get_report as service_get_report,
    list_reports as service_list_reports,
    update_report as service_update_report,
    delete_report as service_delete_report,
)
from app.services.file_metadata_service import (
    upload_workspace_file as service_upload_workspace_file,
    list_workspace_files as service_list_workspace_files,
    delete_workspace_file as service_delete_workspace_file,
    get_workspace_file_bytes,
    cascade_delete_workspace_files,
)
from app.services.analysis_runtime_service import (
    run_analysis_stage,
    get_latest_analysis_stage,
    list_workspace_runs as service_list_workspace_runs,
    get_workspace_run_latest_generic as service_get_workspace_run_latest_generic,
    get_workspace_run_by_id as service_get_workspace_run_by_id,
)
from app.services.workspace_service import (
    create_workspace as service_create_workspace,
    list_workspaces as service_list_workspaces,
    get_workspace as service_get_workspace,
    delete_workspace as service_delete_workspace,
)

from app.models.workspace import CompanyWorkspace, UploadedFileRecord, FinancialSnapshot, AnalysisRun
from app.models.financials import CompanyFinancialSnapshot
from app.models.data_room import (
    DataRoomParsedRecordSet,
    DataRoomSnapshotPreviewInput,
    ParsedFinancialRecord,
)
from app.storage.workspace_store import WorkspaceStore
from app.storage.file_store import FileStore
from app.services.data_room.snapshot_preview import build_snapshot_preview, REQUIRED_CORE_RECORD_KEYS
from app.services.data_room.structured_parser import parse_csv_bytes, parse_xlsx_bytes
from app.models.errors import raise_insufficient_data_error, raise_missing_workspace_error
from app.services.analysis_run_service import (
    execute_financial_health_run,
    execute_valuation_run,
    execute_advisory_precheck_run,
    execute_credit_score_run,
    execute_stress_test_run,
    execute_facility_structuring_run,
    execute_funding_strategy_run,
    execute_advisory_blueprint_run,
    execute_workflow_run,
)

# Monkeypatch WorkspaceStore.save_analysis_run dynamically to bypass runs.json in database mode
_original_save_analysis_run = WorkspaceStore.save_analysis_run

def _db_safe_save_analysis_run(cls, run):
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        # Do not write to runs.json, just return the run object
        return run
    else:
        return _original_save_analysis_run(run)

WorkspaceStore.save_analysis_run = classmethod(_db_safe_save_analysis_run)


_active_db_session = None

def set_active_db_session(session):
    global _active_db_session
    _active_db_session = session

_original_get_workspace = WorkspaceStore.get_workspace

def _db_safe_get_workspace(cls, workspace_id: str):
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        session = _active_db_session
        if session is None:
            # Fallback to creating a new SessionLocal if no active session is registered (e.g. in concurrent production requests)
            from app.db.session import SessionLocal
            if SessionLocal is not None:
                session = SessionLocal()
                try:
                    from app.db.models import Workspace as DbWorkspace
                    w = session.query(DbWorkspace).filter_by(id=workspace_id).first()
                    if w:
                        return CompanyWorkspace(
                            id=w.id,
                            company_name=w.name,
                            created_at=w.created_at.isoformat(),
                            metadata=w.workspace_metadata or {}
                        )
                finally:
                    session.close()
                return None
        
        if session:
            from app.db.models import Workspace as DbWorkspace
            w = session.query(DbWorkspace).filter_by(id=workspace_id).first()
            if w:
                return CompanyWorkspace(
                    id=w.id,
                    company_name=w.name,
                    created_at=w.created_at.isoformat(),
                    metadata=w.workspace_metadata or {}
                )
        return None
    else:
        return _original_get_workspace(workspace_id)

WorkspaceStore.get_workspace = classmethod(_db_safe_get_workspace)

_original_log_audit_event = WorkspaceStore.log_audit_event
_original_get_audit_events = WorkspaceStore.get_audit_events

def _db_safe_log_audit_event(cls, workspace_id: str, event_type: str, description: str):
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        session = _active_db_session
        close_session = False
        if session is None:
            from app.db.session import SessionLocal
            if SessionLocal is not None:
                session = SessionLocal()
                close_session = True
        
        if session:
            try:
                from app.persistence.database_adapters import DatabaseAuditEventRepository
                repo = DatabaseAuditEventRepository(session)
                res = repo.append_event(
                    workspace_id=workspace_id,
                    event_type=event_type,
                    description=description
                )
                from app.models.workspace import AuditEvent as PydanticAuditEvent
                return PydanticAuditEvent(
                    id=res["id"],
                    workspaceId=res["workspaceId"],
                    eventType=res["eventType"],
                    description=res["description"],
                    timestamp=res["timestamp"]
                )
            finally:
                if close_session:
                    session.close()
        return None
    else:
        return _original_log_audit_event(workspace_id, event_type, description)

def _db_safe_get_audit_events(cls, workspace_id: str):
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        session = _active_db_session
        close_session = False
        if session is None:
            from app.db.session import SessionLocal
            if SessionLocal is not None:
                session = SessionLocal()
                close_session = True
        
        if session:
            try:
                from app.persistence.database_adapters import DatabaseAuditEventRepository
                repo = DatabaseAuditEventRepository(session)
                events = repo.list_events(workspace_id=workspace_id)
                from app.models.workspace import AuditEvent as PydanticAuditEvent
                return [
                    PydanticAuditEvent(
                        id=e["id"],
                        workspaceId=e["workspaceId"],
                        eventType=e["eventType"],
                        description=e["description"],
                        timestamp=e["timestamp"]
                    ) for e in events
                ]
            finally:
                if close_session:
                    session.close()
        return []
    else:
        return _original_get_audit_events(workspace_id)

WorkspaceStore.log_audit_event = classmethod(_db_safe_log_audit_event)
WorkspaceStore.get_audit_events = classmethod(_db_safe_get_audit_events)


router = APIRouter()

def get_db_session_optional():
    """
    Yields a database session only if database persistence mode is active.
    
    Safety features:
    1. Returns None when PERSISTENCE_BACKEND="local", avoiding initialization
       of the SQLAlchemy engine/connection pool or any database connections.
    2. Keeps database sessions strictly scoped to the request lifecycle.
    3. Populates _active_db_session registry for any calculation tasks running in same thread.
    """
    global _active_db_session
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        from app.db.session import get_db_session
        for session in get_db_session():
            _active_db_session = session
            try:
                yield session
            finally:
                _active_db_session = None
    else:
        yield None

def get_workspace_repository_dependency(
    db_session: Optional[Session] = Depends(get_db_session_optional)
) -> WorkspaceRepository:
    from app.core.config import settings
    from app.persistence.factory import get_workspace_repository
    return get_workspace_repository(settings, db_session=db_session)

def get_file_metadata_repository_dependency(
    db_session: Optional[Session] = Depends(get_db_session_optional)
) -> FileMetadataRepository:
    from app.core.config import settings
    from app.persistence.factory import get_file_metadata_repository
    return get_file_metadata_repository(settings, db_session=db_session)

def get_analysis_run_repository_dependency(
    db_session: Optional[Session] = Depends(get_db_session_optional)
) -> AnalysisRunRepository:
    from app.core.config import settings
    from app.persistence.factory import get_analysis_run_repository
    return get_analysis_run_repository(settings, db_session=db_session)

def get_report_repository_dependency(
    db_session: Optional[Session] = Depends(get_db_session_optional)
) -> ReportRepository:
    from app.core.config import settings
    from app.persistence.factory import get_report_repository
    return get_report_repository(settings, db_session=db_session)

def get_audit_event_repository_dependency(
    db_session: Optional[Session] = Depends(get_db_session_optional)
) -> AuditEventRepository:
    from app.core.config import settings
    from app.persistence.factory import get_audit_event_repository
    return get_audit_event_repository(settings, db_session=db_session)

from pydantic import BaseModel, Field
from typing import Dict, Any

class ReportCreate(BaseModel):
    reportType: str = Field(..., alias="reportType")
    title: str
    reportPayload: Optional[Dict[str, Any]] = Field(default=None, alias="reportPayload")
    storageUri: Optional[str] = Field(default=None, alias="storageUri")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True

class ReportStatusUpdate(BaseModel):
    status: str
    storageUri: Optional[str] = Field(default=None, alias="storageUri")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True

class WorkspaceReport(BaseModel):
    id: str
    workspaceId: str = Field(..., alias="workspaceId")
    organizationId: str = Field(..., alias="organizationId")
    reportType: str = Field(..., alias="reportType")
    title: str
    status: str
    reportPayload: Optional[Dict[str, Any]] = Field(default=None, alias="reportPayload")
    storageUri: Optional[str] = Field(default=None, alias="storageUri")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    createdAt: Optional[str] = Field(default=None, alias="createdAt")
    updatedAt: Optional[str] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True

# Analysis runs persistence helper moved to analysis_runtime_service

# Map record keys to display labels
RECORD_KEY_LABELS = {
    "pl-statement": "Profit & Loss Statement (P&L)",
    "balance-sheet": "Balance Sheet",
    "cash-flow": "Cash Flow Statement",
    "debt-schedule": "Debt Amortization Schedule",
    "receivables-aging": "Accounts Receivable (AR) Aging Ledger",
}

@router.post("", response_model=CompanyWorkspace)
async def create_workspace(
    company_name: str = Form(..., alias="companyName"),
    currency: Optional[str] = Form(None),
    reportingPeriod: Optional[str] = Form(None, alias="reportingPeriod"),
    repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
    return await service_create_workspace(
        company_name=company_name,
        currency=currency,
        reporting_period=reportingPeriod,
        workspace_repo=repo,
        audit_repo=audit_repo,
        settings=settings,
    )

@router.get("", response_model=List[CompanyWorkspace])
async def list_workspaces(
    repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
):
    return service_list_workspaces(workspace_repo=repo)

@router.get("/config")
async def get_workspaces_config():
    from app.core.config import settings
    return {
        "app_mode": settings.APP_MODE,
        "allow_demo_fallback": settings.ALLOW_DEMO_FALLBACK
    }

@router.post("/reset-sample")
async def reset_sample_workspace():
    from app.core.config import settings
    # Guard check: disabled in production or if demo fallback is not allowed
    if settings.APP_MODE == "production" or not settings.ALLOW_DEMO_FALLBACK:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "DEMO_HELPER_DISABLED",
                "message": "Sample workspace reset is disabled outside development/demo mode.",
                "source": "system_config"
            }
        )

    workspace_id = "workspace_sample_novus"
    company_name = "Novus Retail Solutions Ltd"
    
    # 1. Clean up existing files and workspace
    FileStore.delete_workspace_files(workspace_id)
    WorkspaceStore.delete_workspace(workspace_id)
    
    # 2. Re-create workspace
    workspace = WorkspaceStore.create_workspace(
        workspace_id,
        company_name,
        metadata={"currency": "HKD", "reportingPeriod": "FY2025"}
    )
    
    # 3. Read all 5 CSV statements from demo_data
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    demo_data_dir = os.path.join(repo_root, "demo_data")
    
    file_mapping = {
        "pl-statement": ("pl.csv", "pl.csv"),
        "balance-sheet": ("bs.csv", "bs.csv"),
        "cash-flow": ("cf.csv", "cf.csv"),
        "debt-schedule": ("debt.csv", "debt.csv"),
        "receivables-aging": ("receivables.csv", "receivables.csv"),
    }
    
    for key, (filename, demo_filename) in file_mapping.items():
        filepath = os.path.join(demo_data_dir, demo_filename)
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=500,
                detail=f"Internal setup error: Required sample data file {demo_filename} is missing from demo_data folder."
            )
        try:
            with open(filepath, "rb") as f:
                content_bytes = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal setup error: Failed to read sample data file {demo_filename}. Error: {str(e)}"
            )
            
        FileStore.save_file(
            workspace_id,
            key,
            filename,
            content_bytes,
            "text/csv"
        )
        
    # 4. Parse files to build snapshot
    file_records = FileStore.list_file_records(workspace_id)
    files_by_key = {r.record_key: r for r in file_records}
    
    parsed_record_sets = []
    for key, file_rec in files_by_key.items():
        file_bytes = FileStore.get_file_content(file_rec.id)
        if not file_bytes:
            continue
        preview = parse_csv_bytes(key, file_bytes)
        if preview and preview.parsedRecords:
            parsed_records_dto = [
                ParsedFinancialRecord(
                    fieldKey=r.fieldKey,
                    label=r.label,
                    rawValue=r.rawValue,
                    normalizedValue=r.normalizedValue,
                    confidence=r.confidence,
                    warnings=r.warnings,
                ) for r in preview.parsedRecords
            ]
            record_set = DataRoomParsedRecordSet(
                recordKey=key,
                parsedRecords=parsed_records_dto,
                warnings=preview.warnings,
            )
            parsed_record_sets.append(record_set)
            
    preview_input = DataRoomSnapshotPreviewInput(
        companyId=workspace_id,
        companyName=company_name,
        currency="HKD",
        reportingPeriod="FY2025",
        recordSets=parsed_record_sets,
    )
    
    preview_res = build_snapshot_preview(preview_input)
    if not preview_res.snapshotPreview:
        raise HTTPException(status_code=500, detail="Failed to build snapshot preview for sample workspace")
        
    snapshot_dto = CompanyFinancialSnapshot.model_validate(preview_res.snapshotPreview)
    snapshot_dto.metadata = {
        "freshness": "workspace-derived",
        "persistent": True,
        "source": "workspace_uploaded_statements",
        "built_at": datetime.now(timezone.utc).isoformat()
    }
    
    snapshot_id = f"snap_{workspace_id}_{int(datetime.now(timezone.utc).timestamp())}"
    snapshot = FinancialSnapshot(
        id=snapshot_id,
        workspaceId=workspace_id,
        reportingPeriod=snapshot_dto.reporting_period,
        currency=snapshot_dto.currency,
        incomeStatement=snapshot_dto.income_statement,
        balanceSheet=snapshot_dto.balance_sheet,
        cashFlowStatement=snapshot_dto.cash_flow_statement,
        debtSchedule=snapshot_dto.debt_schedule,
        receivablesAging=snapshot_dto.receivables_aging,
        createdAt=datetime.now(timezone.utc).isoformat(),
        approved=True,
        metadata=snapshot_dto.metadata,
    )
    WorkspaceStore.save_snapshot(snapshot)
    
    # 5. Run workflow run (which internally runs all core sub-analyses)
    wf_run = await execute_workflow_run(workspace_id, snapshot_id)
    sub_runs = wf_run.results.get("subRunIds", {})
    
    return {
        "status": "success",
        "workspaceId": workspace_id,
        "companyName": company_name,
        "snapshotId": snapshot_id,
        "runs": {
            "financial_health": sub_runs.get("financial_health", ""),
            "valuation": sub_runs.get("valuation", ""),
            "credit_score": sub_runs.get("credit_score", ""),
            "funding_strategy": sub_runs.get("funding_strategy", ""),
            "advisory_blueprint": sub_runs.get("advisory_blueprint", ""),
            "workflow": wf_run.id,
        }
    }


@router.get("/{workspace_id}", response_model=CompanyWorkspace)
async def get_workspace(
    workspace_id: str,
    repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
):
    return service_get_workspace(workspace_id=workspace_id, workspace_repo=repo)

@router.post("/{workspace_id}/files", response_model=UploadedFileRecord)
async def upload_workspace_file(
    workspace_id: str,
    recordKey: str = Form(...),
    file: UploadFile = File(...),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
    if file is None or not (file.filename or ""):
        raise HTTPException(status_code=422, detail="file is required")
    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    
    return await service_upload_workspace_file(
        workspace_id=workspace_id,
        record_key=recordKey,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=content_type,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings,
    )

@router.get("/{workspace_id}/files", response_model=List[UploadedFileRecord])
async def list_workspace_files(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
):
    return await service_list_workspace_files(
        workspace_id=workspace_id,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
        settings=settings,
    )

@router.post("/{workspace_id}/snapshot/build")
async def build_workspace_snapshot(
    workspace_id: str,
    currency: Optional[str] = None,
    reportingPeriod: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # 1. Retrieve file records
    file_records = await service_list_workspace_files(
        workspace_id=workspace_id,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
        settings=settings,
    )
        
    files_by_key = {r.record_key: r for r in file_records}
    
    # 2. Check missing required core statements
    missing_keys = [key for key in REQUIRED_CORE_RECORD_KEYS if key not in files_by_key]
    if missing_keys:
        missing_labels = [RECORD_KEY_LABELS.get(k, k) for k in missing_keys]
        raise_insufficient_data_error(missing_labels)
        
    # 3. Parse each file content
    parsed_record_sets: List[DataRoomParsedRecordSet] = []
    warnings: List[str] = []
    
    for key, file_rec in files_by_key.items():
        file_bytes = get_workspace_file_bytes(
            file_id=file_rec.id,
            file_repo=file_repo,
            settings=settings,
        )
            
        if not file_bytes:
            continue
            
        ext = file_rec.file_name.rsplit(".", 1)[-1].lower() if "." in file_rec.file_name else ""
        if ext == "csv":
            preview = parse_csv_bytes(key, file_bytes)
        elif ext == "xlsx":
            preview = parse_xlsx_bytes(key, file_bytes)
        else:
            # Metadata stub
            preview = None
            
        if preview and preview.parsedRecords:
            parsed_records_dto = [
                ParsedFinancialRecord(
                    fieldKey=r.fieldKey,
                    label=r.label,
                    rawValue=r.rawValue,
                    normalizedValue=r.normalizedValue,
                    confidence=r.confidence,
                    warnings=r.warnings,
                ) for r in preview.parsedRecords
            ]
            record_set = DataRoomParsedRecordSet(
                recordKey=key,
                parsedRecords=parsed_records_dto,
                warnings=preview.warnings,
            )
            parsed_record_sets.append(record_set)
            
    # 4. Invoke build_snapshot_preview logic
    preview_input = DataRoomSnapshotPreviewInput(
        companyId=workspace.id,
        companyName=workspace.company_name,
        currency=currency or "HKD",
        reportingPeriod=reportingPeriod or "FY2025",
        recordSets=parsed_record_sets,
    )
    
    preview_res = build_snapshot_preview(preview_input)
    
    if not preview_res.snapshotPreview:
        missing_labels = [RECORD_KEY_LABELS.get(k, k) for k in preview_res.missingRequiredStatements]
        raise_insufficient_data_error(missing_labels)

    # 5. Persist the snapshot
    snapshot_dto = CompanyFinancialSnapshot.model_validate(preview_res.snapshotPreview)
    
    # Overwrite the temporary metadata with persistent workspace metadata
    snapshot_dto.metadata = {
        "freshness": "workspace-derived",
        "persistent": True,
        "source": "workspace_uploaded_statements",
        "built_at": datetime.now(timezone.utc).isoformat()
    }
    
    snapshot_id = f"snap_{workspace_id}_{int(datetime.now(timezone.utc).timestamp())}"
    snapshot = FinancialSnapshot(
        id=snapshot_id,
        workspaceId=workspace_id,
        reportingPeriod=snapshot_dto.reporting_period,
        currency=snapshot_dto.currency,
        incomeStatement=snapshot_dto.income_statement,
        balanceSheet=snapshot_dto.balance_sheet,
        cashFlowStatement=snapshot_dto.cash_flow_statement,
        debtSchedule=snapshot_dto.debt_schedule,
        receivablesAging=snapshot_dto.receivables_aging,
        createdAt=datetime.now(timezone.utc).isoformat(),
        approved=True,
        metadata=snapshot_dto.metadata,
    )
    
    WorkspaceStore.save_snapshot(snapshot)
    
    return {
        "status": "success",
        "snapshot": snapshot.model_dump(by_alias=True)
    }

@router.get("/{workspace_id}/snapshot/active")
async def get_active_workspace_snapshot(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    snapshot = WorkspaceStore.get_active_snapshot(workspace_id)
    if not snapshot:
        raise_missing_workspace_error("ACTIVE_SNAPSHOT_NOT_FOUND")
        
    return {
        "status": "success",
        "snapshot": snapshot.model_dump(by_alias=True)
    }

@router.delete("/{workspace_id}/files/{file_id}")
async def delete_workspace_file(
    workspace_id: str,
    file_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
    context: RequestContext = Depends(require_write_access),
):
    return await service_delete_workspace_file(
        workspace_id=workspace_id,
        file_id=file_id,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings,
    )

@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
    context: RequestContext = Depends(require_admin),
):
    return await service_delete_workspace(
        workspace_id=workspace_id,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/financial-health/run", response_model=AnalysisRun)
async def trigger_financial_health_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_financial_health_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/financial-health/latest", response_model=AnalysisRun)
def get_latest_financial_health_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="financial_health",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/valuation/run", response_model=AnalysisRun)
async def trigger_valuation_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_valuation_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/valuation/latest", response_model=AnalysisRun)
def get_latest_valuation_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="valuation",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/advisory-precheck/run", response_model=AnalysisRun)
async def trigger_advisory_precheck_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_advisory_precheck_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/advisory-precheck/latest", response_model=AnalysisRun)
def get_latest_advisory_precheck_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="advisory_precheck",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/credit-score/run", response_model=AnalysisRun)
async def trigger_credit_score_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_credit_score_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/credit-score/latest", response_model=AnalysisRun)
def get_latest_credit_score_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="credit_score",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/stress-test/run", response_model=AnalysisRun)
async def trigger_stress_test_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_stress_test_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/stress-test/latest", response_model=AnalysisRun)
def get_latest_stress_test_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="stress_test",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/facility-structuring/run", response_model=AnalysisRun)
async def trigger_facility_structuring_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_facility_structuring_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/facility-structuring/latest", response_model=AnalysisRun)
def get_latest_facility_structuring_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="facility_structuring",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/funding-strategy/run", response_model=AnalysisRun)
async def trigger_funding_strategy_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_funding_strategy_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/funding-strategy/latest", response_model=AnalysisRun)
def get_latest_funding_strategy_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="funding_strategy",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/advisory-blueprint/run", response_model=AnalysisRun)
async def trigger_advisory_blueprint_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_advisory_blueprint_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/advisory-blueprint/latest", response_model=AnalysisRun)
def get_latest_advisory_blueprint_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="advisory_blueprint",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/analysis/workflow/run", response_model=AnalysisRun)
async def trigger_workflow_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return await run_analysis_stage(
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        execution_fn=execute_workflow_run,
        run_repo=run_repo,
        workspace_repo=workspace_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/analysis/workflow/latest", response_model=AnalysisRun)
def get_latest_workflow_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return get_latest_analysis_stage(
        workspace_id=workspace_id,
        run_type="workflow_run",
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/runs", response_model=List[AnalysisRun])
def list_workspace_runs(
    workspace_id: str,
    type: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return service_list_workspace_runs(
        workspace_id=workspace_id,
        run_type=type,
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/runs/latest", response_model=AnalysisRun)
def get_latest_workspace_run_generic(
    workspace_id: str,
    type: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return service_get_workspace_run_latest_generic(
        workspace_id=workspace_id,
        run_type=type,
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/runs/{run_id}", response_model=AnalysisRun)
def get_workspace_run_by_id(
    workspace_id: str,
    run_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    return service_get_workspace_run_by_id(
        workspace_id=workspace_id,
        run_id=run_id,
        workspace_repo=workspace_repo,
        run_repo=run_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/reports", response_model=WorkspaceReport)
async def create_workspace_report(
    workspace_id: str,
    payload: ReportCreate,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
    return await service_create_report(
        workspace_id=workspace_id,
        payload=payload,
        workspace_repo=workspace_repo,
        report_repo=report_repo,
        audit_repo=audit_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/reports/{report_id}", response_model=WorkspaceReport)
async def get_workspace_report_by_id(
    workspace_id: str,
    report_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
):
    return await service_get_report(
        workspace_id=workspace_id,
        report_id=report_id,
        workspace_repo=workspace_repo,
        report_repo=report_repo,
    )


@router.get("/{workspace_id}/reports", response_model=List[WorkspaceReport])
async def list_workspace_reports(
    workspace_id: str,
    type: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
):
    return await service_list_reports(
        workspace_id=workspace_id,
        report_type=type,
        workspace_repo=workspace_repo,
        report_repo=report_repo,
    )


@router.patch("/{workspace_id}/reports/{report_id}", response_model=WorkspaceReport)
async def update_workspace_report_status(
    workspace_id: str,
    report_id: str,
    payload: ReportStatusUpdate,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
    return await service_update_report(
        workspace_id=workspace_id,
        report_id=report_id,
        payload=payload,
        workspace_repo=workspace_repo,
        report_repo=report_repo,
        audit_repo=audit_repo,
        settings=settings,
    )


@router.delete("/{workspace_id}/reports/{report_id}")
async def delete_workspace_report(
    workspace_id: str,
    report_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
    context: RequestContext = Depends(require_write_access),
):
    return await service_delete_report(
        workspace_id=workspace_id,
        report_id=report_id,
        workspace_repo=workspace_repo,
        report_repo=report_repo,
        audit_repo=audit_repo,
        settings=settings,
    )


# New Data Room persistent endpoints
@router.post("/{workspace_id}/data-room/files", response_model=UploadedFileRecord)
async def upload_workspace_data_room_file(
    workspace_id: str,
    recordKey: str = Form(...),
    file: UploadFile = File(...),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
    """Alias for POST /{workspace_id}/files, providing a clear production-like endpoint."""
    if file is None or not (file.filename or ""):
        raise HTTPException(status_code=422, detail="file is required")
    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    
    return await service_upload_workspace_file(
        workspace_id=workspace_id,
        record_key=recordKey,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=content_type,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
        audit_repo=audit_repo,
        settings=settings,
    )


@router.get("/{workspace_id}/data-room/files", response_model=List[UploadedFileRecord])
async def list_workspace_data_room_files(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
):
    """Alias for GET /{workspace_id}/files."""
    return await service_list_workspace_files(
        workspace_id=workspace_id,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
        settings=settings,
    )


@router.post("/{workspace_id}/data-room/snapshot")
async def post_workspace_data_room_snapshot(
    workspace_id: str,
    currency: Optional[str] = None,
    reportingPeriod: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
):
    """Compile and save snapshot. Alias of POST /{workspace_id}/snapshot/build."""
    return await build_workspace_snapshot(
        workspace_id=workspace_id,
        currency=currency,
        reportingPeriod=reportingPeriod,
        workspace_repo=workspace_repo,
        file_repo=file_repo,
    )


@router.get("/{workspace_id}/financial-analysis")
async def get_workspace_financial_analysis(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
):
    """Run/retrieve financial analysis from active workspace snapshot instead of demo seed."""
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    snapshot = WorkspaceStore.get_active_snapshot(workspace_id)
    if not snapshot:
        raise HTTPException(
            status_code=404, 
            detail={
                "code": "ACTIVE_SNAPSHOT_NOT_FOUND",
                "message": "No active financial snapshot found for this workspace. Please compile a snapshot first.",
                "source": "workspace_data"
            }
        )
        
    from app.services.analysis_run_service import execute_financial_health_run
    
    try:
        run = execute_financial_health_run(workspace_id, snapshot.id)
        res = dict(run.results)
        
        # Override metadata to show persistent active context
        if "snapshot" in res:
            meta = dict(res["snapshot"].get("metadata") or {})
            meta.update({
                "mode": "production",
                "source": "workspace_persistent_snapshot",
                "persistent": True,
            })
            res["snapshot"]["metadata"] = meta
            
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ANALYSIS_FAILED",
                "message": f"Failed to execute financial health analysis run: {str(exc)}",
            }
        )
