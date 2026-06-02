import { MarketSignal, SourceStatusItem, CompanyProfile } from '../types'
import SignalFeed from './SignalFeed'
import SourceStatusPanel from './SourceStatusPanel'

type MarketPulseTabProps = {
  signals: MarketSignal[]
  sources: SourceStatusItem[]
  profile?: CompanyProfile | null
}

export default function MarketPulseTab({
  signals,
  sources,
  profile,
}: MarketPulseTabProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h2 className="mb-4 text-xl font-bold text-softform-navy-950">
            Market Condition Summary
          </h2>
          <div className="prose prose-sm prose-slate max-w-none text-softform-text-primary">
            <p className="leading-relaxed">
              {profile ? (
                `For ${profile.companyName}, operating in the ${profile.sector} sector, funding conditions remain selective. Higher interest rates impact your HKD ${profile.floatingRateDebtHkd.toLocaleString()} floating-rate debt, making debt-service sensitivity and cash runway key focus areas for upcoming lender conversations.`
              ) : (
                'Funding conditions remain selective in the current macro environment. Higher interest rates make Debt Service Coverage Ratios (DSCR) and cash runway critical focus areas for upcoming lender conversations.'
              )}
            </p>
            <p className="leading-relaxed">
              {profile ? (
                `Your collections cycle is at ${profile.dsoDays} days sales outstanding (DSO) compared to the sector average of 45 days. This working capital gap of HKD ${profile.workingCapitalGapHkd.toLocaleString()} requires active receivables monitoring.`
              ) : (
                'Receivables quality is emerging as a key secondary concern, as sector average payment days have stretched. All external market signals should be contextualized against your uploaded financial records within this workspace.'
              )}
            </p>
          </div>
        </div>

        <div>
          <h3 className="mb-4 text-lg font-bold text-softform-navy-950">
            Recent Stress & Pressure Signals
          </h3>
          <SignalFeed signals={signals} />
        </div>
      </div>

      <div className="space-y-6">
        <div className="softform-navy-card rounded-[28px] p-6 text-white">
          <h3 className="mb-3 text-sm font-semibold text-white/80 uppercase tracking-wider">
            Key Watch Items
          </h3>
          <ul className="space-y-3 text-sm font-medium">
            {profile ? (
              <>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-softform-amber-400" />
                  <span>HIBOR risk on HKD {profile.floatingRateDebtHkd.toLocaleString()} debt. Monthly service: HKD {profile.monthlyDebtServiceHkd.toLocaleString()}.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-softform-teal-400" />
                  <span>FX exposure on {profile.cnySupplierPayablesPercent}% CNY supplier payables and {profile.usdImportCostPercent}% USD import costs.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-softform-aqua-300" />
                  <span>DSO gap: {profile.dsoDays} days vs 45 days sector standard. Working capital gap: HKD {profile.workingCapitalGapHkd.toLocaleString()}.</span>
                </li>
              </>
            ) : (
              <>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-softform-amber-400" />
                  <span>HIBOR movement remains a key watch item for floating-rate facilities.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-softform-teal-400" />
                  <span>Cross-border pooling opportunities emerging from CNY/HKD dynamics.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-softform-aqua-300" />
                  <span>Supplier pricing stabilization in key raw materials.</span>
                </li>
              </>
            )}
          </ul>
        </div>

        <SourceStatusPanel sources={sources} />
      </div>
    </div>
  )
}
