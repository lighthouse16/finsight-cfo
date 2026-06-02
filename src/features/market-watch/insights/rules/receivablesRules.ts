import { MarketWatchSnapshot, MarketWatchInsight, TabInsightSet } from '../types'

export function evaluateReceivablesRules(snapshot: MarketWatchSnapshot): TabInsightSet {
  const { company } = snapshot
  const watchSignals: MarketWatchInsight[] = []
  const supportingInsights: MarketWatchInsight[] = []
  let takeaway: MarketWatchInsight | null = null

  let benchmarkDso = 45
  if (snapshot.sector && typeof snapshot.sector === 'object') {
    const sObj = snapshot.sector as { benchmarks?: Array<{ id: string; value: number }> }
    const dsoBench = sObj.benchmarks?.find(b => b.id === 'dso')
    if (dsoBench && typeof dsoBench.value === 'number') {
      benchmarkDso = dsoBench.value
    }
  }

  const hasDso = typeof company.dsoDays === 'number' && company.dsoDays > 0

  if (!hasDso) {
    takeaway = {
      id: 'receivables-takeaway-missing',
      title: 'Receivables Review Pending',
      description: 'Connect invoicing and receivables aging datasets to analyze collection cycles.',
      severity: 'Neutral',
      category: 'receivables',
      metricRefs: ['dsoDays'],
      sourceRefs: [],
      requiresCompanyData: true,
      confidence: 'low',
    }
  } else if (company.dsoDays > benchmarkDso + 5) {
    takeaway = {
      id: 'receivables-takeaway-stretched',
      title: 'Receivables Stretch Detected',
      description: `Your DSO of ${company.dsoDays} days exceeds the sector benchmark of ${benchmarkDso} days, stretching working capital cycles.`,
      severity: 'Caution',
      category: 'receivables',
      metricRefs: ['dsoDays'],
      sourceRefs: ['receivables-aging'],
      requiresCompanyData: false,
      confidence: 'high',
    }
  } else {
    takeaway = {
      id: 'receivables-takeaway-healthy',
      title: 'Optimal Receivables Cycle',
      description: `Your DSO of ${company.dsoDays} days is within the sector average of ${benchmarkDso} days, showing stable cash collections.`,
      severity: 'Positive',
      category: 'receivables',
      metricRefs: ['dsoDays'],
      sourceRefs: ['receivables-aging'],
      requiresCompanyData: false,
      confidence: 'high',
    }
  }

  return {
    takeaway,
    watchSignals,
    supportingInsights,
  }
}
