import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { LiquidityEvent, RateSnapshot, CompanyProfile } from '../types'
import { RatesSourceInfo } from '../MarketWatchPage'
import clsx from 'clsx'

type RatesLiquidityTabProps = {
  rates: RateSnapshot[]
  liquidityEvents: LiquidityEvent[]
  ratesSource?: RatesSourceInfo | null
  profile?: CompanyProfile | null
}

export default function RatesLiquidityTab({
  rates,
  liquidityEvents,
  ratesSource,
  profile,
}: RatesLiquidityTabProps) {
  const nonRatesWarnings =
    ratesSource?.warnings.filter(
      (w) => !w.includes('Backend unavailable') && !w.includes('seed data'),
    ) ?? []
  const seedFallback = ratesSource?.warnings.some(
    (w) => w.includes('Backend unavailable') || w.includes('seed data'),
  )

  return (
    <div className="space-y-8">
      {/* Source & freshness banner */}
      {ratesSource && (
        <div
          className={clsx(
            'flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl px-5 py-3 text-xs font-medium',
            seedFallback
              ? 'bg-softform-amber-200/20 text-softform-amber-700'
              : 'bg-blue-50/70 text-softform-text-secondary',
          )}
        >
          <span className="flex items-center gap-1.5">
            <span className="opacity-60">Source:</span>
            <span className="font-semibold">{ratesSource.label}</span>
          </span>
          {ratesSource.asOf && (
            <span className="flex items-center gap-1.5">
              <span className="opacity-60">As of:</span>
              <span className="font-semibold">{ratesSource.asOf}</span>
            </span>
          )}
          <span className="text-xs opacity-50">Daily</span>
        </div>
      )}

      {/* Soft caution for partial data */}
      {nonRatesWarnings.length > 0 && (
        <div className="rounded-2xl border border-blue-200/60 bg-blue-50/60 px-5 py-3 text-xs leading-relaxed text-softform-text-secondary">
          <p className="flex items-center gap-2 font-medium text-blue-700">
            Rates connected. Some liquidity data currently unavailable.
          </p>
          {nonRatesWarnings.map((w, i) => (
            <p key={i} className="mt-1 opacity-70">
              {w}
            </p>
          ))}
        </div>
      )}

      {/* Seed fallback message */}
      {seedFallback && (
        <div className="rounded-2xl border border-softform-amber-200/60 bg-softform-amber-200/10 px-5 py-3 text-xs leading-relaxed text-softform-amber-800">
          Backend unavailable. Showing workspace seed data.
        </div>
      )}

      {/* Rate Context */}
      <div>
        <h2 className="mb-4 text-xl font-bold text-softform-navy-950">
          Rate Context
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {rates.map((rate, idx) => (
            <div
              key={idx}
              className="softform-card flex flex-col rounded-[24px] p-5"
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="text-sm font-semibold text-softform-text-secondary">
                  {rate.label}
                </span>
                <span
                  className={clsx(
                    'flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                    rate.trend === 'up' && 'bg-red-500/10 text-red-600',
                    rate.trend === 'down' &&
                      'bg-softform-emerald-soft/10 text-softform-emerald-soft',
                    rate.trend === 'flat' &&
                      'bg-softform-text-muted/10 text-softform-text-secondary',
                  )}
                >
                  {rate.trend === 'up' && <ArrowUpRight size={14} />}
                  {rate.trend === 'down' && <ArrowDownRight size={14} />}
                  {rate.trend === 'flat' && <ArrowRight size={14} />}
                  {Math.abs(rate.changeBasisPoints)} bps
                </span>
              </div>
              <div className="mb-3 tabular-finance text-3xl font-bold tracking-tight text-softform-navy-950">
                {rate.value}
              </div>
              <div className="mt-auto text-xs font-medium leading-relaxed text-softform-text-muted">
                {rate.context}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Liquidity Watch */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h3 className="mb-4 text-lg font-bold text-softform-navy-950">
            Liquidity Watch
          </h3>
          <div className="space-y-4">
            {liquidityEvents.length === 0 ? (
              <div className="rounded-2xl border border-blue-200/60 bg-blue-50/60 px-5 py-5 text-sm text-softform-text-secondary">
                <p className="font-medium text-blue-700">
                  HKMA liquidity data is not yet normalized into workspace events.
                </p>
                <p className="mt-1 text-xs opacity-70">
                  HIBOR and HONIA rates remain connected.
                </p>
              </div>
            ) : (
              liquidityEvents.map((ev) => (
                <div
                  key={ev.id}
                  className="flex flex-col gap-2 rounded-2xl border border-white/50 bg-[linear-gradient(145deg,rgba(255,255,255,0.6),rgba(234,247,244,0.4))] p-4 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep">
                      {ev.date}
                    </span>
                    <span
                      className={clsx(
                        'rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
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
                  <p className="text-sm text-softform-text-primary">
                    {ev.impact}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="softform-navy-card flex flex-col justify-between rounded-[28px] p-6 sm:p-8 text-white">
          <div>
            <h3 className="mb-4 text-lg font-bold">Golden Timing Index</h3>
            <p className="mb-6 text-sm leading-relaxed text-white/80">
              A composite view of historical interbank liquidity, upcoming macro
              events, and rate stability to identify optimal funding windows.
            </p>
            <div className="flex flex-col items-center justify-center rounded-2xl bg-white/5 py-8">
              <span className="text-4xl font-bold tabular-nums">42/100</span>
              <span className="mt-2 rounded-full bg-softform-amber-500/20 px-3 py-1 text-xs font-medium text-softform-amber-300">
                Seeded timing view
              </span>
            </div>
          </div>
          <div className="mt-6 text-xs text-white/50">
            *Indicative workspace score — not yet derived from backend HKMA data.
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          {profile ? (
            `Your monthly debt service of HKD ${profile.monthlyDebtServiceHkd.toLocaleString()} is highly sensitive to HIBOR fluctuations. Leverage the connected debt schedule to review options for your HKD ${profile.floatingRateDebtHkd.toLocaleString()} facility.`
          ) : (
            'Use this context alongside uploaded financial records before lender conversations. Connect company financials to quantify impact.'
          )}
        </p>
      </div>
    </div>
  )
}
