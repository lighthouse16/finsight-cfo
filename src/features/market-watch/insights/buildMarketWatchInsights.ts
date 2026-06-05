import { MarketWatchSnapshot, MarketWatchInsightSet, MarketWatchInsight, ExecutiveSignal } from './types'
import { evaluateFundingRules } from './rules/fundingRules'
import { evaluateRateRules } from './rules/rateRules'
import { evaluateReceivablesRules } from './rules/receivablesRules'
import { evaluateFxRules } from './rules/fxRules'
import { evaluateSectorRules } from './rules/sectorRules'
import { evaluateCommodityRules } from './rules/commodityRules'
import { evaluateStressRules } from './rules/stressRules'

export function buildMarketWatchInsights(snapshot: MarketWatchSnapshot): MarketWatchInsightSet {
  const { company } = snapshot

  // Evaluate each rule group
  const fundingSet = evaluateFundingRules(snapshot)
  const ratesSet = evaluateRateRules(snapshot)
  const receivablesSet = evaluateReceivablesRules(snapshot)
  const fxSet = evaluateFxRules(snapshot)
  const sectorSet = evaluateSectorRules(snapshot)
  const commoditiesSet = evaluateCommodityRules(snapshot)
  const stressSet = evaluateStressRules(snapshot)

  // 1. Gather all insights to extract priorities
  const allInsights: MarketWatchInsight[] = []

  const addInsight = (insight: MarketWatchInsight | null) => {
    if (insight && !allInsights.some(i => i.id === insight.id)) {
      allInsights.push(insight)
    }
  }

  // Take takeaways and watch signals from all categories as priority candidates
  addInsight(fundingSet.takeaway)
  fundingSet.watchSignals.forEach(addInsight)

  addInsight(ratesSet.takeaway)
  ratesSet.watchSignals.forEach(addInsight)

  addInsight(receivablesSet.takeaway)
  receivablesSet.watchSignals.forEach(addInsight)

  addInsight(fxSet.takeaway)
  fxSet.watchSignals.forEach(addInsight)

  addInsight(sectorSet.takeaway)
  sectorSet.watchSignals.forEach(addInsight)

  addInsight(commoditiesSet.takeaway)
  commoditiesSet.watchSignals.forEach(addInsight)

  addInsight(stressSet.takeaway)
  stressSet.watchSignals.forEach(addInsight)

  // Severity sorting order helper
  const severityScore = { High: 0, Caution: 1, Neutral: 2, Positive: 3 }

  // Sort and filter top priorities. Let's keep those that require company data or are Caution/High
  const executivePriorities = allInsights
    .filter(i => !i.id.includes('-missing') && !i.id.includes('-takeaway-none') && !i.id.includes('-takeaway-healthy') && !i.id.includes('-takeaway-stable') && !i.id.includes('-takeaway-services') && !i.id.includes('-takeaway-default'))
    .sort((a, b) => severityScore[a.severity] - severityScore[b.severity])

  // If no negative priorities exist, fallback to all takeaways sorted
  if (executivePriorities.length === 0) {
    const activeTakeaways = [
      fundingSet.takeaway,
      ratesSet.takeaway,
      receivablesSet.takeaway,
      fxSet.takeaway,
      sectorSet.takeaway,
      commoditiesSet.takeaway,
      stressSet.takeaway
    ].filter((i): i is MarketWatchInsight => i !== null)
    executivePriorities.push(...activeTakeaways.sort((a, b) => severityScore[a.severity] - severityScore[b.severity]))
  }

  // 2. Generate Executive Cards
  const executiveCards: ExecutiveSignal[] = []

  // Funding Conditions Card
  const fundingConnected = company.connectedRecords.find(r => r.id === 'bank-transactions')?.status === 'connected'
  let fundingVal = 'Pending'
  let fundingSev: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'
  let fundingDesc = 'Connect bank accounts and debt schedules to assess runway.'
  if (fundingConnected) {
    if (company.dscr !== undefined && company.dscr !== null && company.dscr < 1.0) {
      fundingVal = 'Attention Required'
      fundingSev = 'High'
      fundingDesc = `Operating cashflow coverage is thin. DSCR of ${company.dscr.toFixed(2)}x indicates constrained debt service capacity.`
    } else if (company.cashBalanceHkd && company.monthlyDebtServiceHkd) {
      const ratio = company.cashBalanceHkd / company.monthlyDebtServiceHkd
      if (ratio < 3) {
        fundingVal = 'Tight Buffer'
        fundingSev = 'High'
        fundingDesc = 'Cash covers less than 3 months of debt service obligations.'
      } else if (ratio <= 6) {
        fundingVal = 'Moderate'
        fundingSev = 'Caution'
        fundingDesc = 'Cash runway covers 3 to 6 months of debt service.'
      } else {
        fundingVal = 'Resilient'
        fundingSev = 'Positive'
        fundingDesc = 'Cash reserves cover more than 6 months of debt service.'
      }
    } else {
      fundingVal = 'No Debt Service'
      fundingSev = 'Positive'
      fundingDesc = 'Cash reserves are stable with no active monthly debt payments.'
    }
  }
  executiveCards.push({
    id: 'exec-card-funding',
    label: 'Funding Conditions',
    value: fundingVal,
    status: fundingConnected ? 'Connected' : 'Missing Data',
    severity: fundingSev,
    description: fundingDesc,
    sourceRefs: ['bank-transactions', 'debt-schedule'],
    metricRefs: ['cashBalanceHkd', 'monthlyDebtServiceHkd']
  })

  // Rate Pressure Card
  const ratesConnected = company.connectedRecords.find(r => r.id === 'debt-schedule')?.status === 'connected'
  let ratesVal = 'No Exposure'
  let ratesSev: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'
  let ratesDesc = 'No floating-rate debt exposure detected.'
  if (ratesConnected && company.floatingRateDebtHkd > 0) {
    ratesVal = `HKD ${(company.floatingRateDebtHkd / 1000000).toFixed(1)}M`
    ratesSev = company.floatingRateDebtHkd >= 5000000 ? 'High' : 'Caution'
    ratesDesc = 'Floating-rate facility remains sensitive to HIBOR movement.'
  } else if (!ratesConnected) {
    ratesVal = 'Pending'
    ratesSev = 'Neutral'
    ratesDesc = 'Connect debt schedules to assess benchmark rate sensitivity.'
  }
  executiveCards.push({
    id: 'exec-card-rates',
    label: 'Rate Pressure',
    value: ratesVal,
    status: ratesConnected ? 'Connected' : 'Missing Data',
    severity: ratesSev,
    description: ratesDesc,
    sourceRefs: ['debt-schedule'],
    metricRefs: ['floatingRateDebtHkd']
  })

  // Sector Health / Receivables Card
  const sectorConnected = company.connectedRecords.find(r => r.id === 'receivables-aging')?.status === 'connected'
  let sectorVal = 'Pending'
  let sectorSev: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'
  let sectorDesc = 'Connect aging receivables to compare collection efficiency.'
  if (sectorConnected) {
    const dsoStretch = company.dsoDays > 50
    sectorVal = `${company.dsoDays} Days DSO`
    sectorSev = dsoStretch ? 'Caution' : 'Positive'
    sectorDesc = dsoStretch ? 'Receivables collection cycle exceeds sector average.' : 'Receivables cycle is aligned with benchmark.'
  }
  executiveCards.push({
    id: 'exec-card-sector',
    label: 'Sector Health / Receivables',
    value: sectorVal,
    status: sectorConnected ? 'Connected' : 'Missing Data',
    severity: sectorSev,
    description: sectorDesc,
    sourceRefs: ['receivables-aging'],
    metricRefs: ['dsoDays']
  })

  // FX / GBA Card
  const fxProvider = (snapshot.sourceStatus as Array<{ id?: string; label?: string; status: string }>)?.find(
    s => s.id === 'fx-provider' || s.label?.toLowerCase() === 'fx provider'
  )
  const isFxConnected = fxProvider?.status === 'connected' || 
                        fxProvider?.status === 'seed_data' || 
                        (Array.isArray(snapshot.fx) && snapshot.fx.length > 0)
  
  const fxPairs = snapshot.fx as Array<{ pair: string; rate: string }> | null
  const cnyPair = fxPairs?.find(p => p.pair === 'CNY/HKD')
  const cnyRate = cnyPair ? cnyPair.rate : null

  let fxVal = 'Pending'
  let fxSev: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'
  let fxDesc = 'Connect supplier contracts to map currency sensitivity.'

  if (isFxConnected) {
    fxVal = cnyRate || 'Exposed'
    fxSev = 'Caution'
    const implication = `${company.cnySupplierPayablesPercent}% CNY payables and ${company.usdImportCostPercent}% USD import costs remain exposed.`
    const supplierContractsStatus = company.connectedRecords.find(r => r.id === 'supplier-contracts')?.status
    const supplierContractsMissing = !supplierContractsStatus || supplierContractsStatus === 'missing' || supplierContractsStatus === 'pending'
    
    fxDesc = supplierContractsMissing
      ? `${implication} Supplier contracts pending.`
      : implication
  }

  executiveCards.push({
    id: 'exec-card-fx',
    label: 'FX Exposure',
    value: fxVal,
    status: isFxConnected ? 'Connected' : 'Missing Data',
    severity: fxSev,
    description: fxDesc,
    sourceRefs: ['cross-border-payables'],
    metricRefs: ['cnySupplierPayablesPercent', 'usdImportCostPercent']
  })

  return {
    executivePriorities,
    executiveCards,
    rates: ratesSet,
    fx: fxSet,
    sector: sectorSet,
    commodities: commoditiesSet,
    stress: stressSet,
    generatedAt: new Date().toISOString()
  }
}
