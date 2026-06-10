import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, CheckCircle2, RotateCw, ShieldCheck, Coins, TrendingUp } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import ScoreRing from '../../components/platform/ScoreRing'
import SkeletonLoader from '../../components/platform/SkeletonLoader'
import type { FinancialAnalysisResponse, FinancialSignal, IntegrityCheckResult, RatioMetric } from '../market-watch/types'
import { getFinancialHealthAnalysis } from './financialHealthApi'
import { motion } from 'framer-motion'

type MetricCard = {
  key: string
  label: string
  metric?: RatioMetric | null
  suffix?: string
  hint: string
}

const staggerContainer = {
  show: { transition: { staggerChildren: 0.04 } }
}

const staggerItem = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 }
}

function formatNumber(value?: number | null, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return value.toFixed(digits)
}

function formatHKD(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  if (Math.abs(value) >= 1_000_000) return `HKD ${(value / 1_000_000).toFixed(2)}M`
  return `HKD ${value.toLocaleString()}`
}

function formatBand(value?: string | null) {
  if (!value) return 'Unavailable'
  return value.replace(/_/g, ' ')
}

function bandVariant(value?: string | null): 'signal' | 'caution' | 'neutral' {
  if (value === 'strong' || value === 'adequate' || value === 'safe' || value === 'low') return 'signal'
  if (value === 'watch' || value === 'constrained' || value === 'grey' || value === 'distress' || value === 'elevated') return 'caution'
  return 'neutral'
}

export default function FinancialHealthPage() {
  const [analysis, setAnalysis] = useState<FinancialAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAnalysis = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getFinancialHealthAnalysis()
      setAnalysis(data)
    } catch (e) {
      console.error('Financial health load failed', e)
      setError('Financial Health is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalysis()
  }, [])

  const metrics = useMemo<MetricCard[]>(() => {
    if (!analysis) return []
    return [
      { key: 'current', label: 'Current Ratio', metric: analysis.ratios.currentRatio, suffix: 'x', hint: 'Short-term liquidity buffer' },
      { key: 'quick', label: 'Quick Ratio', metric: analysis.ratios.quickRatio, suffix: 'x', hint: 'Liquid asset coverage' },
      { key: 'coverage', label: 'Interest Coverage', metric: analysis.ratios.interestCoverage, suffix: 'x', hint: 'EBIT / interest expense' },
      { key: 'dscr', label: 'DSCR', metric: analysis.ratios.dscr, suffix: 'x', hint: 'Cash available for debt service' },
      { key: 'debt', label: 'Debt Ratio', metric: analysis.ratios.debtRatio, suffix: 'x', hint: 'Debt load vs assets' },
      { key: 'netdebt', label: 'Net Debt / EBITDA', metric: analysis.ratios.netDebtToEbitda, suffix: 'x', hint: 'Leverage capacity' },
      { key: 'dso', label: 'DSO', metric: analysis.ratios.dso, suffix: ' days', hint: 'Collection cycle quality' },
      { key: 'wcgap', label: 'Working Capital Gap', metric: analysis.ratios.workingCapitalGap, hint: 'Estimated funding gap' },
    ]
  }, [analysis])

  if (loading) {
    return (
      <div className="space-y-8 pb-12">
        {/* Header Skeleton */}
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>

        {/* Cockpit Skeleton */}
        <SkeletonLoader variant="card" className="min-h-[200px]" />

        {/* 8 Metric Cards Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <SkeletonLoader variant="metric" count={8} />
        </div>

        {/* Double section grid skeleton */}
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[300px]" />
          <SkeletonLoader variant="card" className="min-h-[300px]" />
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
            {error || 'Unable to connect to financial health services.'}
          </p>
          <button
            type="button"
            onClick={loadAnalysis}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={14} />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  const summary = analysis.summary
  const snapshot = analysis.snapshot
  const valuation = analysis.valuation
  const projections = analysis.projections
  const projectedYears = projections?.projectedYears ?? []
  const firstProjectedYear = projectedYears[0]
  const lastProjectedYear = projectedYears[projectedYears.length - 1]
  const dcf = valuation?.dcf
  const wacc = valuation?.wacc
  const failedChecks = analysis.integrityChecks.filter((check: IntegrityCheckResult) => !check.passed)
  const passedChecks = analysis.integrityChecks.length - failedChecks.length
  const isPreview = Boolean(snapshot.metadata?.preview_only || snapshot.metadata?.previewOnly || snapshot.metadata?.source === 'data_room_workspace_preview')

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Financial Health"
        subtitle="Liquidity, leverage, coverage, receivables, projection, and valuation diagnostics from the active financial snapshot."
        chip={
          <StatusChip variant={bandVariant(summary?.overallBand)}>
            {isPreview ? 'Preview analysis' : formatBand(summary?.overallBand)}
          </StatusChip>
        }
      />

      {/* Summary Cockpit Hero Section in Premium Navy Contrast Card */}
      <section className="softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse">
              Financial Health Diagnostics
            </span>
            <h2 className="text-3xl font-semibold text-white tracking-tight">
              {snapshot.companyName} · {snapshot.reportingPeriod}
            </h2>
            <p className="text-sm leading-relaxed text-white/80 max-w-3xl">
              {summary?.disclaimer ?? 'This analysis is context-only and assumptions-based. Company records are required for production advisory or credit analysis.'}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-around gap-6 bg-white/5 border border-white/10 rounded-[24px] p-6 backdrop-blur-md">
            <div className="flex items-center gap-4">
              <ScoreRing
                score={
                  summary?.overallBand === 'strong' ? 90 :
                  summary?.overallBand === 'adequate' ? 75 :
                  summary?.overallBand === 'watch' ? 48 :
                  summary?.overallBand === 'constrained' ? 35 : 20
                }
                size={80}
                showText={true}
                label="Health Score"
                textColor="text-white"
              />
              <div>
                <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Overall band</p>
                <p className="mt-1 text-lg font-bold text-white leading-tight">{formatBand(summary?.overallBand)}</p>
              </div>
            </div>
            <div className="h-12 w-[1px] bg-white/10 hidden sm:block" />
            <div className="space-y-2">
              <div>
                <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-white/50">Revenue</p>
                <p className="mt-0.5 text-sm font-bold text-white tabular-finance">{formatHKD(snapshot.incomeStatement.revenue)}</p>
              </div>
              <div>
                <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-white/50">EBITDA</p>
                <p className="mt-0.5 text-sm font-bold text-white tabular-finance">{formatHKD(snapshot.incomeStatement.ebitda)}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Ratio Metric Grid */}
      <motion.section 
        className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
        variants={staggerContainer}
        initial="hidden"
        animate="show"
      >
        {metrics.map((item) => {
          const isCurrency = item.key === 'wcgap'
          const value = isCurrency ? formatHKD(item.metric?.value) : `${formatNumber(item.metric?.value)}${item.metric?.value !== null && item.metric?.value !== undefined ? item.suffix ?? '' : ''}`
          return (
            <motion.div 
              key={item.key} 
              variants={staggerItem}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className={`rounded-[22px] p-5 hover-lift transition-all duration-200 ${
                !item.metric?.warning
                  ? 'softform-metric-card'
                  : 'border border-softform-amber-300/35 bg-softform-cream/45 shadow-sm'
              }`}
            >
              <MetricDisplay
                label={item.label}
                value={value}
                description={item.hint}
                trend={item.metric?.warning ? { value: 'Review Needed', isPositive: false } : undefined}
              />
              {item.metric?.warning && (
                <p className="mt-3 flex gap-2 text-[11px] leading-relaxed text-softform-amber-500 border-t border-softform-amber-300/20 pt-2">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                  <span>{item.metric.warning}</span>
                </p>
              )}
            </motion.div>
          )
        })}
      </motion.section>

      {/* Integrity & Diagnostics Grid */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Integrity Checks"
          icon={<CheckCircle2 size={20} className="text-softform-teal-500" />}
          action={
            <StatusChip variant={failedChecks.length ? 'caution' : 'signal'}>
              {passedChecks}/{analysis.integrityChecks.length} passed
            </StatusChip>
          }
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {analysis.integrityChecks.slice(0, 5).map((check) => (
              <div key={check.checkName} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm flex gap-3 items-start justify-between">
                <div className="space-y-1">
                  <p className="font-semibold text-softform-navy-950">{check.checkName}</p>
                  <p className="text-xs leading-relaxed text-softform-text-secondary">{check.message}</p>
                </div>
                <span className={`shrink-0 flex items-center justify-center rounded-full w-5 h-5 text-xs font-semibold ${check.passed ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'}`}>
                  {check.passed ? '✓' : '✗'}
                </span>
              </div>
            ))}
          </div>
        </SectionBlock>

        <SectionBlock
          title="Risk Diagnostics"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={
            <StatusChip variant={bandVariant(analysis.riskDiagnostics?.altmanZScore?.band)}>
              {formatBand(analysis.riskDiagnostics?.altmanZScore?.band)}
            </StatusChip>
          }
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Altman Z''</p>
              <p className="mt-1 text-2xl font-bold text-softform-navy-950 tabular-finance">{formatNumber(analysis.riskDiagnostics?.altmanZScore?.value)}</p>
              <p className="mt-1 text-xs text-softform-text-secondary">{analysis.riskDiagnostics?.altmanZScore?.methodologyLabel}</p>
            </div>
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Receivables Risk</p>
              <p className="mt-1 text-2xl font-bold text-softform-navy-950">{formatBand(analysis.riskDiagnostics?.receivablesRisk?.zone)}</p>
              <p className="mt-1 text-xs text-softform-text-secondary">
                ECL ratio {formatNumber(analysis.riskDiagnostics?.receivablesRisk?.eclRatio, 4)}
              </p>
            </div>
          </div>
          {summary?.watchItems && summary.watchItems.length > 0 && (
            <div className="space-y-2 border-t border-softform-navy-950/5 pt-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-softform-text-muted">Watch items</p>
              {summary.watchItems.slice(0, 4).map((item, idx) => (
                <p key={idx} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                  {item}
                </p>
              ))}
            </div>
          )}
        </SectionBlock>
      </section>

      {/* Projections & Valuation Grid */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Projections Summary"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Forecast</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Year 1 FCFF</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatHKD(firstProjectedYear?.fcffPrimary)}</p>
            </div>
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Terminal-year FCFF</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatHKD(lastProjectedYear?.fcffPrimary)}</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Forecast is driver-based and assumptions-only. Review revenue growth, EBIT margin, tax, CapEx, and NWC assumptions before using it for advisory decisions.
          </p>
        </SectionBlock>

        <SectionBlock
          title="Valuation Reference"
          icon={<Coins size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">DCF / WACC</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-white/45 px-3.5 py-3 text-center border border-white/60">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Enterprise Value</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatHKD(dcf?.enterpriseValue)}</p>
            </div>
            <div className="rounded-xl bg-white/45 px-3.5 py-3 text-center border border-white/60">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">WACC</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{wacc?.wacc != null ? `${(wacc.wacc * 100).toFixed(2)}%` : 'N/A'}</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Valuation is used as a context signal for funding capacity and business value narrative. It is not a formal appraisal.
          </p>
        </SectionBlock>
      </section>

      {/* Key Signals */}
      {summary?.keySignals && summary.keySignals.length > 0 && (
        <SectionBlock
          title="Key Financial Signals"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Summary</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {summary.keySignals.slice(0, 6).map((signal: FinancialSignal) => (
              <div key={signal.key} className="rounded-[20px] border border-white/60 bg-white/45 p-4 shadow-sm hover-lift flex flex-col justify-between min-h-[140px]">
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{signal.label}</h3>
                    <span className="rounded bg-softform-mist-100 px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider text-softform-teal-deep">
                      {formatBand(signal.band)}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-softform-text-secondary">{signal.message}</p>
                </div>
                <p className="mt-3 border-t border-softform-navy-950/5 pt-2 text-[10px] leading-relaxed text-softform-text-muted">
                  {signal.evidence}
                </p>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* Footer Navigation */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-semibold text-softform-navy-950 text-base">Continue to credit readiness</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Use the Credit Readiness module to convert these financial signals into an explainable funding-readiness scorecard.
          </p>
        </div>
        <Link
          to="/platform/credit-readiness"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
        >
          Open Credit Readiness
          <ArrowRight size={14} />
        </Link>
      </section>
    </div>
  )
}
