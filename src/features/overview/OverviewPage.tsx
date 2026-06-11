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
import type { FinancialAnalysisResponse, FundingChannelRankingResponse, RedFlagsMacroSummaryResponse } from '../market-watch/types'
import type { BochkWorkflowRun } from '../workflow/workflowApi'
import { formatHKD, formatPercent, formatBand, bandVariant, variantForBand } from '../../lib/formatters'

type OverviewState = {
  financial: FinancialAnalysisResponse | null
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
  const [state, setState] = useState<OverviewState>({ financial: null, credit: null, funding: null, macro: null, workflow: null })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadOverview = async () => {
    setLoading(true)
    setError(null)
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

  useEffect(() => {
    loadOverview()
  }, [])

  const valuation = state.financial?.valuation ?? null
  const topChannel = state.funding?.channels?.find((channel) => channel.key === state.funding?.topChannelKey) ?? state.funding?.channels?.[0]

  const nextActions = useMemo(() => {
    const actions: NextAction[] = []
    if (!state.financial) {
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
  }, [state.financial, state.credit, topChannel])

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

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Overview"
        subtitle="Executive command center across financial health, valuation, credit readiness, funding strategy, and macro watch signals."
        chip={<StatusChip variant={bandVariant(state.macro?.summaryBand)}>{formatBand(state.macro?.summaryBand ?? 'workspace')}</StatusChip>}
      />

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
