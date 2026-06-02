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

// Simulate network delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

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

export async function getRatesLiquidity(): Promise<{
  rates: RateSnapshot[]
  liquidityEvents: LiquidityEvent[]
}> {
  await delay(300)
  return {
    rates: seedRateSnapshots,
    liquidityEvents: seedLiquidityEvents,
  }
}

export async function getFxGba(): Promise<{
  fxPairs: FxPair[]
  gbaSignals: GbaFundingSignal[]
}> {
  await delay(300)
  return {
    fxPairs: seedFxPairs,
    gbaSignals: seedGbaSignals,
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
