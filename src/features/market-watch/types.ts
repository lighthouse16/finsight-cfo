export type FreshnessStatus = 'Daily' | 'Monthly' | 'Delayed' | 'Workspace'

export type SignalSeverity = 'Neutral' | 'Caution' | 'High' | 'Positive'

export type SourceStatus =
  | 'Ready for connector'
  | 'Seed data'
  | 'Requires backend'
  | 'Requires company data'

export type MarketMetric = {
  id: string
  label: string
  value: string
  interpretation: string
  severity: SignalSeverity
  freshness: FreshnessStatus
  source: string
}

export type MarketSignal = {
  id: string
  category: string
  title: string
  description: string
  severity: SignalSeverity
  cfoQuestion: string
  affectedArea: string
  timestamp: string
}

export type RateSnapshot = {
  label: string
  value: string
  changeBasisPoints: number
  trend: 'up' | 'down' | 'flat'
  context: string
}

export type LiquidityEvent = {
  id: string
  date: string
  event: string
  impact: string
  severity: SignalSeverity
}

export type FxPair = {
  pair: string
  rate: string
  trend: 'up' | 'down' | 'flat'
  context: string
}

export type GbaFundingSignal = {
  id: string
  title: string
  description: string
  severity: SignalSeverity
}

export type ExposureNote = {
  id: string
  category: string
  note: string
  severity: SignalSeverity
}

export type SectorBenchmark = {
  sector: string
  healthScore: number // 0-100
  pmi: number
  exportGrowth: string
  workingCapitalDays: number
  receivablesDays: number
  inventoryPressure: string
}

export type CommodityExposure = {
  commodity: string
  priceTrend: 'up' | 'down' | 'flat'
  yoyChange: string
  affectedSectors: string[]
  marginSensitivity: string
}

export type StressScenario = {
  id: string
  title: string
  description: string
  affectedArea: string
  impactDirection: 'Negative' | 'Positive' | 'Mixed'
  severity: SignalSeverity
  cfoQuestion: string
  requiredDataStatus: string
}

export type SignalFeedItem = MarketSignal

export type SourceStatusItem = {
  label: string
  status: SourceStatus
}

export interface SectorHealthComponent {
  label: string
  value: number | null
  unit: 'index' | 'percent' | 'text'
  displayValue: string
  context: string
}

export interface SectorHealth {
  score: number | null
  label: string
  severity: SignalSeverity
  components: {
    pmi: SectorHealthComponent | null
    exportGrowth: SectorHealthComponent | null
    industrialProduction: SectorHealthComponent | null
    marginContext: SectorHealthComponent | null
  }
}

export interface SectorBenchmarkItem {
  id: string
  label: string
  value: number | null
  unit: 'days' | 'percent' | 'ratio' | 'index'
  displayValue: string
  comparison: string
  context: string
  severity: SignalSeverity
  sourceTimestamp: string | null
}

export interface SectorWatchSignal {
  id: string
  title: string
  description: string
  affectedArea: string
  severity: SignalSeverity
}

export interface SectorSourceInfo {
  label: string
  asOf: string | null
  warnings: string[]
  freshness: FreshnessStatus
  selectedSector: {
    id: string
    name: string
    code: string | null
    geography: string
    description: string
  }
  sectorHealth: SectorHealth
  watchSignals: SectorWatchSignal[]
  sourceStatus: {
    id: string
    label: string
    status: string
    provider?: string
    lastUpdatedAt?: string | null
  }[]
  isFallback?: boolean
}

