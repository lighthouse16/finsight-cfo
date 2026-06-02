import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, Box, Globe, PieChart, TrendingUp } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import InfoTooltip from '../../components/ui/InfoTooltip'
import {
  getCommodities,
  getFxGba,
  getMarketOverview,
  getMarketSourceStatus,
  getRatesLiquidity,
  getSectorBenchmarks,
  getStressSignals,
  refreshData,
} from './api/marketWatchApi'
import CommoditiesTab from './components/CommoditiesTab'
import FxGbaTab from './components/FxGbaTab'
import MarketMetricCard from './components/MarketMetricCard'
import MarketPulseTab from './components/MarketPulseTab'
import MarketWatchTabs, { TabId } from './components/MarketWatchTabs'
import RatesLiquidityTab from './components/RatesLiquidityTab'
import SectorBenchmarksTab from './components/SectorBenchmarksTab'
import StressSignalsTab from './components/StressSignalsTab'
import {
  CommodityExposure,
  ExposureNote,
  FxPair,
  GbaFundingSignal,
  LiquidityEvent,
  MarketMetric,
  MarketSignal,
  RateSnapshot,
  SectorBenchmarkItem,
  SectorSourceInfo,
  SourceStatusItem,
  StressScenario,
  CommoditySourceInfo,
  StressSourceInfo,
  FreshnessStatus,
} from './types'

export type RatesSourceInfo = {
  label: string
  asOf: string | null
  warnings: string[]
}

export type FxSourceInfo = {
  label: string
  asOf: string | null
  warnings: string[]
  freshness: string
}

export default function MarketWatchPage() {
  const [activeTab, setActiveTab] = useState<TabId>('pulse')

  // Data states
  const [metrics, setMetrics] = useState<MarketMetric[]>([])
  const [signals, setSignals] = useState<MarketSignal[]>([])
  const [rates, setRates] = useState<RateSnapshot[]>([])
  const [liquidityEvents, setLiquidityEvents] = useState<LiquidityEvent[]>([])
  const [ratesSource, setRatesSource] = useState<RatesSourceInfo>({
    label: 'Market sources',
    asOf: null,
    warnings: [],
  })
  const [fxPairs, setFxPairs] = useState<FxPair[]>([])
  const [gbaSignals, setGbaSignals] = useState<GbaFundingSignal[]>([])
  const [exposureNotes, setExposureNotes] = useState<ExposureNote[]>([])
  const [fxSource, setFxSource] = useState<FxSourceInfo | null>(null)
  const [benchmarks, setBenchmarks] = useState<SectorBenchmarkItem[]>([])
  const [sectorSource, setSectorSource] = useState<SectorSourceInfo | null>(null)
  const [commodities, setCommodities] = useState<CommodityExposure[]>([])
  const [commoditySource, setCommoditySource] = useState<CommoditySourceInfo | null>(null)
  const [scenarios, setScenarios] = useState<StressScenario[]>([])
  const [stressSource, setStressSource] = useState<StressSourceInfo | null>(null)
  const [sources, setSources] = useState<SourceStatusItem[]>([])
  const [loading, setLoading] = useState(true)

  // Auto-refresh states
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date())
  const [refreshing, setRefreshing] = useState(false)

  async function loadData(isSilent = false) {
    if (!isSilent) setRefreshing(true)
    try {
      const [
        overview,
        ratesLiq,
        fx,
        sectors,
        comms,
        stress,
        sourceStatus,
      ] = await Promise.all([
        getMarketOverview(),
        getRatesLiquidity(),
        getFxGba(),
        getSectorBenchmarks(),
        getCommodities(),
        getStressSignals(),
        getMarketSourceStatus(),
      ])

      setMetrics(overview.metrics)
      setSignals(overview.signals)
      setRates(ratesLiq.rates)
      setLiquidityEvents(ratesLiq.liquidityEvents)
      if (ratesLiq.ratesSource) {
        setRatesSource(ratesLiq.ratesSource)
      }
      setFxPairs(fx.fxPairs)
      setGbaSignals(fx.gbaSignals)
      if (fx.exposureNotes) {
        setExposureNotes(fx.exposureNotes)
      }
      if (fx.fxSource) {
        setFxSource(fx.fxSource)
      }
      setBenchmarks(sectors.benchmarks)
      if (sectors.sectorSource) {
        setSectorSource(sectors.sectorSource)
      }
      setCommodities(comms.commodities)
      if (comms.commoditySource) {
        setCommoditySource(comms.commoditySource)
      }
      setScenarios(stress.scenarios)
      if (stress.stressSource) {
        setStressSource(stress.stressSource)
      }
      setSources(sourceStatus.sources)
      setLastRefreshed(new Date())
    } catch (error) {
      console.error('Failed to load market watch data', error)
    } finally {
      if (!isSilent) {
        setRefreshing(false)
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Auto-refresh interval setup
  useEffect(() => {
    const refreshSecs = Number(import.meta.env.VITE_MARKET_WATCH_REFRESH_SECONDS) || 300
    const intervalMs = refreshSecs * 1000
    const timer = setInterval(() => {
      loadData(true)
    }, intervalMs)
    return () => clearInterval(timer)
  }, [])

  const handleManualRefresh = async () => {
    await loadData(false)
    try {
      await refreshData('all')
    } catch (err) {
      console.warn('Backend refresh trigger failed', err)
    }
  }

  // Derive metrics dynamically based on active data and source status
  const derivedMetrics = metrics.map((m) => {
    if (m.id === 'rate-pressure') {
      const isFallback = ratesSource.label.toLowerCase().includes('workspace') || ratesSource.warnings.length > 0
      const HIBOR_1M = rates.find(r => r.label.includes('1M HIBOR') || r.label.includes('HIBOR 1-Month'))
      return {
        ...m,
        value: HIBOR_1M ? HIBOR_1M.value : m.value,
        interpretation: isFallback ? 'Floating-rate debt is cost-sensitive.' : 'HKMA base reference rates connected.',
        severity: isFallback ? ('Caution' as const) : ('High' as const),
        freshness: isFallback ? ('Workspace' as const) : ('Daily' as const),
        source: ratesSource.label,
      }
    }
    if (m.id === 'fx-gba-signal') {
      const isFallback = !fxSource || fxSource.label.toLowerCase().includes('workspace') || fxSource.label.toLowerCase().includes('local seed')
      const cnyHkd = fxPairs.find(p => p.pair === 'CNY/HKD')
      return {
        ...m,
        label: 'CNY/HKD',
        value: cnyHkd ? `${cnyHkd.rate}` : m.value,
        interpretation: isFallback ? 'CNY operations watch.' : 'Frankfurter FX provider connected.',
        severity: isFallback ? ('Neutral' as const) : ('Caution' as const),
        freshness: fxSource ? (fxSource.freshness as FreshnessStatus) : ('Workspace' as const),
        source: fxSource ? fxSource.label : 'Fixture',
      }
    }
    if (m.id === 'sector-health') {
      const isFallback = !sectorSource || sectorSource.label.toLowerCase().includes('workspace') || sectorSource.warnings.length > 0
      return {
        ...m,
        value: sectorSource ? `${sectorSource.sectorHealth.score}/100` : m.value,
        interpretation: sectorSource ? sectorSource.sectorHealth.label : m.interpretation,
        severity: sectorSource ? sectorSource.sectorHealth.severity : m.severity,
        freshness: isFallback ? ('Workspace' as const) : ('Monthly' as const),
        source: sectorSource ? sectorSource.label : 'Fixture',
      }
    }
    if (m.id === 'funding-conditions') {
      const isFallback = !stressSource || stressSource.label.toLowerCase().includes('workspace') || stressSource.warnings.length > 0
      return {
        ...m,
        freshness: isFallback ? ('Workspace' as const) : ('Daily' as const),
        source: stressSource ? stressSource.label : 'Fixture',
      }
    }
    return m
  })

  return (
    <div className="w-full">
      <PageHeader
        title="Market Watch"
        titleAddon={
          <InfoTooltip
            label="About Market Watch"
            content="Track rates, FX, sector benchmarks, and market pressure signals that may affect cashflow and funding decisions."
          />
        }
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-[10px] text-softform-text-muted font-semibold mr-2 uppercase tracking-wider">
              Last updated: {lastRefreshed.toLocaleTimeString()} {refreshing && '(refreshing...)'}
            </span>
            <button
              onClick={handleManualRefresh}
              disabled={refreshing}
              className={`rounded-full bg-white/70 hover:bg-white px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-softform-navy-950 shadow-sm border border-softform-navy-950/10 transition-all duration-200 active:scale-95 ${
                refreshing ? 'opacity-50 cursor-wait' : 'hover:-translate-y-0.5 hover:shadow-floating-panel'
              }`}
            >
              Refresh data
            </button>
            <button
              onClick={() => alert('Export snapshot: Workspace integration pending. Company financial records are required before export is enabled.')}
              className="softform-pill rounded-full px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-softform-navy-950/60 cursor-not-allowed border border-softform-navy-950/10 transition-all duration-200"
            >
              Export snapshot
            </button>
            <button
              onClick={() => alert('Configure watchlist: Workspace integration pending. Watchlist options will be enabled upon loading financial records.')}
              className="rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] opacity-60 cursor-not-allowed px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-white/80 shadow-navy-card border border-white/10 transition-all duration-200"
            >
              Configure watchlist
            </button>
          </div>
        }
      />

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="text-sm font-medium text-softform-text-muted">
            Loading market intelligence...
          </div>
        </div>
      ) : (
        <>
          <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {derivedMetrics.map((metric) => (
              <MarketMetricCard key={metric.id} metric={metric} />
            ))}
          </div>

          <MarketWatchTabs
            activeTab={activeTab}
            onChange={setActiveTab}
            tabs={[
              { id: 'pulse', label: 'Market Pulse', icon: Activity },
              { id: 'rates', label: 'Rates & Liquidity', icon: TrendingUp },
              { id: 'fx', label: 'FX & GBA', icon: Globe },
              { id: 'sectors', label: 'Sector Benchmarks', icon: PieChart },
              { id: 'commodities', label: 'Commodities', icon: Box },
              { id: 'stress', label: 'Stress Signals', icon: AlertTriangle },
            ]}
          />

          <div className="min-h-[400px]">
            {activeTab === 'pulse' && (
              <MarketPulseTab signals={signals} sources={sources} />
            )}
            {activeTab === 'rates' && (
              <RatesLiquidityTab
                rates={rates}
                liquidityEvents={liquidityEvents}
                ratesSource={ratesSource}
              />
            )}
            {activeTab === 'fx' && (
              <FxGbaTab
                fxPairs={fxPairs}
                gbaSignals={gbaSignals}
                exposureNotes={exposureNotes}
                fxSource={fxSource}
              />
            )}
            {activeTab === 'sectors' && (
              <SectorBenchmarksTab
                benchmarks={benchmarks}
                sectorSource={sectorSource}
              />
            )}
            {activeTab === 'commodities' && (
              <CommoditiesTab commodities={commodities} commoditySource={commoditySource} />
            )}
            {activeTab === 'stress' && (
              <StressSignalsTab scenarios={scenarios} stressSource={stressSource} />
            )}
          </div>
        </>
      )}
    </div>
  )
}

