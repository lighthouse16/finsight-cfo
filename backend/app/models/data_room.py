from typing import List, Literal, Optional
from pydantic import BaseModel, Field

DataRoomRecordStatus = Literal["demo_available", "missing", "connected", "optional"]
DataRoomRecordCategory = Literal[
    "Core Financials",
    "Debt & Credit",
    "Commercial & Trade",
    "Risk & Treasury",
]
DataRoomRequirement = Literal[
    "valuation",
    "risk diagnostics",
    "stress testing",
    "facility structuring",
]
DataRoomActionLabel = Literal["Upload", "Connect", "Review", "Coming soon"]


class DataRoomRecord(BaseModel):
    id: str
    name: str
    category: DataRoomRecordCategory
    purpose: str
    status: DataRoomRecordStatus
    requiredFor: List[DataRoomRequirement] = Field(default_factory=list)
    lastUpdated: Optional[str] = None
    actionLabel: DataRoomActionLabel


class DataRoomDependency(BaseModel):
    recordGroup: str
    outputs: List[str] = Field(default_factory=list)


class DataRoomReadinessSummary(BaseModel):
    totalRequired: int
    connectedRequired: int
    missingRequired: int
    readinessPercentage: int
    dataMode: Literal["demo_workspace", "connected", "seed_only"]


class DataRoomResponse(BaseModel):
    records: List[DataRoomRecord]
    dependencies: List[DataRoomDependency]
    summary: DataRoomReadinessSummary


# --- Upload metadata stub types ---

DataRoomUploadedFileStatus = Literal[
    "received",
    "pending_review",
    "accepted_metadata",
    "unsupported_type",
    "validation_warning",
    "unavailable",
]

ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "csv", "xlsx", "xls", "docx"}
ALLOWED_UPLOAD_MIME_PREFIXES = {
    "application/pdf",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DataRoomUploadedFile(BaseModel):
    fileId: str
    recordKey: str
    fileName: str
    fileType: str
    fileSizeBytes: Optional[int] = None
    status: DataRoomUploadedFileStatus
    receivedAt: str
    validationMessages: List[str] = Field(default_factory=list)
    source: str = "metadata_upload_stub"
    disclaimer: str = (
        "This is a metadata-only upload stub. "
        "Company records require production ingestion before analysis updates."
    )


class DataRoomUploadResponse(BaseModel):
    companyId: str = "demo-company"
    companyName: str = "Harbour & Finch Trading Ltd."
    uploadedFile: DataRoomUploadedFile
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Metadata received. Analysis will update after production ingestion is connected."
    )


# --- Structured parsing preview types ---

ParsedFinancialConfidence = Literal["high", "medium", "low", "unavailable"]


class ParsedFinancialRecord(BaseModel):
    fieldKey: str
    label: str
    rawValue: str
    normalizedValue: Optional[float] = None
    confidence: ParsedFinancialConfidence
    warnings: List[str] = Field(default_factory=list)


class DataRoomParsePreview(BaseModel):
    recordKey: str
    statementType: str
    parsedRecords: List[ParsedFinancialRecord] = Field(default_factory=list)
    missingExpectedFields: List[str] = Field(default_factory=list)
    unsupportedFields: List[str] = Field(default_factory=list)
    rowCount: int
    warnings: List[str] = Field(default_factory=list)


class DataRoomParseResponse(BaseModel):
    companyId: str = "demo-company"
    companyName: str = "Harbour & Finch Trading Ltd."
    uploadedFile: DataRoomUploadedFile
    preview: DataRoomParsePreview
    disclaimer: str = (
        "Structured parsing preview only. Analysis was not updated and file was not stored."
    )
    warnings: List[str] = Field(default_factory=list)
