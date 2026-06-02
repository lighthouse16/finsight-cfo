import { MarketWatchSnapshot, MarketWatchInsight, TabInsightSet } from '../types'

export function evaluateStressRules(snapshot: MarketWatchSnapshot): TabInsightSet {
  const { company } = snapshot
  const watchSignals: MarketWatchInsight[] = []
  const supportingInsights: MarketWatchInsight[] = []
  let takeaway: MarketWatchInsight | null = null

  const isConnected = (recordId: string): boolean => {
    const record = company.connectedRecords.find(r => r.id === recordId)
    return record ? record.status === 'connected' : false
  }

  // 1. Rate Shock Scenario (Priority)
  const rateShockConnected = isConnected('debt-schedule')
  const rateShockActive = rateShockConnected && company.floatingRateDebtHkd > 0
  let rateShockStatus: 'context_only' | 'requires_company_data' | 'ready_for_model' = 'context_only'
  let rateShockSeverity: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'

  if (!rateShockConnected) {
    rateShockStatus = 'requires_company_data'
    rateShockSeverity = 'Neutral'
  } else if (company.floatingRateDebtHkd > 0) {
    rateShockStatus = 'ready_for_model'
    rateShockSeverity = company.floatingRateDebtHkd >= 5000000 ? 'High' : 'Caution'
  } else {
    rateShockStatus = 'context_only'
    rateShockSeverity = 'Neutral'
  }

  const rateShockInsight: MarketWatchInsight = {
    id: 'stress-rate-shock',
    title: 'Rate Shock (+150 bps)',
    description: 'Review whether operating cashflow has enough buffer under this rate-shock context.',
    severity: rateShockSeverity,
    category: 'stress',
    metricRefs: ['floatingRateDebtHkd'],
    sourceRefs: ['debt-schedule'],
    requiresCompanyData: !rateShockConnected,
    confidence: rateShockConnected ? 'high' : 'low',
    status: rateShockStatus,
  }
  watchSignals.push(rateShockInsight)

  // 2. Receivables Delay Scenario (Priority)
  const receivablesConnected = isConnected('receivables-aging')
  const dsoBenchmark = 45
  const receivablesActive = receivablesConnected && (company.dsoDays > dsoBenchmark || company.workingCapitalGapHkd > 0)
  let receivablesStatus: 'context_only' | 'requires_company_data' | 'ready_for_model' = 'context_only'
  let receivablesSeverity: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'

  if (!receivablesConnected) {
    receivablesStatus = 'requires_company_data'
    receivablesSeverity = 'Neutral'
  } else if (receivablesActive) {
    receivablesStatus = 'ready_for_model'
    receivablesSeverity = 'Caution'
  } else {
    receivablesStatus = 'context_only'
    receivablesSeverity = 'Neutral'
  }

  const receivablesInsight: MarketWatchInsight = {
    id: 'stress-receivables-delay',
    title: 'Receivables Delay (+15 Days)',
    description: 'Review whether credit facilities and collections buffer a 15-day stretch.',
    severity: receivablesSeverity,
    category: 'stress',
    metricRefs: ['dsoDays', 'workingCapitalGapHkd'],
    sourceRefs: ['receivables-aging'],
    requiresCompanyData: !receivablesConnected,
    confidence: receivablesConnected ? 'high' : 'low',
    status: receivablesStatus,
  }
  watchSignals.push(receivablesInsight)

  // 3. FX Scenario (Priority)
  const fxConnected = isConnected('cross-border-payables')
  const fxActive = fxConnected && (company.cnySupplierPayablesPercent >= 30 || company.usdImportCostPercent >= 50)
  let fxStatus: 'context_only' | 'requires_company_data' | 'ready_for_model' = 'context_only'
  let fxSeverity: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'

  if (!fxConnected) {
    fxStatus = 'requires_company_data'
    fxSeverity = 'Neutral'
  } else if (fxActive) {
    fxStatus = 'ready_for_model'
    fxSeverity = 'Caution'
  } else {
    fxStatus = 'context_only'
    fxSeverity = 'Neutral'
  }

  const fxInsight: MarketWatchInsight = {
    id: 'stress-fx-depreciation',
    title: 'CNY Depreciation (-5%)',
    description: 'Review whether import payables conversion margins are protected.',
    severity: fxSeverity,
    category: 'stress',
    metricRefs: ['cnySupplierPayablesPercent', 'usdImportCostPercent'],
    sourceRefs: ['cross-border-payables'],
    requiresCompanyData: !fxConnected,
    confidence: fxConnected ? 'high' : 'low',
    status: fxStatus,
  }
  watchSignals.push(fxInsight)

  // 4. Commodity Shock Scenario (Supporting)
  const commodityConnected = isConnected('supplier-contracts')
  const isCommodityRelevanceHigh = (company.sector || '').toLowerCase().includes('electronics') || (company.sector || '').toLowerCase().includes('manufacturing')
  let commodityStatus: 'context_only' | 'requires_company_data' | 'ready_for_model' = 'context_only'
  let commoditySeverity: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'

  if (!commodityConnected) {
    commodityStatus = 'requires_company_data'
    commoditySeverity = 'Neutral'
  } else if (isCommodityRelevanceHigh) {
    commodityStatus = 'ready_for_model'
    commoditySeverity = 'Caution'
  } else {
    commodityStatus = 'context_only'
    commoditySeverity = 'Neutral'
  }

  const commodityInsight: MarketWatchInsight = {
    id: 'stress-commodity-shock',
    title: 'Commodity Price Squeeze',
    description: 'Review whether supplier/customer terms would absorb this input-cost context.',
    severity: commoditySeverity,
    category: 'stress',
    metricRefs: ['grossMarginPercent'],
    sourceRefs: ['supplier-contracts'],
    requiresCompanyData: !commodityConnected,
    confidence: commodityConnected ? 'high' : 'low',
    status: commodityStatus,
  }
  supportingInsights.push(commodityInsight)

  // 5. Liquidity Squeeze Scenario (Supporting)
  const liquidityConnected = isConnected('bank-transactions')
  const isLiquiditySqueezeActive = liquidityConnected && (company.cashBalanceHkd / (company.monthlyDebtServiceHkd || 1) < 3)
  let liquidityStatus: 'context_only' | 'requires_company_data' | 'ready_for_model' = 'context_only'
  let liquiditySeverity: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'

  if (!liquidityConnected) {
    liquidityStatus = 'requires_company_data'
    liquiditySeverity = 'Neutral'
  } else if (isLiquiditySqueezeActive) {
    liquidityStatus = 'ready_for_model'
    liquiditySeverity = 'High'
  } else {
    liquidityStatus = 'context_only'
    liquiditySeverity = 'Neutral'
  }

  const liquidityInsight: MarketWatchInsight = {
    id: 'stress-liquidity-squeeze',
    title: 'Liquidity Squeeze',
    description: 'Review revolving facility commit status during interbank rate spikes.',
    severity: liquiditySeverity,
    category: 'stress',
    metricRefs: ['cashBalanceHkd', 'monthlyDebtServiceHkd'],
    sourceRefs: ['bank-transactions'],
    requiresCompanyData: !liquidityConnected,
    confidence: liquidityConnected ? 'high' : 'low',
    status: liquidityStatus,
  }
  supportingInsights.push(liquidityInsight)

  // CFO Takeaway
  let takeawayTitle = 'Stress Analysis Complete'
  let takeawayDesc = 'Connect financial records to assess vulnerability to interest rates, receivables delay, and exchange rate shock.'
  let takeawaySev: 'Positive' | 'Neutral' | 'Caution' | 'High' = 'Neutral'

  if (!rateShockConnected || !receivablesConnected || !fxConnected) {
    takeawayTitle = 'Scenario Analysis Pending'
    takeawayDesc = 'Integration with bank accounts and debt schedules is required to model cashflow stress tolerance.'
    takeawaySev = 'Neutral'
  } else if (rateShockActive || receivablesActive || fxActive) {
    takeawayTitle = 'Vulnerability to Volatility Detected'
    const items: string[] = []
    if (rateShockActive) items.push('floating rate debt sensitivity')
    if (receivablesActive) items.push('working capital collection delays')
    if (fxActive) items.push('foreign exchange fluctuations')
    takeawayDesc = `Active exposures identified in: ${items.join(', ')}. Review liquidity buffers to cushion potential shocks.`
    takeawaySev = (rateShockSeverity === 'High' || liquiditySeverity === 'High') ? 'High' : 'Caution'
  } else {
    takeawayTitle = 'Resilient Stress Position'
    takeawayDesc = 'Current cash buffers and operational parameters show resilience against rate shocks and receivables extensions.'
    takeawaySev = 'Positive'
  }

  takeaway = {
    id: 'stress-takeaway',
    title: takeawayTitle,
    description: takeawayDesc,
    severity: takeawaySev,
    category: 'stress',
    metricRefs: ['floatingRateDebtHkd', 'dsoDays', 'cashBalanceHkd'],
    sourceRefs: ['debt-schedule', 'receivables-aging', 'bank-transactions'],
    requiresCompanyData: !rateShockConnected || !receivablesConnected || !fxConnected,
    confidence: (rateShockConnected && receivablesConnected && fxConnected) ? 'high' : 'medium',
    status: (rateShockConnected && receivablesConnected && fxConnected) ? 'ready_for_model' : 'requires_company_data',
  }

  return {
    takeaway,
    watchSignals,
    supportingInsights,
  }
}
