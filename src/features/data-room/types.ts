export type DataRoomRecordStatus = 'demo_available' | 'missing' | 'connected' | 'optional'

export type DataRoomRecordCategory =
  | 'Core Financials'
  | 'Debt & Credit'
  | 'Commercial & Trade'
  | 'Risk & Treasury'

export type DataRoomRequirement =
  | 'valuation'
  | 'risk diagnostics'
  | 'stress testing'
  | 'facility structuring'

export type DataRoomActionLabel = 'Upload' | 'Connect' | 'Review' | 'Coming soon'

export interface DataRoomRecord {
  id: string
  name: string
  category: DataRoomRecordCategory
  purpose: string
  status: DataRoomRecordStatus
  requiredFor: DataRoomRequirement[]
  lastUpdated?: string | null
  actionLabel: DataRoomActionLabel
}

export interface DataRoomDependency {
  recordGroup: string
  outputs: string[]
}

export interface DataRoomReadinessSummary {
  totalRequired: number
  connectedRequired: number
  missingRequired: number
  readinessPercentage: number
  dataMode: 'demo_workspace' | 'connected' | 'seed_only'
}

export interface DataRoomResponse {
  records: DataRoomRecord[]
  dependencies: DataRoomDependency[]
  summary: DataRoomReadinessSummary
}

// --- Upload metadata types ---

export type DataRoomUploadedFileStatus =
  | 'received'
  | 'pending_review'
  | 'accepted_metadata'
  | 'unsupported'
  | 'validation_warning'
  | 'unavailable'
  | 'parsed_structured'
  | 'parsed_pdf_text_layer'
  | 'parsed_docx_text'
  | 'ocr_provider_configured'
  | 'ocr_provider_not_configured'

export interface DataRoomUploadedFile {
  fileId: string
  recordKey: string
  fileName: string
  fileType: string
  fileSizeBytes: number | null
  status: DataRoomUploadedFileStatus
  receivedAt: string
  validationMessages: string[]
  source: string
  disclaimer: string
}

export interface DataRoomUploadResponse {
  companyId: string
  companyName: string
  uploadedFile: DataRoomUploadedFile
  warnings: string[]
  disclaimer: string
}

export type ParsedFinancialConfidence = 'high' | 'medium' | 'low' | 'unavailable'

export interface ParsedFinancialRecord {
  fieldKey: string
  label: string
  rawValue: string
  normalizedValue: number | null
  confidence: ParsedFinancialConfidence
  warnings: string[]
}

export interface DataRoomParsePreview {
  recordKey: string
  statementType: string
  parsedRecords: ParsedFinancialRecord[]
  missingExpectedFields: string[]
  unsupportedFields: string[]
  rowCount: number
  warnings: string[]
}

export interface DataRoomParseResponse {
  companyId: string
  companyName: string
  uploadedFile: DataRoomUploadedFile
  preview: DataRoomParsePreview
  disclaimer: string
  warnings: string[]
}

// --- Financial snapshot preview types ---

export interface DataRoomParsedRecordSet {
  recordKey: string
  parsedRecords: ParsedFinancialRecord[]
  warnings: string[]
}

export interface DataRoomSnapshotPreviewInput {
  companyId?: string
  companyName?: string
  currency?: string
  reportingPeriod?: string
  recordSets: DataRoomParsedRecordSet[]
}

export interface DataRoomIntegrityCheck {
  checkName: string
  passed: boolean
  message: string
  details?: Record<string, number | string | boolean | null>
}

export interface DataRoomRatioMetric {
  value: number | null
  warning: string | null
  label: string
}

export type DataRoomRatioKey =
  | 'currentRatio'
  | 'quickRatio'
  | 'interestCoverage'
  | 'dscr'
  | 'debtRatio'
  | 'netDebtToEbitda'
  | 'dso'
  | 'workingCapitalGap'
  | 'expectedCreditLossAr'

export type DataRoomRatioPreview = Partial<Record<DataRoomRatioKey, DataRoomRatioMetric>>

export interface DataRoomSnapshotPreviewResponse {
  companyId: string
  companyName: string
  currency: string
  reportingPeriod: string
  snapshotPreview?: Record<string, unknown> | null
  integrityChecks: DataRoomIntegrityCheck[]
  ratios: DataRoomRatioPreview | null
  missingRequiredStatements: string[]
  warnings: string[]
  disclaimer: string
}


// --- Workspace preview context API types ---

export interface DataRoomWorkspacePreviewContextInput {
  companyId?: string
  companyName: string
  currency: string
  reportingPeriod: string
  snapshotPreview: Record<string, unknown>
  integrityChecks: DataRoomIntegrityCheck[]
  ratios: DataRoomRatioPreview | null
  warnings: string[]
}

export interface DataRoomWorkspacePreviewContextResponse extends DataRoomWorkspacePreviewContextInput {
  workspaceId: string
  companyId: string
  activatedAt: string
  source: 'data_room_snapshot_preview'
  disclaimer: string
}

export interface DataRoomWorkspacePreviewContextStatus {
  workspaceId: string
  active: boolean
  context: DataRoomWorkspacePreviewContextResponse | null
  disclaimer: string
}
