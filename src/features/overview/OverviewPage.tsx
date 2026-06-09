import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  FileText,
  HeartPulse,
  Landmark,
  RotateCw,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import DemoFlowRail from '../../components/platform/DemoFlowRail'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import { getCreditScore } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getFundingChannelRanking, getRedFlagsMacroSummary } from '../market-watch/api/marketWatchApi'
import type { CreditScoringResult } from '../advisory-blueprint/types'
import type { FinancialAnalysisResponse, FundingChannelRankingResponse, RedFlagsMacroSummaryResponse } from '../market-watch/types'

type OverviewState = {
  financial: FinancialAnalysisResponse | null
  credit: CreditScoringResult | null
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

function variantForBand(value?: string | null): 'signal' | 'caution' | 'neutral' {
  if (!value) return 'neutral'
  if (['strong', 'adequate', 'clear', 'low', 'ready_context', 'bank_review_ready', 'working_capital_priority', 'trade_cycle_priority'].includes(value)) {
    return 'signal'
  }
  if (['watch', 'constrained', 'elevated', 'stressed', 'high', 'needs_review', 'not_ready', 'risk_context_priority'].includes(value)) {
    return 'caution'
  }
  return 'neutral'
}

export default function OverviewPage() {
  const [state, setState] = useState<OverviewState>({ financial: null, credit: null, funding: null, macro: null })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadOverview = async () => {
    setLoading(true)
    setError(null)
    try {
      const [financial, credit, funding, macro] = await Promise.all([
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
      ])
      setState({ financial, credit, funding, macro })
    } catch (e) {
      console.error('Overview load failed', e)
      setError('Overview is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOverview()
  }, [])

  const valuation = ((state.financial as unknown as { valuation?: { dcf?: { enterpriseValue?: number | null; equityValue?: number | null }; wacc?: { wacc?: number | null } } })?.valuation ?? null)
  const topChannel = state.funding?.channels?.find((channel) => channel.key === state.funding?.topChannelKey) ?? state.funding?.channels?.[0]

  const nextActions = useMemo(() => {
    const actions: { title: string; body: string; to: string; icon: typeof ArrowRight }[] = []
    if (!state.financial) {
      actions.push({ title: 'Upload financial records', body: 'Start with Data Room to activate preview analysis.', to: '/platform/data-room', icon: ArrowRight })
    } else if ((state.financial.summary?.watchItems?.length ?? 0) > 0) {
      actions.push({ title: 'Review financial watch items', body: state.financial.summary?.watchItems?.[0] ?? 'Inspect ratio and integrity signals.', to: '/platform/financial-health', icon: ArrowRight })
    }
    if (state.credit?.fundingReadiness === 'needs_review' || state.credit?.fundingReadiness === 'not_ready') {
      actions.push({ title: 'Improve readiness scorecard', body: state.credit.nextDataNeeded?.[0] ?? 'Review scorecard drivers and next data needs.', to: '/platform/credit-readiness', icon: ArrowRight })
    }
    if (topChannel) {
      actions.push({ title: `Prioritize ${topChannel.label}`, body: topChannel.useCase, to: '/platform/funding-strategy', icon: ArrowRight })
    }
    actions.push({ title: 'Generate advisory blueprint', body: 'Convert the current context into an advisor-ready brief.', to: '/platform/advisory-blueprint', icon: ArrowRight })
    return actions.slice(0, 4)
  }, [state.financial, state.credit, topChannel])

  if (loading) {
    return (
      <div className="flex min-h-[50dvh] flex-col items-center justify-center space-y-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep animate-spin">
          <RotateCw size={24} />
        </div>
        <p className="text-sm font-medium text-softform-text-secondary animate-pulse">Loading executive overview...</p>
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
            onClick={loadOverview}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={14} />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Overview"
        subtitle="Executive command center across financial health, valuation, credit readiness, funding strategy, and macro watch signals."
        chip={<StatusChip variant={variantForBand(state.macro?.summaryBand)}>{formatBand(state.macro?.summaryBand ?? 'workspace')}</StatusChip>}
      />

      <DemoFlowRail />

      <section className="softform-panel rounded-[32px] p-8 space-y-6 shadow-floating-panel relative overflow-hidden bg-gradient-to-br from-white/95 via-softform-mist-50/70 to-softform-ice-100/50 border border-white">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-softform-teal-deep">FinSight CFO cockpit</span>
            <h2 className="text-3xl font-black text-softform-navy-950 tracking-tight">
              {state.financial?.snapshot.companyName ?? 'Workspace Company'} · CFO decision view
            </h2>
            <p className="text-sm leading-relaxed text-softform-text-secondary max-w-3xl">
              {state.macro?.headline ?? 'Use this view to move from uploaded records to financial diagnostics, indicative valuation, readiness scoring, channel strategy, and advisory output.'}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <Link to="/platform/data-room" className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner hover-lift">
              <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Data mode</p>
              <p className="mt-1 text-sm font-black text-softform-navy-950">{state.financial?.snapshot.metadata?.source ? 'Workspace preview' : 'Demo / fallback'}</p>
            </Link>
            <Link to="/platform/advisory-blueprint" className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner hover-lift">
              <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Advisor output</p>
              <p className="mt-1 text-sm font-black text-softform-navy-950">Blueprint ready</p>
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Link to="/platform/financial-health" className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <HeartPulse size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Financial Health</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950">{formatBand(state.financial?.summary?.overallBand)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">Revenue {formatHKD(state.financial?.snapshot.incomeStatement.revenue)}</p>
        </Link>
        <Link to="/platform/valuation" className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <BarChart3 size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Valuation</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950 tabular-finance">{formatHKD(valuation?.dcf?.enterpriseValue)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">WACC {formatPercent(valuation?.wacc?.wacc)}</p>
        </Link>
        <Link to="/platform/credit-readiness" className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <ShieldCheck size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Credit Readiness</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950 tabular-finance">{state.credit?.compositeScore ?? 'N/A'}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">{formatBand(state.credit?.fundingReadiness)}</p>
        </Link>
        <Link to="/platform/funding-strategy" className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <Landmark size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Funding Strategy</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950">{topChannel ? `#${topChannel.rank}` : 'N/A'}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">{topChannel?.label ?? 'Channel context unavailable'}</p>
        </Link>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <TrendingUp size={20} className="text-softform-teal-deep" />
              Macro & Market Watch
            </h2>
            <StatusChip variant={variantForBand(state.macro?.summaryBand)}>{formatBand(state.macro?.summaryBand)}</StatusChip>
          </div>
          <div className="space-y-3">
            {(state.macro?.redFlags ?? []).slice(0, 3).map((flag) => (
              <div key={flag.flagKey} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-bold text-softform-navy-950">{flag.label}</p>
                  <span className="rounded bg-softform-cream px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-softform-amber-500">
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
        </div>

        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <FileText size={20} className="text-softform-teal-deep" />
              Recommended Next Actions
            </h2>
            <StatusChip variant="neutral">Workflow</StatusChip>
          </div>
          <div className="space-y-3">
            {nextActions.map((action) => (
              <Link key={action.title} to={action.to} className="group flex items-start justify-between gap-4 rounded-xl border border-white/60 bg-white/45 px-4 py-3 hover:bg-white/70 transition">
                <div>
                  <p className="text-sm font-bold text-softform-navy-950">{action.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-softform-text-secondary">{action.body}</p>
                </div>
                <ArrowRight size={16} className="mt-1 shrink-0 text-softform-teal-deep transition group-hover:translate-x-1" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-bold text-softform-navy-950 text-base">Start from source documents</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Upload or activate records in Data Room, then move through diagnostics, valuation, readiness, funding strategy, and advisory output.
          </p>
        </div>
        <Link
          to="/platform/data-room"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-softform-navy-800 transition shadow-sm"
        >
          Open Data Room
          <ArrowRight size={14} />
        </Link>
      </section>
    </div>
  )
}
