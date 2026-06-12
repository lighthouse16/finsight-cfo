/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useMemo } from 'react'
import { Landmark, ShieldCheck, TrendingUp, Loader2, RefreshCw, Play } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import ServiceErrorState from '../../components/platform/ServiceErrorState'
import NavyHeroSection from '../../components/platform/NavyHeroSection'
import PageLoadingSkeleton from '../../components/platform/PageLoadingSkeleton'
import WorkflowFooter from '../../components/platform/WorkflowFooter'
import { getCreditScore, getAdvisoryFacilityStructures } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getFundingChannelRanking, getMarketFundingIntelligence } from '../market-watch/api/marketWatchApi'
import { createAndFetchMockCdiData } from '../cdi/cdiApi'
import type { FacilityStructuringResponse } from '../advisory-blueprint/types'
import type { FundingChannelRankingResponse } from '../market-watch/types'
import type { CdiConsentSession, CdiMockDataResponse } from '../cdi/cdiApi'
import { formatHKD, formatPercent, formatBand, bandVariant } from '../../lib/formatters'
import RunMetadataBadge from '../../components/platform/RunMetadataBadge'
import { fetchLatestRunSafe, triggerAnalysisRun } from '../../lib/workspaceRunHelpers'

import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'

function fitTone(value?: string) {
  if (value === 'strong_fit' || value === 'strong' || value === 'clear') return 'bg-emerald-500/10 text-emerald-700'
  if (value === 'moderate_fit' || value === 'adequate' || value === 'moderate') return 'bg-softform-mist-100 text-softform-teal-deep'
  return 'bg-softform-cream text-softform-amber-500'
}

export default function FundingStrategyPage() {
  const [creditScore, setCreditScore] = useState<any>(null)
  const [ranking, setRanking] = useState<FundingChannelRankingResponse | null>(null)
  const [facilities, setFacilities] = useState<FacilityStructuringResponse | null>(null)
  const [cdiConsent, setCdiConsent] = useState<CdiConsentSession | null>(null)
  const [cdiData, setCdiData] = useState<CdiMockDataResponse | null>(null)
  const [marketFunding, setMarketFunding] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasSnapshotButNoRun, setHasSnapshotButNoRun] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const loadStrategy = async () => {
    setLoading(true)
    setError(null)
    setHasSnapshotButNoRun(false)
    try {
      // Fetch market-funding intelligence in parallel
      const marketFundingRes = await getMarketFundingIntelligence().catch(() => null)
      setMarketFunding(marketFundingRes)

      // 1. Check legacy/direct funding channels to determine if we have insufficient data
      const legacyScore = await getCreditScore().catch(() => null)
      const legacyRanking = await getFundingChannelRanking().catch(() => null)
      
      if (
        (legacyScore && (legacyScore as any).status === 'insufficient_data') ||
        (legacyRanking && (legacyRanking as any).status === 'insufficient_data')
      ) {
        setCreditScore(legacyScore || { status: 'insufficient_data' })
        return
      }

      // 2. We have workspace and snapshot! Now check for latest run of type funding_strategy
      const workspaceId = localStorage.getItem('active_workspace_id')
      if (workspaceId) {
        const latestRun = await fetchLatestRunSafe(workspaceId, 'funding_strategy')
        if (latestRun) {
          const runRanking = {
            ...latestRun.results,
            run_metadata: {
              id: latestRun.id,
              runId: latestRun.id,
              snapshotId: latestRun.snapshotId,
              status: latestRun.status,
              runType: latestRun.runType,
              createdAt: latestRun.createdAt,
              logicVersion: latestRun.logicVersion,
              warningsCount: latestRun.warnings?.length ?? 0
            }
          }
          
          // Load other requirements for strategy dashboard in parallel
          const [facilityContext, scoreData] = await Promise.all([
            getAdvisoryFacilityStructures().catch(() => null),
            getCreditScore().catch(() => null),
          ])

          if (scoreData) {
            const cdiContext = await createAndFetchMockCdiData({
              companyId: scoreData?.companyId ?? 'demo-company',
              companyName: scoreData?.companyName ?? 'Demo Trading Limited',
            }).catch(() => null)
            setCdiConsent(cdiContext?.consent ?? null)
            setCdiData(cdiContext?.data ?? null)
          }

          setRanking(runRanking)
          setCreditScore(scoreData)
          setFacilities(facilityContext)
        } else {
          // Snapshot exists, but no run yet
          setHasSnapshotButNoRun(true)
          setCreditScore(legacyScore)
          setRanking(legacyRanking)
        }
      } else {
        setCreditScore({
          status: 'insufficient_data',
          missingRequirements: ['Please select or create a workspace in the Data Room.'],
          nextActions: ['Go to the Data Room']
        })
      }
    } catch (e) {
      console.error('Funding strategy load failed', e)
      setError('Funding Strategy is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const handleRunAnalysis = async () => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return
    setIsRunning(true)
    try {
      await triggerAnalysisRun(workspaceId, 'funding_strategy')
      await loadStrategy()
    } catch (err: any) {
      console.error('Failed to trigger funding strategy run:', err)
      alert(`Failed to run funding strategy: ${err.message || err}`)
    } finally {
      setIsRunning(false)
    }
  }

  useEffect(() => {
    loadStrategy()
  }, [])

  const isInsufficientData = useMemo(() => {
    return creditScore && creditScore.status === 'insufficient_data'
  }, [creditScore])

  if (loading) {
    return <PageLoadingSkeleton layout="funding" />
  }

  if (isInsufficientData) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Funding Strategy"
          subtitle="Compare channel fit, facility structures, rate context, consent-based CDI signals, and cross-border considerations from the finance workflow."
        />
        <WorkspaceInsufficientDataState
          missingRequirements={creditScore?.missingRequirements}
          nextActions={creditScore?.nextActions}
        />
      </div>
    )
  }

  if (hasSnapshotButNoRun) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Funding Strategy"
          subtitle="Compare channel fit, facility structures, rate context, consent-based CDI signals, and cross-border considerations from the finance workflow."
        />
        <div className="flex flex-col items-center justify-center p-8 sm:p-12 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 flex items-center justify-center text-softform-teal-deep dark:text-softform-aqua-300">
            <Landmark size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Funding Strategy Analysis Needed</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              An active workspace snapshot exists, but no funding strategy analysis run has been triggered for this snapshot yet. Run the analysis to generate ranking.
            </p>
          </div>
          <button
            onClick={handleRunAnalysis}
            disabled={isRunning}
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-sm font-semibold rounded-full shadow-sm disabled:opacity-50 transition-colors"
          >
            {isRunning ? (
              <Loader2 size={16} className="animate-spin text-softform-teal-deep dark:text-softform-aqua-300" />
            ) : (
              <Play size={16} fill="currentColor" className="ml-0.5" />
            )}
            <span>Run Funding Strategy Analysis</span>
          </button>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <ServiceErrorState
        message={error}
        onRetry={loadStrategy}
      />
    )
  }

  const topChannel = ranking?.channels?.find((channel) => channel.key === ranking.topChannelKey) ?? ranking?.channels?.[0]
  const topFacilities = facilities?.candidates?.slice(0, 3) ?? []

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Funding Strategy"
        subtitle="Compare channel fit, facility structures, rate context, consent-based CDI signals, and cross-border considerations from the finance workflow."
        chip={
          <StatusChip variant={bandVariant(creditScore?.fundingReadiness)}>
            {creditScore ? formatBand(creditScore.fundingReadiness) : 'Context only'}
          </StatusChip>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <RunMetadataBadge metadata={ranking?.run_metadata} />
        {ranking?.run_metadata && (
          <button
            onClick={handleRunAnalysis}
            disabled={isRunning}
            className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-xs font-semibold rounded-full shadow-sm transition-colors disabled:opacity-50"
          >
            {isRunning ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <RefreshCw size={12} />
            )}
            <span>Rerun Analysis</span>
          </button>
        )}
      </div>

      {ranking?.warnings?.some(w => w.toLowerCase().includes('fixture')) && (
        <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 text-xs text-amber-800 flex items-start gap-2.5">
          <span className="shrink-0 mt-0.5 text-amber-600">⚠️</span>
          <div>
            <span className="font-semibold">Fixture Data Warning:</span>{' '}
            {ranking.warnings.find(w => w.toLowerCase().includes('fixture'))}
          </div>
        </div>
      )}

      {/* Cockpit Strategy Bridge Hero Section in Premium Navy Contrast Card */}
      <NavyHeroSection
        eyebrow="Strategy bridge"
        title={topChannel ? topChannel.label : 'Funding channel context'}
        description={ranking?.explanation ?? 'Funding Strategy combines readiness scorecard context, channel ranking, cross-border funding context, consent-based CDI signals, and facility structures.'}
        badges={topChannel && (
          <div className="flex flex-wrap gap-2 pt-1">
            <span className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] ${fitTone(topChannel.fitBand)}`}>
              {formatBand(topChannel.fitBand)}
            </span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white">
              Score {topChannel.score}
            </span>
          </div>
        )}
        aside={
          <div className="flex flex-wrap items-center justify-around gap-6 bg-white/5 border border-white/10 rounded-[24px] p-6 backdrop-blur-md">
            <div className="space-y-2.5 w-full">
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Readiness score</span>
                <span className="text-sm font-bold text-white tabular-finance">{creditScore?.compositeScore ?? 'N/A'}</span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Interest coverage</span>
                <span className="text-sm font-bold text-white tabular-finance">{creditScore ? formatBand(creditScore.pdProxyBand) : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">CDI consent</span>
                <span className="text-sm font-bold text-white tabular-finance">{formatBand(cdiConsent?.status ?? 'unavailable')}</span>
              </div>
            </div>
          </div>
        }
      />


      {/* CDI Trust Bridge */}
      {cdiData && (
        <SectionBlock
          title="CDI Trust Bridge & Digital Collateral"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">{formatBand(cdiConsent?.status ?? 'authorized')}</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-4">
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Eligible invoices</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatHKD(cdiData.receivablesSignal.eligibleInvoiceValue)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Verified pool</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatHKD(cdiData.receivablesSignal.verifiedInvoiceValue)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Buyer concentration</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatPercent(cdiData.receivablesSignal.topBuyerConcentration)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Bureau band</p>
              <p className="mt-1 text-lg font-semibold text-softform-navy-950">{formatBand(cdiData.creditBureauSignal.bureauBand)}</p>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2 pt-2">
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">Funding implications</p>
              {cdiData.fundingImplications.map((item) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Signal:</strong> {item}
                </p>
              ))}
            </div>
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-amber-500">Risk implications</p>
              {cdiData.riskImplications.map((item) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Watch:</strong> {item}
                </p>
              ))}
            </div>
          </div>
        </SectionBlock>
      )}

      {/* Market Timing & Red Flags */}
      {marketFunding && (
        <SectionBlock
          title="Market Research & Timing Signals"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={
            <StatusChip variant="signal">
              Timing Index: {marketFunding.golden_timing_index}/100
            </StatusChip>
          }
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Rates & Spread Analysis */}
            <div className="space-y-4 rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-softform-navy-950">Rates & Spread Analysis</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl border border-white bg-white/50 p-3">
                  <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">1M HIBOR</p>
                  <p className="mt-1 text-base font-bold text-softform-navy-950">{marketFunding.current_hibor.toFixed(2)}%</p>
                </div>
                <div className="rounded-xl border border-white bg-white/50 p-3">
                  <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">1Y LPR Proxy</p>
                  <p className="mt-1 text-base font-bold text-softform-navy-950">{marketFunding.lpr_or_proxy_rate.toFixed(2)}%</p>
                </div>
                <div className="rounded-xl border border-white bg-white/50 p-3">
                  <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Spread (HIBOR - LPR)</p>
                  <p className="mt-1 text-base font-bold text-softform-navy-950">+{marketFunding.hibor_lpr_spread.toFixed(2)}%</p>
                </div>
                <div className="rounded-xl border border-white bg-white/50 p-3">
                  <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">FX Hedging Cost</p>
                  <p className="mt-1 text-base font-bold text-softform-navy-950">{marketFunding.fx_hedging_cost_proxy.toFixed(2)}%</p>
                </div>
              </div>
              <div className="rounded-xl bg-softform-teal-deep/5 border border-softform-teal-deep/10 p-3 text-xs">
                <span className="font-semibold text-softform-teal-deep uppercase tracking-wider text-[10px] block mb-1">Spread Signal</span>
                <p className="text-softform-navy-950 leading-relaxed">
                  The current spread is <strong className="capitalize">{marketFunding.spread_signal}</strong> for GBA cross-border funding options.
                </p>
              </div>
            </div>

            {/* Market Red Flags */}
            <div className="space-y-4 rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-softform-navy-950">Market Red Flags</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-2">
                  <span className="text-xs text-softform-text-primary">Quarter-End Window Dressing</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${marketFunding.market_red_flags.window_dressing ? 'bg-red-500/10 text-red-600' : 'bg-emerald-500/10 text-emerald-600'}`}>
                    {marketFunding.market_red_flags.window_dressing ? '🚨 Active' : '✓ Normal'}
                  </span>
                </div>
                <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-2">
                  <span className="text-xs text-softform-text-primary">Mega IPO Liquidity Drain</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${marketFunding.market_red_flags.mega_ipo_liquidity ? 'bg-red-500/10 text-red-600' : 'bg-emerald-500/10 text-emerald-600'}`}>
                    {marketFunding.market_red_flags.mega_ipo_liquidity ? '🚨 Active' : '✓ Normal'}
                  </span>
                </div>
                <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-2">
                  <span className="text-xs text-softform-text-primary">Yield Curve Inversion</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${marketFunding.market_red_flags.inverted_curve ? 'bg-red-500/10 text-red-600' : 'bg-emerald-500/10 text-emerald-600'}`}>
                    {marketFunding.market_red_flags.inverted_curve ? '🚨 Inverted' : '✓ Normal'}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-1">
                  <span className="text-xs text-softform-text-primary">High Rate Environment</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${marketFunding.market_red_flags.high_rate_environment ? 'bg-red-500/10 text-red-600' : 'bg-emerald-500/10 text-emerald-600'}`}>
                    {marketFunding.market_red_flags.high_rate_environment ? '🚨 High' : '✓ Low'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </SectionBlock>
      )}

      {/* Ranked Funding Channels */}
      {marketFunding && marketFunding.funding_channels && marketFunding.funding_channels.length > 0 && (
        <SectionBlock
          title="Ranked Funding Channels & SFGS Options"
          icon={<Landmark size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">Policy Mapping</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="space-y-6">
            {marketFunding.funding_channels.map((channel: any, idx: number) => {
              const isSfgs = channel.name.includes("SFGS")
              return (
                <div key={idx} className="rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm hover:shadow-md transition duration-200 space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-softform-teal-deep text-white text-xs font-bold shrink-0">
                        {idx + 1}
                      </span>
                      <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{channel.name}</h3>
                      {isSfgs && (
                        <span className="rounded bg-softform-teal-deep/10 text-softform-teal-deep text-[10px] font-semibold px-2 py-0.5 uppercase tracking-wider">
                          Govt Guaranteed
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-softform-text-primary">
                      <span>Max Limit: <strong className="text-softform-navy-950 font-bold">{formatHKD(channel.max_amount_hkd)}</strong></span>
                      <span className="h-3 w-px bg-softform-navy-950/15" />
                      <span>Tenor: <strong className="text-softform-navy-950 font-semibold">{channel.tenor}</strong></span>
                    </div>

                    {/* Source metadata + mode badge */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] text-softform-text-muted">
                        Source: <span className="font-medium text-slate-700 dark:text-slate-300">{channel.sourceName || 'Unknown'}</span>
                      </span>
                      {channel.sourceMode && (
                        <span className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider ${
                          channel.sourceMode === 'live' || channel.sourceMode === 'provider_configured'
                            ? 'bg-emerald-500/10 text-emerald-700'
                            : channel.sourceMode === 'fixture'
                            ? 'bg-amber-500/10 text-amber-800'
                            : 'bg-softform-navy-900/10 text-softform-text-secondary'
                        }`}>
                          {channel.sourceMode.replace('_', ' ')}
                        </span>
                      )}
                    </div>

                    {/* Fit Score Progress Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] font-medium text-softform-text-secondary">
                        <span>Fit Score</span>
                        <span className="font-semibold">{channel.score} / 100</span>
                      </div>
                      <div className="w-full h-1.5 bg-softform-text-muted/15 rounded-full overflow-hidden">
                        <div className="h-full bg-softform-teal-500" style={{ width: `${channel.score}%` }} />
                      </div>
                    </div>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 text-xs border-t border-b border-softform-navy-950/5 py-3 my-2">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider mb-0.5">Estimated Cost</span>
                      <span className="text-softform-navy-950 font-medium">{channel.estimated_cost_band}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider mb-0.5">Speed</span>
                      <span className="text-softform-navy-950 font-medium">{channel.speed_band}</span>
                    </div>
                    <div className="md:col-span-2 lg:col-span-1">
                      <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider mb-0.5">Eligibility</span>
                      <span className="text-softform-navy-950">{channel.eligibility_notes}</span>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2 text-xs">
                    <div className="space-y-1.5 bg-emerald-500/5 border border-emerald-500/10 rounded-xl p-3">
                      <span className="text-[10px] font-semibold text-emerald-800 uppercase tracking-wider block">Pros</span>
                      <ul className="list-disc list-inside space-y-0.5 text-emerald-700">
                        {channel.pros.map((pro: string, i: number) => (
                          <li key={i}>{pro}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="space-y-1.5 bg-red-500/5 border border-red-500/10 rounded-xl p-3">
                      <span className="text-[10px] font-semibold text-red-800 uppercase tracking-wider block">Cons</span>
                      <ul className="list-disc list-inside space-y-0.5 text-red-700">
                        {channel.cons.map((con: string, i: number) => (
                          <li key={i}>{con}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="bg-softform-mist-50 border border-softform-navy-950/5 rounded-xl p-3 text-xs leading-relaxed text-softform-text-primary">
                    <strong className="text-softform-navy-950">Reason:</strong> {channel.recommendation_reason}
                  </div>

                  {channel.matchedProducts && channel.matchedProducts.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-softform-navy-950/5 space-y-2">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">
                        Matched Lender Products
                      </p>
                      <div className="space-y-2.5">
                        {channel.matchedProducts.map((prod) => (
                          <div key={prod.product_id} className="text-[11px] leading-relaxed bg-white/20 dark:bg-slate-900/20 rounded-xl p-2.5 border border-white/30 dark:border-slate-800/30">
                            <div className="flex justify-between items-start gap-1 font-medium text-softform-navy-950">
                              <span>{prod.product_name}</span>
                              <span className="text-[9px] text-softform-text-muted uppercase tracking-wider">
                                {prod.provider}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-x-2 gap-y-1 mt-1 text-[10px] text-softform-text-secondary">
                              <div><span className="font-medium text-softform-text-muted">Limit:</span> {prod.limits}</div>
                              <div><span className="font-medium text-softform-text-muted">Tenor:</span> {prod.tenor_range}</div>
                              <div className="col-span-2"><span className="font-medium text-softform-text-muted">Collateral:</span> {prod.collateral_requirements}</div>
                            </div>
                            {prod.caveats && (
                              <div className="mt-1 text-[9px] text-softform-text-muted leading-snug italic border-l border-softform-teal-deep/30 pl-1.5">
                                Caveat: {prod.caveats}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </SectionBlock>
      )}

      {/* Candidate Facility Structures */}
      {topFacilities.length > 0 && (
        <SectionBlock
          title="Candidate Facility Structures"
          icon={<Landmark size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Advisory Fit</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-3">
            {topFacilities.map((facility) => (
              <div key={facility.facilityKey} className="rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm hover-lift space-y-4 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{facility.label}</h3>
                    <span className={`shrink-0 rounded px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider ${fitTone(facility.fitAssessment.fitBand)}`}>
                      {formatBand(facility.fitAssessment.fitBand)}
                    </span>
                  </div>
                  <div className="space-y-2 text-xs text-softform-text-secondary bg-white/30 rounded-xl p-3 border border-white/40">
                    <div className="flex justify-between border-b border-softform-navy-950/5 pb-1">
                      <span className="font-medium text-softform-text-secondary">Est. limit</span>
                      <span className="tabular-finance font-bold text-softform-navy-950">{formatHKD(facility.estimatedLimit)}</span>
                    </div>
                    {facility.estimatedPricingBps !== undefined && facility.estimatedPricingBps !== null && (
                      <div className="flex justify-between">
                        <span className="font-medium text-softform-text-secondary">Pricing</span>
                        <span className="tabular-finance font-bold text-softform-navy-950">{facility.estimatedPricingBps} bps</span>
                      </div>
                    )}
                  </div>
                  <p className="text-xs leading-relaxed text-softform-text-secondary">{facility.purpose}</p>
                </div>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* Disclaimer */}
      {marketFunding && (
        <div className="rounded-[22px] border border-softform-navy-950/10 bg-softform-navy-950/[0.025] p-5 text-xs text-softform-text-secondary leading-relaxed">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-softform-navy-950/10 text-[10px] font-bold text-softform-navy-700 shrink-0 mt-0.5">i</span>
            <p className="font-medium">{marketFunding.advisory_disclaimer}</p>
          </div>
        </div>
      )}

      {/* Navigation Footer */}
      <WorkflowFooter
        title="Convert strategy into advisor-ready actions"
        description="Use Advisory Blueprint to consolidate this strategy into stress context, facility rationale, and next data requirements."
        linkTo="/platform/advisory-blueprint"
        linkLabel="Open Advisory Blueprint"
      />
    </div>
  )
}
