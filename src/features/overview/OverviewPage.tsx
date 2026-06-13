/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart3,
  FileText,
  HeartPulse,
  Landmark,
  ShieldCheck,
  TrendingUp,
  ArrowRight,
  Loader2,
  Play,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import ServiceErrorState from '../../components/platform/ServiceErrorState'
import NavyHeroSection from '../../components/platform/NavyHeroSection'
import PageLoadingSkeleton from '../../components/platform/PageLoadingSkeleton'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import { getCreditScore } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getFundingChannelRanking, getRedFlagsMacroSummary } from '../market-watch/api/marketWatchApi'
import { getBochkWorkflowRun } from '../workflow/workflowApi'
import type { CreditScoringResult } from '../advisory-blueprint/types'
import type { FundingChannelRankingResponse, RedFlagsMacroSummaryResponse } from '../market-watch/types'
import type { BochkWorkflowRun } from '../workflow/workflowApi'
import { formatHKD, formatPercent, formatBand, bandVariant, variantForBand } from '../../lib/formatters'
import { isDemoWorkspace, listWorkspaces, SYNTHETIC_DEMO_BADGE } from '../data-room/api/dataRoomApi'
import {
  triggerAnalysisRun,
  fetchAllRunStatuses,
  ANALYSIS_RUN_TYPES,
} from '../../lib/workspaceRunHelpers'
import { API_BASE_URL } from '../../lib/apiBase'
import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'
import WorkspaceDashboard from './WorkspaceDashboard'
import { useWorkspace } from '../../context/workspaceContext'
import ReleaseOnboardingChecklist from '../../components/platform/ReleaseOnboardingChecklist'

type OverviewState = {
  financial: any
  credit: CreditScoringResult | null
  funding: FundingChannelRankingResponse | null
  macro: RedFlagsMacroSummaryResponse | null
  workflow: BochkWorkflowRun | null
}

type NextAction = {
  title: string
  body: string
  to: string
}

export default function OverviewPage() {
  const { activeWorkspace } = useWorkspace()
  const [state, setState] = useState<OverviewState>({ financial: null, credit: null, funding: null, macro: null, workflow: null })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Workspace readiness state
  const [workspaceName, setWorkspaceName] = useState<string>('')
  const [hasSnapshot, setHasSnapshot] = useState<boolean | null>(null)
  const [runStatuses, setRunStatuses] = useState<Record<string, any | null>>({})
  const [runningAll, setRunningAll] = useState(false)
  const [runningAllProgress, setRunningAllProgress] = useState('')

  const loadOverview = async () => {
    setLoading(true)
    setError(null)
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (workspaceId) {
      try {
        const workspaces = await listWorkspaces().catch(() => [])
        const active = workspaces.find((w) => w.id === workspaceId)
        if (active) {
          setWorkspaceName(active.companyName)
        }
        
        const snapshotRes = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/snapshot/active`, {
          headers: { 'x-workspace-id': workspaceId }
        })
        if (snapshotRes.ok) {
          setHasSnapshot(true)
        } else {
          setHasSnapshot(false)
        }
        
        const statuses = await fetchAllRunStatuses(workspaceId)
        setRunStatuses(statuses)
      } catch (e) {
        console.warn('Overview workspace loading failed', e)
        setHasSnapshot(false)
      }
    } else {
      setHasSnapshot(false)
    }

    try {
      const [financial, credit, funding, macro, workflow] = await Promise.all([
        getFinancialHealthAnalysis().catch((e) => {
          console.warn('Overview financial context unavailable', e)
          return null
        }),
        getCreditScore().catch((e) => {
          console.warn('Overview credit context unavailable', e)
          return null
        }),
        getFundingChannelRanking().catch((e) => {
          console.warn('Overview funding context unavailable', e)
          return null
        }),
        getRedFlagsMacroSummary().catch((e) => {
          console.warn('Overview macro context unavailable', e)
          return null
        }),
        getBochkWorkflowRun().catch((e) => {
          console.warn('BOCHK workflow runner unavailable', e)
          return null
        }),
      ])
      setState({ financial, credit, funding, macro, workflow })
    } catch (e) {
      console.error('Overview load failed', e)
      setError('Overview is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const handleRunAllMissing = async () => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return

    const missingCoreTypes = ANALYSIS_RUN_TYPES.filter(
      (typeInfo) => typeInfo.isCore && !runStatuses[typeInfo.key]
    )

    if (missingCoreTypes.length === 0) {
      return
    }

    setRunningAll(true)
    try {
      for (let i = 0; i < missingCoreTypes.length; i++) {
        const typeInfo = missingCoreTypes[i]
        setRunningAllProgress(`Running ${typeInfo.label} (${i + 1}/${missingCoreTypes.length})...`)
        try {
          await triggerAnalysisRun(workspaceId, typeInfo.key)
        } catch (err) {
          console.error(`Sequential run failed for ${typeInfo.key}:`, err)
        }
      }
      setRunningAllProgress('Refreshing...')
      const statuses = await fetchAllRunStatuses(workspaceId)
      setRunStatuses(statuses)
      // Reload overview metrics to match updated runs
      await loadOverview()
    } catch (err) {
      console.error('Error during Run All operation:', err)
    } finally {
      setRunningAll(false)
      setRunningAllProgress('')
    }
  }

  useEffect(() => {
    loadOverview()
  }, [])

  const isInsufficientData = useMemo(() => {
    return state.financial && state.financial.status === 'insufficient_data'
  }, [state.financial])

  const valuation = state.financial?.valuation ?? null
  const topChannel = state.funding?.channels?.find((channel) => channel.key === state.funding?.topChannelKey) ?? state.funding?.channels?.[0]

  const nextActions = useMemo(() => {
    const actions: NextAction[] = []
    if (!state.financial || isInsufficientData) {
      actions.push({ title: 'Upload financial records', body: 'Start with Data Room to activate preview analysis.', to: '/platform/data-room' })
    } else if ((state.financial.summary?.watchItems?.length ?? 0) > 0) {
      actions.push({ title: 'Review financial watch items', body: state.financial.summary?.watchItems?.[0] ?? 'Inspect ratio and integrity signals.', to: '/platform/financial-health' })
    }
    if (state.credit?.fundingReadiness === 'needs_review' || state.credit?.fundingReadiness === 'not_ready') {
      actions.push({ title: 'Improve readiness scorecard', body: state.credit.nextDataNeeded?.[0] ?? 'Review scorecard drivers and next data needs.', to: '/platform/credit-readiness' })
    }
    if (topChannel) {
      actions.push({ title: `Prioritize ${topChannel.label}`, body: topChannel.useCase, to: '/platform/funding-strategy' })
    }
    actions.push({ title: 'Generate advisory blueprint', body: 'Convert the current context into an advisor-ready brief.', to: '/platform/advisory-blueprint' })
    return actions.slice(0, 4)
  }, [state.financial, isInsufficientData, state.credit, topChannel])

  if (loading) {
    return <PageLoadingSkeleton layout="overview" />
  }

  if (error) {
    return (
      <ServiceErrorState
        message={error}
        onRetry={loadOverview}
      />
    )
  }

  if (isInsufficientData) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Overview"
          subtitle="Executive command center across financial health, valuation, credit readiness, funding strategy, and macro watch signals."
        />
        <WorkspaceInsufficientDataState
          missingRequirements={state.financial.missingRequirements}
          nextActions={state.financial.nextActions}
        />
      </div>
    )
  }


  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Overview"
        subtitle="Executive command center across financial health, valuation, credit readiness, funding strategy, and macro watch signals."
        chip={
          isDemoWorkspace(activeWorkspace) ? (
            <StatusChip variant="neutral">{SYNTHETIC_DEMO_BADGE}</StatusChip>
          ) : (
            <StatusChip variant={bandVariant(state.macro?.summaryBand)}>{formatBand(state.macro?.summaryBand ?? 'workspace')}</StatusChip>
          )
        }
      />

      <WorkspaceDashboard />

      {/* Cockpit Hero Section in Premium Navy Contrast Card */}
      <NavyHeroSection
        eyebrow="FinSight CFO cockpit"
        title={`${state.financial?.snapshot.companyName ?? 'Workspace Company'} · CFO decision view`}
        description={state.macro?.headline ?? 'Use this view to move from uploaded records to financial diagnostics, indicative valuation, readiness scoring, channel strategy, and advisory output.'}
        layoutClassName="relative grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center"
        aside={
          <div className="grid gap-3 sm:grid-cols-2">
            <Link to="/platform/data-room" className="rounded-[22px] border border-white/10 bg-white/5 p-4 shadow-soft-inner hover-lift">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-white/50">Data mode</p>
              <p className="mt-1 text-sm font-semibold text-white">{state.financial?.snapshot.metadata?.source ? 'Workspace preview' : 'Context-only'}</p>
            </Link>
            <Link to="/platform/advisory-blueprint" className="rounded-[22px] border border-white/10 bg-white/5 p-4 shadow-soft-inner hover-lift">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-white/50">Advisor output</p>
              <p className="mt-1 text-sm font-semibold text-white">Blueprint ready</p>
            </Link>
          </div>
        }
      />


      {/* Onboarding Checklist */}
      <ReleaseOnboardingChecklist />

      {/* KPI Metric Grid */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Link to="/platform/financial-health" className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Financial Health"
            value={formatBand(state.financial?.summary?.overallBand)}
            description={`Revenue ${formatHKD(state.financial?.snapshot.incomeStatement.revenue)}`}
            icon={<HeartPulse size={16} className="text-softform-teal-500" />}
          />
        </Link>
        <Link to="/platform/valuation" className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Valuation"
            value={formatHKD(valuation?.dcf?.enterpriseValue)}
            description={`WACC ${formatPercent(valuation?.wacc?.wacc)}`}
            icon={<BarChart3 size={16} className="text-softform-teal-500" />}
          />
        </Link>
        <Link to="/platform/credit-readiness" className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Credit Readiness"
            value={state.credit?.compositeScore ?? 'N/A'}
            description={`Readiness: ${formatBand(state.credit?.fundingReadiness)}`}
            icon={<ShieldCheck size={16} className="text-softform-teal-500" />}
          />
        </Link>
        <Link to="/platform/funding-strategy" className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Funding Strategy"
            value={topChannel ? `#${topChannel.rank}` : 'N/A'}
            description={`Top: ${topChannel?.label ?? 'None'}`}
            icon={<Landmark size={16} className="text-softform-teal-500" />}
          />
        </Link>
      </section>

      {/* Workspace Readiness Panel */}
      <section className="bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-[32px] p-6 sm:p-8 backdrop-blur-md shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-softform-navy-950/5 pb-4 gap-3">
          <div>
            <h2 className="text-lg font-semibold text-softform-navy-950">Workspace Ingestion & Analysis Readiness</h2>
            <p className="text-xs text-softform-text-muted mt-1">
              Monitor active company records, statements, and calculated outputs.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Status:</span>
            {hasSnapshot ? (
              <StatusChip variant="signal">Snapshot Ingested</StatusChip>
            ) : (
              <StatusChip variant="caution">Ingestion Incomplete</StatusChip>
            )}
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {/* Col 1: Workspace info */}
          <div className="bg-white/45 dark:bg-slate-800/10 border border-white/70 dark:border-slate-800/30 rounded-2xl p-5 space-y-2">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-text-muted">Active Company Workspace</span>
            <p className="text-base font-bold text-softform-navy-950 leading-snug">
              {workspaceName || 'No Active Workspace'}
            </p>
            {hasSnapshot && (
              <p className="text-xs text-softform-teal-deep font-semibold">
                Active financial snapshot is compiled.
              </p>
            )}
          </div>

          {/* Col 2: Runs Progress */}
          <div className="bg-white/45 dark:bg-slate-800/10 border border-white/70 dark:border-slate-800/30 rounded-2xl p-5 space-y-2 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-text-muted">Core Runs Completed</span>
              <p className="text-2xl font-bold text-softform-navy-950 mt-1 tabular-finance">
                {ANALYSIS_RUN_TYPES.filter(t => t.isCore).filter(t => runStatuses[t.key]).length} <span className="text-sm font-medium text-softform-text-muted">/ 6 Runs</span>
              </p>
            </div>
            {hasSnapshot && ANALYSIS_RUN_TYPES.filter(t => t.isCore).filter(t => !runStatuses[t.key]).length > 0 && (
              <span className="text-xs text-softform-amber-500 font-semibold">
                {ANALYSIS_RUN_TYPES.filter(t => t.isCore).filter(t => !runStatuses[t.key]).length} core calculations are missing or outdated.
              </span>
            )}
          </div>

          {/* Col 3: Next Recommendation & Action */}
          <div className="bg-white/45 dark:bg-slate-800/10 border border-white/70 dark:border-slate-800/30 rounded-2xl p-5 space-y-3 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-text-muted">Recommended Action</span>
              <p className="text-xs text-softform-text-secondary mt-1 leading-relaxed">
                {!hasSnapshot 
                  ? 'First select or create a workspace and upload financials in the Data Room.' 
                  : ANALYSIS_RUN_TYPES.filter(t => t.isCore).filter(t => !runStatuses[t.key]).length > 0 
                  ? 'Execute the missing core analyses to enable full Reports and AI CFO context.'
                  : 'Your workspace is fully analyzed. Open Reports to view insights.'}
              </p>
            </div>

            <div className="pt-2">
              {!hasSnapshot ? (
                <Link
                  to="/platform/data-room"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-xs font-semibold rounded-full shadow-sm transition-colors"
                >
                  <span>Go to Data Room</span>
                  <ArrowRight size={12} />
                </Link>
              ) : ANALYSIS_RUN_TYPES.filter(t => t.isCore).filter(t => !runStatuses[t.key]).length > 0 ? (
                <button
                  onClick={handleRunAllMissing}
                  disabled={runningAll}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-xs font-semibold rounded-full shadow-sm disabled:opacity-50 transition-colors"
                >
                  {runningAll ? (
                    <Loader2 size={12} className="animate-spin text-softform-teal-deep dark:text-softform-aqua-300" />
                  ) : (
                    <Play size={12} fill="currentColor" className="ml-0.5" />
                  )}
                  <span>{runningAll ? runningAllProgress : 'Run Missing Analyses'}</span>
                </button>
              ) : (
                <Link
                  to="/platform/reports"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-softform-teal-deep hover:bg-softform-teal-deep/90 text-white text-xs font-semibold rounded-full shadow-sm transition-colors"
                >
                  <span>View Reports</span>
                  <ArrowRight size={12} />
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Macro & Next Actions Panels */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Macro & Market Watch"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant={variantForBand(state.macro?.summaryBand)}>{formatBand(state.macro?.summaryBand)}</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {(state.macro?.redFlags ?? []).slice(0, 3).map((flag) => (
              <div key={flag.flagKey} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 border-l-4 border-l-amber-500">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-softform-navy-950">{flag.label}</p>
                  <span className="rounded bg-softform-cream px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider text-softform-amber-500">
                    {flag.severity}
                  </span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-softform-text-secondary">{flag.rationale}</p>
              </div>
            ))}
            {(state.macro?.redFlags?.length ?? 0) === 0 && (
              <p className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                Macro watch context is unavailable or clear. Open Market Watch for detailed source status.
              </p>
            )}
          </div>
        </SectionBlock>

        <SectionBlock
          title="Recommended Next Actions"
          icon={<FileText size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Workflow</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {nextActions.map((action) => (
              <Link key={action.title} to={action.to} className="softform-action-card group flex items-start justify-between gap-4 rounded-xl px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-softform-navy-950">{action.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-softform-text-secondary">{action.body}</p>
                </div>
                <ArrowRight size={16} className="mt-1 shrink-0 text-softform-teal-deep transition group-hover:translate-x-1" />
              </Link>
            ))}
          </div>
        </SectionBlock>
      </section>

      {/* Bottom CTA Banner */}
      <section className="softform-navy-card rounded-[32px] p-8 relative overflow-hidden flex flex-col sm:flex-row gap-6 items-center justify-between">
        <div className="absolute inset-0 bg-white/5 backdrop-blur-sm pointer-events-none" />
        <div className="relative space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-semibold text-white text-base">Start from source documents</p>
          <p className="text-xs leading-relaxed text-white/75">
            Upload or activate records in Data Room, then move through diagnostics, valuation, readiness, funding strategy, and advisory output.
          </p>
        </div>
        <Link
          to="/platform/data-room"
          className="relative z-10 inline-flex items-center justify-center gap-1.5 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-softform-navy-950 hover:bg-white/90 transition shadow-sm"
        >
          Open Data Room
          <ArrowRight size={14} />
        </Link>
      </section>
    </div>
  )
}
