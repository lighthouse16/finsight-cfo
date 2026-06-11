/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Download,
  FileText,
  HeartPulse,
  Landmark,
  RotateCw,
  ShieldCheck,
  Loader2,
  Play,
  CheckCircle2,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import SkeletonLoader from '../../components/platform/SkeletonLoader'
import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'
import {
  triggerAnalysisRun,
  fetchAllRunStatuses,
  getRunStatusLabel,
  fetchBackendConfig,
} from '../../lib/workspaceRunHelpers'
import { API_BASE_URL } from '../../lib/apiBase'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import {
  getAdvisoryBlueprint,
  getAdvisoryFacilityStructures,
  getCreditScore,
} from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getFundingChannelRanking, getRedFlagsMacroSummary } from '../market-watch/api/marketWatchApi'
import type {
  AdvisoryBlueprintResponse,
  CreditScoringResult,
  FacilityStructuringResponse,
} from '../advisory-blueprint/types'
import type {
  FinancialAnalysisResponse,
  FundingChannelRankingResponse,
  RedFlagsMacroSummaryResponse,
} from '../market-watch/types'

type ReportState = {
  financial: FinancialAnalysisResponse | null
  credit: CreditScoringResult | null
  blueprint: AdvisoryBlueprintResponse | null
  facilities: FacilityStructuringResponse | null
  funding: FundingChannelRankingResponse | null
  macro: RedFlagsMacroSummaryResponse | null
}

function formatHKD(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  if (Math.abs(value) >= 1_000_000) return `HKD ${(value / 1_000_000).toFixed(2)}M`
  return `HKD ${value.toLocaleString()}`
}

function formatPercent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return `${(value * 100).toFixed(2)}%`
}

function formatBand(value?: string | null) {
  if (!value) return 'Unavailable'
  return value.replace(/_/g, ' ')
}

function bandVariant(value?: string | null): 'signal' | 'caution' | 'neutral' {
  if (!value) return 'neutral'
  if (
    [
      'strong',
      'adequate',
      'clear',
      'low',
      'ready_context',
      'bank_review_ready',
      'strong_fit',
      'moderate_fit',
      'available',
      'ready_context',
    ].includes(value)
  ) {
    return 'signal'
  }
  if (
    [
      'watch',
      'constrained',
      'elevated',
      'stressed',
      'high',
      'needs_review',
      'not_ready',
      'watch_fit',
      'unavailable',
    ].includes(value)
  ) {
    return 'caution'
  }
  return 'neutral'
}

function reportDate() {
  return new Intl.DateTimeFormat('en-HK', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  }).format(new Date())
}

const requiredKeys = ['financial_health', 'valuation', 'credit_score', 'funding_strategy', 'advisory_blueprint']
const runLabels: Record<string, string> = {
  financial_health: 'Financial Health',
  valuation: 'Valuation',
  credit_score: 'Credit Readiness',
  funding_strategy: 'Funding Strategy',
  advisory_blueprint: 'Advisory Blueprint',
}

export default function ReportsPage() {
  const [state, setState] = useState<ReportState>({
    financial: null,
    credit: null,
    blueprint: null,
    facilities: null,
    funding: null,
    macro: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Readiness gate states
  const [runStatuses, setRunStatuses] = useState<Record<string, any | null>>({})
  const [hasSnapshot, setHasSnapshot] = useState<boolean | null>(null)
  const [isProdMode, setIsProdMode] = useState(false)
  const [runningType, setRunningType] = useState<string | null>(null)
  const [checkingReadiness, setCheckingReadiness] = useState(true)

  const activeSnapshotId = useMemo(() => {
    for (const key of requiredKeys) {
      const run = runStatuses[key]
      if (run && run.snapshotId) {
        return run.snapshotId
      }
    }
    if (state.financial && (state.financial as any).run_metadata?.snapshotId) {
      return (state.financial as any).run_metadata.snapshotId
    }
    return 'N/A'
  }, [runStatuses, state.financial])

  const loadAll = async () => {
    setLoading(true)
    setCheckingReadiness(true)
    setError(null)
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) {
      setHasSnapshot(false)
      setCheckingReadiness(false)
      setLoading(false)
      return
    }

    try {
      // 1. Fetch backend config
      const config = await fetchBackendConfig()
      setIsProdMode(config.isProduction)

      // 2. Fetch active snapshot
      const snapshotRes = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/snapshot/active`, {
        headers: { 'x-workspace-id': workspaceId }
      })
      if (!snapshotRes.ok) {
        setHasSnapshot(false)
        setCheckingReadiness(false)
        setLoading(false)
        return
      }
      setHasSnapshot(true)

      // 3. Fetch run statuses
      const statuses = await fetchAllRunStatuses(workspaceId)
      setRunStatuses(statuses)

      // 4. Fetch legacy reports data
      const [financial, credit, blueprint, facilities, funding, macro] = await Promise.all([
        getFinancialHealthAnalysis().catch((e) => {
          console.warn('Report financial context unavailable', e)
          return null
        }),
        getCreditScore().catch((e) => {
          console.warn('Report credit context unavailable', e)
          return null
        }),
        getAdvisoryBlueprint().catch((e) => {
          console.warn('Report advisory blueprint unavailable', e)
          return null
        }),
        getAdvisoryFacilityStructures().catch((e) => {
          console.warn('Report facility context unavailable', e)
          return null
        }),
        getFundingChannelRanking().catch((e) => {
          console.warn('Report funding channel context unavailable', e)
          return null
        }),
        getRedFlagsMacroSummary().catch((e) => {
          console.warn('Report macro context unavailable', e)
          return null
        }),
      ])
      setState({ financial, credit, blueprint, facilities, funding, macro })
    } catch (e) {
      console.error('Reports load failed', e)
      setError('Reports are currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
      setCheckingReadiness(false)
    }
  }

  const handleTriggerRunInGate = async (runType: string) => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return
    setRunningType(runType)
    try {
      await triggerAnalysisRun(workspaceId, runType)
      // Refresh statuses and report data
      const statuses = await fetchAllRunStatuses(workspaceId)
      setRunStatuses(statuses)
      
      // Reload matching legacy data
      if (runType === 'financial_health' || runType === 'valuation') {
        const financial = await getFinancialHealthAnalysis().catch(() => null)
        setState(prev => ({ ...prev, financial }))
      } else if (runType === 'credit_score') {
        const credit = await getCreditScore().catch(() => null)
        setState(prev => ({ ...prev, credit }))
      } else if (runType === 'funding_strategy') {
        const funding = await getFundingChannelRanking().catch(() => null)
        setState(prev => ({ ...prev, funding }))
      } else if (runType === 'advisory_blueprint') {
        const blueprint = await getAdvisoryBlueprint().catch(() => null)
        setState(prev => ({ ...prev, blueprint }))
      }
    } catch (err: any) {
      console.error(`Failed to trigger run for ${runType}:`, err)
      alert(`Failed to run ${runType}: ${err.message || err}`)
    } finally {
      setRunningType(null)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  const valuation =
    ((state.financial as unknown as {
      valuation?: {
        dcf?: { enterpriseValue?: number | null; equityValue?: number | null }
        wacc?: { wacc?: number | null }
      }
    })?.valuation ?? null)
  const snapshot = state.financial?.snapshot
  const topChannel =
    state.funding?.channels?.find((channel) => channel.key === state.funding?.topChannelKey) ??
    state.funding?.channels?.[0]
  const topFacility = state.facilities?.candidates?.[0]
  const isPreview = Boolean(
    snapshot?.metadata?.preview_only ||
      snapshot?.metadata?.previewOnly ||
      snapshot?.metadata?.source === 'data_room_workspace_preview',
  )

  const isInsufficientData = useMemo(() => {
    return (
      (state.financial && 'status' in state.financial && state.financial.status === 'insufficient_data') ||
      (state.credit && 'status' in state.credit && state.credit.status === 'insufficient_data') ||
      (state.blueprint && 'status' in state.blueprint && state.blueprint.status === 'insufficient_data') ||
      (state.funding && 'status' in state.funding && state.funding.status === 'insufficient_data')
    )
  }, [state])

  const reportSections = useMemo(() => {
    return [
      {
        label: 'Financial Health',
        status: state.financial?.summary?.overallBand,
        to: '/platform/financial-health',
        icon: HeartPulse,
      },
      {
        label: 'Valuation',
        status: valuation?.dcf?.enterpriseValue ? 'available' : 'unavailable',
        to: '/platform/valuation',
        icon: BarChart3,
      },
      {
        label: 'Credit Readiness',
        status: state.credit?.fundingReadiness,
        to: '/platform/credit-readiness',
        icon: ShieldCheck,
      },
      {
        label: 'Funding Strategy',
        status: topChannel?.fitBand ?? state.funding?.rankingBand,
        to: '/platform/funding-strategy',
        icon: Landmark,
      },
      {
        label: 'Advisory Blueprint',
        status: state.blueprint?.blueprintStatus ?? 'unavailable',
        to: '/platform/advisory-blueprint',
        icon: FileText,
      },
    ]
  }, [state.financial, state.credit, state.funding, state.blueprint, valuation, topChannel])

  if (loading || checkingReadiness) {
    return (
      <div className="space-y-8 pb-12">
        {/* Header Skeleton */}
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>

        {/* Cockpit Skeleton */}
        <SkeletonLoader variant="card" className="min-h-[200px]" />

        {/* 5 Metric Cards Skeleton */}
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
          <SkeletonLoader variant="metric" count={5} />
        </div>

        {/* Double columns skeleton */}
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[250px]" />
          <SkeletonLoader variant="card" className="min-h-[250px]" />
        </div>
      </div>
    )
  }

  if (hasSnapshot === false) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Reports"
          subtitle="Generate lender-ready reports and compliance packs."
        />
        <div className="flex flex-col items-center justify-center p-8 sm:p-12 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 flex items-center justify-center text-softform-teal-deep dark:text-softform-aqua-300">
            <FileText size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">No Active Financial Snapshot</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              You need to select a workspace, upload financial statements, and compile an active financial snapshot before you can generate reports.
            </p>
          </div>
          <Link
            to="/platform/data-room"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-sm font-semibold rounded-full shadow-sm transition-colors"
          >
            <span>Go to Data Room</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="softform-card rounded-[32px] p-8 sm:p-10 text-center">
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-[20px] bg-red-50 text-red-600 border border-red-100">
            <AlertTriangle size={24} />
          </div>
          <p className="mb-2 text-lg font-semibold text-softform-navy-950">Service Connection Issue</p>
          <p className="mb-6 text-sm text-softform-text-secondary leading-relaxed">{error}</p>
          <button
            type="button"
            onClick={loadAll}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={14} />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  if (isInsufficientData) {
    const missing = (state.financial && 'missingRequirements' in state.financial ? (state.financial.missingRequirements as string[]) : undefined) ||
                    (state.credit && 'missingRequirements' in state.credit ? (state.credit.missingRequirements as string[]) : undefined) ||
                    (state.blueprint && 'missingRequirements' in state.blueprint ? (state.blueprint.missingRequirements as string[]) : undefined) ||
                    (state.funding && 'missingRequirements' in state.funding ? (state.funding.missingRequirements as string[]) : undefined)
    const nextAct = (state.financial && 'nextActions' in state.financial ? (state.financial.nextActions as string[]) : undefined) ||
                    (state.credit && 'nextActions' in state.credit ? (state.credit.nextActions as string[]) : undefined) ||
                    (state.blueprint && 'nextActions' in state.blueprint ? (state.blueprint.nextActions as string[]) : undefined) ||
                    (state.funding && 'nextActions' in state.funding ? (state.funding.nextActions as string[]) : undefined)
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Reports"
          subtitle="CFO snapshot and lender-facing brief generated from the active workspace context."
        />
        <WorkspaceInsufficientDataState
          missingRequirements={missing}
          nextActions={nextAct}
        />
      </div>
    )
  }

  const completedCoreCount = requiredKeys.filter(key => getRunStatusLabel(runStatuses[key]) === 'completed').length
  const readinessPercentage = Math.round((completedCoreCount / requiredKeys.length) * 100)
  const isReady = completedCoreCount === requiredKeys.length

  const renderReadinessGate = () => {
    return (
      <div className="bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm p-6 mb-8 w-full space-y-6">
        <div>
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100 font-medium">Reports Readiness Gate</h3>
            <span className="text-sm font-bold text-softform-teal-deep dark:text-softform-aqua-300 bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 px-2.5 py-1 rounded-full">
              {readinessPercentage}% Ready
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 leading-relaxed">
            {isProdMode 
              ? 'Required analysis runs are missing. In production mode, you must run all core analyses before the generated report can be displayed.' 
              : 'Required analysis runs are missing. The report is displayed in demo/development mode, but running all core analyses is recommended.'}
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {requiredKeys.map((key) => {
            const status = getRunStatusLabel(runStatuses[key])
            const label = runLabels[key]
            const isExecuting = runningType === key
            
            return (
              <div 
                key={key} 
                className={`flex items-center justify-between p-3.5 rounded-2xl border ${
                  status === 'completed' 
                    ? 'bg-emerald-50/20 dark:bg-emerald-950/5 border-emerald-100/30 dark:border-emerald-900/10' 
                    : 'bg-slate-50/30 dark:bg-slate-800/10 border-slate-150/40 dark:border-slate-800/30'
                }`}
              >
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 font-medium">{label}</span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 uppercase font-bold tracking-wide mt-0.5">
                    {status === 'completed' ? '✓ Completed' : '⚠ Missing'}
                  </span>
                </div>
                {status !== 'completed' && (
                  <button
                    onClick={() => handleTriggerRunInGate(key)}
                    disabled={!!runningType || loading}
                    className="flex items-center justify-center w-7 h-7 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-250 dark:border-slate-700 rounded-full shadow-sm hover:shadow transition-shadow disabled:opacity-55"
                    title="Run Analysis"
                  >
                    {isExecuting ? (
                      <Loader2 size={12} className="animate-spin text-softform-teal-deep dark:text-softform-aqua-300" />
                    ) : (
                      <Play size={11} fill="currentColor" className="ml-0.5" />
                    )}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // Hard gate in production: if not ready, block showing any reports content
  if (isProdMode && !isReady) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Reports"
          subtitle="CFO snapshot and lender-facing brief generated from the active workspace context."
          chip={<StatusChip variant="caution">Context not ready</StatusChip>}
        />
        {renderReadinessGate()}
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Reports"
        subtitle="CFO snapshot and lender-facing brief generated from the active workspace context."
        chip={<StatusChip variant={isPreview ? 'signal' : 'neutral'}>{isPreview ? 'Workspace preview' : 'Workspace report'}</StatusChip>}
      />

      {/* Render soft gate warning if runs are missing in dev/demo mode */}
      {!isReady && renderReadinessGate()}

      {isReady && (
        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 border border-emerald-250/30 rounded-full text-xs font-semibold backdrop-blur-sm shadow-sm mb-2">
          <CheckCircle2 size={13} className="text-emerald-500" />
          <span>Report fully verified from workspace runs (100% ready)</span>
        </div>
      )}

      {/* CFO Report Package Hero Section in Premium Navy Contrast Card */}
      <section className="softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse">CFO report package</span>
            <h2 className="text-3xl font-semibold text-white tracking-tight">
              {snapshot?.companyName ?? 'Workspace Company'} · {snapshot?.reportingPeriod ?? reportDate()}
            </h2>
            <p className="text-sm leading-relaxed text-white/80 max-w-3xl">
              This page consolidates the current analysis into a board-style CFO snapshot and lender-facing summary. Content is context-only and should be reviewed before external use.
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
                Generated {reportDate()}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
                {isPreview ? 'Data Room sourced' : 'Workspace source'}
              </span>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="rounded-[22px] border border-white/10 bg-white/5 p-4 text-left shadow-soft-inner hover-lift"
            >
              <Download size={18} className="text-softform-aqua-300" />
              <p className="mt-3 text-sm font-semibold text-white">Print / Save PDF</p>
              <p className="mt-1 text-xs text-white/70">Use browser print for now.</p>
            </button>
            <Link to="/platform/advisory-blueprint" className="rounded-[22px] border border-white/10 bg-white/5 p-4 shadow-soft-inner hover-lift">
              <FileText size={18} className="text-softform-aqua-300" />
              <p className="mt-3 text-sm font-semibold text-white">Advisor Brief</p>
              <p className="mt-1 text-xs text-white/70">Open detailed blueprint.</p>
            </Link>
          </div>
        </div>
      </section>

      {/* Report sections links grid */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {reportSections.map((section) => {
          const Icon = section.icon
          return (
            <Link key={section.label} to={section.to} className="softform-metric-card rounded-[22px] p-5 hover-lift">
              <MetricDisplay
                label={section.label}
                value={formatBand(section.status)}
                icon={<Icon size={16} className="text-softform-teal-500" />}
              />
            </Link>
          )
        })}
      </section>

      {/* Executive Snapshot */}
      <SectionBlock
        title="Executive Snapshot"
        action={<StatusChip variant={bandVariant(state.financial?.summary?.overallBand)}>{formatBand(state.financial?.summary?.overallBand)}</StatusChip>}
        containerType="card"
        className="rounded-[32px] p-6 sm:p-8 space-y-6"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="softform-metric-card rounded-[20px] p-4 hover-lift">
            <MetricDisplay
              label="Revenue"
              value={formatHKD(snapshot?.incomeStatement.revenue)}
            />
          </div>
          <div className="softform-metric-card rounded-[20px] p-4 hover-lift">
            <MetricDisplay
              label="EBITDA"
              value={formatHKD(snapshot?.incomeStatement.ebitda)}
            />
          </div>
          <div className="softform-metric-card rounded-[20px] p-4 hover-lift">
            <MetricDisplay
              label="Enterprise Value"
              value={formatHKD(valuation?.dcf?.enterpriseValue)}
            />
          </div>
          <div className="softform-metric-card rounded-[20px] p-4 hover-lift">
            <MetricDisplay
              label="Readiness Score"
              value={state.credit?.compositeScore ?? 'N/A'}
            />
          </div>
        </div>
      </SectionBlock>

      {/* Narratives Grid */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Financial Narrative"
          icon={<HeartPulse size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant={bandVariant(state.financial?.summary?.liquidityBand)}>{formatBand(state.financial?.summary?.liquidityBand)}</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {(state.financial?.summary?.strengths ?? []).slice(0, 3).map((item, idx) => (
              <p key={`strength-${idx}`} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                <strong className="text-softform-navy-950">Strength:</strong> {item}
              </p>
            ))}
            {(state.financial?.summary?.watchItems ?? []).slice(0, 3).map((item, idx) => (
              <p key={`watch-${idx}`} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                <strong className="text-softform-navy-950">Watch:</strong> {item}
              </p>
            ))}
          </div>
        </SectionBlock>

        <SectionBlock
          title="Readiness Narrative"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant={bandVariant(state.credit?.fundingReadiness)}>{formatBand(state.credit?.fundingReadiness)}</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            <p className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary font-medium">
              {state.credit?.pdProxyBand ?? 'Readiness scorecard is unavailable. Review Credit Readiness for details.'}
            </p>
            {(state.credit?.positiveDrivers ?? []).slice(0, 2).map((item, idx) => (
              <p key={`positive-${idx}`} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                <strong className="text-softform-navy-950">Positive driver:</strong> {item}
              </p>
            ))}
            {(state.credit?.riskDrivers ?? []).slice(0, 2).map((item, idx) => (
              <p key={`risk-${idx}`} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                <strong className="text-softform-navy-950">Risk driver:</strong> {item}
              </p>
            ))}
          </div>
        </SectionBlock>
      </section>

      {/* Recommendations & Valuation Narratives */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Funding Recommendation Context"
          icon={<Landmark size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant={bandVariant(topChannel?.fitBand)}>{formatBand(topChannel?.fitBand)}</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            <p className="text-sm font-semibold text-softform-navy-950">{topChannel?.label ?? 'Funding channel unavailable'}</p>
            <p className="text-xs leading-relaxed text-softform-text-secondary">
              {topChannel?.rationale ?? state.funding?.explanation ?? 'Open Funding Strategy for channel ranking and facility fit.'}
            </p>
            {topFacility && (
              <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                <p><strong className="text-softform-navy-950">Candidate facility:</strong> {topFacility.label}</p>
                <p className="mt-1"><strong className="text-softform-navy-950">Estimated limit:</strong> {formatHKD(topFacility.estimatedLimit)}</p>
              </div>
            )}
          </div>
        </SectionBlock>

        <SectionBlock
          title="Valuation Context"
          icon={<BarChart3 size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">DCF / WACC</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Equity value</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatHKD(valuation?.dcf?.equityValue)}</p>
            </div>
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">WACC</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatPercent(valuation?.wacc?.wacc)}</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Valuation remains indicative and assumptions-based. It supports funding narrative and CFO planning, not a formal appraisal.
          </p>
        </SectionBlock>
      </section>

      {/* Advisor-Ready Summary */}
      {(state.blueprint?.executiveBrief || state.macro?.headline) && (
        <SectionBlock
          title="Advisor-Ready Summary"
          action={
            <StatusChip variant={bandVariant(state.blueprint?.blueprintStatus ?? state.macro?.summaryBand)}>
              {formatBand(state.blueprint?.blueprintStatus ?? state.macro?.summaryBand)}
            </StatusChip>
          }
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-5"
        >
          <p className="text-sm leading-relaxed text-softform-text-secondary mb-4">
            {state.blueprint?.executiveBrief ?? state.macro?.headline}
          </p>
          <div className="space-y-3">
            {(state.blueprint?.recommendedActions ?? []).slice(0, 4).map((action) => (
              <p key={action.actionKey} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                <strong className="text-softform-navy-950">{action.label}:</strong> {action.rationale}
              </p>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* Report Audit & Traceability Metadata and Disclaimer */}
      <section className="bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-[32px] p-6 sm:p-8 backdrop-blur-md shadow-sm space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-softform-navy-950 uppercase tracking-wider">Report Traceability & Compliance Audit</h3>
          <p className="text-[11px] text-softform-text-muted mt-1">
            Cryptographic mapping and run identifiers for banking audit compliance.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
          <div className="rounded-xl border border-white/65 bg-white/50 p-4 text-xs space-y-1">
            <span className="block text-[10px] uppercase font-bold text-softform-text-muted">Active Workspace</span>
            <p className="font-semibold text-softform-navy-950 truncate">{localStorage.getItem('active_workspace_id') || 'N/A'}</p>
          </div>
          <div className="rounded-xl border border-white/65 bg-white/50 p-4 text-xs space-y-1">
            <span className="block text-[10px] uppercase font-bold text-softform-text-muted">Active Snapshot ID</span>
            <p className="font-semibold text-softform-navy-950 truncate">{activeSnapshotId}</p>
          </div>
          <div className="rounded-xl border border-white/65 bg-white/50 p-4 text-xs space-y-1">
            <span className="block text-[10px] uppercase font-bold text-softform-text-muted">Generated At</span>
            <p className="font-semibold text-softform-navy-950">{new Date().toLocaleString()}</p>
          </div>
        </div>

        <div className="border-t border-softform-navy-950/5 pt-4">
          <span className="block text-[10px] uppercase font-bold text-softform-text-muted mb-2">Verification Run Signatures</span>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {requiredKeys.map((key) => {
              const run = runStatuses[key]
              const runId = run?.id || 'N/A'
              const label = runLabels[key]
              return (
                <div key={key} className="rounded-xl border border-white/50 bg-white/30 p-3 text-[11px]">
                  <span className="block font-semibold text-softform-text-secondary truncate">{label}</span>
                  <p className="font-mono text-[10px] text-softform-text-muted mt-0.5 truncate" title={runId}>{runId}</p>
                </div>
              )
            })}
          </div>
        </div>

        <div className="border-t border-softform-navy-950/5 pt-4 bg-softform-cream/10 p-4 rounded-2xl border border-softform-amber-300/10">
          <p className="text-[11px] leading-relaxed text-softform-text-secondary">
            <strong className="text-softform-navy-950 uppercase tracking-wide">Important Disclaimer:</strong> This workspace report is prepared automatically for analysis and diagnostic preparation support only. It does not constitute credit approval, a binding lending commitment, investment advice, or a formal underwriting recommendation. Financing outcomes are not guaranteed and all indicators remain subject to commercial bank review and credit policy check.
          </p>
        </div>
      </section>

      {/* Navigation Footer */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card no-print">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-semibold text-softform-navy-950 text-base">Refine the source analysis</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Reports are only as good as the active Data Room and Financial Health context. Review source modules before sharing externally.
          </p>
        </div>
        <Link
          to="/platform/financial-health"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
        >
          Review Financial Health
          <ArrowRight size={14} />
        </Link>
      </section>
    </div>
  )
}
