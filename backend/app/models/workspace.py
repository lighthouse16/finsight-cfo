from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.financials import (
    IncomeStatementPeriod,
    BalanceSheetPeriod,
    CashFlowStatementPeriod,
    DebtSchedule,
    ReceivablesAging,
)

class CompanyWorkspace(BaseModel):
    id: str = Field(..., alias="id")
    company_name: str = Field(..., alias="companyName")
    created_at: str = Field(..., alias="createdAt")
    metadata: Dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True

class UploadedFileRecord(BaseModel):
    id: str = Field(..., alias="id")
    workspace_id: str = Field(..., alias="workspaceId")
    record_key: str = Field(..., alias="recordKey")
    file_name: str = Field(..., alias="fileName")
    file_type: str = Field(..., alias="fileType")
    file_size_bytes: int = Field(..., alias="fileSizeBytes")
    status: str
    uploaded_at: str = Field(..., alias="uploadedAt")
    file_path: str = Field(..., alias="filePath")
    storage_mode: str = Field("local_file", alias="storageMode")
    object_key: Optional[str] = Field(None, alias="objectKey")
    object_uri: Optional[str] = Field(None, alias="objectUri")
    provider_status: Optional[str] = Field(None, alias="providerStatus")
    warnings: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True

class FinancialSnapshot(BaseModel):
    id: str = Field(..., alias="id")
    workspace_id: str = Field(..., alias="workspaceId")
    reporting_period: str = Field(..., alias="reportingPeriod")
    currency: str
    income_statement: IncomeStatementPeriod = Field(..., alias="incomeStatement")
    balance_sheet: BalanceSheetPeriod = Field(..., alias="balanceSheet")
    cash_flow_statement: CashFlowStatementPeriod = Field(..., alias="cashFlowStatement")
    debt_schedule: DebtSchedule = Field(..., alias="debtSchedule")
    receivables_aging: Optional[ReceivablesAging] = Field(None, alias="receivablesAging")
    created_at: str = Field(..., alias="createdAt")
    approved: bool = True
    metadata: Dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True

class AnalysisRun(BaseModel):
    id: str = Field(..., alias="id")
    workspace_id: str = Field(..., alias="workspaceId")
    snapshot_id: str = Field(..., alias="snapshotId")
    run_type: str = Field("financial_health", alias="runType")
    status: str
    inputs: Dict = Field(default_factory=dict)
    results: Dict
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    source_trace: Dict = Field(default_factory=dict, alias="sourceTrace")
    logic_version: str = Field("v1", alias="logicVersion")
    created_at: str = Field(..., alias="createdAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")
    duration_ms: Optional[int] = Field(None, alias="durationMs")

    class Config:
        populate_by_name = True

class AuditEvent(BaseModel):
    id: str = Field(..., alias="id")
    workspace_id: str = Field(..., alias="workspaceId")
    event_type: str = Field(..., alias="eventType")
    description: str
    timestamp: str

    class Config:
        populate_by_name = True
