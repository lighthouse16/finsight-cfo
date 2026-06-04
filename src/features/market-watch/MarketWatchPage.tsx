import { useEffect, useState, useMemo } from 'react'
import { Activity, AlertTriangle, Box, Globe, PieChart, TrendingUp, RotateCw } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { useSearchParams } from 'react-router-dom'
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
  getCompanyContext,
} from './api/marketWatchApi'
import CommoditiesTab from './components/CommoditiesTab'
import FxGbaTab from './components/FxGbaTab'
import MarketMetricCard from './components/MarketMetricCard'
import MarketPulseTab from './components/MarketPulseTab'
import MarketWatchTabs, { TabId } from './components/MarketWatchTabs'
import RatesLiquidityTab from './components/RatesLiquidityTab'
import SectorBenchmarksTab from './components/SectorBenchmarksTab'
import StressSignalsTab from './components/StressSignalsTab'
import { buildMarketWatchSnapshot, buildMarketWatchInsights } from './insights'
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
  CompanyContext,
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

const TAB_ID_TO_PARAM: Record<TabId, string> = {
  pulse: 'market-pulse',
  rates: 'rates-liquidity',
  fx: 'fx-gba',
  sectors: 'sector-benchmarks',
  commodities: 'commodities',
  stress: 'stress-signals',
}

const PARAM_TO_TAB_ID: Record<string, TabId> = {
  'market-pulse': 'pulse',
  'rates-liquidity': 'rates',
  'fx-gba': 'fx',
  'sector-benchmarks': 'sectors',
  commodities: 'commodities',
  'stress-signals': 'stress',
}

function tabFromParam(param: string | null): TabId {
  if (param && param in PARAM_TO_TAB_ID) return PARAM_TO_TAB_ID[param]
  return 'pulse'
}

export default function MarketWatchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = tabFromParam(searchParams.get('tab'))

  function handleTabChange(tabId: TabId) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('tab', TAB_ID_TO_PARAM[tabId])
      return next
    }, { replace: true })
  }

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
  const [companyContext, setCompanyContext] = useState<CompanyContext | null>(null)

  // Card-level loading state for executive signal cards
  const [cardLoadState, setCardLoadState] = useState<'initial' | 'updating' | 'idle'>('initial')

  // Minimum display duration helper to avoid flicker
  const MIN_CARD_LOAD_MS = 500
  async function withMinDuration<T>(fn: () => Promise<T>): Promise<T> {
    const start = Date.now()
    const result = await fn()
    const elapsed = Date.now() - start
    if (elapsed < MIN_CARD_LOAD_MS) {
      await new Promise(r => setTimeout(r, MIN_CARD_LOAD_MS - elapsed))
    }
    return result
  }

  // Auto-refresh states
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date())
  const [refreshing, setRefreshing] = useState(false)

  async function loadData(isSilent = false) {
    if (!isSilent) {
      setRefreshing(true)
      setCardLoadState(prev => prev === 'idle' ? 'updating' : 'initial')
    }
    try {
      let sectorParam: string | undefined = undefined
      let geoParam: string | undefined = undefined
      let companyIdParam: string | undefined = undefined

      await withMinDuration(async () => {
        const context = await getCompanyContext()
        if (context) {
          setCompanyContext(context)
          const profile = context.profile
          companyIdParam = profile.companyName
          sectorParam = profile.sector.toLowerCase().includes('electronics') ? 'electronics-import' : 'trading-distribution'
          geoParam = 'HK'
        }

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
          getSectorBenchmarks(sectorParam, geoParam),
          getCommodities(sectorParam, geoParam),
          getStressSignals(companyIdParam, sectorParam),
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
      })
    } catch (error) {
      console.error('Failed to load market watch data', error)
    } finally {
      if (!isSilent) {
        setRefreshing(false)
        setCardLoadState('idle')
      }
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Auto-refresh interval setup
  useEffect(() => {
    const refreshSecs = Number(import.meta.env.VITE_MARKET_WATCH_REFRESH_SECONDS) || 300
    const intervalMs = refreshSecs * 1000
    const timer = setInterval(() => {
      loadData(true)
    }, intervalMs)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleManualRefresh = async () => {
    await loadData(false)
    try {
      await refreshData('all')
    } catch (err) {
      console.warn('Backend refresh trigger failed', err)
    }
  }

  // Derive snapshot and insights from states using rules engine
  const snapshot = useMemo(() => {
    try {
      return buildMarketWatchSnapshot({
        companyContext: companyContext
          ? {
              profile: companyContext.profile,
              dataMode: companyContext.dataMode,
            }
          : null,
        ratesData: rates,
        fxData: fxPairs,
        sectorData: benchmarks,
        commoditiesData: commodities,
        stressData: scenarios,
        sourceStatus: sources,
        refreshedAt: lastRefreshed.toISOString(),
      })
    } catch (e) {
      console.error('Failed to build snapshot', e)
      return null
    }
  }, [companyContext, rates, fxPairs, benchmarks, commodities, scenarios, sources, lastRefreshed])

  const insights = useMemo(() => {
    if (!snapshot) return null
    try {
      return buildMarketWatchInsights(snapshot)
    } catch (e) {
      console.error('Failed to build insights', e)
      return null
    }
  }, [snapshot])

  // Derive metrics dynamically based on active data and source status
  const derivedMetrics = metrics.map((m) => {
    if (insights) {
      if (m.id === 'funding-conditions') {
        const card = insights.executiveCards.find(c => c.id === 'exec-card-funding')
        if (card) {
          const isFallback = !stressSource || stressSource.label.toLowerCase().includes('workspace') || stressSource.warnings.length > 0
          return {
            ...m,
            value: card.value,
            interpretation: card.description,
            severity: card.severity,
            freshness: isFallback ? ('Workspace' as const) : ('Daily' as const),
            source: stressSource ? stressSource.label : 'Fixture',
          }
        }
      }
      if (m.id === 'rate-pressure') {
        const card = insights.executiveCards.find(c => c.id === 'exec-card-rates')
        if (card) {
          const isFallback = ratesSource.label.toLowerCase().includes('workspace') || ratesSource.warnings.length > 0
          return {
            ...m,
            value: card.value,
            interpretation: card.description,
            severity: card.severity,
            freshness: isFallback ? ('Workspace' as const) : ('Daily' as const),
            source: ratesSource.label,
          }
        }
      }
      if (m.id === 'sector-health') {
        const card = insights.executiveCards.find(c => c.id === 'exec-card-sector')
        if (card) {
          const isFallback = !sectorSource || sectorSource.label.toLowerCase().includes('workspace') || sectorSource.warnings.length > 0
          return {
            ...m,
            value: card.value,
            interpretation: card.description,
            severity: card.severity,
            freshness: isFallback ? ('Workspace' as const) : ('Monthly' as const),
            source: sectorSource ? sectorSource.label : 'Fixture',
          }
        }
      }
      if (m.id === 'fx-gba-signal') {
        const card = insights.executiveCards.find(c => c.id === 'exec-card-fx')
        if (card) {
          return {
            ...m,
            label: 'FX / GBA Signal',
            value: card.value,
            interpretation: card.description,
            severity: card.severity,
            freshness: fxSource ? (fxSource.freshness as FreshnessStatus) : ('Workspace' as const),
            source: fxSource ? fxSource.label : 'Fixture',
          }
        }
      }
    }

    // Defensive fallback to existing logic if insights are missing
    if (m.id === 'rate-pressure') {
      const isFallback = ratesSource.label.toLowerCase().includes('workspace') || ratesSource.warnings.length > 0
      const HIBOR_1M = rates.find(r => r.label.includes('1M HIBOR') || r.label.includes('HIBOR 1-Month'))
      return {
        ...m,
        value: HIBOR_1M ? HIBOR_1M.value : m.value,
        interpretation: companyContext
          ? 'HIBOR rates affect HKD 6.5M floating-rate facility.'
          : (isFallback ? 'Floating-rate debt is cost-sensitive.' : 'HKMA base reference rates connected.'),
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
        interpretation: companyContext
          ? 'Payables: 38% CNY. Imports: 72% USD cost base.'
          : (isFallback ? 'CNY operations watch.' : 'Frankfurter FX provider connected.'),
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
        interpretation: companyContext
          ? 'DSO at 52d vs sector benchmark of 45d.'
          : (sectorSource ? sectorSource.sectorHealth.label : m.interpretation),
        severity: sectorSource ? sectorSource.sectorHealth.severity : m.severity,
        freshness: isFallback ? ('Workspace' as const) : ('Monthly' as const),
        source: sectorSource ? sectorSource.label : 'Fixture',
      }
    }
    if (m.id === 'funding-conditions') {
      const isFallback = !stressSource || stressSource.label.toLowerCase().includes('workspace') || stressSource.warnings.length > 0
      return {
        ...m,
        interpretation: companyContext
          ? 'Cash: HKD 3.2M. Debt service: HKD 420K/mo.'
          : m.interpretation,
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
            <span className="text-[10px] text-softform-text-muted font-medium mr-2 uppercase tracking-wider">
              Last updated: {lastRefreshed.toLocaleTimeString()} {refreshing && '(refreshing...)'}
            </span>
            <button
              onClick={handleManualRefresh}
              disabled={refreshing}
              className={`inline-flex items-center gap-2 rounded-full bg-white/70 hover:bg-white px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-softform-navy-950 shadow-sm border border-softform-navy-950/10 transition-all duration-200 active:scale-95 ${
                refreshing ? 'opacity-50 cursor-wait' : 'hover:-translate-y-0.5 hover:shadow-floating-panel'
              }`}
            >
              <RotateCw className={clsx("h-3 w-3 transition-transform", refreshing && "animate-spin")} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh data'}</span>
            </button>
            <button
              onClick={() => alert('Export snapshot: Workspace integration pending. Company financial records are required before export is enabled.')}
              className="softform-pill rounded-full px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-softform-navy-950/60 cursor-not-allowed border border-softform-navy-950/10 transition-all duration-200"
            >
              Export snapshot
            </button>
            <button
              onClick={() => alert('Configure watchlist: Workspace integration pending. Watchlist options will be enabled upon loading financial records.')}
              className="rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] opacity-60 cursor-not-allowed px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-white/80 shadow-navy-card border border-white/10 transition-all duration-200"
            >
              Configure watchlist
            </button>
          </div>
        }
      />

      {/*** Executive signal cards — always render grid, with loading/updating state ***/}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <AnimatePresence mode="popLayout">
          {cardLoadState !== 'idle'
            ? Array.from({ length: 4 }).map((_, i) => (
                <motion.div
                  key={`skeleton-${i}`}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                >
                  <MarketMetricCard
                    loading
                    loadingLabel={cardLoadState === 'updating' ? 'Updating insights...' : 'Calculating insights...'}
                  />
                </motion.div>
              ))
            : derivedMetrics.map((metric, idx) => (
                <motion.div
                  key={metric.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ 
                    duration: 0.24, 
                    ease: [0.22, 1, 0.36, 1],
                    delay: idx * 0.04 
                  }}
                >
                  <MarketMetricCard metric={metric} />
                </motion.div>
              ))}
        </AnimatePresence>
      </div>

      <>
        <MarketWatchTabs
            activeTab={activeTab}
            onChange={handleTabChange}
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
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
              >
                {activeTab === 'pulse' && (
                  <MarketPulseTab
                    signals={signals}
                    sources={sources}
                    profile={companyContext?.profile}
                    insights={insights || undefined}
                    loading={cardLoadState !== 'idle'}
                  />
                )}
                {activeTab === 'rates' && (
                  <RatesLiquidityTab
                    rates={rates}
                    liquidityEvents={liquidityEvents}
                    ratesSource={ratesSource}
                    profile={companyContext?.profile}
                    insights={insights || undefined}
                    loading={cardLoadState !== 'idle'}
                  />
                )}
                {activeTab === 'fx' && (
                  <FxGbaTab
                    fxPairs={fxPairs}
                    gbaSignals={gbaSignals}
                    exposureNotes={exposureNotes}
                    fxSource={fxSource}
                    profile={companyContext?.profile}
                    insights={insights || undefined}
                    loading={cardLoadState !== 'idle'}
                  />
                )}
                {activeTab === 'sectors' && (
                  <SectorBenchmarksTab
                    benchmarks={benchmarks}
                    sectorSource={sectorSource}
                    profile={companyContext?.profile}
                    insights={insights || undefined}
                    loading={cardLoadState !== 'idle'}
                  />
                )}
                {activeTab === 'commodities' && (
                  <CommoditiesTab
                    commodities={commodities}
                    commoditySource={commoditySource}
                    profile={companyContext?.profile}
                    insights={insights || undefined}
                    loading={cardLoadState !== 'idle'}
                  />
                )}
                {activeTab === 'stress' && (
                  <StressSignalsTab
                    scenarios={scenarios}
                    stressSource={stressSource}
                    profile={companyContext?.profile}
                    insights={insights || undefined}
                    loading={cardLoadState !== 'idle'}
                  />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </>
      </div>
    )
}
