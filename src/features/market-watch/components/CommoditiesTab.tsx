import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { CommodityExposure, CommoditySourceInfo, CompanyProfile } from '../types'
import clsx from 'clsx'
import SourceBanner from './SourceBanner'

type CommoditiesTabProps = {
  commodities: CommodityExposure[]
  commoditySource: CommoditySourceInfo | null
  profile?: CompanyProfile | null
}

export default function CommoditiesTab({
  commodities,
  commoditySource,
  profile,
}: CommoditiesTabProps) {
  if (!commoditySource) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm font-medium text-softform-text-muted">
          Loading commodities intelligence...
        </div>
      </div>
    )
  }

  // Filter high/low relevance
  const highRelevance = commodities.filter(c => {
    const name = c.commodity.toLowerCase()
    return name.includes('copper') || name.includes('energy') || name.includes('freight') || name.includes('oil')
  })
  const lowRelevance = commodities.filter(c => {
    const name = c.commodity.toLowerCase()
    return !name.includes('copper') && !name.includes('energy') && !name.includes('freight') && !name.includes('oil')
  })

  // Margin pressure signals with Gross Margin 18.5% connection
  const marginSignals = commoditySource.marginPressureSignal?.map(sig => {
    if (sig.id === 'mod-input-cost-press') {
      return {
        ...sig,
        description: profile 
          ? `Input cost exposure monitored relative to your gross margin of 18.5%. Company-specific margin analysis requires supplier contracts.`
          : `Sector-level input cost exposure may pressure margins; company-specific impact requires financial records.`
      }
    }
    return sig
  }) || []

  return (
    <div className="space-y-8">
      {/* Source banner standard */}
      <SourceBanner
        source={{
          label: commoditySource.label,
          asOf: commoditySource.asOf,
          freshness: commoditySource.freshness,
          warnings: commoditySource.warnings,
        }}
      />

      {/* Main panel */}
      <div className="softform-panel rounded-[28px] p-8">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-softform-navy-950/5 pb-4">
          <div>
            <h2 className="text-xl font-bold text-softform-navy-950">
              Commodity & Input Cost Pressure
            </h2>
            <p className="mt-1 text-sm text-softform-text-secondary">
              Input cost exposure for Electronics Import sector.
            </p>
          </div>
          <div className="inline-flex items-center rounded-full bg-softform-navy-900/5 px-4 py-1.5 text-xs font-semibold text-softform-navy-950">
            Viewing: {commoditySource.selectedSector.name} ({commoditySource.selectedSector.geography})
          </div>
        </div>

        {/* High Relevance Section */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-softform-navy-900">
            Key Operational Inputs
          </h3>
          <div className="grid gap-6 md:grid-cols-3">
            {highRelevance.map((item, idx) => {
              const displayVal = item.displayValue || (item.yoyChange ? `${item.yoyChange} YoY` : '')
              let shortSensitivity = item.marginSensitivity
              if (item.commodity.includes('Copper')) {
                shortSensitivity = "Copper increases pressure printed circuit board and wiring cost base."
              } else if (item.commodity.includes('Energy')) {
                shortSensitivity = "Higher fuel and oil prices increase logistics and transport surcharges."
              } else if (item.commodity.includes('Freight')) {
                shortSensitivity = "Container spot rates volatility affects cross-border landed cost."
              }

              return (
                <div
                  key={idx}
                  className="softform-card rounded-2xl p-6 flex flex-col justify-between hover:shadow-floating-panel transition-all"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-bold text-softform-navy-900">{item.commodity}</span>
                      <span
                        className={clsx(
                          'flex shrink-0 items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider',
                          item.priceTrend === 'up' && 'bg-red-500/10 text-red-700',
                          item.priceTrend === 'down' && 'bg-softform-emerald-soft/10 text-emerald-700',
                          item.priceTrend === 'flat' && 'bg-softform-text-muted/10 text-softform-text-secondary',
                        )}
                      >
                        {item.priceTrend === 'up' && <ArrowUpRight size={12} />}
                        {item.priceTrend === 'down' && <ArrowDownRight size={12} />}
                        {item.priceTrend === 'flat' && <ArrowRight size={12} />}
                        <span>Trend</span>
                      </span>
                    </div>

                    <div className="text-3xl font-extrabold text-softform-navy-950 tracking-tight mb-2">
                      {displayVal}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-softform-navy-950/5">
                    <span className="block text-[10px] font-bold uppercase tracking-wider text-softform-text-muted mb-1">
                      Margin Sensitivity
                    </span>
                    <p className="text-xs text-softform-text-secondary leading-relaxed">
                      {shortSensitivity}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Low Relevance Section */}
        <div className="mt-8 pt-6 border-t border-softform-navy-950/5 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-softform-text-muted">
            Secondary / Indirect Inputs (Lower Relevance for Electronics Import)
          </h3>
          <div className="grid gap-6 md:grid-cols-2">
            {lowRelevance.map((item, idx) => {
              const displayVal = item.displayValue || (item.yoyChange ? `${item.yoyChange} YoY` : '')
              let shortSensitivity = item.marginSensitivity
              if (item.commodity.includes('Steel')) {
                shortSensitivity = "Casings and hardware impact is limited; components exposure remains low."
              } else if (item.commodity.includes('Cotton')) {
                shortSensitivity = "Indirect impact only. Easing textile inputs does not directly influence electronics margins."
              }

              return (
                <div
                  key={idx}
                  className="rounded-xl border border-white/50 bg-white/30 p-4 flex items-center justify-between opacity-80"
                >
                  <div>
                    <span className="font-semibold text-xs text-softform-navy-900 block">{item.commodity}</span>
                    <span className="text-[11px] text-softform-text-muted leading-relaxed">
                      {shortSensitivity}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-softform-navy-950 block">{displayVal}</span>
                    <span className="text-[9px] uppercase tracking-wider text-softform-text-muted">
                      {item.priceTrend}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Grouped Signals & Status */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Signals */}
        <div className="softform-panel rounded-[28px] p-6 lg:col-span-2 space-y-6">
          {marginSignals.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-bold text-softform-navy-950 uppercase tracking-wider">
                Margin Pressure Signals
              </h3>
              <div className="space-y-3">
                {marginSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className={clsx(
                      'rounded-xl border p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 bg-white/40 border-white/50',
                      signal.severity === 'Caution' && 'border-softform-amber-500/10 bg-softform-amber-500/5',
                    )}
                  >
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <h4 className="text-xs font-bold text-softform-navy-900 uppercase tracking-wider">
                          {signal.label}
                        </h4>
                        <span className="rounded-full bg-softform-amber-200/20 text-softform-amber-700 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                          {signal.severity}
                        </span>
                      </div>
                      <p className="text-xs text-softform-text-secondary leading-relaxed">
                        {signal.description}
                      </p>
                    </div>
                    <div className="shrink-0 text-[9px] font-bold text-softform-text-muted uppercase tracking-wider bg-softform-navy-900/5 rounded px-2 py-1">
                      Area: {signal.affectedArea}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Watch Signals */}
          {commoditySource.watchSignals && commoditySource.watchSignals.length > 0 && (
            <div className="border-t border-softform-navy-950/5 pt-6">
              <h3 className="mb-3 text-sm font-bold text-softform-navy-950 uppercase tracking-wider">
                Commodity Watch Signals
              </h3>
              <div className="space-y-3">
                {commoditySource.watchSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="rounded-xl border border-white/50 bg-white/40 p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-xs font-bold text-softform-navy-900 uppercase tracking-wider">
                          {signal.title}
                        </h4>
                        <span className="rounded-full bg-softform-navy-900/5 text-softform-text-secondary px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider">
                          {signal.severity}
                        </span>
                      </div>
                      <p className="text-xs text-softform-text-secondary leading-relaxed">
                        {signal.description.replace('Monitor copper and steel price trends if sourcing raw components or casings. ', '')}
                      </p>
                    </div>
                    <div className="shrink-0 text-[9px] font-bold text-softform-text-muted uppercase tracking-wider bg-softform-navy-900/5 rounded px-2 py-1">
                      Area: {signal.affectedArea}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Integration Status (Slimmer and Light themed) */}
        <div className="softform-card rounded-[28px] p-6 flex flex-col justify-between text-softform-navy-950">
          <div>
            <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-softform-navy-900">Integration Status</h3>
            <p className="mb-4 text-xs leading-relaxed text-softform-text-secondary">
              Connection health for commodity and cost-pressure data sources.
            </p>
            <div className="space-y-2">
              {commoditySource.sourceStatus.map((src) => (
                <div
                  key={src.id}
                  className="flex items-center justify-between rounded-lg bg-softform-navy-900/5 p-2 text-xs border border-softform-navy-950/5"
                >
                  <span className="font-semibold text-softform-navy-900">{src.label}</span>
                  <span
                    className={clsx(
                      'rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider',
                      src.status.toLowerCase() === 'connected' &&
                        'bg-softform-emerald-soft/10 text-emerald-700',
                      (src.status.toLowerCase() === 'seed_data' ||
                        src.status.toLowerCase() === 'seed data') &&
                        'bg-softform-navy-900/10 text-softform-text-secondary',
                      src.status.toLowerCase() === 'requires_backend' &&
                        'bg-softform-amber-200/20 text-softform-amber-700',
                      (src.status.toLowerCase() === 'requires_company_data' ||
                        src.status.toLowerCase() === 'requires company data') &&
                        'bg-purple-100 text-purple-700',
                    )}
                  >
                    {src.status.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 text-[10px] text-softform-text-muted italic leading-normal">
            *Sector-level commodity inputs and freight indexes represent context only. Company-specific margin impact requires company records.
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          {profile ? (
            `Input-cost fluctuations in Copper and Energy affect your distribution margins. Review supplier agreements relative to your current gross margin of ${profile.grossMarginPercent}%.`
          ) : (
            'Use this context alongside treasury policy and advisor review before making cross-border funding decisions. Connect company financials to quantify impact.'
          )}
        </p>
      </div>
    </div>
  )
}
