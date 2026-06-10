import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, RotateCw, ShieldCheck, TrendingUp } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import ScoreRing from '../../components/platform/ScoreRing'
import SkeletonLoader from '../../components/platform/SkeletonLoader'
import { getCreditScore } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { createAndFetchMockCdiData } from '../cdi/cdiApi'
import type { CreditScoringResult, CreditScoreFactor, FundingReadinessBand, PdRiskTier } from '../advisory-blueprint/types'
import type { CdiConsentSession, CdiMockDataResponse } from '../cdi/cdiApi'

const readinessLabels: Record<FundingReadinessBand, string> = {
  ready_context: 'Ready context',
  bank_review_ready: 'Bank review ready',
  needs_review: 'Needs review',
  not_ready: 'Not ready',
  unavailable: 'Unavailable',
}

const tierLabels: Record<PdRiskTier, string> = {
  low: 'Low risk',
  moderate: 'Moderate risk',
  elevated: 'Elevated risk',
  high: 'High risk',
  unavailable: 'Unavailable',
}

function formatHKD(value?: number | null) {
  if (value === undefined || value === null) return 'N/A'
  if (value >= 1_000_000) return `HKD ${(value / 1_000_000).toFixed(2)}M`
  return `HKD ${value.toLocaleString()}`
}

function formatPercent(value?: number | null) {
  if (value === undefined || value === null) return 'N/A'
  return `${(value * 100).toFixed(1)}%`
}

function formatBand(value?: string | null) {
  if (!value) return 'Unavailable'
  return value.replace(/_/g, ' ')
}

function chipVariantForTier(tier: PdRiskTier): 'signal' | 'caution' | 'neutral' {
  if (tier === 'low' || tier === 'moderate') return 'signal'
  if (tier === 'elevated' || tier === 'high') return 'caution'
  return 'neutral'
}

function factorTone(factor: CreditScoreFactor) {
  if (factor.rawScore >= 75) return 'text-emerald-700 bg-emerald-500/10'
  if (factor.rawScore >= 55) return 'text-softform-amber-500 bg-softform-cream'
  return 'text-red-700 bg-red-500/10'
}

export default function CreditReadinessPage() {
  const [creditScore, setCreditScore] = useState<CreditScoringResult | null>(null)
  const [cdiConsent, setCdiConsent] = useState<CdiConsentSession | null>(null)
  const [cdiData, setCdiData] = useState<CdiMockDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCreditScore = async () => {
    setLoading(true)
    setError(null)
    try {
      const score = await getCreditScore()
      const cdiContext = await createAndFetchMockCdiData({
        companyId: score.companyId,
        companyName: score.companyName,
      }).catch((e) => {
        console.warn('Mock CDI overlay unavailable for credit readiness', e)
        return null
      })

      setCreditScore(score)
      setCdiConsent(cdiContext?.consent ?? null)
      setCdiData(cdiContext?.data ?? null)
    } catch (e) {
      console.error('Credit score load failed', e)
      setError('Credit readiness score is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCreditScore()
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

        {/* Double columns skeleton */}
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[250px]" />
          <SkeletonLoader variant="card" className="min-h-[250px]" />
        </div>

        {/* 6 Metric Cards Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <SkeletonLoader variant="metric" count={6} />
        </div>
      </div>
    )
  }

  if (error || !creditScore) {
    return (
      <div className="softform-card rounded-[32px] p-8 sm:p-10 text-center">
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-[20px] bg-red-50 text-red-600 border border-red-100">
            <AlertTriangle size={24} />
          </div>
          <p className="mb-2 text-lg font-semibold text-softform-navy-950">Service Connection Issue</p>
          <p className="mb-6 text-sm text-softform-text-secondary leading-relaxed">
            {error || 'Unable to connect to credit readiness services.'}
          </p>
          <button
            type="button"
            onClick={loadCreditScore}
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
        title="Credit Readiness"
        subtitle="Explainable SME PD proxy scorecard built from liquidity, leverage, coverage, receivables, FCFF, stress, and consent-based CDI signals."
        chip={
          <StatusChip variant={chipVariantForTier(creditScore.riskTier)}>
            {tierLabels[creditScore.riskTier]}
          </StatusChip>
        }
      />

      {/* Hero Score Card in Premium Navy Contrast Card */}
      <section className="softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-4 max-w-3xl">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse">
              Finance-first PD proxy
            </span>
            <div>
              <h2 className="text-3xl font-bold text-white tracking-tight">
                {creditScore.companyName}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-white/80">
                {creditScore.methodologyLabel}. This page is context-only and designed to explain the drivers behind lender-readiness, not to issue a formal credit decision.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
                {readinessLabels[creditScore.fundingReadiness]}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
                {creditScore.pdProxyBand}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
                CDI {formatBand(cdiConsent?.status ?? 'not requested')}
              </span>
            </div>
          </div>

          <div className="flex flex-col items-center justify-center rounded-[28px] bg-white/5 border border-white/10 p-6 backdrop-blur-md min-w-[200px] shrink-0">
            <ScoreRing
              score={creditScore.compositeScore}
              size={96}
              showText={true}
              label={creditScore.scoreScale}
              textColor="text-white"
            />
            <span className="mt-3 rounded-full bg-white text-softform-navy-950 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.1em]">
              {tierLabels[creditScore.riskTier]}
            </span>
          </div>
        </div>
      </section>

      {/* Positive and Risk Drivers */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Positive Drivers"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-4"
        >
          {creditScore.positiveDrivers.length > 0 ? (
            <ul className="space-y-3">
              {creditScore.positiveDrivers.slice(0, 5).map((driver, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-softform-text-secondary">
                  <span className="mt-1 h-2 w-2 rounded-full bg-softform-teal-deep shrink-0" />
                  <span>{driver}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-softform-text-secondary">No strong positive drivers detected yet.</p>
          )}
        </SectionBlock>

        <SectionBlock
          title="Risk Drivers"
          icon={<AlertTriangle size={20} className="text-softform-amber-500" />}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-4"
        >
          {creditScore.riskDrivers.length > 0 ? (
            <ul className="space-y-3">
              {creditScore.riskDrivers.slice(0, 5).map((driver, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-softform-text-secondary">
                  <span className="mt-1 h-2 w-2 rounded-full bg-softform-amber-500 shrink-0" />
                  <span>{driver}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-softform-text-secondary">No major risk drivers detected under current assumptions.</p>
          )}
        </SectionBlock>
      </section>

      {/* CDI Overlay Section */}
      {cdiData && (
        <SectionBlock
          title="Consent-Based CDI Overlay"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">{formatBand(cdiData.creditBureauSignal.bureauBand)}</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-4">
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Net cash-flow trend</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950">{formatBand(cdiData.cashflowSignal.netCashflowTrend)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Eligible invoices</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatHKD(cdiData.receivablesSignal.eligibleInvoiceValue)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Buyer concentration</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatPercent(cdiData.receivablesSignal.topBuyerConcentration)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Delinquencies 12m</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{cdiData.creditBureauSignal.repaymentDelinquencyCount12m}</p>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2 pt-2">
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">CDI supports</p>
              {cdiData.fundingImplications.slice(0, 3).map((item) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Signal:</strong> {item}
                </p>
              ))}
            </div>
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-amber-500">CDI watch items</p>
              {cdiData.riskImplications.slice(0, 3).map((item) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Watch:</strong> {item}
                </p>
              ))}
            </div>
          </div>
        </SectionBlock>
      )}

      {/* Score Factor Breakdown */}
      <SectionBlock
        title="Score Factor Breakdown"
        icon={<TrendingUp size={20} className="text-softform-teal-500" />}
        action={<StatusChip variant="neutral">Explainable Scorecard</StatusChip>}
        containerType="card"
        className="rounded-[32px] p-6 sm:p-8 space-y-6"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {creditScore.factors.map((factor) => {
            const rawScore = factor.rawScore
            const barColor = rawScore >= 75 ? 'bg-emerald-500' : rawScore >= 55 ? 'bg-amber-500' : 'bg-red-500'
            return (
              <div key={factor.key} className="rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm hover-lift space-y-4 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{factor.label}</h3>
                    <span className={`shrink-0 rounded px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider ${factorTone(factor)}`}>
                      {formatBand(factor.band)}
                    </span>
                  </div>

                  {/* Score progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-medium text-softform-text-secondary">
                      <span>Score</span>
                      <span className="font-semibold">{rawScore} / 100</span>
                    </div>
                    <div className="w-full h-2 bg-softform-text-muted/15 rounded-full overflow-hidden">
                      <div className={`h-full ${barColor}`} style={{ width: `${rawScore}%` }} />
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs text-softform-text-secondary border-t border-softform-navy-950/5 pt-3">
                    <div className="flex justify-between">
                      <span className="font-medium text-softform-navy-950/80">Weight</span>
                      <span className="tabular-finance font-semibold text-softform-navy-950">{Math.round(factor.weight * 100)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-softform-navy-950/80">Weighted Score</span>
                      <span className="tabular-finance font-semibold text-softform-navy-950">{factor.weightedScore.toFixed(2)}</span>
                    </div>
                  </div>
                  <p className="text-xs leading-relaxed text-softform-text-secondary">{factor.message}</p>
                </div>
                <p className="text-[10px] leading-relaxed text-softform-text-muted border-t border-softform-navy-950/5 pt-3 mt-2">
                  <strong className="font-semibold text-softform-navy-950">Evidence:</strong> {factor.evidence}
                </p>
              </div>
            )
          })}
        </div>
      </SectionBlock>

      {/* Constraints & Next Data */}
      {(creditScore.hardConstraints.length > 0 || creditScore.nextDataNeeded.length > 0) && (
        <section className="grid gap-6 lg:grid-cols-2">
          {creditScore.hardConstraints.length > 0 && (
            <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-4 border border-softform-amber-300/20">
              <h2 className="text-lg font-semibold text-softform-navy-950 flex items-center gap-2">
                <AlertTriangle size={18} className="text-softform-amber-500" />
                Hard Constraints
              </h2>
              <ul className="space-y-3">
                {creditScore.hardConstraints.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-sm text-softform-text-secondary">
                    <AlertTriangle size={14} className="mt-0.5 text-softform-amber-500 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-4">
            <h2 className="text-lg font-semibold text-softform-navy-950 flex items-center gap-2">
              <ShieldCheck size={18} className="text-softform-teal-500" />
              Next Data Needed
            </h2>
            <div className="grid gap-2">
              {creditScore.nextDataNeeded.slice(0, 6).map((item, idx) => (
                <div key={idx} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs font-semibold text-softform-text-secondary shadow-sm">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Continue CTA */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-semibold text-softform-navy-950 text-base">Move from scorecard to advisory action</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Use the Advisory Blueprint to convert this PD proxy context into facility options, stress interpretation, and next actions.
          </p>
        </div>
        <Link
          to="/platform/advisory-blueprint"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
        >
          Open Advisory Blueprint
          <ArrowRight size={14} />
        </Link>
      </section>

      <footer className="pt-6 border-t border-softform-navy-950/5 text-center space-y-2">
        <p className="text-xs text-softform-text-muted">{creditScore.disclaimer}</p>
      </footer>
    </div>
  )
}
