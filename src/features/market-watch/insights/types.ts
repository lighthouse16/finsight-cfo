export type CompanyDataMode = 'demo_workspace' | 'connected_workspace' | 'fallback'

export type ConnectedRecordStatus = 'connected' | 'pending' | 'missing'

export interface ConnectedRecord {
  id: string
  label: string
  status: ConnectedRecordStatus
  description?: string
}

export interface CompanyContext {
  companyName: string
  sector: string
  geography: string
  dataMode: CompanyDataMode
  revenueTtmHkd: number
  cashBalanceHkd: number
  receivablesHkd: number
  payablesHkd: number
  inventoryHkd: number
  dsoDays: number
  dpoDays: number
  inventoryDays: number
  grossMarginPercent: number
  floatingRateDebtHkd: number
  monthlyDebtServiceHkd: number
  cnySupplierPayablesPercent: number
  usdImportCostPercent: number
  topCustomerConcentrationPercent: number
  workingCapitalGapHkd: number
  connectedRecords: ConnectedRecord[]
}

export interface MarketWatchSnapshot {
  company: CompanyContext
  rates: unknown
  fx: unknown
  sector: unknown
  commodities: unknown
  stress: unknown
  sourceStatus: unknown[]
  refreshedAt: string
}

export interface MarketWatchInsight {
  id: string
  title: string
  description: string
  severity: 'Positive' | 'Neutral' | 'Caution' | 'High'
  category: 'funding' | 'rates' | 'fx' | 'sector' | 'commodities' | 'stress' | 'receivables' | 'liquidity'
  metricRefs: string[]
  sourceRefs: string[]
  requiresCompanyData: boolean
  confidence: 'high' | 'medium' | 'low'
}
