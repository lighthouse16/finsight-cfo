import { useState } from 'react'
import { LiquidityEvent, RateSnapshot, CompanyProfile } from '../types'
import { RatesSourceInfo } from '../MarketWatchPage'
import clsx from 'clsx'
import { MarketWatchInsightSet } from '../insights/types'
import LoadingState from './LoadingState'
import SourceInfoTooltip from './SourceInfoTooltip'
import MotionStagger from './MotionStagger'
import MotionReveal from './MotionReveal'

type RatesLiquidityTabProps = {
  rates: RateSnapshot[]
  liquidityEvents: LiquidityEvent[]
  ratesSource?: RatesSourceInfo | null
  profile?: CompanyProfile | null
  insights?: MarketWatchInsightSet
  loading?: boolean
}

export default function RatesLiquidityTab({
  rates,
  liquidityEvents,
  ratesSource,
  profile,
  insights,
  loading,
}: RatesLiquidityTabProps) {
  const [showDetails, setShowDetails] = useState(false)

  const isHoniaAvailable = rates.some(r => r.id === 'honia-on')
  const isLiquidityAvailable = liquidityEvents.length > 0

  const sourceWarnings: string[] = []
  if (!isHoniaAvailable) {
    sourceWarnings.push('HONIA: unavailable')
  }
  if (!isLiquidityAvailable) {
    sourceWarnings.push('Liquidity: unavailable')
  }
  if (ratesSource?.warnings) {
    ratesSource.warnings.forEach(w => {
      const wLower = w.toLowerCase()
      const isDuplicate = wLower.includes('honia was not available') ||
                          wLower.includes('liquidity records were unavailable') ||
                          wLower.includes('interbank liquidity records')
      if (!isDuplicate) {
        sourceWarnings.push(w)
      }
    })
  }

  if (loading) {
    return (
      <div className="space-y-8">
        {/* Rate Context Loading */}
        <div className="space-y-4">
          <div className="h-6 w-32 bg-softform-navy-950/5 rounded animate-pulse" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <LoadingState key={i} variant="card" label="Fetching rates..." lines={2} />
            ))}
          </div>
        </div>
        {/* Company Exposure Loading */}
        <LoadingState variant="row" label="Analyzing debt sensitivity..." />
        {/* Liquidity Watch Loading */}
        <div className="space-y-4">
          <div className="h-6 w-36 bg-softform-navy-950/5 rounded animate-pulse" />
          <div className="grid gap-4 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <LoadingState key={i} variant="card" label="Checking liquidity balances..." lines={2} />
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Check if we fell back to HKMA
  const isHkabFallback = ratesSource?.warnings?.some(w => w.toLowerCase().includes('hkab hibor page unavailable'))
  const sourceLabel = isHkabFallback ? (ratesSource?.label || 'HKMA Public API') : 'HKAB public HIBOR page'

  const printedWarnings = sourceWarnings.filter(
    w => w !== 'HONIA: unavailable' && w !== 'Liquidity: unavailable'
  )

  const rateContextSources = [
    {
      label: `HIBOR: ${sourceLabel}`,
      asOf: ratesSource?.asOf,
      freshness: 'Daily',
      mode: isHkabFallback ? ('local-fallback' as const) : ('provider-backed' as const),
      warnings: printedWarnings.length > 0 ? printedWarnings : undefined
    },
    {
      label: `HONIA: ${isHoniaAvailable ? "HKMA public API" : "unavailable"}`,
      asOf: isHoniaAvailable ? (ratesSource?.asOf || null) : null,
      freshness: isHoniaAvailable ? 'Daily' : undefined,
      mode: isHoniaAvailable ? ('provider-backed' as const) : ('unavailable' as const)
    }
  ]

  return (
    <MotionStagger className="space-y-8">
      {/* 1. Rate Context (six rate cards spanning full width) */}
      <MotionReveal>
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-softform-navy-950 border-b border-softform-navy-950/5 pb-2 flex items-center gap-2">
            <span>Rate Context</span>
            {ratesSource && (
              <SourceInfoTooltip
                title="Rate Context Sourcing"
                sources={rateContextSources}
              />
            )}
          </h2>
          <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {rates.map((rate, idx) => (
              <div
                key={idx}
                className="softform-card flex flex-col rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200"
              >
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-[11px] font-medium text-softform-text-secondary uppercase tracking-wider">
                    {rate.label}
                  </span>
                  <span
                    className={clsx(
                      'flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider',
                      rate.trend === 'up' && 'bg-red-500/10 text-red-700',
                      rate.trend === 'down' &&
                        'bg-softform-emerald-soft/10 text-emerald-700',
                      rate.trend === 'flat' &&
                        'bg-softform-text-muted/10 text-softform-text-secondary',
                    )}
                  >
                    {Math.abs(rate.changeBasisPoints)} bps
                  </span>
                </div>
                <div className="mb-2 tabular-finance text-3xl font-bold tracking-tight text-softform-navy-950">
                  {rate.value}
                </div>
                <div className="mt-auto text-xs font-normal leading-relaxed text-softform-text-secondary">
                  {rate.context}
                </div>
              </div>
            ))}
          </div>
        </div>
      </MotionReveal>

      {/* 2. Company Rate Exposure compact strip */}
      <MotionReveal>
        <div className="softform-panel rounded-[24px] p-6 bg-white/45 backdrop-blur-md border border-white/60 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-softform-teal-500/10 hover:shadow-floating-panel transition-all duration-200">
          <div className="space-y-1 max-w-md">
            <h3 className="text-sm font-semibold text-softform-navy-950">
              Company Rate Exposure
            </h3>
            <p className="text-xs text-softform-text-secondary leading-relaxed">
              Rate-linked debt remains sensitive to HIBOR movement.
            </p>
            {insights?.rates?.watchSignals && insights.rates.watchSignals.length > 0 && (
              <div className="mt-1.5 space-y-1">
                {insights.rates.watchSignals.map(sig => (
                  <div key={sig.id} className="text-[11px] font-normal text-softform-amber-700">
                    • {sig.description}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-x-8 gap-y-4">
            <div>
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                Floating-Rate Debt
              </span>
              <span className="text-base font-bold text-softform-navy-950 tabular-finance">
                {profile ? `HKD ${(profile.floatingRateDebtHkd / 1000000).toFixed(1)}M` : 'HKD 6.5M'}
              </span>
            </div>
            <div className="h-8 w-px bg-softform-navy-950/10 hidden md:block" />
            <div>
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                Monthly Debt Service
              </span>
              <span className="text-base font-bold text-softform-navy-950 tabular-finance">
                {profile ? `HKD ${(profile.monthlyDebtServiceHkd / 1000).toFixed(0)}K` : 'HKD 420K'}
              </span>
            </div>
            <div className="h-8 w-px bg-softform-navy-950/10 hidden md:block" />
            <div>
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                Sensitivity
              </span>
              <span className="text-[10px] font-medium text-softform-amber-700 bg-softform-amber-500/10 rounded px-2.5 py-0.5 block mt-0.5 uppercase tracking-wider">
                {profile ? 'Workspace-derived context' : 'Context-only'}
              </span>
            </div>
          </div>
        </div>
      </MotionReveal>

      {/* 3. Liquidity Watch (full width, no right sidebar card) */}
      <MotionReveal>
        {liquidityEvents.length === 0 ? (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-softform-navy-950/5 bg-softform-navy-900/5 p-5">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-softform-text-secondary">
                Liquidity Watch
              </span>
              <span className="rounded-full bg-amber-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-amber-700 uppercase tracking-wider">
                unavailable
              </span>
            </div>
            <p className="text-xs text-softform-text-secondary">
              HKMA interbank liquidity source and Funding Window context are unavailable for this view.
            </p>
          </div>
        ) : (
          <div className="softform-panel rounded-[28px] flex flex-col justify-between p-6 sm:p-8 space-y-6">
            <div className="flex items-center gap-2 border-b border-softform-navy-950/5 pb-3">
              <h3 className="text-lg font-semibold text-softform-navy-950">
                Liquidity Watch
              </h3>
              <SourceInfoTooltip
                title="Liquidity Sourcing"
                sources={[
                  {
                    label: `Liquidity: HKMA liquidity`,
                    asOf: liquidityEvents[0]?.date || null,
                    freshness: 'Daily',
                    mode: 'provider-backed' as const
                  }
                ]}
              />
            </div>

            <div className="space-y-6">
              {(() => {
                const getEventValue = (keyword: string) => {
                  const ev = liquidityEvents.find(e => e.event.includes(keyword))
                  if (!ev) return ''
                  const parts = ev.event.split(':')
                  return parts.length > 1 ? parts.slice(1).join(':').trim() : ''
                }

                const closingValue = getEventValue('Closing Aggregate Balance')
                const openingValue = getEventValue('Opening Aggregate Balance')
                const t1Value = getEventValue('Forecast Aggregate Balance T+1')
                const t2Value = getEventValue('Forecast Aggregate Balance T+2')
                const baseRateValue = getEventValue('Discount Window Base Rate')
                const efbnT1Value = getEventValue('Exchange Fund Paper Net Issuance (T+1)')
                const efbnT2Value = getEventValue('Exchange Fund Paper Net Issuance (T+2)')

                return (
                  <div className="space-y-6">
                    <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                      {/* Aggregate Balance */}
                      <div className="softform-card flex flex-col justify-between rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200">
                        <div>
                          <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                            Aggregate Balance
                          </span>
                          <span className="mt-2 tabular-finance text-2xl font-bold tracking-tight text-softform-navy-950 block">
                            {closingValue || 'N/A'}
                          </span>
                        </div>
                        {openingValue && (
                          <span className="mt-2 text-xs font-normal text-softform-text-secondary block">
                            Opening: {openingValue}
                          </span>
                        )}
                      </div>

                      {/* Forward Balance */}
                      <div className="softform-card flex flex-col justify-between rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200">
                        <div>
                          <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                            Forward Balance
                          </span>
                          <span className="mt-2 tabular-finance text-base font-bold text-softform-navy-950 block">
                            T+1: {t1Value || 'N/A'}
                          </span>
                        </div>
                        {t2Value && (
                          <span className="mt-2 text-xs font-normal text-softform-text-secondary block">
                            T+2: {t2Value}
                          </span>
                        )}
                      </div>

                      {/* Policy / Paper Context */}
                      <div className="softform-card flex flex-col justify-between rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200">
                        <div>
                          <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                            Policy / Paper Context
                          </span>
                          <span className="mt-2 tabular-finance text-base font-bold text-softform-navy-950 block">
                            Base Rate: {baseRateValue || 'N/A'}
                          </span>
                        </div>
                        {(efbnT1Value || efbnT2Value) && (
                          <span className="mt-2 text-xs font-normal text-softform-text-secondary block leading-relaxed">
                            EFB Net: T+1 {efbnT1Value || 'N/A'} / T+2 {efbnT2Value || 'N/A'}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="pt-4 border-t border-softform-navy-950/5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <button
                        onClick={() => setShowDetails(!showDetails)}
                        className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted hover:text-softform-navy-950 transition-colors"
                      >
                        <span>{showDetails ? '▼ Hide HKMA source detail' : '▶ View HKMA source detail'}</span>
                      </button>

                      <span className="text-xs font-normal text-softform-text-muted leading-none">
                        * Funding window context requires liquidity history and facility terms.
                      </span>
                    </div>

                    {showDetails && (
                      <div className="space-y-4 pt-2 transition-all duration-200">
                        {liquidityEvents.map((ev) => (
                          <div
                            key={ev.id}
                            className="flex flex-col gap-1.5 rounded-2xl border border-white/50 bg-[linear-gradient(145deg,rgba(255,255,255,0.6),rgba(234,247,244,0.4))] p-4 shadow-sm hover:scale-[1.005] transition-all"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-[10px] font-semibold uppercase tracking-wider text-softform-teal-deep">
                                {ev.date ? `Source date ${ev.date}` : 'Source date unavailable'}
                              </span>
                              <span
                                className={clsx(
                                  'rounded-full px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider',
                                  ev.severity === 'Caution'
                                    ? 'bg-softform-amber-200/20 text-softform-amber-700'
                                    : 'bg-softform-navy-900/5 text-softform-text-secondary',
                                )}
                              >
                                {ev.severity}
                              </span>
                            </div>
                            <h4 className="text-sm font-semibold text-softform-navy-900">
                              {ev.event}
                            </h4>
                            <p className="text-xs text-softform-text-secondary leading-relaxed">
                              {ev.impact}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })()}
            </div>
          </div>
        )}
      </MotionReveal>
    </MotionStagger>
  )
}
