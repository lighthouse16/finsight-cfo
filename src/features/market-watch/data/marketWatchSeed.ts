import {
  CommodityExposure,
  FxPair,
  GbaFundingSignal,
  LiquidityEvent,
  MarketMetric,
  MarketSignal,
  RateSnapshot,
  SectorBenchmark,
  SourceStatusItem,
  StressScenario,
} from '../types'

export const seedMarketMetrics: MarketMetric[] = [
  {
    id: 'funding-conditions',
    label: 'Funding Conditions',
    value: 'Selective',
    interpretation: 'Credit access favors stronger documentation.',
    severity: 'Caution',
    freshness: 'Daily',
    source: 'Market context',
  },
  {
    id: 'rate-pressure',
    label: 'Rate Pressure',
    value: 'Elevated',
    interpretation: 'Floating-rate debt remains cost-sensitive.',
    severity: 'High',
    freshness: 'Daily',
    source: 'HKMA rates',
  },
  {
    id: 'sector-health',
    label: 'Sector Health',
    value: 'Divergent',
    interpretation: 'Sector signals vary by demand cycle.',
    severity: 'Neutral',
    freshness: 'Monthly',
    source: 'Sector benchmark',
  },
  {
    id: 'fx-gba-signal',
    label: 'FX / GBA Signal',
    value: 'CNY Watch',
    interpretation: 'Cross-border exposure needs review.',
    severity: 'Caution',
    freshness: 'Daily',
    source: 'FX context',
  },
]

export const seedMarketSignals: MarketSignal[] = [
  {
    id: 'signal-1',
    category: 'Rates',
    title: 'HIBOR Persistence',
    description: '1M HIBOR remains elevated above 4.5%, directly impacting floating-rate debt service capacity.',
    severity: 'High',
    cfoQuestion: 'Is our cash buffer sufficient for 6 months if rates do not cut as expected?',
    affectedArea: 'Debt Service',
    timestamp: 'Today, 09:00',
  },
  {
    id: 'signal-2',
    category: 'Sector',
    title: 'Receivables Stretching',
    description: 'Sector average Days Sales Outstanding (DSO) has stretched by 12 days year-to-date.',
    severity: 'Caution',
    cfoQuestion: 'Are our key buyers requesting extended terms? How does this affect our working capital gap?',
    affectedArea: 'Working Capital',
    timestamp: 'Yesterday, 14:30',
  },
  {
    id: 'signal-3',
    category: 'Commodities',
    title: 'Input Cost Stabilization',
    description: 'Key raw material inputs are showing signs of stabilization after Q1 volatility.',
    severity: 'Positive',
    cfoQuestion: 'Can we lock in supplier pricing now to secure Q3/Q4 margins?',
    affectedArea: 'Gross Margin',
    timestamp: '2 days ago',
  },
]

export const seedRateSnapshots: RateSnapshot[] = [
  {
    label: '1M HIBOR',
    value: '4.58%',
    changeBasisPoints: 2,
    trend: 'up',
    context: 'Base reference for short-term corporate facilities.',
  },
  {
    label: 'Prime Rate',
    value: '5.875%',
    changeBasisPoints: 0,
    trend: 'flat',
    context: 'Standard reference for SME uncollateralized lending.',
  },
  {
    label: '1Y LPR (CNY)',
    value: '3.45%',
    changeBasisPoints: -10,
    trend: 'down',
    context: 'Cross-border onshore borrowing reference.',
  },
]

export const seedLiquidityEvents: LiquidityEvent[] = [
  {
    id: 'liq-1',
    date: 'End of Quarter',
    event: 'Quarter-end Window Dressing',
    impact: 'Potential short-term interbank liquidity tightening.',
    severity: 'Caution',
  },
  {
    id: 'liq-2',
    date: 'Next Week',
    event: 'Large IPO Lock-up',
    impact: 'Temporary diversion of market liquidity.',
    severity: 'Neutral',
  },
]

export const seedFxPairs: FxPair[] = [
  {
    pair: 'USD/HKD',
    rate: '7.8150',
    trend: 'flat',
    context: 'Peg remains stable. Minimal translation risk.',
  },
  {
    pair: 'CNY/HKD',
    rate: '1.0820',
    trend: 'down',
    context: 'CNY depreciation impacts repatriated onshore earnings.',
  },
]

export const seedGbaSignals: GbaFundingSignal[] = [
  {
    id: 'gba-1',
    title: 'Cross-Border Pooling',
    description: 'Favorable spread between onshore LPR and offshore HIBOR encourages cross-border treasury pooling for eligible SMEs.',
    severity: 'Positive',
  },
]

export const seedSectorBenchmarks: SectorBenchmark[] = [
  {
    sector: 'Manufacturing (Export)',
    healthScore: 72,
    pmi: 51.2,
    exportGrowth: '+2.4%',
    workingCapitalDays: 65,
    receivablesDays: 45,
    inventoryPressure: 'Moderate',
  },
  {
    sector: 'Retail (Domestic)',
    healthScore: 58,
    pmi: 48.5,
    exportGrowth: 'N/A',
    workingCapitalDays: 30,
    receivablesDays: 15,
    inventoryPressure: 'High',
  },
]

export const seedCommodityExposures: CommodityExposure[] = [
  {
    commodity: 'Copper (LME)',
    priceTrend: 'up',
    yoyChange: '+14%',
    affectedSectors: ['Electronics', 'Construction', 'Machinery'],
    marginSensitivity: 'High impact on raw material COGS.',
  },
  {
    commodity: 'Brent Crude',
    priceTrend: 'flat',
    yoyChange: '+2%',
    affectedSectors: ['Logistics', 'Manufacturing'],
    marginSensitivity: 'Moderate transport cost impact.',
  },
  {
    commodity: 'Steel / Iron Ore',
    priceTrend: 'down',
    yoyChange: '-8%',
    affectedSectors: ['Construction', 'Heavy Machinery', 'Infrastructure'],
    marginSensitivity: 'Softening reduces raw material pressures for developers and builders.',
  },
  {
    commodity: 'Cotton',
    priceTrend: 'up',
    yoyChange: '+6%',
    affectedSectors: ['Textiles', 'Apparel', 'Retail'],
    marginSensitivity: 'Rising input costs squeeze margins for export-driven apparel manufacturers.',
  },
]

export const seedStressScenarios: StressScenario[] = [
  {
    id: 'stress-1',
    title: 'Rate Shock (+150 bps)',
    description: 'Simulates a sustained 150 basis point increase in borrowing costs.',
    affectedArea: 'Debt Service Coverage Ratio (DSCR)',
    impactDirection: 'Negative',
    severity: 'High',
    cfoQuestion: 'Would our cashflow cover interest payments under this stress?',
    requiredDataStatus: 'Requires company financials',
  },
  {
    id: 'stress-2',
    title: 'Receivables Delay (+30 Days)',
    description: 'Simulates major customers delaying payments by a full billing cycle.',
    affectedArea: 'Working Capital Runway',
    impactDirection: 'Negative',
    severity: 'Caution',
    cfoQuestion: 'Do we have sufficient revolving credit to bridge a 30-day gap?',
    requiredDataStatus: 'Requires company financials',
  },
  {
    id: 'stress-3',
    title: 'CNY Depreciation (-5%)',
    description: 'Simulates further weakening of the RMB against HKD/USD.',
    affectedArea: 'Repatriated Earnings',
    impactDirection: 'Negative',
    severity: 'Caution',
    cfoQuestion: 'Are our onshore revenues sufficiently hedged?',
    requiredDataStatus: 'Requires company financials',
  },
]

export const seedSourceStatus: SourceStatusItem[] = [
  { label: 'HKMA Reference Rates', status: 'Ready for connector' },
  { label: 'Interbank Liquidity', status: 'Ready for connector' },
  { label: 'FX Provider', status: 'Seed data' },
  { label: 'Sector Benchmarks', status: 'Requires backend' },
  { label: 'Commodity Provider', status: 'Seed data' },
  { label: 'Internal Financial Records', status: 'Requires company data' },
]
