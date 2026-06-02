import { MarketWatchSnapshot, MarketWatchInsight, TabInsightSet } from '../types'

export function evaluateFxRules(snapshot: MarketWatchSnapshot): TabInsightSet {
  const { company, fx } = snapshot
  const watchSignals: MarketWatchInsight[] = []
  const supportingInsights: MarketWatchInsight[] = []
  let takeaway: MarketWatchInsight | null = null

  const hasCnyPercent = typeof company.cnySupplierPayablesPercent === 'number'
  const hasUsdPercent = typeof company.usdImportCostPercent === 'number'

  // Extract source provider if Frankfurter is active
  const sourceRefs: string[] = []
  if (fx && typeof fx === 'object') {
    const fxObj = fx as { fxSource?: { label: string } }
    if (fxObj.fxSource && fxObj.fxSource.label) {
      sourceRefs.push(fxObj.fxSource.label)
    }
  }

  if (!hasCnyPercent || !hasUsdPercent) {
    takeaway = {
      id: 'fx-takeaway-missing',
      title: 'FX Exposure Evaluation Pending',
      description: 'Connect payables and supplier components pricing data to map cross-border currency exposures.',
      severity: 'Neutral',
      category: 'fx',
      metricRefs: ['cnySupplierPayablesPercent', 'usdImportCostPercent'],
      sourceRefs: [],
      requiresCompanyData: true,
      confidence: 'low',
    }
  } else {
    const isCnyHigh = company.cnySupplierPayablesPercent >= 30
    const isUsdHigh = company.usdImportCostPercent >= 50

    if (isCnyHigh || isUsdHigh) {
      const descriptions: string[] = []
      if (isCnyHigh) {
        descriptions.push(`${company.cnySupplierPayablesPercent}% CNY supplier payables are exposed to cross-border exchange rate shifts.`)
      }
      if (isUsdHigh) {
        descriptions.push(`${company.usdImportCostPercent}% of raw component imports are USD-invoiced, creating cost-base sensitivity to USD fluctuations.`)
      }
      takeaway = {
        id: 'fx-takeaway-exposed',
        title: 'Material Foreign Exchange Exposure',
        description: descriptions.join(' '),
        severity: 'Caution',
        category: 'fx',
        metricRefs: ['cnySupplierPayablesPercent', 'usdImportCostPercent'],
        sourceRefs: sourceRefs.length > 0 ? sourceRefs : ['payables-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      }
    } else {
      takeaway = {
        id: 'fx-takeaway-limited',
        title: 'Limited Currency Exposure',
        description: 'FX exposure appears limited based on current corporate payables and sourcing records.',
        severity: 'Neutral',
        category: 'fx',
        metricRefs: ['cnySupplierPayablesPercent', 'usdImportCostPercent'],
        sourceRefs: sourceRefs.length > 0 ? sourceRefs : ['payables-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      }
    }

    if (isCnyHigh) {
      watchSignals.push({
        id: 'fx-cny-watch',
        title: 'CNY Supplier Exposure',
        description: 'CNY supplier exposure should be monitored. Review pricing terms under cross-border contracts.',
        severity: 'Caution',
        category: 'fx',
        metricRefs: ['cnySupplierPayablesPercent'],
        sourceRefs: ['payables-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      })
    }

    if (isUsdHigh) {
      watchSignals.push({
        id: 'fx-usd-watch',
        title: 'USD Import Cost Base',
        description: 'USD-linked import costs are material. Monitor volatility in components landed-cost margin.',
        severity: 'Caution',
        category: 'fx',
        metricRefs: ['usdImportCostPercent'],
        sourceRefs: ['supplier-contracts'],
        requiresCompanyData: false,
        confidence: 'high',
      })
    }
  }

  return {
    takeaway,
    watchSignals,
    supportingInsights,
  }
}
