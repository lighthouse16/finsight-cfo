import { AlertCircle, ArrowUpRight, ShieldAlert, Zap } from 'lucide-react'
import { MarketSignal, SourceStatusItem, CompanyProfile } from '../types'
import SourceStatusPanel from './SourceStatusPanel'

type MarketPulseTabProps = {
  signals: MarketSignal[]
  sources: SourceStatusItem[]
  profile?: CompanyProfile | null
}

export default function MarketPulseTab({
  sources,
  profile,
}: MarketPulseTabProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        {/* What Needs Attention Now Section */}
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h2 className="mb-4 text-xl font-bold text-softform-navy-950 flex items-center gap-2">
            <AlertCircle size={20} className="text-softform-amber-500" />
            What Needs Attention Now
          </h2>
          
          <div className="space-y-4">
            {profile ? (
              <>
                <div className="flex items-start gap-3 rounded-2xl bg-red-500/5 border border-red-500/10 p-4">
                  <ShieldAlert size={18} className="text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-red-800">
                      Floating-rate Exposure
                    </h4>
                    <p className="text-sm font-semibold text-softform-navy-950 mt-0.5">
                      HKD 6.5M facility remains sensitive to HIBOR movement.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 rounded-2xl bg-softform-amber-500/5 border border-softform-amber-500/10 p-4">
                  <Zap size={18} className="text-softform-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-softform-amber-800">
                      Receivables Stretch
                    </h4>
                    <p className="text-sm font-semibold text-softform-navy-950 mt-0.5">
                      DSO 52d vs 45d benchmark, creating working-capital pressure.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 rounded-2xl bg-blue-50/70 border border-blue-100 p-4">
                  <ArrowUpRight size={18} className="text-blue-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-blue-800">
                      FX/Input-cost Exposure
                    </h4>
                    <p className="text-sm font-semibold text-softform-navy-950 mt-0.5">
                      38% CNY supplier payables and 72% USD import costs need monitoring.
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-sm text-softform-text-primary">
                Please connect workspace company profile to display prioritized CFO attention items.
              </div>
            )}
          </div>
        </div>

        {/* Latest Signals */}
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h3 className="mb-4 text-base font-bold text-softform-navy-950 uppercase tracking-wider">
            Latest Signals
          </h3>
          <ul className="space-y-3 text-sm text-softform-navy-900 font-medium">
            <li className="flex items-center gap-2 border-b border-softform-navy-950/5 pb-2.5">
              <span className="h-1.5 w-1.5 rounded-full bg-softform-amber-500 shrink-0" />
              <span>HIBOR remains relevant to HKD 6.5M facility.</span>
            </li>
            <li className="flex items-center gap-2 border-b border-softform-navy-950/5 pb-2.5">
              <span className="h-1.5 w-1.5 rounded-full bg-softform-amber-500 shrink-0" />
              <span>DSO remains above sector benchmark.</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
              <span>Copper and energy costs remain input-cost watch items.</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="space-y-6">
        {/* Workspace Context */}
        <div className="softform-navy-card rounded-[28px] p-6 text-white">
          <h3 className="mb-3 text-sm font-semibold text-white/80 uppercase tracking-wider">
            Workspace Context
          </h3>
          <p className="text-xs leading-relaxed text-white/95 mb-4">
            {profile ? (
              `Harbour & Finch Trading Ltd. operates in GBA/Hong Kong. Electronics Import sector conditions remain selective.`
            ) : (
              'Workspace market watch context. Higher interest rates make debt service coverage critical.'
            )}
          </p>
          <div className="h-px bg-white/10 my-4" />
          <h4 className="mb-2 text-[10px] font-bold text-white/60 uppercase tracking-wider">
            Context Metrics
          </h4>
          <ul className="space-y-2 text-xs">
            {profile && (
              <>
                <li className="flex justify-between">
                  <span className="opacity-70">TTM Revenue:</span>
                  <span className="font-bold">HKD {profile.revenueTtmHkd.toLocaleString()}</span>
                </li>
                <li className="flex justify-between">
                  <span className="opacity-70">Cash Balance:</span>
                  <span className="font-bold">HKD {profile.cashBalanceHkd.toLocaleString()}</span>
                </li>
                <li className="flex justify-between">
                  <span className="opacity-70">Working Capital Gap:</span>
                  <span className="font-bold">HKD {profile.workingCapitalGapHkd.toLocaleString()}</span>
                </li>
              </>
            )}
          </ul>
        </div>

        <SourceStatusPanel sources={sources} />
      </div>

      {/* CFO Takeaway */}
      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm lg:col-span-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          {profile ? (
            `Floating-rate HIBOR debt and receivables stretch of ${profile.dsoDays} days are the primary drivers of working capital pressure. Active hedging and collection controls should be reviewed.`
          ) : (
            'Use this context alongside treasury policy and advisor review before making cross-border funding decisions. Connect company financials to quantify impact.'
          )}
        </p>
      </div>
    </div>
  )
}
