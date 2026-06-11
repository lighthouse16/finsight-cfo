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
import { getCrossBorderFundingContext, getFundingChannelRanking } from '../market-watch/api/marketWatchApi'
import { createAndFetchMockCdiData } from '../cdi/cdiApi'
import type { FacilityStructuringResponse } from '../advisory-blueprint/types'
import type { CrossBorderFundingContextResponse, FundingChannelItem, FundingChannelRankingResponse } from '../market-watch/types'
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
  const [crossBorder, setCrossBorder] = useState<CrossBorderFundingContextResponse | null>(null)
  const [facilities, setFacilities] = useState<FacilityStructuringResponse | null>(null)
  const [cdiConsent, setCdiConsent] = useState<CdiConsentSession | null>(null)
  const [cdiData, setCdiData] = useState<CdiMockDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasSnapshotButNoRun, setHasSnapshotButNoRun] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const loadStrategy = async () => {
    setLoading(true)
    setError(null)
    setHasSnapshotButNoRun(false)
    try {
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
          const [crossBorderContext, facilityContext, scoreData] = await Promise.all([
            getCrossBorderFundingContext().catch(() => null),
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
          setCrossBorder(crossBorderContext)
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

      {/* Funding Channel Ranking */}
      {ranking && ranking.channels.length > 0 && (
        <SectionBlock
          title="Funding Channel Ranking"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">Context Ranking</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-3">
            {ranking.channels.slice(0, 3).map((channel: FundingChannelItem) => {
              const rankBadgeColor =
                channel.rank === 1 ? 'bg-amber-500/10 text-amber-600 border-amber-500/20' :
                channel.rank === 2 ? 'bg-slate-500/10 text-slate-600 border-slate-500/20' :
                'bg-orange-500/10 text-orange-600 border-orange-500/20'
              const rankLabel = channel.rank === 1 ? '1st' : channel.rank === 2 ? '2nd' : '3rd'

              return (
                <div key={channel.key} className="rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm hover-lift space-y-4 flex flex-col justify-between">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-bold ${rankBadgeColor}`}>
                          {rankLabel}
                        </span>
                        <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{channel.label}</h3>
                      </div>
                      <span className={`shrink-0 rounded px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider ${fitTone(channel.fitBand)}`}>
                        {formatBand(channel.fitBand)}
                      </span>
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

                    <p className="text-xs leading-relaxed text-softform-text-secondary">{channel.rationale}</p>
                  </div>

                  <div className="space-y-2 border-t border-softform-navy-950/5 pt-3 mt-2">
                    {channel.supportingSignals.slice(0, 2).map((signal, idx) => (
                      <p key={idx} className="text-[11px] leading-relaxed text-softform-text-secondary">
                        <strong className="text-softform-navy-950 font-semibold">Signal:</strong> {signal}
                      </p>
                    ))}
                  </div>
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

      {/* Cross-Border Funding Context */}
      {crossBorder && (
        <SectionBlock
          title="Cross-Border Funding Context"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">HKD / RMB</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <p className="text-sm leading-relaxed text-softform-text-secondary">{crossBorder.explanation}</p>
          <div className="grid gap-4 sm:grid-cols-3 pt-2">
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">HKD reference</p>
              <p className="mt-1 text-sm font-semibold text-softform-navy-950">{crossBorder.hkdFundingReference.displayValue}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">RMB reference</p>
              <p className="mt-1 text-sm font-semibold text-softform-navy-950">{crossBorder.rmbFundingReference.displayValue}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Spread band</p>
              <p className="mt-1 text-sm font-semibold text-softform-navy-950">{formatBand(crossBorder.spreadBand)}</p>
            </div>
          </div>
        </SectionBlock>
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
