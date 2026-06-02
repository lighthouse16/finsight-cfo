import { MarketWatchSnapshot, MarketWatchInsight, TabInsightSet } from '../types'

export function evaluateFundingRules(snapshot: MarketWatchSnapshot): TabInsightSet {
  const { company } = snapshot
  const watchSignals: MarketWatchInsight[] = []
  const supportingInsights: MarketWatchInsight[] = []
  let takeaway: MarketWatchInsight | null = null

  const hasCash = typeof company.cashBalanceHkd === 'number' && company.cashBalanceHkd > 0
  const hasDebtService = typeof company.monthlyDebtServiceHkd === 'number' && company.monthlyDebtServiceHkd > 0

  if (!hasCash || !hasDebtService) {
    takeaway = {
      id: 'funding-takeaway-missing',
      title: 'Funding Assessment Pending',
      description: 'Connect bank transactions and debt schedule to analyze cash runway relative to monthly debt service.',
      severity: 'Neutral',
      category: 'funding',
      metricRefs: ['cashBalanceHkd', 'monthlyDebtServiceHkd'],
      sourceRefs: [],
      requiresCompanyData: true,
      confidence: 'low',
    }
  } else {
    const ratio = company.cashBalanceHkd / company.monthlyDebtServiceHkd
    
    if (ratio < 3) {
      takeaway = {
        id: 'funding-takeaway-tight',
        title: 'Tight Cash Buffer',
        description: 'Cash buffer is tight relative to monthly debt service requirements. Explore short-term funding options.',
        severity: 'High',
        category: 'funding',
        metricRefs: ['cashBalanceHkd', 'monthlyDebtServiceHkd'],
        sourceRefs: ['bank-transactions', 'debt-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      }
    } else if (ratio >= 3 && ratio <= 6) {
      takeaway = {
        id: 'funding-takeaway-monitor',
        title: 'Moderate Cash Buffer',
        description: 'Cash buffer should be monitored. Monthly debt obligations consume a significant portion of cash reserves.',
        severity: 'Caution',
        category: 'funding',
        metricRefs: ['cashBalanceHkd', 'monthlyDebtServiceHkd'],
        sourceRefs: ['bank-transactions', 'debt-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      }
    } else {
      takeaway = {
        id: 'funding-takeaway-resilient',
        title: 'Resilient Cash Buffer',
        description: 'Cash buffer appears more resilient. Reserves cover more than 6 months of current debt service.',
        severity: 'Positive',
        category: 'funding',
        metricRefs: ['cashBalanceHkd', 'monthlyDebtServiceHkd'],
        sourceRefs: ['bank-transactions', 'debt-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      }
    }

    if (company.workingCapitalGapHkd > 0) {
      watchSignals.push({
        id: 'funding-wc-gap',
        title: 'Working Capital Gap Pressure',
        description: `Working capital gap of HKD ${(company.workingCapitalGapHkd / 1000000).toFixed(1)}M pressures liquid cash runway.`,
        severity: company.workingCapitalGapHkd > 2000000 ? 'Caution' : 'Neutral',
        category: 'funding',
        metricRefs: ['workingCapitalGapHkd'],
        sourceRefs: ['invoices', 'payables-schedule'],
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
