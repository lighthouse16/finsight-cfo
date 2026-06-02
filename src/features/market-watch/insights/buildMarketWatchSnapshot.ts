import { CompanyContext, MarketWatchSnapshot } from './types'
import { defaultCompanyProfile } from './companyProfiles'

export interface BuildSnapshotInput {
  companyContext?: {
    profile: unknown
    dataMode: string
  } | null
  ratesData?: unknown
  fxData?: unknown
  sectorData?: unknown
  commoditiesData?: unknown
  stressData?: unknown
  sourceStatus?: unknown[]
  refreshedAt?: string
}

interface ConnectedRecordInput {
  id?: string
  label?: string
  status?: string
  description?: string
}

interface CompanyProfileInput {
  companyName?: string
  sector?: string
  geography?: string
  revenueTtmHkd?: number
  cashBalanceHkd?: number
  receivablesHkd?: number
  payablesHkd?: number
  inventoryHkd?: number
  dsoDays?: number
  dpoDays?: number
  inventoryDays?: number
  grossMarginPercent?: number
  floatingRateDebtHkd?: number
  monthlyDebtServiceHkd?: number
  cnySupplierPayablesPercent?: number
  usdImportCostPercent?: number
  topCustomerConcentrationPercent?: number
  workingCapitalGapHkd?: number
  connectedRecords?: ConnectedRecordInput[]
}

export function buildMarketWatchSnapshot(input: BuildSnapshotInput): MarketWatchSnapshot {
  let company: CompanyContext = defaultCompanyProfile

  if (input.companyContext && input.companyContext.profile) {
    const p = input.companyContext.profile as CompanyProfileInput
    
    company = {
      companyName: p.companyName || defaultCompanyProfile.companyName,
      sector: p.sector || defaultCompanyProfile.sector,
      geography: p.geography || defaultCompanyProfile.geography,
      dataMode: (input.companyContext.dataMode as 'demo_workspace' | 'connected_workspace' | 'fallback') || defaultCompanyProfile.dataMode,
      revenueTtmHkd: typeof p.revenueTtmHkd === 'number' ? p.revenueTtmHkd : defaultCompanyProfile.revenueTtmHkd,
      cashBalanceHkd: typeof p.cashBalanceHkd === 'number' ? p.cashBalanceHkd : defaultCompanyProfile.cashBalanceHkd,
      receivablesHkd: typeof p.receivablesHkd === 'number' ? p.receivablesHkd : defaultCompanyProfile.receivablesHkd,
      payablesHkd: typeof p.payablesHkd === 'number' ? p.payablesHkd : defaultCompanyProfile.payablesHkd,
      inventoryHkd: typeof p.inventoryHkd === 'number' ? p.inventoryHkd : defaultCompanyProfile.inventoryHkd,
      dsoDays: typeof p.dsoDays === 'number' ? p.dsoDays : defaultCompanyProfile.dsoDays,
      dpoDays: typeof p.dpoDays === 'number' ? p.dpoDays : defaultCompanyProfile.dpoDays,
      inventoryDays: typeof p.inventoryDays === 'number' ? p.inventoryDays : defaultCompanyProfile.inventoryDays,
      grossMarginPercent: typeof p.grossMarginPercent === 'number' ? p.grossMarginPercent : defaultCompanyProfile.grossMarginPercent,
      floatingRateDebtHkd: typeof p.floatingRateDebtHkd === 'number' ? p.floatingRateDebtHkd : defaultCompanyProfile.floatingRateDebtHkd,
      monthlyDebtServiceHkd: typeof p.monthlyDebtServiceHkd === 'number' ? p.monthlyDebtServiceHkd : defaultCompanyProfile.monthlyDebtServiceHkd,
      cnySupplierPayablesPercent: typeof p.cnySupplierPayablesPercent === 'number' ? p.cnySupplierPayablesPercent : defaultCompanyProfile.cnySupplierPayablesPercent,
      usdImportCostPercent: typeof p.usdImportCostPercent === 'number' ? p.usdImportCostPercent : defaultCompanyProfile.usdImportCostPercent,
      topCustomerConcentrationPercent: typeof p.topCustomerConcentrationPercent === 'number' ? p.topCustomerConcentrationPercent : defaultCompanyProfile.topCustomerConcentrationPercent,
      workingCapitalGapHkd: typeof p.workingCapitalGapHkd === 'number' ? p.workingCapitalGapHkd : defaultCompanyProfile.workingCapitalGapHkd,
      connectedRecords: Array.isArray(p.connectedRecords) 
        ? p.connectedRecords.map((r) => ({
            id: r.id || '',
            label: r.label || '',
            status: (r.status as 'connected' | 'pending' | 'missing') || 'missing',
            description: r.description
          }))
        : defaultCompanyProfile.connectedRecords
    }
  }

  return {
    company,
    rates: input.ratesData || null,
    fx: input.fxData || null,
    sector: input.sectorData || null,
    commodities: input.commoditiesData || null,
    stress: input.stressData || null,
    sourceStatus: input.sourceStatus || [],
    refreshedAt: input.refreshedAt || new Date().toISOString()
  }
}
