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
  | 'unsupported_type'
  | 'validation_warning'
  | 'unavailable'

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
