import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { CommodityExposure } from '../types'
import clsx from 'clsx'

type CommoditiesTabProps = {
  commodities: CommodityExposure[]
}

export default function CommoditiesTab({ commodities }: CommoditiesTabProps) {
  return (
    <div className="space-y-6">
      <div className="softform-panel rounded-[28px] p-6 sm:p-8">
        <h2 className="mb-4 text-xl font-bold text-softform-navy-950">
          Commodity & Input Cost Pressure
        </h2>
        <p className="mb-8 text-sm leading-relaxed text-softform-text-primary">
          Monitor raw material price trends to anticipate COGS pressure and margin
          compression before they impact your financial statements.
        </p>

        <div className="grid gap-4 sm:grid-cols-2">
          {commodities.map((item, idx) => (
            <div
              key={idx}
              className="softform-card flex flex-col justify-between rounded-2xl p-5"
            >
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-softform-navy-900">
                    {item.commodity}
                  </h3>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {item.affectedSectors.map((sector) => (
                      <span
                        key={sector}
                        className="rounded-full bg-softform-navy-900/5 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-softform-text-secondary"
                      >
                        {sector}
                      </span>
                    ))}
                  </div>
                </div>
                <div
                  className={clsx(
                    'flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
                    item.priceTrend === 'up' && 'bg-red-500/10 text-red-700',
                    item.priceTrend === 'down' &&
                      'bg-softform-emerald-soft/10 text-emerald-700',
                    item.priceTrend === 'flat' &&
                      'bg-softform-text-muted/10 text-softform-text-secondary',
                  )}
                >
                  {item.priceTrend === 'up' && <ArrowUpRight size={14} />}
                  {item.priceTrend === 'down' && <ArrowDownRight size={14} />}
                  {item.priceTrend === 'flat' && <ArrowRight size={14} />}
                  <span>{item.yoyChange} YoY</span>
                </div>
              </div>

              <div className="rounded-xl border border-softform-text-muted/10 bg-white/40 p-3 text-sm text-softform-navy-900">
                <span className="block text-xs font-semibold text-softform-text-muted mb-1">
                  Margin Sensitivity:
                </span>
                {item.marginSensitivity}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          Use this context alongside uploaded financial records before lender conversations. Connect company financials to quantify impact.
        </p>
      </div>
    </div>
  )
}
