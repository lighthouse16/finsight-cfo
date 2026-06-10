import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, BarChart3, Calculator, RotateCw, TrendingUp } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import SkeletonLoader from '../../components/platform/SkeletonLoader'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import type { FinancialAnalysisResponse, ValuationOutput } from '../market-watch/types'

function formatHKD(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  if (Math.abs(value) >= 1_000_000) return `HKD ${(value / 1_000_000).toFixed(2)}M`
  return `HKD ${value.toLocaleString()}`
}

function formatPercent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return `${(value * 100).toFixed(2)}%`
}

function formatMultiple(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return `${value.toFixed(2)}x`
}

function statusVariant(status?: string | null): 'signal' | 'caution' | 'neutral' {
  if (status === 'pass') return 'signal'
  if (status === 'warning' || status === 'fail') return 'caution'
  return 'neutral'
}

function assumptionNumber(valuation: ValuationOutput, key: string) {
  const value = valuation.assumptions?.[key]
  return typeof value === 'number' ? value : null
}

export default function ValuationPage() {
  const [analysis, setAnalysis] = useState<FinancialAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadValuation = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getFinancialHealthAnalysis()
      setAnalysis(data)
    } catch (e) {
      console.error('Valuation load failed', e)
      setError('Valuation is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadValuation()
  }, [])

  if (loading) {
    return (
      <div className="space-y-8 pb-12">
        {/* Header Skeleton */}
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>

        {/* Cockpit Skeleton */}
        <SkeletonLoader variant="card" className="min-h-[200px]" />

        {/* 4 Metric Cards Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <SkeletonLoader variant="metric" count={4} />
        </div>

        {/* Double columns skeleton */}
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[250px]" />
          <SkeletonLoader variant="card" className="min-h-[250px]" />
        </div>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <div className="softform-card rounded-[32px] p-8 sm:p-10 text-center">
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-[20px] bg-red-50 text-red-600 border border-red-100">
            <AlertTriangle size={24} />
          </div>
          <p className="mb-2 text-lg font-semibold text-softform-navy-950">Service Connection Issue</p>
          <p className="mb-6 text-sm text-softform-text-secondary leading-relaxed">
            {error || 'Unable to connect to valuation services.'}
          </p>
          <button
            type="button"
            onClick={loadValuation}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={14} />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  const valuation = analysis.valuation ?? {}
  const snapshot = analysis.snapshot
  const dcf = valuation.dcf
  const wacc = valuation.wacc
  const valuationYears = dcf?.valuationYears ?? []
  const sensitivity = valuation.sensitivity ?? []
  const sanityChecks = valuation.sanityChecks ?? []
  const modelWarnings = Array.from(
    new Set([
      ...(valuation.warnings ?? []),
      ...(dcf?.warnings ?? []),
      ...(wacc?.warnings ?? []),
    ])
  )
  const isPreview = Boolean(snapshot.metadata?.preview_only || snapshot.metadata?.previewOnly || snapshot.metadata?.source === 'data_room_workspace_preview')

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Valuation"
        subtitle="Indicative WACC and DCF valuation view built from the active financial analysis snapshot."
        chip={
          <StatusChip variant="neutral">
            {isPreview ? 'Preview valuation' : 'Demo valuation'}
          </StatusChip>
        }
      />

      {/* Business Valuation Hero Section in Premium Navy Contrast Card */}
      <section className="softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse">
              Business valuation engine
            </span>
            <h2 className="text-3xl font-semibold text-white tracking-tight">
              {snapshot.companyName} · {snapshot.reportingPeriod}
            </h2>
            <p className="text-sm leading-relaxed text-white/80 max-w-3xl">
              This DCF view is assumptions-based and intended to support the CFO narrative, funding readiness, and advisory preparation. It is not a formal appraisal or investment recommendation.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-around gap-6 bg-white/5 border border-white/10 rounded-[24px] p-6 backdrop-blur-md">
            <div className="space-y-2.5 w-full">
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Enterprise value</span>
                <span className="text-sm font-bold text-white tabular-finance">{formatHKD(dcf?.enterpriseValue)}</span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Equity value</span>
                <span className="text-sm font-bold text-white tabular-finance">{formatHKD(dcf?.equityValue)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">WACC</span>
                <span className="text-sm font-bold text-white tabular-finance">{formatPercent(wacc?.wacc)}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* KPI metric grid */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="PV explicit FCFF"
            value={formatHKD(dcf?.pvExplicitFcff)}
            description="Discounted operating cash flows"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="PV terminal value"
            value={formatHKD(dcf?.pvTerminalValue)}
            description="Long-term value component"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Net debt bridge"
            value={formatHKD(dcf?.netDebt)}
            description="Total debt less cash"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Implied EV / EBITDA"
            value={formatMultiple(dcf?.impliedEvEbitda)}
            description="Sanity-check multiple"
          />
        </div>
      </section>

      {/* WACC and DCF Bridge */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="WACC Build-Up"
          icon={<Calculator size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">CAPM-style</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              ['Cost of equity', formatPercent(wacc?.costOfEquity)],
              ['After-tax debt cost', formatPercent(wacc?.afterTaxCostOfDebt)],
              ['Debt weight', formatPercent(wacc?.debtWeight)],
              ['Equity weight', formatPercent(wacc?.equityWeight)],
              ['Risk-free rate', formatPercent(assumptionNumber(valuation, 'riskFreeRate'))],
              ['Terminal growth', formatPercent(assumptionNumber(valuation, 'terminalGrowthRate'))],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 flex justify-between items-center text-xs">
                <span className="font-semibold text-softform-text-secondary">{label}</span>
                <span className="font-bold text-softform-navy-950 tabular-finance">{value}</span>
              </div>
            ))}
          </div>
        </SectionBlock>

        <SectionBlock
          title="DCF Bridge"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">EV to Equity</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {[
              ['Enterprise value', formatHKD(dcf?.enterpriseValue)],
              ['Less net debt', formatHKD(dcf?.netDebt)],
              ['Equity value', formatHKD(dcf?.equityValue)],
              ['Terminal value share', formatPercent(dcf?.terminalValueShareOfEnterpriseValue)],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm">
                <span className="font-semibold text-softform-text-secondary">{label}</span>
                <span className="font-bold text-softform-navy-950 tabular-finance">{value}</span>
              </div>
            ))}
          </div>
        </SectionBlock>
      </section>

      {/* Valuation Years */}
      {valuationYears.length > 0 && (
        <SectionBlock
          title="Valuation Years"
          icon={<BarChart3 size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">FCFF PV</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {valuationYears.slice(0, 5).map((year) => (
              <div key={year.year} className="rounded-[20px] border border-white/60 bg-white/45 p-4 shadow-sm hover-lift flex flex-col justify-between min-h-[120px]">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">Year {year.year}</p>
                  <p className="mt-2 text-sm font-semibold text-softform-navy-950">FCFF {formatHKD(year.fcff)}</p>
                  <p className="mt-1 text-xs text-softform-text-secondary">PV {formatHKD(year.pvFcff)}</p>
                </div>
                <p className="mt-2 border-t border-softform-navy-950/5 pt-1.5 text-[10px] text-softform-text-muted">
                  Discount {year.discountFactor.toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* Sensitivity & Sanity Checks */}
      <section className="grid gap-6 lg:grid-cols-2">
        {sensitivity.length > 0 && (
          <SectionBlock
            title="Sensitivity Points"
            action={<StatusChip variant="neutral">WACC / Growth</StatusChip>}
            containerType="card"
            className="rounded-[28px] p-6 sm:p-8 space-y-5"
          >
            <div className="space-y-3">
              {sensitivity.slice(0, 5).map((point, idx) => (
                <div key={`${point.wacc}-${point.terminalGrowthRate}-${idx}`} className="grid grid-cols-3 gap-2 rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs items-center">
                  <span className="font-semibold text-softform-text-secondary">{formatPercent(point.wacc)}</span>
                  <span className="font-semibold text-softform-text-secondary text-center">g {formatPercent(point.terminalGrowthRate)}</span>
                  <span className="text-right font-bold text-softform-navy-950 tabular-finance">{formatHKD(point.enterpriseValue)}</span>
                </div>
              ))}
            </div>
          </SectionBlock>
        )}

        {sanityChecks.length > 0 && (
          <SectionBlock
            title="Valuation Sanity Checks"
            action={<StatusChip variant="neutral">Review</StatusChip>}
            containerType="card"
            className="rounded-[28px] p-6 sm:p-8 space-y-5"
          >
            <div className="space-y-3">
              {sanityChecks.slice(0, 5).map((check) => (
                <div key={check.name} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm flex gap-3 items-start justify-between">
                  <div className="space-y-1">
                    <p className="font-semibold text-softform-navy-950">{check.name}</p>
                    <p className="text-xs leading-relaxed text-softform-text-secondary">{check.message}</p>
                  </div>
                  <StatusChip variant={statusVariant(check.status)} className="text-[9px] px-2 py-0.5 shrink-0">
                    {check.status}
                  </StatusChip>
                </div>
              ))}
            </div>
          </SectionBlock>
        )}
      </section>

      {/* Model Warnings */}
      {modelWarnings.length > 0 && (
        <section className="rounded-[24px] border border-softform-amber-300/25 bg-softform-cream/35 p-5 shadow-soft-inner">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="mt-0.5 shrink-0 text-softform-amber-500" />
            <div className="space-y-2">
              <p className="text-sm font-semibold text-softform-navy-950">Model Warnings</p>
              {modelWarnings.slice(0, 5).map((warning, idx) => (
                <p key={idx} className="text-xs leading-relaxed text-softform-text-secondary">{warning}</p>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Bottom Navigation */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-semibold text-softform-navy-950 text-base">Use valuation in the funding narrative</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Continue to Funding Strategy to compare channel fit and facility structures using this valuation context.
          </p>
        </div>
        <Link
          to="/platform/funding-strategy"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
        >
          Open Funding Strategy
          <ArrowRight size={14} />
        </Link>
      </section>
    </div>
  )
}
