import { LiquidityEvent, RateSnapshot, CompanyProfile } from '../types'
import { RatesSourceInfo } from '../MarketWatchPage'
import clsx from 'clsx'
import SourceBanner from './SourceBanner'

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


  return (
    <div className="space-y-8">
      {ratesSource && (
        <SourceBanner
          source={{
            label: ratesSource.label,
            asOf: ratesSource.asOf,
            freshness: 'Daily',
            warnings: ratesSource.warnings,
          }}
        />
      )}

      {/* Rate Context & Exposure Section */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-softform-navy-950">
            Rate Context
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {rates.map((rate, idx) => (
              <div
                key={idx}
                className="softform-card flex flex-col rounded-[24px] p-5"
              >
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-bold text-softform-text-secondary">
                    {rate.label}
                  </span>
                  <span
                    className={clsx(
                      'flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-bold',
                      rate.trend === 'up' && 'bg-red-500/10 text-red-600',
                      rate.trend === 'down' &&
                        'bg-softform-emerald-soft/10 text-softform-emerald-soft',
                      rate.trend === 'flat' &&
                        'bg-softform-text-muted/10 text-softform-text-secondary',
                    )}
                  >
                    {Math.abs(rate.changeBasisPoints)} bps
                  </span>
                </div>
                <div className="mb-2 tabular-finance text-2xl font-extrabold tracking-tight text-softform-navy-950">
                  {rate.value}
                </div>
                <div className="mt-auto text-[10px] font-medium leading-normal text-softform-text-muted">
                  {rate.context}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Company Rate Exposure Context */}
        <div className="softform-panel rounded-[28px] p-6 flex flex-col justify-between">
          <h3 className="text-xs font-bold text-softform-navy-950 uppercase tracking-wider mb-3">
            Company Rate Exposure
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-[10px] uppercase font-bold text-softform-text-muted block">Floating-Rate debt</span>
              <span className="text-lg font-bold text-softform-navy-950">HKD 6.5M</span>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-softform-text-muted block">Monthly Debt Service</span>
              <span className="text-lg font-bold text-softform-navy-950">HKD 420K</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-softform-navy-950/5">
            <span className="text-[10px] uppercase font-bold text-softform-text-muted block mb-1">Sensitivity status</span>
            <span className="text-[10px] font-bold text-softform-amber-700 bg-softform-amber-500/10 rounded px-2 py-0.5 inline-block">
              demo workspace context
            </span>
          </div>
        </div>
      </div>

      {/* Liquidity Watch & Funding Window */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="softform-panel rounded-[28px] p-6 sm:p-8 lg:col-span-2">
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
                  className="flex flex-col gap-1 rounded-2xl border border-white/50 bg-[linear-gradient(145deg,rgba(255,255,255,0.6),rgba(234,247,244,0.4))] p-4 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-softform-teal-deep">
                      {ev.date}
                    </span>
                    <span
                      className={clsx(
                        'rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
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
                  <p className="text-xs text-softform-text-secondary">
                    {ev.impact}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Funding window context card */}
        <div className="softform-card flex flex-col justify-between rounded-[28px] p-6 text-softform-navy-950">
          <div>
            <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-softform-navy-900">Funding Window Context</h3>
            <p className="mb-6 text-xs leading-relaxed text-softform-text-secondary">
              A composite view of historical interbank liquidity and macro stability to identify optimal funding timing.
            </p>
            <div className="flex flex-col items-center justify-center rounded-2xl bg-softform-navy-900/5 py-6 border border-softform-navy-950/5">
              <span className="text-3xl font-extrabold tabular-nums">42/100</span>
              <span className="mt-1.5 rounded-full bg-softform-amber-500/10 px-2.5 py-0.5 text-[10px] font-bold text-softform-amber-700">
                Workspace derived
              </span>
            </div>
          </div>
          <div className="mt-6 text-[10px] text-softform-text-muted italic leading-normal">
            *Indicative timing context only — not derived from bank or HKMA platforms.
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
