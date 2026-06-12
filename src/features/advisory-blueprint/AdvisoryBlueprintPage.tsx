/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  BarChart3,
  ShieldCheck,
  AlertTriangle,
  Landmark,
  FolderOpen,
  RotateCw,
  CheckSquare,
  ArrowRight,
  Loader2,
  RefreshCw,
  Play,
  DollarSign,
  TrendingUp,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import SkeletonLoader from '../../components/platform/SkeletonLoader'
import SourceInfoTooltip from '../market-watch/components/SourceInfoTooltip'
import RunMetadataBadge from '../../components/platform/RunMetadataBadge'
import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'
import {
  getAdvisoryBlueprint,
  getAdvisoryRiskScore,
  getAdvisoryStressTests,
  getAdvisoryFacilityStructures,
  getFinancialPreviewAnalysis,
} from './api/advisoryBlueprintApi'
import { fetchLatestRunSafe, triggerAnalysisRun } from '../../lib/workspaceRunHelpers'
import {
  AdvisoryBlueprintResponse,
  UnifiedRiskScoreResult,
  StressTestingResponse,
  FacilityStructuringResponse,
} from './types'
import {
  loadWorkspaceAnalysisContext,
  WORKSPACE_ANALYSIS_CONTEXT_KEY,
  type WorkspaceAnalysisContext,
} from '../data-room/utils/workspaceAnalysisContext'
import type { FinancialAnalysisResponse } from '../market-watch/types'

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import FundingBlueprintHelper from './components/FundingBlueprintHelper'

// CDI & Market integration imports
import { createAndFetchMockCdiData } from '../cdi/cdiApi'
import type { CdiConsentSession, CdiMockDataResponse } from '../cdi/cdiApi'
import { getFundingChannelRanking, getCrossBorderFundingContext } from '../market-watch/api/marketWatchApi'
import type {
  FundingChannelRankingResponse,
  CrossBorderFundingContextResponse,
} from '../market-watch/types'
import { formatHKD, formatPercent, formatBand } from '../../lib/formatters'

export default function AdvisoryBlueprintPage() {
  const [blueprint, setBlueprint] = useState<AdvisoryBlueprintResponse | null>(null)
  const [riskScore, setRiskScore] = useState<UnifiedRiskScoreResult | null>(null)
  const [stressTests, setStressTests] = useState<StressTestingResponse | null>(null)
  const [facilityStructures, setFacilityStructures] = useState<FacilityStructuringResponse | null>(null)
  const [hasSnapshotButNoRun, setHasSnapshotButNoRun] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const [loading, setLoading] = useState<boolean>(true)
  const [loadingStep, setLoadingStep] = useState<string>('Preparing advisory blueprint...')
  const [error, setError] = useState<string | null>(null)
  const [workspaceAnalysisContext, setWorkspaceAnalysisContext] = useState<WorkspaceAnalysisContext | null>(null)
  const [financialPreviewAnalysis, setFinancialPreviewAnalysis] = useState<FinancialAnalysisResponse | null>(null)
  const [shockBps, setShockBps] = useState<number>(150)

  // CDI consent & data state
  const [cdiConsent, setCdiConsent] = useState<CdiConsentSession | null>(null)
  const [cdiData, setCdiData] = useState<CdiMockDataResponse | null>(null)
  const [cdiLoading, setCdiLoading] = useState<boolean>(false)

  // Market ranking state
  const [marketRanking, setMarketRanking] = useState<FundingChannelRankingResponse | null>(null)
  const [crossBorderContext, setCrossBorderContext] = useState<CrossBorderFundingContextResponse | null>(null)

  // Funding request input state
  const [fundingRequestAmount, setFundingRequestAmount] = useState<string>('')

  const handleCdiToggle = async () => {
    if (cdiData) {
      // Toggle off — clear CDI state
      setCdiConsent(null)
      setCdiData(null)
      return
    }

    setCdiLoading(true)
    try {
      const cdiContext = await createAndFetchMockCdiData({
        companyId: 'demo-company-001',
        companyName: workspaceAnalysisContext?.companyName ?? 'Demo Company Ltd',
        requestedScopes: ['bank_transactions', 'trade_receivables', 'credit_bureau_summary'],
      })
      setCdiConsent(cdiContext?.consent ?? null)
      setCdiData(cdiContext?.data ?? null)
    } catch (e) {
      console.error('CDI mock consent fetch failed', e)
    } finally {
      setCdiLoading(false)
    }
  }

  const loadAllData = async () => {
    setLoading(true)
    setError(null)
    setHasSnapshotButNoRun(false)
    try {
      setLoadingStep('Preparing advisory blueprint...')
      const bp = await getAdvisoryBlueprint()
      if (bp && (bp as any).status === 'insufficient_data') {
        setBlueprint(bp)
        setLoading(false)
        return
      }

      const workspaceId = localStorage.getItem('active_workspace_id')
      if (workspaceId) {
        const latestRun = await fetchLatestRunSafe(workspaceId, 'advisory_blueprint')
        if (latestRun) {
          const bpData = {
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
          setBlueprint(bpData)

          // Load other requirements for advisory dashboard in parallel
          setLoadingStep('Loading risk profile...')
          const rs = await getAdvisoryRiskScore().catch(() => null)
          setRiskScore(rs)

          setLoadingStep('Checking stress scenarios...')
          const [st, fs] = await Promise.all([
            getAdvisoryStressTests(shockBps).catch(() => null),
            getAdvisoryFacilityStructures().catch(() => null),
          ])
          setStressTests(st)
          setFacilityStructures(fs)

          // Fetch market intelligence in parallel
          setLoadingStep('Loading market intelligence...')
          const [marketRankingResult, crossBorderResult] = await Promise.all([
            getFundingChannelRanking().catch(() => null),
            getCrossBorderFundingContext().catch(() => null),
          ])
          setMarketRanking(marketRankingResult)
          setCrossBorderContext(crossBorderResult)
        } else {
          // Snapshot exists, but no run yet
          setHasSnapshotButNoRun(true)
          setBlueprint(bp)
        }
      } else {
        setBlueprint({
          status: 'insufficient_data',
          missingRequirements: ['Please select or create a workspace in the Data Room.'],
          nextActions: ['Go to the Data Room']
        } as any)
      }

      const activeWorkspaceContext = loadWorkspaceAnalysisContext()
      setWorkspaceAnalysisContext(activeWorkspaceContext)
      if (activeWorkspaceContext) {
        setFinancialPreviewAnalysis(await getFinancialPreviewAnalysis())
      } else {
        setFinancialPreviewAnalysis(null)
      }

      setLoading(false)
    } catch (e) {
      console.error('Failed to load advisory blueprint context', e)
      setError('Advisory blueprint is currently unavailable. Please check the backend connection.')
      setLoading(false)
    }
  }

  const refreshStressData = async (bps: number) => {
    try {
      const [st] = await Promise.all([
        getAdvisoryStressTests(bps).catch(() => null),
      ])
      setStressTests(st)
    } catch (e) {
      console.error('Failed to refresh stress data', e)
    }
  }

  const handleStressShockChange = (bps: number) => {
    setShockBps(bps)
    refreshStressData(bps)
  }

  const handleRunAnalysis = async () => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return
    setIsRunning(true)
    try {
      await triggerAnalysisRun(workspaceId, 'advisory_blueprint')
      await loadAllData()
    } catch (err: any) {
      console.error('Failed to trigger advisory blueprint run:', err)
      alert(`Failed to run advisory blueprint: ${err.message || err}`)
    } finally {
      setIsRunning(false)
    }
  }

  useEffect(() => {
    loadAllData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setWorkspaceAnalysisContext(loadWorkspaceAnalysisContext())

    const handleStorage = (event: StorageEvent) => {
      if (event.key === WORKSPACE_ANALYSIS_CONTEXT_KEY) {
        setWorkspaceAnalysisContext(loadWorkspaceAnalysisContext())
      }
    }

    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  // Maps blueprint status to calm, readable labels
  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'constrained_context':
        return 'Constrained context'
      case 'needs_data':
        return 'Needs data'
      case 'ready_for_review':
        return 'Ready for review'
      case 'unavailable':
      default:
        return 'Unavailable'
    }
  }

  const formatPreviewRatio = (value?: number | null) => {
    if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
    return value.toFixed(2)
  }

  const formatPreviewBand = (value?: string | null) => {
    if (!value) return 'Preview context'
    return value.replace(/_/g, ' ')
  }

  // Source provenance data
  const sourceItems = [
    { label: 'Sample Financial Analysis', mode: 'fixture-backed' as const, asOf: 'FY2025' },
    { label: 'Advisory Precheck Engine', mode: 'workspace-derived' as const },
    { label: 'Unified Risk Scoring Engine', mode: 'workspace-derived' as const },
    { label: 'Stress Testing Engine', mode: 'workspace-derived' as const },
    { label: 'Facility Structuring Engine', mode: 'workspace-derived' as const },
  ]

  if (loading) {
    return (
      <div className="space-y-8 pb-12">
        {/* Header Skeleton */}
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>

        {/* Cockpit Skeleton */}
        <SkeletonLoader variant="card" className="min-h-[220px]" />

        <div className="text-center py-4">
          <p className="text-sm font-medium text-softform-text-secondary animate-pulse">{loadingStep}</p>
        </div>

        {/* Grid skeleton */}
        <div className="grid gap-6 md:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[200px]" count={2} />
        </div>
      </div>
    )
  }

  const isInsufficientData = blueprint && (blueprint as any).status === 'insufficient_data'

  if (isInsufficientData) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Advisory Blueprint"
          subtitle="Context-only financing readiness brief based on sample financial analysis."
        />
        <WorkspaceInsufficientDataState
          missingRequirements={(blueprint as any)?.missingRequirements}
          nextActions={(blueprint as any)?.nextActions}
        />
      </div>
    )
  }

  if (hasSnapshotButNoRun) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Advisory Blueprint"
          subtitle="Context-only financing readiness brief based on sample financial analysis."
        />
        <div className="flex flex-col items-center justify-center p-8 sm:p-12 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 flex items-center justify-center text-softform-teal-deep dark:text-softform-aqua-300">
            <Landmark size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Advisory Blueprint Analysis Needed</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              An active workspace snapshot exists, but no advisory blueprint run has been triggered for this snapshot yet. Run the analysis to generate the final advisory brief.
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
            <span>Run Advisory Blueprint Analysis</span>
          </button>
        </div>
      </div>
    )
  }

  if (error || !blueprint) {
    return (
      <div className="softform-card rounded-[32px] p-8 sm:p-10 text-center">
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-[20px] bg-red-50 text-red-600 border border-red-100">
            <AlertTriangle size={24} />
          </div>
          <p className="mb-2 text-lg font-semibold text-softform-navy-950">
            Service Connection Issue
          </p>
          <p className="mb-6 text-sm text-softform-text-secondary leading-relaxed">
            {error || 'Unable to connect to the advisory services.'}
          </p>
          <button
            type="button"
            onClick={loadAllData}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={14} />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  const snapshotMeta = financialPreviewAnalysis?.snapshot?.metadata
  const isPersistent = Boolean(blueprint?.run_metadata || snapshotMeta?.persistent || snapshotMeta?.source === 'workspace_persistent_snapshot')
  const isPreview = !isPersistent && Boolean(snapshotMeta?.preview_only || snapshotMeta?.previewOnly || snapshotMeta?.source === 'data_room_workspace_preview')
  const { keySections, recommendedActions, executiveBrief, blueprintStatus, companyName } = blueprint

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Page Header */}
      <PageHeader
        title="Advisory Blueprint"
        subtitle="Context-only financing readiness brief based on sample financial analysis."
        titleAddon={
          <SourceInfoTooltip
            title="Advisory Blueprint Provenance"
            sources={sourceItems}
            ariaLabel="Advisory blueprint source information"
          />
        }
        chip={
          <StatusChip variant={blueprintStatus === 'constrained_context' ? 'caution' : 'neutral'}>
            {isPersistent ? 'Workspace Analysis' : isPreview ? 'Preview analysis' : getStatusLabel(blueprintStatus)}
          </StatusChip>
        }
      />

      {/* Fallback Badges / Banners */}
      {!isPersistent && (
        <div className="rounded-[24px] border border-white bg-white/70 p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-softform-amber-500/10 text-softform-amber-500 border border-softform-amber-500/20">
              <AlertTriangle size={14} />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-semibold text-softform-navy-950">
                {isPreview ? "Preview Data Fallback" : "Demo Sample Data Fallback"}
              </p>
              <p className="text-xs text-softform-text-secondary leading-relaxed">
                {isPreview 
                  ? "Displaying advisory readiness from temporary in-memory parsed statements. Re-compiling or restarting the server will reset this state. Please calibrate a persistent workspace snapshot in the Data Room." 
                  : "Displaying Harbour & Finch mock demo advisory blueprint because no persistent active snapshot exists. Go to the Data Room to upload company records and calibrate outcomes."}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <RunMetadataBadge metadata={blueprint?.run_metadata} />
        {blueprint?.run_metadata && (
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

      {workspaceAnalysisContext && (
        <div className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/45 px-5 py-4 shadow-soft-inner">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-softform-navy-950">Using local Data Room preview context</p>
              <p className="mt-1 text-xs leading-relaxed text-softform-text-secondary">
                Preview provenance is active for {workspaceAnalysisContext.companyName} ({workspaceAnalysisContext.reportingPeriod}). Sample/provider data remains active; backend workspace persistence pending.
              </p>
            </div>
            <span className="rounded-full border border-white/70 bg-white/60 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-softform-teal-deep">
              Local preview context
            </span>
          </div>
        </div>
      )}

      {/* 2a. Funding Request Amount Input */}
      <section className="softform-card rounded-[26px] p-6 sm:p-8 border border-white/60">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-softform-mist-100/60 text-softform-teal-deep border border-softform-aqua-300/20">
                <DollarSign size={16} />
              </div>
              <h3 className="font-semibold text-softform-navy-950 text-sm">Funding Request</h3>
            </div>
            <p className="text-xs text-softform-text-secondary leading-relaxed">
              Enter a target funding amount to contextualise the blueprint analysis.
            </p>
          </div>
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <span className="text-sm font-bold text-softform-navy-950">HKD</span>
            <input
              type="text"
              inputMode="numeric"
              value={fundingRequestAmount}
              onChange={(e) => {
                const raw = e.target.value.replace(/[^0-9,]/g, '')
                setFundingRequestAmount(raw)
              }}
              placeholder="e.g. 5,000,000"
              className="w-full sm:w-48 rounded-xl border border-white/80 bg-white/60 px-4 py-2.5 text-sm font-semibold text-softform-navy-950 placeholder:text-softform-text-muted/60 focus:outline-none focus:ring-2 focus:ring-softform-aqua-300/40 focus:border-softform-aqua-300/60 transition-all tabular-finance"
            />
            {fundingRequestAmount && (
              <button
                onClick={() => setFundingRequestAmount('')}
                className="text-xs text-softform-text-muted hover:text-softform-navy-950 transition-colors underline underline-offset-2"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </section>

      {/* 2b. CDI Trust Bridge & Digital Collateral */}
      <section className="softform-card rounded-[26px] p-6 sm:p-8 border border-white/60">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="space-y-3 flex-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-softform-mist-100/60 text-softform-teal-deep border border-softform-aqua-300/20">
                <ShieldCheck size={16} />
              </div>
              <h3 className="font-semibold text-softform-navy-950 text-sm">CDI Trust Bridge & Digital Collateral</h3>
              <StatusChip variant="signal" className="text-[9px] px-2 py-0.5">
                {formatBand(cdiConsent?.status ?? 'unavailable')}
              </StatusChip>
            </div>
            <p className="text-sm leading-relaxed text-softform-text-secondary">
              Mock consent simulation for CDI (Commercial Data Intelligence) integration. Toggle to fetch simulated receivables, bureau, and cashflow signals.
            </p>
          </div>
          <button
            onClick={handleCdiToggle}
            disabled={cdiLoading}
            className={`shrink-0 inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-full border transition-all ${
              cdiData
                ? 'bg-softform-navy-900 text-white border-softform-navy-900 shadow-sm'
                : 'bg-white/60 text-softform-navy-950 border-white/80 hover:bg-white hover:shadow-sm'
            } disabled:opacity-50`}
          >
            {cdiLoading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : cdiData ? (
              <ShieldCheck size={14} />
            ) : (
              <Play size={14} fill="currentColor" />
            )}
            <span>{cdiData ? 'CDI Mock Active' : 'Enable Mock CDI'}</span>
          </button>
        </div>

        {cdiData && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Cashflow Signal */}
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4 space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-softform-text-muted/80">
                Cashflow Trend
              </p>
              <p className="text-sm font-bold text-softform-navy-950">{formatBand(cdiData.cashflowSignal.netCashflowTrend)}</p>
              <p className="text-[10px] text-softform-text-secondary">
                Volatility: {formatBand(cdiData.cashflowSignal.volatilityBand)}
              </p>
              <p className="text-[10px] text-softform-text-secondary">
                Bounced (6m): {cdiData.cashflowSignal.bouncedPaymentCount6m}
              </p>
            </div>
            {/* Receivables Signal */}
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4 space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-softform-text-muted/80">
                Digital Collateral
              </p>
              <p className="text-sm font-bold text-softform-navy-950 tabular-finance">{formatHKD(cdiData.receivablesSignal.eligibleInvoiceValue)}</p>
              <p className="text-[10px] text-softform-text-secondary">
                Verified: {formatHKD(cdiData.receivablesSignal.verifiedInvoiceValue)}
              </p>
              <p className="text-[10px] text-softform-text-secondary">
                Top buyer: {formatPercent(cdiData.receivablesSignal.topBuyerConcentration)}
              </p>
            </div>
            {/* Bureau Signal */}
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4 space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-softform-text-muted/80">
                Credit Bureau
              </p>
              <p className="text-sm font-bold text-softform-navy-950">{formatBand(cdiData.creditBureauSignal.bureauBand)}</p>
              <p className="text-[10px] text-softform-text-secondary">
                Delinquencies (12m): {cdiData.creditBureauSignal.repaymentDelinquencyCount12m}
              </p>
              <p className="text-[10px] text-softform-text-secondary">
                Trade refs: {cdiData.creditBureauSignal.tradeReferenceCount}
              </p>
            </div>
            {/* Implications */}
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4 space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-softform-text-muted/80">
                Funding Implications
              </p>
              {cdiData.fundingImplications.slice(0, 2).map((item, idx) => (
                <p key={idx} className="text-[10px] text-softform-text-secondary leading-relaxed">
                  • {item}
                </p>
              ))}
            </div>
          </div>
        )}

        {cdiData && (
          <p className="mt-4 text-[10px] text-softform-text-muted italic leading-relaxed border-t border-softform-navy-950/5 pt-3">
            {cdiData.disclaimer}
          </p>
        )}
      </section>

      {/* 2c. Market Timing Signal Card */}
      {marketRanking && (
        <section className="softform-card rounded-[26px] p-6 sm:p-8 border border-white/60">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="space-y-3 flex-1">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-softform-mist-100/60 text-softform-teal-deep border border-softform-aqua-300/20">
                  <TrendingUp size={16} />
                </div>
                <h3 className="font-semibold text-softform-navy-950 text-sm">Market & Funding Timing Signal</h3>
                <StatusChip variant="signal" className="text-[9px] px-2 py-0.5">
                  {marketRanking.rankingBand.replace(/_/g, ' ')}
                </StatusChip>
              </div>
              <p className="text-sm leading-relaxed text-softform-text-secondary">
                {marketRanking.explanation}
              </p>
              {marketRanking.channels && marketRanking.channels.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {marketRanking.channels.slice(0, 4).map((ch) => (
                    <span
                      key={ch.key}
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-semibold border ${
                        ch.fitBand === 'strong_fit'
                          ? 'bg-emerald-500/10 text-emerald-700 border-emerald-200/50'
                          : ch.fitBand === 'moderate_fit'
                          ? 'bg-softform-mist-100 text-softform-teal-deep border-softform-aqua-300/20'
                          : 'bg-softform-cream text-softform-amber-500 border-softform-amber-300/20'
                      }`}
                    >
                      {ch.label}
                      <span className="opacity-70">#{ch.rank}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
            {crossBorderContext && (
              <div className="shrink-0 w-full sm:w-64 space-y-2 rounded-[18px] border border-white/60 bg-white/45 p-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-softform-text-muted/80">
                  Cross-Border Context
                </p>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-softform-text-secondary">HKD ref.</span>
                    <span className="font-bold text-softform-navy-950 tabular-finance">{crossBorderContext.hkdFundingReference.displayValue}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-softform-text-secondary">RMB ref.</span>
                    <span className="font-bold text-softform-navy-950 tabular-finance">{crossBorderContext.rmbFundingReference.displayValue}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-softform-text-secondary">Spread</span>
                    <span className="font-bold text-softform-navy-950 tabular-finance">{formatBand(crossBorderContext.spreadBand)}</span>
                  </div>
                </div>
                <p className="text-[10px] text-softform-text-muted italic leading-relaxed pt-1 border-t border-softform-navy-950/5">
                  {crossBorderContext.explanation}
                </p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* 2. Executive Brief Panel in Premium Navy Contrast Card */}
      <section className="softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse">
                Executive Briefing
              </span>
              <h2 className="text-2xl font-semibold text-white tracking-tight">
                Financing Readiness Outlook
              </h2>
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-white bg-white/10 px-3 py-1 rounded-full border border-white/10">
              {companyName}
            </span>
          </div>
          <p className="text-base md:text-lg text-white/90 font-medium leading-relaxed max-w-4xl">
            {executiveBrief}
          </p>

          {workspaceAnalysisContext && financialPreviewAnalysis && (
            <div className="rounded-[24px] border border-white/10 bg-white/5 p-5 backdrop-blur-md">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="max-w-2xl">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-softform-aqua-300">
                    Data Room preview financial context
                  </p>
                  <h3 className="mt-1 text-base font-semibold text-white">
                    {financialPreviewAnalysis.snapshot.companyName} · {financialPreviewAnalysis.snapshot.reportingPeriod}
                  </h3>
                  <p className="mt-1 text-xs leading-relaxed text-white/70">
                    Preview-only financial context is available for review. The advisory blueprint response remains based on the existing local advisory pipeline.
                  </p>
                </div>
                <div className="grid min-w-0 flex-1 gap-2 sm:grid-cols-3 xl:grid-cols-5">
                  {[
                    ['Integrity', financialPreviewAnalysis.integrityChecks?.length ? `${financialPreviewAnalysis.integrityChecks.length} checks` : 'N/A'],
                    ['Current', financialPreviewAnalysis.ratios.currentRatio?.value],
                    ['Quick', financialPreviewAnalysis.ratios.quickRatio?.value],
                    ['DSCR', financialPreviewAnalysis.ratios.dscr?.value],
                    ['Band', formatPreviewBand(financialPreviewAnalysis.summary?.overallBand)],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-2xl border border-white/5 bg-white/5 px-3 py-2">
                      <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-white/50">{label}</p>
                      <p className="mt-1 text-sm font-bold text-white">
                        {typeof value === 'number' ? formatPreviewRatio(value) : value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* 3. Key Sections */}
      <SectionBlock
        title="Key Sections Summary"
        containerType="none"
        className="space-y-6"
      >
        <div className="grid gap-6 md:grid-cols-2">
          {/* Financial Posture */}
          {keySections.financialPosture && (
            <div className="softform-card rounded-[26px] p-6 sm:p-8 flex flex-col justify-between h-full border border-white/60 hover-lift">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-softform-mist-100/60 text-softform-teal-deep border border-softform-aqua-300/20 shadow-sm animate-pulse">
                      <BarChart3 size={18} />
                    </div>
                    <h3 className="font-semibold text-softform-navy-950 text-base">
                      {keySections.financialPosture.title}
                    </h3>
                  </div>
                  <StatusChip variant="neutral">Financial</StatusChip>
                </div>
                
                <p className="text-sm leading-relaxed text-softform-text-secondary">
                  {keySections.financialPosture.summary}
                </p>

                {keySections.financialPosture.signals && keySections.financialPosture.signals.length > 0 && (
                  <div className="space-y-2 pt-1.5">
                    <h4 className="text-xs font-semibold text-softform-navy-950/70 tracking-wide">
                      Key Indicators
                    </h4>
                    <ul className="space-y-2">
                      {keySections.financialPosture.signals.map((sig, i) => (
                        <li key={i} className="text-xs text-softform-text-secondary flex items-start gap-2">
                          <span className="text-softform-teal-500 font-bold mt-0.5">•</span>
                          <span className="leading-relaxed">{sig}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {keySections.financialPosture.warnings && keySections.financialPosture.warnings.length > 0 && (
                <div className="mt-5 rounded-xl bg-softform-cream/60 p-3.5 text-xs text-softform-amber-500 border border-softform-amber-300/30">
                  {keySections.financialPosture.warnings.map((w, idx) => (
                    <p key={idx} className="flex gap-2 items-start leading-relaxed font-normal">
                      <AlertTriangle size={13} className="shrink-0 mt-0.5 text-softform-amber-500" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Advisory Readiness */}
          {keySections.advisoryReadiness && (
            <div className="softform-card rounded-[26px] p-6 sm:p-8 flex flex-col justify-between h-full border border-white/60 hover-lift">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-softform-mist-100/60 text-softform-teal-deep border border-softform-aqua-300/20 shadow-sm animate-pulse">
                      <ShieldCheck size={18} />
                    </div>
                    <h3 className="font-semibold text-softform-navy-950 text-base">
                      {keySections.advisoryReadiness.title}
                    </h3>
                  </div>
                  <StatusChip variant="signal">Readiness</StatusChip>
                </div>
                
                <p className="text-sm leading-relaxed text-softform-text-secondary">
                  {keySections.advisoryReadiness.summary}
                </p>

                {keySections.advisoryReadiness.constraints && keySections.advisoryReadiness.constraints.length > 0 && (
                  <div className="space-y-2 pt-1.5">
                    <h4 className="text-xs font-semibold text-softform-navy-950/70 tracking-wide">
                      Identified Constraints
                    </h4>
                    <ul className="space-y-2">
                      {keySections.advisoryReadiness.constraints.map((c, i) => (
                        <li key={i} className="text-xs text-softform-text-secondary flex items-start gap-2">
                          <span className="text-red-500 font-bold mt-0.5">•</span>
                          <span className="leading-relaxed">{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {keySections.advisoryReadiness.warnings && keySections.advisoryReadiness.warnings.length > 0 && (
                <div className="mt-5 rounded-xl bg-softform-cream/60 p-3.5 text-xs text-softform-amber-500 border border-softform-amber-300/30">
                  {keySections.advisoryReadiness.warnings.map((w, idx) => (
                    <p key={idx} className="flex gap-2 items-start leading-relaxed font-normal">
                      <AlertTriangle size={13} className="shrink-0 mt-0.5 text-softform-amber-500" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </SectionBlock>

      {/* 4. Recommended Actions */}
      <SectionBlock
        title="Recommended Actions Workflow"
        containerType="none"
        className="space-y-6"
      >
        <div className="space-y-4">
          {recommendedActions.map((act) => {
            let category = 'Information Gathering'
            let expectedOutcome = 'Prepares the workspace for formal, record-backed review.'
            if (act.actionKey === 'review_debt_service_headroom') {
              category = 'Debt Optimization'
              expectedOutcome = 'Avoids over-leveraging and aligns sizing to current cash flow reality.'
            } else if (act.actionKey === 'compare_working_capital_options') {
              category = 'Treasury Comparison'
              expectedOutcome = 'Identifies structural alternatives that reduce financing costs.'
            }

            return (
              <div
                key={act.actionKey}
                className="softform-action-card rounded-[22px] p-6 flex flex-col md:flex-row md:items-start justify-between gap-5"
              >
                <div className="space-y-3.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">
                      {category}
                    </span>
                    <StatusChip variant={act.priority === 'high' ? 'caution' : 'neutral'} className="text-[9px] px-2 py-0.5">
                      {act.priority} priority
                    </StatusChip>
                  </div>
                  <h3 className="font-semibold text-softform-navy-950 text-base flex items-center gap-2">
                    <CheckSquare size={16} className="text-softform-teal-deep shrink-0 animate-pulse" />
                    {act.label}
                  </h3>
                  <div className="space-y-1.5">
                    <p className="text-sm text-softform-text-secondary leading-relaxed">
                      <strong className="text-softform-navy-950">Rationale:</strong> {act.rationale}
                    </p>
                    <p className="text-sm text-softform-text-secondary leading-relaxed">
                      <strong className="text-softform-navy-950">Expected Outcome:</strong> {expectedOutcome}
                    </p>
                  </div>
                  {act.requiredData && act.requiredData.length > 0 && (
                    <div className="pt-2">
                      <span className="text-[10px] font-semibold text-softform-text-muted/95 uppercase tracking-[0.12em] block mb-1">
                        Required Records
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {act.requiredData.map((d, idx) => (
                          <span
                            key={idx}
                            className="inline-block rounded-lg bg-softform-mist-100/50 px-2.5 py-1 text-xs text-softform-text-secondary border border-white/60 shadow-sm"
                          >
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                {act.ownerHint && (
                  <div className="shrink-0 text-xs text-softform-text-muted md:text-right md:border-l md:border-softform-navy-950/5 md:pl-5 md:h-full flex flex-col justify-center gap-0.5">
                    <span className="font-semibold text-softform-navy-950 block">Assigned Owner</span>
                    <span className="font-medium">{act.ownerHint}</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </SectionBlock>

      {/* 5. Candidate Financing Structures */}
      {facilityStructures && (
        <SectionBlock
          title="Candidate Financing Structures"
          icon={<Landmark size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Baseline Fit</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <p className="text-sm leading-relaxed text-softform-text-secondary mb-4">
            Structured context-only financing packages under baseline metrics. Note: Limit and pricing metrics are assumptions-only and subject to lender review.
          </p>

          <div className="grid gap-6 sm:grid-cols-3">
            {facilityStructures.candidates.slice(0, 3).map((cand) => (
              <div
                key={cand.facilityKey}
                className="rounded-[22px] bg-white/40 p-5 border border-white/60 shadow-sm flex flex-col justify-between gap-4 hover-lift"
              >
                <div className="space-y-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-softform-navy-950 text-sm leading-snug">
                      {cand.label}
                    </h3>
                    <span
                      className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${
                        cand.fitAssessment.fitBand === 'strong'
                          ? 'bg-emerald-500/10 text-emerald-700'
                          : cand.fitAssessment.fitBand === 'adequate'
                          ? 'bg-softform-mist-100 text-softform-teal-deep'
                          : 'bg-softform-cream text-softform-amber-500'
                      }`}
                    >
                      {cand.fitAssessment.fitBand} fit
                    </span>
                  </div>
                  <div className="space-y-1.5 text-xs text-softform-text-secondary">
                    <div className="flex justify-between border-b border-softform-navy-950/5 pb-1">
                      <span className="font-semibold text-softform-navy-950/80">Est. Limit</span>
                      <span className="tabular-finance font-bold text-softform-navy-950">{formatHKD(cand.estimatedLimit)}</span>
                    </div>
                    {cand.estimatedPricingBps !== undefined && cand.estimatedPricingBps !== null && (
                      <div className="flex justify-between border-b border-softform-navy-950/5 pb-1">
                        <span className="font-semibold text-softform-navy-950/80">Est. Pricing</span>
                        <span className="tabular-finance font-bold text-softform-navy-950">{cand.estimatedPricingBps} bps spread</span>
                      </div>
                    )}
                    {cand.estimatedAnnualCost !== undefined && cand.estimatedAnnualCost !== null && (
                      <div className="flex justify-between pb-0.5">
                        <span className="font-semibold text-softform-navy-950/80">Est. Annual Cost</span>
                        <span className="tabular-finance font-bold text-softform-navy-950">{formatHKD(cand.estimatedAnnualCost)}</span>
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-softform-text-secondary leading-relaxed">
                    <strong className="text-softform-navy-950">Purpose:</strong> {cand.purpose}
                  </p>
                </div>
                <p className="text-[10px] text-softform-text-muted leading-relaxed italic border-t border-softform-navy-950/5 pt-2">
                  {cand.disclaimer}
                </p>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* 6. Risk Context Summary */}
      {riskScore && (
        <SectionBlock
          title="Advisory Readiness Score Context"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">Readiness Score</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="flex flex-col md:flex-row gap-8 items-center">
            <div className="flex flex-col items-center justify-center p-6 rounded-[22px] bg-white/50 border border-softform-aqua-300/30 w-36 shrink-0 shadow-inner">
              <span className="text-4xl font-bold text-softform-teal-deep tracking-tight">{riskScore.score}</span>
              <span className="text-[9px] uppercase tracking-[0.14em] font-semibold text-softform-text-muted/80 mt-1">
                Scale 0-100
              </span>
              <span className="mt-3 text-[10px] font-medium px-2.5 py-0.5 rounded-full bg-softform-navy-950 text-white uppercase tracking-[0.08em]">
                {riskScore.band} Band
              </span>
            </div>
            <div className="space-y-4 flex-1">
              <p className="text-sm text-softform-text-secondary leading-relaxed">
                This score provides context for advisory readiness and financing fit only. It does not represent a probability of default or a credit rating.
              </p>
              {riskScore.factors && riskScore.factors.length > 0 && (
                <div className="grid gap-3.5 sm:grid-cols-2">
                  {riskScore.factors.slice(0, 4).map((f) => (
                    <div key={f.key} className="p-4 rounded-xl bg-white/45 border border-white/50 text-xs space-y-1.5 hover-lift shadow-sm">
                      <div className="flex justify-between font-semibold text-softform-navy-950">
                        <span>{f.label}</span>
                        <span className="text-softform-teal-deep font-bold">Impact: -{f.scoreImpact}</span>
                      </div>
                      <p className="text-softform-text-secondary leading-relaxed">{f.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </SectionBlock>
      )}

      {/* 7. Stress Context Summary */}
      {stressTests && (
        <SectionBlock
          title="Stress Test Sensitivity Context"
          icon={<AlertTriangle size={20} className="text-softform-amber-500" />}
          action={<StatusChip variant="caution">Sensitivity Model</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          {/* Stress Shock Level Selector */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-2">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-softform-text-muted/80">
              Rate Shock Simulation
            </span>
            <div className="flex gap-1.5">
              {[0, 100, 150, 200].map((bps) => (
                <button
                  key={bps}
                  onClick={() => handleStressShockChange(bps)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-all ${
                    shockBps === bps
                      ? 'bg-softform-navy-900 text-white border-softform-navy-900 shadow-sm'
                      : 'bg-white/60 text-softform-navy-950 border-white/80 hover:bg-white hover:shadow-sm'
                  }`}
                >
                  +{bps} bps
                </button>
              ))}
            </div>
          </div>

          <p className="text-sm leading-relaxed text-softform-text-secondary mb-4">
            Simulated scenario shocks applied to baseline metrics. Displays impact on key performance signals.
          </p>

          <div className="grid gap-6 sm:grid-cols-2">
            {stressTests.scenarios.map((scen) => (
              <div
                key={scen.scenarioKey}
                className="p-5 rounded-[22px] bg-white/40 border border-white/60 shadow-sm space-y-4 hover-lift"
              >
                <div className="flex items-center justify-between gap-2">
                  <h3 className="font-semibold text-softform-navy-950 text-sm">{scen.label}</h3>
                  <span
                    className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${
                      scen.severity === 'high'
                        ? 'bg-red-500/10 text-red-700'
                        : scen.severity === 'elevated'
                        ? 'bg-softform-cream text-softform-amber-500'
                        : 'bg-softform-teal-deep/10 text-softform-teal-deep'
                    }`}
                  >
                    {scen.severity} severity
                  </span>
                </div>
                <p className="text-xs text-softform-text-secondary italic leading-relaxed">
                  {scen.keyTakeaway}
                </p>
                {scen.impacts && scen.impacts.length > 0 && (
                  <div className="border-t border-softform-navy-950/5 pt-3 space-y-2">
                    {scen.impacts.slice(0, 2).map((imp, idx) => (
                      <div key={idx} className="flex justify-between text-xs items-center">
                        <span className="text-softform-text-secondary font-normal">{imp.metric}:</span>
                        <span className="font-semibold text-softform-navy-950 tabular-finance">
                          {imp.baseValue.toFixed(2)} → {imp.stressedValue.toFixed(2)} ({imp.interpretation})
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* 8. Data Readiness Gaps */}
      {keySections.dataReadiness && (
        <SectionBlock
          title="Information Gaps for Production Advisory"
          icon={<FolderOpen size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Data Readiness</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-5"
        >
          <p className="text-sm leading-relaxed text-softform-text-secondary mb-4">
            The following documentation gaps must be resolved to transition from this local context to a record-backed production advisory:
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {keySections.dataReadiness.nextDataNeeded.map((gap, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-4 rounded-xl bg-white/40 border border-white/60 text-xs text-softform-text-secondary font-semibold hover-lift shadow-sm"
              >
                <div className="h-2 w-2 rounded-full bg-softform-teal-deep shrink-0 animate-pulse" />
                <span>{gap}</span>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* 9. BOCHK Phase 3 Interactive Engine */}
      <FundingBlueprintHelper />

      {/* Subtle CTA to Data Room & Market Watch */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-semibold text-softform-navy-950 text-base">Advisory Planning Context</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Blueprint uses context-only local analysis and Data Room preview context when available. Production records are required for a record-backed advisory.
          </p>
        </div>
        <div className="flex gap-3.5 shrink-0 w-full sm:w-auto justify-center sm:justify-end">
          <Link
            to="/platform/market-watch"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-white/80 bg-white/60 px-4 py-2.5 text-xs font-semibold text-softform-navy-950 hover:bg-white transition shadow-sm"
          >
            Review Market Watch
          </Link>
          <Link
            to="/platform/data-room"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
          >
            Review Data Room
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>

      {/* Footer Info */}
      <footer className="pt-6 border-t border-softform-navy-950/5 text-center space-y-2">
        <p className="text-xs text-softform-text-muted font-normal">
          All data in this report is context-only, assumptions-based, and for planning purposes. Not a formal credit decision.
        </p>
        <p className="text-xs text-softform-text-muted font-normal">
          FinSight CFO Workspace • Powered by softform design token system.
        </p>
      </footer>
    </div>
  )
}
