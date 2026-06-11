import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

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

router = APIRouter()

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
    workspace = WorkspaceStore.create_workspace(workspace_id, company_name, metadata=metadata)
    return workspace

@router.get("", response_model=List[CompanyWorkspace])
async def list_workspaces():
    return WorkspaceStore.list_workspaces()

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
async def get_workspace(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@router.post("/{workspace_id}/files", response_model=UploadedFileRecord)
async def upload_workspace_file(
    workspace_id: str,
    recordKey: str = Form(...),
    file: UploadFile = File(...),
):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    record_key = recordKey.strip()
    if not record_key:
        raise HTTPException(status_code=422, detail="recordKey is required")
    if file is None or not (file.filename or ""):
        raise HTTPException(status_code=422, detail="file is required")

    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    
    record = FileStore.save_file(
        workspace_id=workspace_id,
        record_key=record_key,
        file_name=file.filename,
        file_bytes=file_bytes,
        content_type=content_type,
    )
    return record

@router.get("/{workspace_id}/files", response_model=List[UploadedFileRecord])
async def list_workspace_files(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return FileStore.list_file_records(workspace_id)

@router.post("/{workspace_id}/snapshot/build")
async def build_workspace_snapshot(
    workspace_id: str,
    currency: Optional[str] = None,
    reportingPeriod: Optional[str] = None,
):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # 1. Retrieve file records
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
async def delete_workspace_file(workspace_id: str, file_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    file_record = FileStore.get_file_record(file_id)
    if not file_record or file_record.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="File not found in this workspace")
        
    success = FileStore.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete file")
        
    return {"status": "success", "message": f"File {file_id} deleted successfully"}

@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # 1. Cascade physical files and file metadata
    FileStore.delete_workspace_files(workspace_id)
    
    # 2. Cascade workspace metadata, snapshots, runs, audits
    success = WorkspaceStore.delete_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete workspace")
        
    return {"status": "success", "message": f"Workspace {workspace_id} deleted successfully"}


@router.post("/{workspace_id}/analysis/financial-health/run", response_model=AnalysisRun)
def trigger_financial_health_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return execute_financial_health_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/financial-health/latest", response_model=AnalysisRun)
def get_latest_financial_health_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "financial_health")
    if not run:
        raise HTTPException(status_code=404, detail="No financial health runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/valuation/run", response_model=AnalysisRun)
def trigger_valuation_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return execute_valuation_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/valuation/latest", response_model=AnalysisRun)
def get_latest_valuation_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "valuation")
    if not run:
        raise HTTPException(status_code=404, detail="No valuation runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/advisory-precheck/run", response_model=AnalysisRun)
def trigger_advisory_precheck_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return execute_advisory_precheck_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/advisory-precheck/latest", response_model=AnalysisRun)
def get_latest_advisory_precheck_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "advisory_precheck")
    if not run:
        raise HTTPException(status_code=404, detail="No advisory precheck runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/credit-score/run", response_model=AnalysisRun)
def trigger_credit_score_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return execute_credit_score_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/credit-score/latest", response_model=AnalysisRun)
def get_latest_credit_score_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "credit_score")
    if not run:
        raise HTTPException(status_code=404, detail="No credit score runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/stress-test/run", response_model=AnalysisRun)
def trigger_stress_test_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return execute_stress_test_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/stress-test/latest", response_model=AnalysisRun)
def get_latest_stress_test_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "stress_test")
    if not run:
        raise HTTPException(status_code=404, detail="No stress test runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/facility-structuring/run", response_model=AnalysisRun)
def trigger_facility_structuring_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return execute_facility_structuring_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/facility-structuring/latest", response_model=AnalysisRun)
def get_latest_facility_structuring_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "facility_structuring")
    if not run:
        raise HTTPException(status_code=404, detail="No facility structuring runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/funding-strategy/run", response_model=AnalysisRun)
async def trigger_funding_strategy_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return await execute_funding_strategy_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/funding-strategy/latest", response_model=AnalysisRun)
def get_latest_funding_strategy_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "funding_strategy")
    if not run:
        raise HTTPException(status_code=404, detail="No funding strategy runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/advisory-blueprint/run", response_model=AnalysisRun)
def trigger_advisory_blueprint_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return execute_advisory_blueprint_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/advisory-blueprint/latest", response_model=AnalysisRun)
def get_latest_advisory_blueprint_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "advisory_blueprint")
    if not run:
        raise HTTPException(status_code=404, detail="No advisory blueprint runs found for this workspace")
    return run


@router.post("/{workspace_id}/analysis/workflow/run", response_model=AnalysisRun)
async def trigger_workflow_run(workspace_id: str, snapshot_id: Optional[str] = None):
    return await execute_workflow_run(workspace_id, snapshot_id)


@router.get("/{workspace_id}/analysis/workflow/latest", response_model=AnalysisRun)
def get_latest_workflow_run(workspace_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, "workflow_run")
    if not run:
        raise HTTPException(status_code=404, detail="No workflow runs found for this workspace")
    return run


@router.get("/{workspace_id}/runs", response_model=List[AnalysisRun])
def list_workspace_runs(workspace_id: str, type: Optional[str] = None):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceStore.list_runs(workspace_id, run_type=type)


@router.get("/{workspace_id}/runs/latest", response_model=AnalysisRun)
def get_latest_workspace_run_generic(workspace_id: str, type: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_latest_run_by_type(workspace_id, type)
    if not run:
        raise HTTPException(status_code=404, detail=f"No run found of type {type} for this workspace")
    return run


@router.get("/{workspace_id}/runs/{run_id}", response_model=AnalysisRun)
def get_workspace_run_by_id(workspace_id: str, run_id: str):
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = WorkspaceStore.get_run(run_id)
    if not run or run.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Run not found in this workspace")
    return run
