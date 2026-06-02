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
  const [scenarios, setScenarios] = useState<StressScenario[]>([])
  const [sources, setSources] = useState<SourceStatusItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
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
        setScenarios(stress.scenarios)
        setSources(sourceStatus.sources)
      } catch (error) {
        console.error('Failed to load market watch data', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

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
          <>
            <button className="softform-pill rounded-full px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-softform-navy-950 transition-all duration-200 hover:bg-white/90 hover:shadow-floating-panel active:scale-95">
              Export snapshot
            </button>
            <button className="rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-white shadow-navy-card border border-white/10 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-floating-panel active:translate-y-0">
              Configure watchlist
            </button>
          </>
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
            {metrics.map((metric) => (
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
              <CommoditiesTab commodities={commodities} />
            )}
            {activeTab === 'stress' && (
              <StressSignalsTab scenarios={scenarios} />
            )}
          </div>
        </>
      )}
    </div>
  )
}
