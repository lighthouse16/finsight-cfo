import { MarketWatchSnapshot, MarketWatchInsight, TabInsightSet } from '../types'

export function evaluateRateRules(snapshot: MarketWatchSnapshot): TabInsightSet {
  const { company, rates } = snapshot
  const watchSignals: MarketWatchInsight[] = []
  const supportingInsights: MarketWatchInsight[] = []
  let takeaway: MarketWatchInsight | null = null

  const hasDebt = typeof company.floatingRateDebtHkd === 'number'

  if (!hasDebt) {
    takeaway = {
      id: 'rates-takeaway-missing',
      title: 'Rate Assessment Pending',
      description: 'Connect corporate debt schedule to assess floating rate exposure.',
      severity: 'Neutral',
      category: 'rates',
      metricRefs: ['floatingRateDebtHkd'],
      sourceRefs: [],
      requiresCompanyData: true,
      confidence: 'low',
    }
  } else if (company.floatingRateDebtHkd > 0) {
    const isLarge = company.floatingRateDebtHkd >= 5000000
    takeaway = {
      id: 'rates-takeaway-exposed',
      title: isLarge ? 'Significant Floating Rate Exposure' : 'Floating Rate Exposure',
      description: `Your HKD ${(company.floatingRateDebtHkd / 1000000).toFixed(1)}M floating-rate facility remains sensitive to HIBOR movement.`,
      severity: isLarge ? 'High' : 'Caution',
      category: 'rates',
      metricRefs: ['floatingRateDebtHkd'],
      sourceRefs: ['debt-schedule'],
      requiresCompanyData: false,
      confidence: 'high',
    }
  } else {
    takeaway = {
      id: 'rates-takeaway-none',
      title: 'No Floating Rate Debt',
      description: 'No floating-rate debt exposure detected in workspace data.',
      severity: 'Neutral',
      category: 'rates',
      metricRefs: ['floatingRateDebtHkd'],
      sourceRefs: ['debt-schedule'],
      requiresCompanyData: false,
      confidence: 'high',
    }
  }

  // Supporting rates insights if rates data is available
  if (rates && typeof rates === 'object') {
    const rObj = rates as { rates?: Array<{ label: string; value: string }> }
    if (rObj.rates && rObj.rates.length > 0) {
      const hibor = rObj.rates.find(r => r.label.includes('1M HIBOR') || r.label.includes('HIBOR'))
      if (hibor) {
        supportingInsights.push({
          id: 'rates-hibor-status',
          title: `Base Reference Rate (${hibor.label})`,
          description: `HIBOR benchmark is currently at ${hibor.value}. Monitor daily reference shifts for debt-service forecasts.`,
          severity: 'Neutral',
          category: 'rates',
          metricRefs: [],
          sourceRefs: ['hkma-rates'],
          requiresCompanyData: false,
          confidence: 'high',
        })
      }
    }
  }

  return {
    takeaway,
    watchSignals,
    supportingInsights,
  }
}
