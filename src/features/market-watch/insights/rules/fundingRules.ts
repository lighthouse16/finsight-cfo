import { MarketWatchSnapshot, MarketWatchInsight, TabInsightSet } from '../types'

/**
 * Maps a backend FinancialBand to a MarketWatchInsight severity.
 * summary.debtServiceBand is the primary interpretation source.
 */
function bandToSeverity(band: string): MarketWatchInsight['severity'] {
  switch (band) {
    case 'strong':   return 'Positive'
    case 'adequate': return 'Positive'
    case 'watch':    return 'Caution'
    case 'constrained': return 'High'
    default:         return 'Neutral'
  }
}

export function evaluateFundingRules(snapshot: MarketWatchSnapshot): TabInsightSet {
  const { company, financialSummary } = snapshot
  const watchSignals: MarketWatchInsight[] = []
  const supportingInsights: MarketWatchInsight[] = []
  let takeaway: MarketWatchInsight | null = null

  // ── Priority 1: use backend summary if available ──────────────────────────
  if (financialSummary) {
    const band = financialSummary.debtServiceBand

    // Find DSCR signal from backend for evidence text
    const dscrSignal = financialSummary.keySignals.find(s => s.key === 'dscr')
    const dscrMsg = dscrSignal?.message ?? 'Debt service coverage assessed from demo financial analysis.'
    const dscrVal = dscrSignal?.value

    if (band === 'constrained') {
      takeaway = {
        id: 'funding-takeaway-constrained',
        title: 'Debt-Service Coverage: Constrained',
        description: dscrMsg,
        severity: 'High',
        category: 'funding',
        metricRefs: ['dscr', 'monthlyDebtServiceHkd'],
        sourceRefs: ['financial-demo-analysis'],
        requiresCompanyData: false,
        confidence: 'high',
        status: 'context_only',
      }
      // Add constraints from summary as watch signals
      financialSummary.constraints.forEach((constraint, i) => {
        watchSignals.push({
          id: `funding-constraint-${i}`,
          title: 'Financial Analysis Constraint',
          description: constraint,
          severity: 'High',
          category: 'funding',
          metricRefs: [],
          sourceRefs: ['financial-demo-analysis'],
          requiresCompanyData: false,
          confidence: 'high',
          status: 'context_only',
        })
      })
    } else if (band === 'watch') {
      takeaway = {
        id: 'funding-takeaway-watch',
        title: 'Debt-Service Coverage: Watch',
        description: dscrMsg,
        severity: 'Caution',
        category: 'funding',
        metricRefs: ['dscr'],
        sourceRefs: ['financial-demo-analysis'],
        requiresCompanyData: false,
        confidence: 'high',
        status: 'context_only',
      }
    } else if (band === 'adequate' || band === 'strong') {
      takeaway = {
        id: 'funding-takeaway-adequate',
        title: band === 'strong' ? 'Debt-Service Coverage: Strong' : 'Debt-Service Coverage: Adequate',
        description: dscrMsg,
        severity: bandToSeverity(band),
        category: 'funding',
        metricRefs: ['dscr'],
        sourceRefs: ['financial-demo-analysis'],
        requiresCompanyData: false,
        confidence: 'high',
        status: 'context_only',
      }
    } else {
      // unavailable
      takeaway = {
        id: 'funding-takeaway-missing',
        title: 'Debt-Service Assessment Pending',
        description: 'Financial analysis summary unavailable. Company records required for production analysis.',
        severity: 'Neutral',
        category: 'funding',
        metricRefs: [],
        sourceRefs: [],
        requiresCompanyData: true,
        confidence: 'low',
      }
    }

    // Working capital watch from summary watch items
    financialSummary.watchItems
      .filter(w => w.toLowerCase().includes('liquidity') || w.toLowerCase().includes('working capital') || w.toLowerCase().includes('current ratio') || w.toLowerCase().includes('quick ratio'))
      .forEach((item, i) => {
        watchSignals.push({
          id: `funding-liquidity-watch-${i}`,
          title: 'Liquidity Watch Item',
          description: item,
          severity: 'Caution',
          category: 'funding',
          metricRefs: ['currentRatio', 'quickRatio'],
          sourceRefs: ['financial-demo-analysis'],
          requiresCompanyData: false,
          confidence: 'high',
          status: 'context_only',
        })
      })

    // Strengths as supporting insights
    financialSummary.strengths
      .filter(s => s.toLowerCase().includes('interest coverage') || s.toLowerCase().includes('leverage') || s.toLowerCase().includes('debt'))
      .forEach((strength, i) => {
        supportingInsights.push({
          id: `funding-strength-${i}`,
          title: 'Financial Strength',
          description: strength,
          severity: 'Positive',
          category: 'funding',
          metricRefs: [],
          sourceRefs: ['financial-demo-analysis'],
          requiresCompanyData: false,
          confidence: 'high',
          status: 'context_only',
        })
      })

    // Working capital gap from raw company data (still useful evidence)
    if (company.workingCapitalGapHkd > 0 && dscrVal !== null && dscrVal !== undefined) {
      watchSignals.push({
        id: 'funding-wc-gap',
        title: 'Working-capital gap watch',
        description: `Working capital gap of HKD ${(company.workingCapitalGapHkd / 1000000).toFixed(1)}M pressures liquid cash runway.`,
        severity: company.workingCapitalGapHkd > 2000000 ? 'Caution' : 'Neutral',
        category: 'funding',
        metricRefs: ['workingCapitalGapHkd'],
        sourceRefs: ['invoices', 'payables-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      })
    }

    return { takeaway, watchSignals, supportingInsights }
  }

  // ── Fallback: raw company ratios (no backend summary) ─────────────────────
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

    if (company.dscr !== undefined && company.dscr !== null && company.dscr < 1.0) {
      takeaway = {
        id: 'funding-takeaway-constrained',
        title: 'Constrained Debt Service',
        description: `Operating cashflow coverage is thin. DSCR of ${company.dscr.toFixed(2)}x indicates constrained debt service capacity.`,
        severity: 'High',
        category: 'funding',
        metricRefs: ['cashBalanceHkd', 'monthlyDebtServiceHkd'],
        sourceRefs: ['bank-transactions', 'debt-schedule'],
        requiresCompanyData: false,
        confidence: 'high',
      }
    } else if (ratio < 3) {
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
        title: 'Working-capital gap watch',
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
