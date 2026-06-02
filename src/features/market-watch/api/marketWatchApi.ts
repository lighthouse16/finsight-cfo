import {
  seedCommodityExposures,
  seedFxPairs,
  seedGbaSignals,
  seedLiquidityEvents,
  seedMarketMetrics,
  seedMarketSignals,
  seedRateSnapshots,
  seedSourceStatus,
  seedStressScenarios,
} from '../data/marketWatchSeed'
import {
  CommodityExposure,
  ExposureNote,
  FxPair,
  GbaFundingSignal,
  LiquidityEvent,
  MarketMetric,
  MarketSignal,
  RateSnapshot,
  SourceStatusItem,
  StressScenario,
  SectorSourceInfo,
  SectorBenchmarkItem,
  FreshnessStatus,
} from '../types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

// Simulate network delay for seed-only paths
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

// ------------------------------------------------------------------
// Backend response types (only for adapter, not exported)
// ------------------------------------------------------------------
type BackendRateSnapshot = {
  id: string
  label: string
  tenor: string
  value: number | null
  unit: string
  displayValue: string
  changeBasisPoints: number | null
  trend: 'up' | 'down' | 'flat' | 'unknown'
  context: string
  sourceTimestamp: string | null
}

type BackendResponseMetadata = {
  asOf: string | null
  fetchedAt: string
  freshness: string
  isStale: boolean
  source: { provider: string; name: string; url?: string }
  warnings: string[]
}

type BackendLiquidityEvent = {
  id: string
  date: string
  event: string
  impact: string
  severity: 'Neutral' | 'Caution' | 'High' | 'Positive'
}

type BackendRatesLiquidityResponse = {
  metadata: BackendResponseMetadata
  rates: BackendRateSnapshot[]
  liquidityEvents: BackendLiquidityEvent[]
}

type BackendFxPair = {
  id: string
  pair: string
  value: number | null
  unit: string
  displayValue: string
  trend: 'up' | 'down' | 'flat' | 'unknown'
  changePips: number | null
  context: string
  sourceTimestamp: string | null
}

type BackendGbaFundingSignal = {
  id: string
  title: string
  description: string
  severity: 'Neutral' | 'Caution' | 'High' | 'Positive'
}

type BackendExposureNote = {
  id: string
  category: string
  note: string
  severity: 'Neutral' | 'Caution' | 'High' | 'Positive'
}

type BackendFxGbaResponse = {
  metadata: BackendResponseMetadata
  fxPairs: BackendFxPair[]
  gbaFundingSignal: BackendGbaFundingSignal[]
  exposureNotes: BackendExposureNote[]
}

// ------------------------------------------------------------------
// Adapter
// ------------------------------------------------------------------
function adaptRate(backend: BackendRateSnapshot): RateSnapshot {
  const formattedValue = (() => {
    const match = backend.displayValue.match(/^([\d.]+)/)
    if (match) {
      const num = parseFloat(match[1])
      return `${num.toFixed(2)}%`
    }
    return backend.displayValue
  })()

  return {
    label: backend.label,
    value: formattedValue,
    changeBasisPoints: backend.changeBasisPoints ?? 0,
    trend: backend.trend === 'unknown' ? 'flat' : backend.trend,
    context: backend.context,
  }
}

function adaptLiquidityEvent(
  backend: BackendLiquidityEvent,
): LiquidityEvent {
  return {
    id: backend.id,
    date: backend.date,
    event: backend.event,
    impact: backend.impact,
    severity: backend.severity,
  }
}

function adaptFxPair(backend: BackendFxPair): FxPair {
  return {
    pair: backend.pair,
    rate: backend.displayValue,
    trend: backend.trend === 'unknown' ? 'flat' : backend.trend,
    context: backend.context,
  }
}

function adaptGbaSignal(backend: BackendGbaFundingSignal): GbaFundingSignal {
  return {
    id: backend.id,
    title: backend.title,
    description: backend.description,
    severity: backend.severity,
  }
}

function adaptExposureNote(backend: BackendExposureNote): ExposureNote {
  return {
    id: backend.id,
    category: backend.category,
    note: backend.note,
    severity: backend.severity,
  }
}

// ------------------------------------------------------------------
// Exported API functions
// ------------------------------------------------------------------

export async function getRatesLiquidity(): Promise<{
  rates: RateSnapshot[]
  liquidityEvents: LiquidityEvent[]
  ratesSource?: {
    label: string
    asOf: string | null
    warnings: string[]
  }
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/market-watch/rates-liquidity`,
      { signal: AbortSignal.timeout(5000) },
    )

    if (!res.ok) {
      throw new Error(`Backend returned ${res.status}`)
    }

    const body: BackendRatesLiquidityResponse = await res.json()

    const rates = body.rates.map(adaptRate)
    const liquidityEvents = body.liquidityEvents.map(adaptLiquidityEvent)

    return {
      rates,
      liquidityEvents,
      ratesSource: {
        label: body.metadata.source.name,
        asOf: body.metadata.asOf,
        warnings: body.metadata.warnings ?? [],
      },
    }
  } catch {
    // Fallback to seed data when backend is unavailable
    await delay(300)
    return {
      rates: seedRateSnapshots,
      liquidityEvents: seedLiquidityEvents,
      ratesSource: {
        label: 'Workspace Seed Data',
        asOf: null,
        warnings: [
          'Backend unavailable. Using workspace seed data.',
        ],
      },
    }
  }
}

export async function getMarketOverview(): Promise<{
  metrics: MarketMetric[]
  signals: MarketSignal[]
}> {
  await delay(400)
  return {
    metrics: seedMarketMetrics,
    signals: seedMarketSignals,
  }
}

export async function getFxGba(): Promise<{
  fxPairs: FxPair[]
  gbaSignals: GbaFundingSignal[]
  exposureNotes?: ExposureNote[]
  fxSource?: {
    label: string
    asOf: string | null
    warnings: string[]
  }
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/market-watch/fx-gba`,
      { signal: AbortSignal.timeout(5000) },
    )

    if (!res.ok) {
      throw new Error(`Backend returned ${res.status}`)
    }

    const body: BackendFxGbaResponse = await res.json()

    return {
      fxPairs: body.fxPairs.map(adaptFxPair),
      gbaSignals: body.gbaFundingSignal.map(adaptGbaSignal),
      exposureNotes: body.exposureNotes.map(adaptExposureNote),
      fxSource: {
        label: body.metadata.source.name,
        asOf: body.metadata.asOf,
        warnings: body.metadata.warnings ?? [],
      },
    }
  } catch {
    await delay(300)
    return {
      fxPairs: seedFxPairs,
      gbaSignals: seedGbaSignals,
      fxSource: {
        label: 'Workspace Seed Data',
        asOf: null,
        warnings: [
          'Backend unavailable. Using workspace seed data.',
        ],
      },
    }
  }
}

type BackendSectorHealthComponent = {
  label: string
  value: number | null
  unit: 'index' | 'percent' | 'text'
  displayValue: string
  context: string
}

type BackendSectorHealth = {
  score: number | null
  label: string
  severity: 'Neutral' | 'Caution' | 'High' | 'Positive'
  components: {
    pmi: BackendSectorHealthComponent | null
    exportGrowth: BackendSectorHealthComponent | null
    industrialProduction: BackendSectorHealthComponent | null
    marginContext: BackendSectorHealthComponent | null
  }
}

type BackendSectorBenchmark = {
  id: string
  label: string
  value: number | null
  unit: 'days' | 'percent' | 'ratio' | 'index'
  displayValue: string
  comparison: string
  context: string
  severity: 'Neutral' | 'Caution' | 'High' | 'Positive'
  sourceTimestamp: string | null
}

type BackendSectorWatchSignal = {
  id: string
  title: string
  description: string
  affectedArea: string
  severity: 'Neutral' | 'Caution' | 'High' | 'Positive'
}

type BackendSelectedSector = {
  id: string
  name: string
  code: string | null
  geography: string
  description: string
}

type BackendSectorBenchmarksResponse = {
  metadata: BackendResponseMetadata
  selectedSector: BackendSelectedSector
  sectorHealth: BackendSectorHealth
  benchmarks: BackendSectorBenchmark[]
  watchSignals: BackendSectorWatchSignal[]
  sourceStatus: {
    id: string
    label: string
    status: 'connected' | 'seed_data' | 'requires_backend' | 'requires_company_data' | 'unavailable' | 'stale'
    provider?: string
    lastUpdatedAt?: string | null
  }[]
}

// Local fallback data generator
function getLocalSectorBenchmarksFallback(): {
  benchmarks: SectorBenchmarkItem[]
  sectorSource: SectorSourceInfo
} {
  return {
    benchmarks: [
      {
        id: 'dso',
        label: 'Days Sales Outstanding',
        value: 45,
        unit: 'days',
        displayValue: '45 days',
        comparison: 'Compared to industry standard (40 days)',
        context: 'Receivables cycle slightly elevated due to local latency. Receivables discipline remains important.',
        severity: 'Caution',
        sourceTimestamp: null,
      },
      {
        id: 'dio',
        label: 'Inventory Days',
        value: 65,
        unit: 'days',
        displayValue: '65 days',
        comparison: 'Compared to industry standard (60 days)',
        context: 'Inventory turnaround stable. Monitor storage costs.',
        severity: 'Neutral',
        sourceTimestamp: null,
      },
      {
        id: 'dpo',
        label: 'Days Payable Outstanding',
        value: 50,
        unit: 'days',
        displayValue: '50 days',
        comparison: 'Compared to industry standard (45 days)',
        context: 'Supplier terms leverage matches collection periods.',
        severity: 'Neutral',
        sourceTimestamp: null,
      },
      {
        id: 'gross-margin',
        label: 'Gross Margin Context',
        value: 18.5,
        unit: 'percent',
        displayValue: '18.5%',
        comparison: 'Compared to historical average (20.0%)',
        context: 'Input cost pressure watch. Regional averages may vary.',
        severity: 'Caution',
        sourceTimestamp: null,
      },
      {
        id: 'documentation-readiness',
        label: 'Documentation Readiness',
        value: 85,
        unit: 'percent',
        displayValue: '85%',
        comparison: 'Compared to target (90%)',
        context: 'Invoice records complete; declarations pending final review.',
        severity: 'Neutral',
        sourceTimestamp: null,
      },
    ],
    sectorSource: {
      label: 'Workspace Seed Data',
      asOf: null,
      freshness: 'Workspace',
      warnings: ['Backend unavailable. Showing workspace seed data.'],
      selectedSector: {
        id: 'manufacturing-export',
        name: 'Manufacturing (Export)',
        code: 'HK-SME-MFG',
        geography: 'HK',
        description: 'Export-oriented manufacturing SMEs with raw material and inventory sensitivities.',
      },
      sectorHealth: {
        score: 72,
        label: 'Stable expansion',
        severity: 'Positive',
        components: {
          pmi: {
            label: 'PMI',
            value: 51.2,
            unit: 'index',
            displayValue: '51.2',
            context: 'Mild expansion zone.',
          },
          exportGrowth: {
            label: 'Export Growth',
            value: 2.4,
            unit: 'percent',
            displayValue: '+2.4%',
            context: 'Positive export growth trend.',
          },
          industrialProduction: {
            label: 'Industrial Production',
            value: 3.1,
            unit: 'percent',
            displayValue: '+3.1%',
            context: 'Steady industrial output.',
          },
          marginContext: {
            label: 'Margin Context',
            value: null,
            unit: 'text',
            displayValue: 'Input cost pressure',
            context: 'Slight input cost increases monitored.',
          },
        },
      },
      watchSignals: [
        {
          id: 'sig-1',
          title: 'Receivables Discipline Important',
          description: 'Receivables discipline remains important for lender review. Focus on collections.',
          affectedArea: 'Cashflow Planning',
          severity: 'Caution',
        },
        {
          id: 'sig-2',
          title: 'Inventory Cycle Monitor',
          description: 'Inventory buildup can pressure working capital. Review buffer stock policies.',
          affectedArea: 'Warehouse Management',
          severity: 'Neutral',
        },
      ],
      sourceStatus: [
        {
          id: 'sector-benchmark-provider',
          label: 'Sector Benchmark Provider',
          status: 'seed_data',
          provider: 'Fixture',
        },
      ],
      isFallback: true,
    },
  }
}

export async function getSectorBenchmarks(): Promise<{
  benchmarks: SectorBenchmarkItem[]
  sectorSource: SectorSourceInfo
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/market-watch/sector-benchmarks`,
      { signal: AbortSignal.timeout(5000) },
    )

    if (!res.ok) {
      throw new Error(`Backend returned ${res.status}`)
    }

    const body: BackendSectorBenchmarksResponse = await res.json()

    return {
      benchmarks: body.benchmarks,
      sectorSource: {
        label: body.metadata.source.name,
        asOf: body.metadata.asOf,
        warnings: body.metadata.warnings ?? [],
        freshness: body.metadata.freshness as FreshnessStatus,
        selectedSector: body.selectedSector,
        sectorHealth: body.sectorHealth,
        watchSignals: body.watchSignals,
        sourceStatus: body.sourceStatus,
        isFallback: false,
      },
    }
  } catch (error) {
    console.warn('Sector Benchmarks fetch failed, using fallback', error)
    await delay(300)
    return getLocalSectorBenchmarksFallback()
  }
}


export async function getCommodities(): Promise<{
  commodities: CommodityExposure[]
}> {
  await delay(300)
  return {
    commodities: seedCommodityExposures,
  }
}

export async function getStressSignals(): Promise<{
  scenarios: StressScenario[]
}> {
  await delay(400)
  return {
    scenarios: seedStressScenarios,
  }
}

export async function getMarketSourceStatus(): Promise<{
  sources: SourceStatusItem[]
}> {
  await delay(200)
  return {
    sources: seedSourceStatus,
  }
}
