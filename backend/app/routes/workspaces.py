import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.persistence.interfaces import WorkspaceRepository, FileMetadataRepository, AnalysisRunRepository, ReportRepository, AuditEventRepository
from app.services.audit_service import record_audit_event_best_effort

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

def _db_save_run(run_dto: AnalysisRun, run_repo: AnalysisRunRepository, workspace_id: str) -> dict:
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
        from app.core.config import settings
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
    company_name = company_name.strip()
    if not company_name:
        raise HTTPException(status_code=422, detail="CompanyName is required")
    workspace_id = f"workspace_{uuid.uuid4().hex[:12]}"
    metadata = {}
    if currency:
        metadata["currency"] = currency
    if reportingPeriod:
        metadata["reportingPeriod"] = reportingPeriod
    workspace = repo.create_workspace(workspace_id, company_name, metadata=metadata)
    await record_audit_event_best_effort(
        audit_repo=audit_repo,
        settings=settings,
        workspace_id=workspace_id,
        action="workspace.created",
        description=f"Workspace '{company_name}' was created."
    )
    return workspace

@router.get("", response_model=List[CompanyWorkspace])
async def list_workspaces(
    repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
):
    return repo.list_workspaces()

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
    workspace = repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@router.post("/{workspace_id}/files", response_model=UploadedFileRecord)
async def upload_workspace_file(
    workspace_id: str,
    recordKey: str = Form(...),
    file: UploadFile = File(...),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    record_key = recordKey.strip()
    if not record_key:
        raise HTTPException(status_code=422, detail="recordKey is required")
    if file is None or not (file.filename or ""):
        raise HTTPException(status_code=422, detail="file is required")

    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        import os
        from app.storage.workspace_store import STORAGE_DIR
        upload_root = os.path.join(STORAGE_DIR, "uploads")
        workspace_dir = os.path.join(upload_root, workspace_id)
        os.makedirs(workspace_dir, exist_ok=True)
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
        dest_filename = f"{record_key}.{ext}"
        file_path = os.path.join(workspace_dir, dest_filename)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        res_dict = file_repo.save_file_record(
            workspace_id=workspace_id,
            record_key=record_key,
            filename=file.filename,
            content_type=content_type,
            file_size_bytes=len(file_bytes),
            storage_uri=file_path,
        )
        await record_audit_event_best_effort(
            audit_repo=audit_repo,
            settings=settings,
            workspace_id=workspace_id,
            action="file.uploaded",
            description=f"File '{file.filename}' uploaded to key '{record_key}'."
        )
        return UploadedFileRecord.model_validate(res_dict)
    else:
        record = FileStore.save_file(
            workspace_id=workspace_id,
            record_key=record_key,
            file_name=file.filename,
            file_bytes=file_bytes,
            content_type=content_type,
        )
        return record

@router.get("/{workspace_id}/files", response_model=List[UploadedFileRecord])
async def list_workspace_files(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        records = file_repo.list_file_records(workspace_id)
        return [UploadedFileRecord.model_validate(r) for r in records]
    else:
        return FileStore.list_file_records(workspace_id)

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
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        db_records = file_repo.list_file_records(workspace_id)
        file_records = [UploadedFileRecord.model_validate(r) for r in db_records]
    else:
        file_records = FileStore.list_file_records(workspace_id)
        
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
        if settings.normalized_persistence_backend == "database":
            import os
            file_rec_dict = file_repo.get_file_record(file_rec.id)
            file_bytes = None
            if file_rec_dict and file_rec_dict.get("filePath"):
                file_path = file_rec_dict["filePath"]
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                    except Exception:
                        pass
        else:
            file_bytes = FileStore.get_file_content(file_rec.id)
            
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
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        import os
        file_record = file_repo.get_file_record(file_id)
        if not file_record or file_record.get("workspaceId") != workspace_id:
            raise HTTPException(status_code=404, detail="File not found in this workspace")
            
        file_path = file_record.get("filePath")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
        success = file_repo.delete_file_record(file_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        await record_audit_event_best_effort(
            audit_repo=audit_repo,
            settings=settings,
            workspace_id=workspace_id,
            action="file.deleted",
            description=f"File '{file_id}' deleted."
        )
    else:
        file_record = FileStore.get_file_record(file_id)
        if not file_record or file_record.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="File not found in this workspace")
            
        success = FileStore.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")
            
    return {"status": "success", "message": f"File {file_id} deleted successfully"}

@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    file_repo: FileMetadataRepository = Depends(get_file_metadata_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # 1. Cascade physical files and file metadata
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        import os
        import shutil
        db_records = file_repo.list_file_records(workspace_id)
        for r in db_records:
            fid = r.get("id")
            fpath = r.get("filePath")
            if fpath and os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass
            file_repo.delete_file_record(fid)
            
        ws_dir = os.path.join(FileStore._upload_root, workspace_id)
        if os.path.exists(ws_dir):
            try:
                shutil.rmtree(ws_dir)
            except Exception:
                pass
    else:
        FileStore.delete_workspace_files(workspace_id)
    
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


@router.post("/{workspace_id}/analysis/financial-health/run", response_model=AnalysisRun)
def trigger_financial_health_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = execute_financial_health_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return execute_financial_health_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/financial-health/latest", response_model=AnalysisRun)
def get_latest_financial_health_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "financial_health"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No financial health runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "financial_health")
        if not run:
            raise HTTPException(status_code=404, detail="No financial health runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/valuation/run", response_model=AnalysisRun)
def trigger_valuation_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = execute_valuation_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return execute_valuation_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/valuation/latest", response_model=AnalysisRun)
def get_latest_valuation_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "valuation"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No valuation runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "valuation")
        if not run:
            raise HTTPException(status_code=404, detail="No valuation runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/advisory-precheck/run", response_model=AnalysisRun)
def trigger_advisory_precheck_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = execute_advisory_precheck_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return execute_advisory_precheck_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/advisory-precheck/latest", response_model=AnalysisRun)
def get_latest_advisory_precheck_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "advisory_precheck"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No advisory precheck runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "advisory_precheck")
        if not run:
            raise HTTPException(status_code=404, detail="No advisory precheck runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/credit-score/run", response_model=AnalysisRun)
def trigger_credit_score_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = execute_credit_score_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return execute_credit_score_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/credit-score/latest", response_model=AnalysisRun)
def get_latest_credit_score_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "credit_score"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No credit score runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "credit_score")
        if not run:
            raise HTTPException(status_code=404, detail="No credit score runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/stress-test/run", response_model=AnalysisRun)
def trigger_stress_test_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = execute_stress_test_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return execute_stress_test_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/stress-test/latest", response_model=AnalysisRun)
def get_latest_stress_test_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "stress_test"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No stress test runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "stress_test")
        if not run:
            raise HTTPException(status_code=404, detail="No stress test runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/facility-structuring/run", response_model=AnalysisRun)
def trigger_facility_structuring_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = execute_facility_structuring_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return execute_facility_structuring_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/facility-structuring/latest", response_model=AnalysisRun)
def get_latest_facility_structuring_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "facility_structuring"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No facility structuring runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "facility_structuring")
        if not run:
            raise HTTPException(status_code=404, detail="No facility structuring runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/funding-strategy/run", response_model=AnalysisRun)
async def trigger_funding_strategy_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = await execute_funding_strategy_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return await execute_funding_strategy_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/funding-strategy/latest", response_model=AnalysisRun)
def get_latest_funding_strategy_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "funding_strategy"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No funding strategy runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "funding_strategy")
        if not run:
            raise HTTPException(status_code=404, detail="No funding strategy runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/advisory-blueprint/run", response_model=AnalysisRun)
def trigger_advisory_blueprint_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = execute_advisory_blueprint_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return execute_advisory_blueprint_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/advisory-blueprint/latest", response_model=AnalysisRun)
def get_latest_advisory_blueprint_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "advisory_blueprint"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No advisory blueprint runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "advisory_blueprint")
        if not run:
            raise HTTPException(status_code=404, detail="No advisory blueprint runs found for this workspace")
        return run


@router.post("/{workspace_id}/analysis/workflow/run", response_model=AnalysisRun)
async def trigger_workflow_run(
    workspace_id: str,
    snapshot_id: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        run_dto = await execute_workflow_run(workspace_id, snapshot_id)
        res_dict = _db_save_run(run_dto, run_repo, workspace_id)
        return AnalysisRun.model_validate(res_dict)
    else:
        return await execute_workflow_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/workflow/latest", response_model=AnalysisRun)
def get_latest_workflow_run(
    workspace_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == "workflow_run"), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail="No workflow runs found for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, "workflow_run")
        if not run:
            raise HTTPException(status_code=404, detail="No workflow runs found for this workspace")
        return run


@router.get("/{workspace_id}/runs", response_model=List[AnalysisRun])
def list_workspace_runs(
    workspace_id: str,
    type: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        if type:
            runs = [r for r in runs if r.get("runType") == type]
        return [AnalysisRun.model_validate(r) for r in runs]
    else:
        return WorkspaceStore.list_runs(workspace_id, run_type=type)


@router.get("/{workspace_id}/runs/latest", response_model=AnalysisRun)
def get_latest_workspace_run_generic(
    workspace_id: str,
    type: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
    if settings.normalized_persistence_backend == "database":
        runs = run_repo.list_runs(workspace_id)
        latest_run = next((r for r in runs if r.get("runType") == type), None)
        if not latest_run:
            raise HTTPException(status_code=404, detail=f"No run found of type {type} for this workspace")
        return AnalysisRun.model_validate(latest_run)
    else:
        run = WorkspaceStore.get_latest_run_by_type(workspace_id, type)
        if not run:
            raise HTTPException(status_code=404, detail=f"No run found of type {type} for this workspace")
        return run


@router.get("/{workspace_id}/runs/{run_id}", response_model=AnalysisRun)
def get_workspace_run_by_id(
    workspace_id: str,
    run_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    run_repo: AnalysisRunRepository = Depends(get_analysis_run_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    from app.core.config import settings
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


@router.post("/{workspace_id}/reports", response_model=WorkspaceReport)
async def create_workspace_report(
    workspace_id: str,
    payload: ReportCreate,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/reports/{report_id}", response_model=WorkspaceReport)
async def get_workspace_report_by_id(
    workspace_id: str,
    report_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    report = report_repo.get_report(report_id)
    if not report or report.get("workspaceId") != workspace_id:
        raise HTTPException(status_code=404, detail="Report not found in this workspace")
    return report


@router.get("/{workspace_id}/reports", response_model=List[WorkspaceReport])
async def list_workspace_reports(
    workspace_id: str,
    type: Optional[str] = None,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
):
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    reports = report_repo.list_reports(workspace_id, report_type=type)
    return reports


@router.patch("/{workspace_id}/reports/{report_id}", response_model=WorkspaceReport)
async def update_workspace_report_status(
    workspace_id: str,
    report_id: str,
    payload: ReportStatusUpdate,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workspace_id}/reports/{report_id}")
async def delete_workspace_report(
    workspace_id: str,
    report_id: str,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
    audit_repo: AuditEventRepository = Depends(get_audit_event_repository_dependency),
):
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
