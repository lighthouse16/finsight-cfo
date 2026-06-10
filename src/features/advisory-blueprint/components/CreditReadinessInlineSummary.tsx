import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react'
import StatusChip from '../../../components/platform/StatusChip'
import { getCreditScore } from '../api/advisoryBlueprintApi'
import type { CreditScoringResult, FundingReadinessBand, PdRiskTier } from '../types'

const readinessLabels: Record<FundingReadinessBand, string> = {
  ready_context: 'Ready context',
  bank_review_ready: 'Review ready',
  needs_review: 'Needs review',
  not_ready: 'Not ready',
  unavailable: 'Unavailable',
}

const tierLabels: Record<PdRiskTier, string> = {
  low: 'Low risk context',
  moderate: 'Moderate context',
  elevated: 'Elevated context',
  high: 'High context',
  unavailable: 'Unavailable',
}

function chipVariantForTier(tier: PdRiskTier): 'signal' | 'caution' | 'neutral' {
  if (tier === 'low' || tier === 'moderate') return 'signal'
  if (tier === 'elevated' || tier === 'high') return 'caution'
  return 'neutral'
}

export default function CreditReadinessInlineSummary() {
  const [scorecard, setScorecard] = useState<CreditScoringResult | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let mounted = true
    getCreditScore()
      .then((score) => {
        if (mounted) setScorecard(score)
      })
      .catch((error) => {
        console.warn('Readiness summary unavailable', error)
        if (mounted) setFailed(true)
      })
    return () => {
      mounted = false
    }
  }, [])

  if (failed) {
    return (
      <section className="rounded-[24px] border border-softform-amber-300/25 bg-softform-cream/35 px-5 py-4 shadow-soft-inner">
        <div className="flex items-start gap-3">
          <AlertTriangle size={18} className="mt-0.5 shrink-0 text-softform-amber-500" />
          <div>
            <p className="text-sm font-semibold text-softform-navy-950">Readiness context unavailable</p>
            <p className="mt-1 text-xs leading-relaxed text-softform-text-secondary">
              Advisory Blueprint can still load, but the scorecard summary could not be fetched from the backend.
            </p>
          </div>
        </div>
      </section>
    )
  }

  if (!scorecard) return null

  const topRiskDriver = scorecard.riskDrivers[0]
  const topPositiveDriver = scorecard.positiveDrivers[0]

  return (
    <section className="softform-card rounded-[28px] p-5 sm:p-6 border border-softform-aqua-300/20 shadow-base-card">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-softform-mist-100 text-softform-teal-deep border border-softform-aqua-300/25 shadow-soft-inner">
            <ShieldCheck size={22} />
          </div>
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-softform-navy-950">Credit Readiness Signal</p>
              <StatusChip variant={chipVariantForTier(scorecard.riskTier)} className="text-[9px] px-2 py-0.5">
                {tierLabels[scorecard.riskTier]}
              </StatusChip>
              <span className="rounded-full border border-white/70 bg-white/60 px-2.5 py-0.5 text-[9px] font-medium uppercase tracking-[0.12em] text-softform-navy-950">
                {readinessLabels[scorecard.fundingReadiness]}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-softform-text-secondary max-w-4xl">
              The scorecard is now part of the advisory workflow. {scorecard.pdProxyBand}. Treat this as context-only and read it together with stress tests and facility fit.
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {topPositiveDriver && (
                <p className="rounded-xl bg-white/45 px-3 py-2 text-[11px] leading-relaxed text-softform-text-secondary border border-white/60">
                  <strong className="text-softform-navy-950 font-semibold">Positive:</strong> {topPositiveDriver}
                </p>
              )}
              {topRiskDriver && (
                <p className="rounded-xl bg-white/45 px-3 py-2 text-[11px] leading-relaxed text-softform-text-secondary border border-white/60">
                  <strong className="text-softform-navy-950 font-semibold">Watch:</strong> {topRiskDriver}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 lg:min-w-[250px] lg:justify-end">
          <div className="rounded-[22px] bg-softform-mist-100/70 border border-softform-aqua-300/25 px-5 py-4 text-center shadow-soft-inner">
            <p className="text-3xl font-bold text-softform-teal-deep tabular-finance">{scorecard.compositeScore}</p>
            <p className="mt-1 text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Scorecard</p>
          </div>
          <Link
            to="/platform/credit-readiness"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
          >
            View Score
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </section>
  )
}
