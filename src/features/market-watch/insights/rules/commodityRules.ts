import { MarketWatchSnapshot, MarketWatchInsight, TabInsightSet } from '../types'

export function evaluateCommodityRules(snapshot: MarketWatchSnapshot): TabInsightSet {
  const { company, commodities } = snapshot
  const watchSignals: MarketWatchInsight[] = []
  const supportingInsights: MarketWatchInsight[] = []
  let takeaway: MarketWatchInsight | null = null

  const sector = (company.sector || '').toLowerCase()
  const isElectronics = sector.includes('electronics')
  const isManufacturing = sector.includes('manufacturing')
  const isServices = sector.includes('services')

  const hasMargin = typeof company.grossMarginPercent === 'number'

  // Helper to extract commodity trend
  const getCommodityTrend = (commId: string): 'up' | 'down' | 'flat' => {
    if (commodities && Array.isArray(commodities)) {
      const itemsList = commodities as Array<{ commodity?: string; priceTrend?: 'up' | 'down' | 'flat' }>
      const item = itemsList.find((c) => c?.commodity?.toLowerCase().includes(commId))
      if (item && item.priceTrend) {
        return item.priceTrend
      }
    }
    return 'flat'
  }

  if (!hasMargin) {
    takeaway = {
      id: 'commodities-takeaway-missing',
      title: 'Commodity Risk Analysis Pending',
      description: 'Connect component inventory data to assess gross margin sensitivity to raw components and freight indexes.',
      severity: 'Neutral',
      category: 'commodities',
      metricRefs: ['grossMarginPercent'],
      sourceRefs: [],
      requiresCompanyData: true,
      confidence: 'low',
    }
  } else {
    // Determine relevance and cost pressures
    const copperTrend = getCommodityTrend('copper')
    const energyTrend = getCommodityTrend('energy') || getCommodityTrend('brent')
    const freightTrend = getCommodityTrend('freight')
    const steelTrend = getCommodityTrend('steel')


    if (isElectronics) {
      const primaryUp = copperTrend === 'up' || energyTrend === 'up' || freightTrend === 'up'
      const isMarginTight = company.grossMarginPercent < 20.0

      if (primaryUp && isMarginTight) {
        takeaway = {
          id: 'commodities-takeaway-pressure',
          title: 'Input Cost Margin Pressure',
          description: `Rising copper, energy, or freight indexes raise landed-cost exposure relative to your current gross margin of ${company.grossMarginPercent}%.`,
          severity: 'Caution',
          category: 'commodities',
          metricRefs: ['grossMarginPercent'],
          sourceRefs: ['supplier-contracts'],
          requiresCompanyData: false,
          confidence: 'high',
        }
      } else {
        takeaway = {
          id: 'commodities-takeaway-stable',
          title: 'Component Inputs Stable',
          description: 'Key components and logistics indexes show stable trends relative to your current gross margins.',
          severity: 'Neutral',
          category: 'commodities',
          metricRefs: ['grossMarginPercent'],
          sourceRefs: ['supplier-contracts'],
          requiresCompanyData: false,
          confidence: 'high',
        }
      }

      // Add low relevance notice
      supportingInsights.push({
        id: 'commodities-cotton-low-relevance',
        title: 'Soft Commodities Index (Cotton)',
        description: 'Cotton index shifts represent low operational relevance for the electronics import sector.',
        severity: 'Neutral',
        category: 'commodities',
        metricRefs: [],
        sourceRefs: ['workspace-seed'],
        requiresCompanyData: false,
        confidence: 'medium',
      })
    } else if (isManufacturing) {
      const primaryUp = copperTrend === 'up' || energyTrend === 'up' || freightTrend === 'up' || steelTrend === 'up'
      
      takeaway = {
        id: 'commodities-takeaway-mfg',
        title: primaryUp ? 'Raw Component Price Pressure' : 'Component Cost Stability',
        description: primaryUp
          ? 'Elevated metals and freight indexes increase manufacturing inputs cost base.'
          : 'Manufacturing input costs show stable benchmark trends.',
        severity: primaryUp ? 'Caution' : 'Neutral',
        category: 'commodities',
        metricRefs: ['grossMarginPercent'],
        sourceRefs: ['supplier-contracts'],
        requiresCompanyData: false,
        confidence: 'high',
      }
    } else if (isServices) {
      takeaway = {
        id: 'commodities-takeaway-services',
        title: 'Low Sourcing Index Exposure',
        description: 'Commodity cost changes do not directly impact service provider operating structures.',
        severity: 'Neutral',
        category: 'commodities',
        metricRefs: [],
        sourceRefs: [],
        requiresCompanyData: false,
        confidence: 'high',
      }
    } else {
      takeaway = {
        id: 'commodities-takeaway-default',
        title: 'Sourcing Risk Assessment',
        description: 'Raw materials component index monitoring is active for this workspace.',
        severity: 'Neutral',
        category: 'commodities',
        metricRefs: [],
        sourceRefs: [],
        requiresCompanyData: false,
        confidence: 'low',
      }
    }
  }

  return {
    takeaway,
    watchSignals,
    supportingInsights,
  }
}
