import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, BarChart3, Calculator, RotateCw, TrendingUp } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import DemoFlowRail from '../../components/platform/DemoFlowRail'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import type { FinancialAnalysisResponse } from '../market-watch/types'

type ValuationYear = {
  year: number
  fcff: number
  discountFactor: number
  pvFcff: number
}

type SensitivityPoint = {
  wacc: number
  terminalGrowthRate: number
  enterpriseValue?: number | null
  equityValue?: number | null
}

type SanityCheck = {
  name: string
  status: string
  message: string
  value?: number | null
}

type ValuationShape = {
  assumptions?: {
    riskFreeRate?: number
    observedBeta?: number
    targetDebtWeight?: number
    targetEquityWeight?: number
    equityRiskPremium?: number
    sizePremium?: number
    industryRiskPremium?: number
    companySpecificPremium?: number
    preTaxCostOfDebt?: number
    taxRate?: number
    terminalGrowthRate?: number
    exitMultiple?: number | null
    currency?: string
  }
  wacc?: {
    costOfEquity?: number
    preTaxCostOfDebt?: number
    afterTaxCostOfDebt?: number
    debtWeight?: number
    equityWeight?: number
    wacc?: number
    unleveredBeta?: number
    releveredBeta?: number
    warnings?: string[]
  }
  dcf?: {
    valuationYears?: ValuationYear[]
    pvExplicitFcff?: number
    terminalValueGordonGrowth?: number | null
    pvTerminalValue?: number | null
    enterpriseValue?: number | null
    totalDebt?: number
    cash?: number
    netDebt?: number
    equityValue?: number | null
    impliedEvEbitda?: number | null
    terminalGrowthRate?: number
    wacc?: number
    terminalValueShareOfEnterpriseValue?: number | null
    exitMultipleTerminalValue?: number | null
    impliedExitMultiple?: number | null
    warnings?: string[]
  }
  sensitivity?: SensitivityPoint[]
  sanityChecks?: SanityCheck[]
  warnings?: string[]
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

function formatMultiple(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return `${value.toFixed(2)}x`
}

function statusVariant(status?: string | null): 'signal' | 'caution' | 'neutral' {
  if (status === 'pass') return 'signal'
  if (status === 'warning' || status === 'fail') return 'caution'
  return 'neutral'
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
      <div className="flex min-h-[50dvh] flex-col items-center justify-center space-y-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep animate-spin">
          <RotateCw size={24} />
        </div>
        <p className="text-sm font-medium text-softform-text-secondary animate-pulse">Loading valuation model...</p>
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

  const valuation = ((analysis as unknown as { valuation?: ValuationShape }).valuation ?? {}) as ValuationShape
  const snapshot = analysis.snapshot
  const dcf = valuation.dcf
  const wacc = valuation.wacc
  const assumptions = valuation.assumptions
  const valuationYears = dcf?.valuationYears ?? []
  const sensitivity = valuation.sensitivity ?? []
  const sanityChecks = valuation.sanityChecks ?? []
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

      <DemoFlowRail />

      <section className="softform-panel rounded-[32px] p-8 space-y-6 shadow-floating-panel relative overflow-hidden bg-gradient-to-br from-white/95 via-softform-mist-50/70 to-softform-ice-100/50 border border-white">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-softform-teal-deep">
              Business valuation engine
            </span>
            <h2 className="text-3xl font-black text-softform-navy-950 tracking-tight">
              {snapshot.companyName} · {snapshot.reportingPeriod}
            </h2>
            <p className="text-sm leading-relaxed text-softform-text-secondary max-w-3xl">
              This DCF view is assumptions-based and intended to support the CFO narrative, funding readiness, and advisory preparation. It is not a formal appraisal or investment recommendation.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner">
              <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Enterprise value</p>
              <p className="mt-1 text-xl font-black text-softform-navy-950 tabular-finance">{formatHKD(dcf?.enterpriseValue)}</p>
            </div>
            <div className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner">
              <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Equity value</p>
              <p className="mt-1 text-xl font-black text-softform-navy-950 tabular-finance">{formatHKD(dcf?.equityValue)}</p>
            </div>
            <div className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner">
              <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">WACC</p>
              <p className="mt-1 text-xl font-black text-softform-navy-950 tabular-finance">{formatPercent(wacc?.wacc)}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">PV explicit FCFF</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950 tabular-finance">{formatHKD(dcf?.pvExplicitFcff)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">Discounted operating cash flows</p>
        </div>
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">PV terminal value</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950 tabular-finance">{formatHKD(dcf?.pvTerminalValue)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">Long-term value component</p>
        </div>
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Net debt bridge</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950 tabular-finance">{formatHKD(dcf?.netDebt)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">Total debt less cash</p>
        </div>
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Implied EV / EBITDA</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950 tabular-finance">{formatMultiple(dcf?.impliedEvEbitda)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">Sanity-check multiple</p>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <Calculator size={20} className="text-softform-teal-deep" />
              WACC Build-Up
            </h2>
            <StatusChip variant="neutral">CAPM-style</StatusChip>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              ['Cost of equity', formatPercent(wacc?.costOfEquity)],
              ['After-tax debt cost', formatPercent(wacc?.afterTaxCostOfDebt)],
              ['Debt weight', formatPercent(wacc?.debtWeight)],
              ['Equity weight', formatPercent(wacc?.equityWeight)],
              ['Risk-free rate', formatPercent(assumptions?.riskFreeRate)],
              ['Terminal growth', formatPercent(assumptions?.terminalGrowthRate)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">{label}</p>
                <p className="mt-1 text-lg font-black text-softform-navy-950 tabular-finance">{value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <TrendingUp size={20} className="text-softform-teal-deep" />
              DCF Bridge
            </h2>
            <StatusChip variant="neutral">EV to Equity</StatusChip>
          </div>
          <div className="space-y-3">
            {[
              ['Enterprise value', formatHKD(dcf?.enterpriseValue)],
              ['Less net debt', formatHKD(dcf?.netDebt)],
              ['Equity value', formatHKD(dcf?.equityValue)],
              ['Terminal value share', formatPercent(dcf?.terminalValueShareOfEnterpriseValue)],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm">
                <span className="font-semibold text-softform-navy-950/80">{label}</span>
                <span className="font-black text-softform-navy-950 tabular-finance">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {valuationYears.length > 0 && (
        <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <BarChart3 size={20} className="text-softform-teal-deep" />
              Valuation Years
            </h2>
            <StatusChip variant="neutral">FCFF PV</StatusChip>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {valuationYears.slice(0, 5).map((year) => (
              <div key={year.year} className="rounded-[20px] border border-white/60 bg-white/45 p-4 shadow-sm hover-lift">
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-teal-deep">Year {year.year}</p>
                <p className="mt-2 text-sm font-bold text-softform-navy-950">FCFF {formatHKD(year.fcff)}</p>
                <p className="mt-1 text-xs text-softform-text-secondary">PV {formatHKD(year.pvFcff)}</p>
                <p className="mt-1 text-[10px] text-softform-text-muted">Discount {year.discountFactor.toFixed(3)}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="grid gap-6 lg:grid-cols-2">
        {sensitivity.length > 0 && (
          <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
            <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
              <h2 className="text-lg font-bold text-softform-navy-950">Sensitivity Points</h2>
              <StatusChip variant="neutral">WACC / Growth</StatusChip>
            </div>
            <div className="space-y-3">
              {sensitivity.slice(0, 5).map((point, idx) => (
                <div key={idx} className="grid grid-cols-3 gap-2 rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs">
                  <span className="font-semibold text-softform-navy-950/80">{formatPercent(point.wacc)}</span>
                  <span className="font-semibold text-softform-navy-950/80">g {formatPercent(point.terminalGrowthRate)}</span>
                  <span className="text-right font-black text-softform-navy-950 tabular-finance">{formatHKD(point.enterpriseValue)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {sanityChecks.length > 0 && (
          <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
            <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
              <h2 className="text-lg font-bold text-softform-navy-950">Valuation Sanity Checks</h2>
              <StatusChip variant="neutral">Review</StatusChip>
            </div>
            <div className="space-y-3">
              {sanityChecks.slice(0, 5).map((check) => (
                <div key={check.name} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-bold text-softform-navy-950">{check.name}</p>
                    <StatusChip variant={statusVariant(check.status)} className="text-[9px] px-2 py-0.5">
                      {check.status}
                    </StatusChip>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-softform-text-secondary">{check.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {(valuation.warnings?.length || dcf?.warnings?.length || wacc?.warnings?.length) && (
        <section className="rounded-[24px] border border-softform-amber-300/25 bg-softform-cream/35 p-5 shadow-soft-inner">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="mt-0.5 shrink-0 text-softform-amber-500" />
            <div className="space-y-2">
              <p className="text-sm font-bold text-softform-navy-950">Model Warnings</p>
              {[...(valuation.warnings ?? []), ...(dcf?.warnings ?? []), ...(wacc?.warnings ?? [])].slice(0, 5).map((warning, idx) => (
                <p key={idx} className="text-xs leading-relaxed text-softform-text-secondary">{warning}</p>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-bold text-softform-navy-950 text-base">Use valuation in the funding narrative</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Continue to Funding Strategy to compare channel fit and facility structures using this valuation context.
          </p>
        </div>
        <Link
          to="/platform/funding-strategy"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-softform-navy-800 transition shadow-sm"
        >
          Open Funding Strategy
          <ArrowRight size={14} />
        </Link>
      </section>
    </div>
  )
}
