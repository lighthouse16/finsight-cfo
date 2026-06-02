import {
  seedCommodityExposures,
  seedFxPairs,
  seedGbaSignals,
  seedLiquidityEvents,
  seedMarketMetrics,
  seedMarketSignals,
  seedRateSnapshots,
  seedSectorBenchmarks,
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
  SectorBenchmark,
  SourceStatusItem,
  StressScenario,
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

export async function getSectorBenchmarks(): Promise<{
  benchmarks: SectorBenchmark[]
}> {
  await delay(500)
  return {
    benchmarks: seedSectorBenchmarks,
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
