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
