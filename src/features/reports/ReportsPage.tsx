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
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import DemoFlowRail from '../../components/platform/DemoFlowRail'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import { getCreditScore, getAdvisoryBlueprint, getAdvisoryFacilityStructures } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getFundingChannelRanking, getRedFlagsMacroSummary } from '../market-watch/api/marketWatchApi'
import type { CreditScoringResult, AdvisoryBlueprintResponse, FacilityStructuringResponse } from '../advisory-blueprint/types'
import type { FinancialAnalysisResponse, FundingChannelRankingResponse, RedFlagsMacroSummaryResponse } from '../market-watch/types'

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
  if (['strong', 'adequate', 'clear', 'low', 'ready_context', 'bank_review_ready', 'strong_fit', 'moderate_fit'].includes(value)) return 'signal'
  if (['watch', 'constrained', 'elevated', 'stressed', 'high', 'needs_review', 'not_ready', 'watch_fit'].includes(value)) return 'caution'
  return 'neutral'
}

function reportDate() {
  return new Intl.DateTimeFormat('en-HK', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  }).format(new Date())
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

  const loadReports = async () => {
    setLoading(true)
    setError(null)
    try {
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
    }
  }

  useEffect(() => {
    loadReports()
  }, [])

  const valuation = ((state.financial as unknown as { valuation?: { dcf?: { enterpriseValue?: number | null; equityValue?: number | null }; wacc?: { wacc?: number | null } } })?.valuation ?? null)
  const snapshot = state.financial?.snapshot
  const topChannel = state.funding?.channels?.find((channel) => channel.key === state.funding?.topChannelKey) ?? state.funding?.channels?.[0]
  const topFacility = state.facilities?.candidates?.[0]
  const isPreview = Boolean(snapshot?.metadata?.preview_only || snapshot?.metadata?.previewOnly || snapshot?.metadata?.source === 'data_room_workspace_preview')

  const reportSections = useMemo(() => {
    const sections = [
      { label: 'Financial Health', status: state.financial?.summary?.overallBand, to: '/platform/financial-health', icon: HeartPulse },
      { label: 'Valuation', status: valuation?.dcf?.enterpriseValue ? 'available' : 'unavailable', to: '/platform/valuation', icon: BarChart3 },
      { label: 'Credit Readiness', status: state.credit?.fundingReadiness, to: '/platform/credit-readiness', icon: ShieldCheck },
      { label: 'Funding Strategy', status: topChannel?.fitBand ?? state.funding?.rankingBand, to: '/platform/funding-strategy', icon: Landmark },
      { label: 'Advisory Blueprint', status: state.blueprint ? 'available' : 'unavailable', to: '/platform/advisory-blueprint', icon: FileText },
    ]
    return sections
  }, [state.financial, state.credit, state.funding, state.blueprint, valuation, topChannel])

  if (loading) {
    return (
      <div className="flex min-h-[50dvh] flex-col items-center justify-center space-y-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep animate-spin">
          <RotateCw size={24} />
        </div>
        <p className="text-sm font-medium text-softform-text-secondary animate-pulse">Preparing CFO report...</p>
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
            onClick={loadReports}
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
        title="Reports"
        subtitle="CFO snapshot and lender-facing brief generated from the active workspace context."
        chip={<StatusChip variant={isPreview ? 'signal' : 'neutral'}>{isPreview ? 'Workspace preview' : 'Demo report'}</StatusChip>}
      />

      <DemoFlowRail />

      <section className="softform-panel rounded-[32px] p-8 space-y-6 shadow-floating-panel relative overflow-hidden bg-gradient-to-br from-white/95 via-softform-mist-50/70 to-softform-ice-100/50 border border-white">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-softform-teal-deep">CFO report package</span>
            <h2 className="text-3xl font-black text-softform-navy-950 tracking-tight">
              {snapshot?.companyName ?? 'Workspace Company'} · {snapshot?.reportingPeriod ?? reportDate()}
            </h2>
            <p className="text-sm leading-relaxed text-softform-text-secondary max-w-3xl">
              This page consolidates the current analysis into a board-style CFO snapshot and lender-facing summary. Content is context-only and should be reviewed before external use.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-white/70 bg-white/60 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-softform-navy-950">
                Generated {reportDate()}
              </span>
              <span className="rounded-full border border-white/70 bg-white/60 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-softform-navy-950">
                {isPreview ? 'Data Room sourced' : 'Demo source'}
              </span>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 text-left shadow-soft-inner hover-lift"
            >
              <Download size={18} className="text-softform-teal-deep" />
              <p className="mt-3 text-sm font-black text-softform-navy-950">Print / Save PDF</p>
              <p className="mt-1 text-xs text-softform-text-secondary">Use browser print for now.</p>
            </button>
            <Link to="/platform/advisory-blueprint" className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner hover-lift">
              <FileText size={18} className="text-softform-teal-deep" />
              <p className="mt-3 text-sm font-black text-softform-navy-950">Advisor Brief</p>
              <p className="mt-1 text-xs text-softform-text-secondary">Open detailed blueprint.</p>
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {reportSections.map((section) => {
          const Icon = section.icon
          return (
            <Link key={section.label} to={section.to} className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
              <Icon size={20} className="text-softform-teal-deep" />
              <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">{section.label}</p>
              <p className="mt-2 text-sm font-black text-softform-navy-950 capitalize">{formatBand(section.status)}</p>
            </Link>
          )
        })}
      </section>

      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-bold text-softform-navy-950">Executive Snapshot</h2>
          <StatusChip variant={bandVariant(state.financial?.summary?.overallBand)}>{formatBand(state.financial?.summary?.overallBand)}</StatusChip>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-[20px] border border-white/60 bg-white/45 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Revenue</p>
            <p className="mt-2 text-xl font-black text-softform-navy-950 tabular-finance">{formatHKD(snapshot?.incomeStatement.revenue)}</p>
          </div>
          <div className="rounded-[20px] border border-white/60 bg-white/45 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">EBITDA</p>
            <p className="mt-2 text-xl font-black text-softform-navy-950 tabular-finance">{formatHKD(snapshot?.incomeStatement.ebitda)}</p>
          </div>
          <div className="rounded-[20px] border border-white/60 bg-white/45 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Enterprise Value</p>
            <p className="mt-2 text-xl font-black text-softform-navy-950 tabular-finance">{formatHKD(valuation?.dcf?.enterpriseValue)}</p>
          </div>
          <div className="rounded-[20px] border border-white/60 bg-white/45 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Readiness Score</p>
            <p className="mt-2 text-xl font-black text-softform-navy-950 tabular-finance">{state.credit?.compositeScore ?? 'N/A'}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <HeartPulse size={20} className="text-softform-teal-deep" />
              Financial Narrative
            </h2>
            <StatusChip variant={bandVariant(state.financial?.summary?.liquidityBand)}>{formatBand(state.financial?.summary?.liquidityBand)}</StatusChip>
          </div>
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
        </div>

        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <ShieldCheck size={20} className="text-softform-teal-deep" />
              Readiness Narrative
            </h2>
            <StatusChip variant={bandVariant(state.credit?.fundingReadiness)}>{formatBand(state.credit?.fundingReadiness)}</StatusChip>
          </div>
          <div className="space-y-3">
            <p className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
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
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <Landmark size={20} className="text-softform-teal-deep" />
              Funding Recommendation Context
            </h2>
            <StatusChip variant={bandVariant(topChannel?.fitBand)}>{formatBand(topChannel?.fitBand)}</StatusChip>
          </div>
          <div className="space-y-3">
            <p className="text-sm font-black text-softform-navy-950">{topChannel?.label ?? 'Funding channel unavailable'}</p>
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
        </div>

        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <BarChart3 size={20} className="text-softform-teal-deep" />
              Valuation Context
            </h2>
            <StatusChip variant="neutral">DCF / WACC</StatusChip>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Equity value</p>
              <p className="mt-1 text-xl font-black text-softform-navy-950 tabular-finance">{formatHKD(valuation?.dcf?.equityValue)}</p>
            </div>
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">WACC</p>
              <p className="mt-1 text-xl font-black text-softform-navy-950 tabular-finance">{formatPercent(valuation?.wacc?.wacc)}</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Valuation remains indicative and assumptions-based. It supports funding narrative and CFO planning, not a formal appraisal.
          </p>
        </div>
      </section>

      {(state.blueprint?.executiveSummary || state.macro?.headline) && (
        <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950">Advisor-Ready Summary</h2>
            <StatusChip variant={bandVariant(state.macro?.summaryBand)}>{formatBand(state.macro?.summaryBand)}</StatusChip>
          </div>
          <p className="text-sm leading-relaxed text-softform-text-secondary">
            {state.blueprint?.executiveSummary ?? state.macro?.headline}
          </p>
          {(state.blueprint?.recommendedActions ?? []).slice(0, 4).map((action, idx) => (
            <p key={idx} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
              {action}
            </p>
          ))}
        </section>
      )}

      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-bold text-softform-navy-950 text-base">Refine the source analysis</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Reports are only as good as the active Data Room and Financial Health context. Review source modules before sharing externally.
          </p>
        </div>
        <Link
          to="/platform/financial-health"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-softform-navy-800 transition shadow-sm"
        >
          Review Financial Health
          <ArrowRight size={14} />
        </Link>
      </section>
    </div>
  )
}
