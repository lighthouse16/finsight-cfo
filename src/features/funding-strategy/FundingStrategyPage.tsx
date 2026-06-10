import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, Landmark, RotateCw, ShieldCheck, TrendingUp } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import SkeletonLoader from '../../components/platform/SkeletonLoader'
import { getCreditScore, getAdvisoryFacilityStructures } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getCrossBorderFundingContext, getFundingChannelRanking } from '../market-watch/api/marketWatchApi'
import { createAndFetchMockCdiData } from '../cdi/cdiApi'
import type { CreditScoringResult, FacilityStructuringResponse } from '../advisory-blueprint/types'
import type { CrossBorderFundingContextResponse, FundingChannelItem, FundingChannelRankingResponse } from '../market-watch/types'
import type { CdiConsentSession, CdiMockDataResponse } from '../cdi/cdiApi'

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

function fitTone(value?: string) {
  if (value === 'strong_fit' || value === 'strong' || value === 'clear') return 'bg-emerald-500/10 text-emerald-700'
  if (value === 'moderate_fit' || value === 'adequate' || value === 'moderate') return 'bg-softform-mist-100 text-softform-teal-deep'
  return 'bg-softform-cream text-softform-amber-500'
}

function statusVariant(score?: CreditScoringResult | null): 'signal' | 'caution' | 'neutral' {
  if (!score) return 'neutral'
  if (score.fundingReadiness === 'ready_context' || score.fundingReadiness === 'bank_review_ready') return 'signal'
  if (score.fundingReadiness === 'needs_review' || score.fundingReadiness === 'not_ready') return 'caution'
  return 'neutral'
}

export default function FundingStrategyPage() {
  const [creditScore, setCreditScore] = useState<CreditScoringResult | null>(null)
  const [ranking, setRanking] = useState<FundingChannelRankingResponse | null>(null)
  const [crossBorder, setCrossBorder] = useState<CrossBorderFundingContextResponse | null>(null)
  const [facilities, setFacilities] = useState<FacilityStructuringResponse | null>(null)
  const [cdiConsent, setCdiConsent] = useState<CdiConsentSession | null>(null)
  const [cdiData, setCdiData] = useState<CdiMockDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadStrategy = async () => {
    setLoading(true)
    setError(null)
    try {
      const [score, channelRanking, crossBorderContext, facilityContext] = await Promise.all([
        getCreditScore().catch((e) => {
          console.warn('Credit score unavailable for funding strategy', e)
          return null
        }),
        getFundingChannelRanking().catch((e) => {
          console.warn('Funding ranking unavailable', e)
          return null
        }),
        getCrossBorderFundingContext().catch((e) => {
          console.warn('Cross-border context unavailable', e)
          return null
        }),
        getAdvisoryFacilityStructures().catch((e) => {
          console.warn('Facility structures unavailable', e)
          return null
        }),
      ])

      const cdiContext = await createAndFetchMockCdiData({
        companyId: score?.companyId ?? 'demo-company',
        companyName: score?.companyName ?? 'Demo Trading Limited',
      }).catch((e) => {
        console.warn('Mock CDI context unavailable', e)
        return null
      })

      setCreditScore(score)
      setRanking(channelRanking)
      setCrossBorder(crossBorderContext)
      setFacilities(facilityContext)
      setCdiConsent(cdiContext?.consent ?? null)
      setCdiData(cdiContext?.data ?? null)
    } catch (e) {
      console.error('Funding strategy load failed', e)
      setError('Funding Strategy is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStrategy()
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

        {/* 3 Cards Skeleton */}
        <div className="grid gap-4 lg:grid-cols-3">
          <SkeletonLoader variant="metric" count={3} />
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
            onClick={loadStrategy}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={14} />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  const topChannel = ranking?.channels?.find((channel) => channel.key === ranking.topChannelKey) ?? ranking?.channels?.[0]
  const topFacilities = facilities?.candidates?.slice(0, 3) ?? []

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Funding Strategy"
        subtitle="Compare channel fit, facility structures, rate context, consent-based CDI signals, and cross-border considerations from the finance workflow."
        chip={
          <StatusChip variant={statusVariant(creditScore)}>
            {creditScore ? formatBand(creditScore.fundingReadiness) : 'Context only'}
          </StatusChip>
        }
      />

      {/* Cockpit Strategy Bridge Hero Section in Premium Navy Contrast Card */}
      <section className="softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse">Strategy bridge</span>
            <h2 className="text-3xl font-bold text-white tracking-tight">
              {topChannel ? topChannel.label : 'Funding channel context'}
            </h2>
            <p className="text-sm leading-relaxed text-white/80 max-w-3xl">
              {ranking?.explanation ?? 'Funding Strategy combines readiness scorecard context, channel ranking, cross-border funding context, consent-based CDI signals, and facility structures.'}
            </p>
            {topChannel && (
              <div className="flex flex-wrap gap-2 pt-1">
                <span className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] ${fitTone(topChannel.fitBand)}`}>
                  {formatBand(topChannel.fitBand)}
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white">
                  Score {topChannel.score}
                </span>
              </div>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-around gap-6 bg-white/5 border border-white/10 rounded-[24px] p-6 backdrop-blur-md">
            <div className="space-y-2.5 w-full">
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Readiness score</span>
                <span className="text-sm font-bold text-white tabular-finance">{creditScore?.compositeScore ?? 'N/A'}</span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Ranking band</span>
                <span className="text-sm font-semibold text-white">{formatBand(ranking?.rankingBand)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">CDI trust bridge</span>
                <span className="text-sm font-semibold text-white">{formatBand(cdiData?.receivablesSignal.digitalCollateralBand)}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CDI Trust Bridge */}
      {cdiData && (
        <SectionBlock
          title="CDI Trust Bridge & Digital Collateral"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">{formatBand(cdiConsent?.status ?? 'authorized')}</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-4">
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Eligible invoices</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatHKD(cdiData.receivablesSignal.eligibleInvoiceValue)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Verified pool</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatHKD(cdiData.receivablesSignal.verifiedInvoiceValue)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Buyer concentration</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatPercent(cdiData.receivablesSignal.topBuyerConcentration)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Bureau band</p>
              <p className="mt-1 text-lg font-semibold text-softform-navy-950">{formatBand(cdiData.creditBureauSignal.bureauBand)}</p>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2 pt-2">
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">Funding implications</p>
              {cdiData.fundingImplications.map((item) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Signal:</strong> {item}
                </p>
              ))}
            </div>
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-amber-500">Risk implications</p>
              {cdiData.riskImplications.map((item) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Watch:</strong> {item}
                </p>
              ))}
            </div>
          </div>
        </SectionBlock>
      )}

      {/* Funding Channel Ranking */}
      {ranking && ranking.channels.length > 0 && (
        <SectionBlock
          title="Funding Channel Ranking"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">Context Ranking</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-3">
            {ranking.channels.slice(0, 3).map((channel: FundingChannelItem) => {
              const rankBadgeColor =
                channel.rank === 1 ? 'bg-amber-500/10 text-amber-600 border-amber-500/20' :
                channel.rank === 2 ? 'bg-slate-500/10 text-slate-600 border-slate-500/20' :
                'bg-orange-500/10 text-orange-600 border-orange-500/20'
              const rankLabel = channel.rank === 1 ? '1st' : channel.rank === 2 ? '2nd' : '3rd'

              return (
                <div key={channel.key} className="rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm hover-lift space-y-4 flex flex-col justify-between">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-bold ${rankBadgeColor}`}>
                          {rankLabel}
                        </span>
                        <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{channel.label}</h3>
                      </div>
                      <span className={`shrink-0 rounded px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider ${fitTone(channel.fitBand)}`}>
                        {formatBand(channel.fitBand)}
                      </span>
                    </div>

                    {/* Fit Score Progress Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] font-medium text-softform-text-secondary">
                        <span>Fit Score</span>
                        <span className="font-semibold">{channel.score} / 100</span>
                      </div>
                      <div className="w-full h-1.5 bg-softform-text-muted/15 rounded-full overflow-hidden">
                        <div className="h-full bg-softform-teal-500" style={{ width: `${channel.score}%` }} />
                      </div>
                    </div>

                    <p className="text-xs leading-relaxed text-softform-text-secondary">{channel.rationale}</p>
                  </div>

                  <div className="space-y-2 border-t border-softform-navy-950/5 pt-3 mt-2">
                    {channel.supportingSignals.slice(0, 2).map((signal, idx) => (
                      <p key={idx} className="text-[11px] leading-relaxed text-softform-text-secondary">
                        <strong className="text-softform-navy-950 font-semibold">Signal:</strong> {signal}
                      </p>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </SectionBlock>
      )}

      {/* Candidate Facility Structures */}
      {topFacilities.length > 0 && (
        <SectionBlock
          title="Candidate Facility Structures"
          icon={<Landmark size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Advisory Fit</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-3">
            {topFacilities.map((facility) => (
              <div key={facility.facilityKey} className="rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm hover-lift space-y-4 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{facility.label}</h3>
                    <span className={`shrink-0 rounded px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider ${fitTone(facility.fitAssessment.fitBand)}`}>
                      {formatBand(facility.fitAssessment.fitBand)}
                    </span>
                  </div>
                  <div className="space-y-2 text-xs text-softform-text-secondary bg-white/30 rounded-xl p-3 border border-white/40">
                    <div className="flex justify-between border-b border-softform-navy-950/5 pb-1">
                      <span className="font-medium text-softform-text-secondary">Est. limit</span>
                      <span className="tabular-finance font-bold text-softform-navy-950">{formatHKD(facility.estimatedLimit)}</span>
                    </div>
                    {facility.estimatedPricingBps !== undefined && facility.estimatedPricingBps !== null && (
                      <div className="flex justify-between">
                        <span className="font-medium text-softform-text-secondary">Pricing</span>
                        <span className="tabular-finance font-bold text-softform-navy-950">{facility.estimatedPricingBps} bps</span>
                      </div>
                    )}
                  </div>
                  <p className="text-xs leading-relaxed text-softform-text-secondary">{facility.purpose}</p>
                </div>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* Cross-Border Funding Context */}
      {crossBorder && (
        <SectionBlock
          title="Cross-Border Funding Context"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">HKD / RMB</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <p className="text-sm leading-relaxed text-softform-text-secondary">{crossBorder.explanation}</p>
          <div className="grid gap-4 sm:grid-cols-3 pt-2">
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">HKD reference</p>
              <p className="mt-1 text-sm font-semibold text-softform-navy-950">{crossBorder.hkdFundingReference.displayValue}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">RMB reference</p>
              <p className="mt-1 text-sm font-semibold text-softform-navy-950">{crossBorder.rmbFundingReference.displayValue}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Spread band</p>
              <p className="mt-1 text-sm font-semibold text-softform-navy-950">{formatBand(crossBorder.spreadBand)}</p>
            </div>
          </div>
        </SectionBlock>
      )}

      {/* Navigation Footer */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <p className="font-semibold text-softform-navy-950 text-base">Convert strategy into advisor-ready actions</p>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Use Advisory Blueprint to consolidate this strategy into stress context, facility rationale, and next data requirements.
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
    </div>
  )
}
