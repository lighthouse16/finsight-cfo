import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { CommodityExposure, CommoditySourceInfo, CompanyProfile } from '../types'
import clsx from 'clsx'
import SourceInfoTooltip from './SourceInfoTooltip'
import { MarketWatchInsightSet } from '../insights/types'
import LoadingState from './LoadingState'
import MotionStagger from './MotionStagger'
import MotionReveal from './MotionReveal'

type CommoditiesTabProps = {
  commodities: CommodityExposure[]
  commoditySource: CommoditySourceInfo | null
  profile?: CompanyProfile | null
  insights?: MarketWatchInsightSet
  loading?: boolean
}

export default function CommoditiesTab({
  commodities,
  commoditySource,
  profile,
  insights,
  loading,
}: CommoditiesTabProps) {

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="softform-panel rounded-[28px] p-8">
          <div className="grid gap-6 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <LoadingState key={i} variant="card" label="Mapping input-cost exposure..." lines={3} />
            ))}
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <LoadingState variant="card" label="Checking margin pressure context..." lines={3} />
            <LoadingState variant="card" label="Preparing commodity watch context..." lines={2} />
          </div>
          <LoadingState variant="card" label="Checking connections..." lines={4} />
        </div>
      </div>
    )
  }

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
    <MotionStagger className="space-y-8">
      {/* Main panel */}
      <MotionReveal>
        <div className="softform-panel rounded-[28px] p-8">
          <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-softform-navy-950/5 pb-4">
            <div>
              <h2 className="text-xl font-semibold text-softform-navy-950 flex items-center gap-2">
                <span>Commodity & Input Cost Pressure</span>
                <SourceInfoTooltip
                  title="Commodities Sourcing"
                  sources={[
                    {
                      label: commoditySource.label,
                      asOf: commoditySource.asOf,
                      freshness: commoditySource.freshness,
                      warnings: commoditySource.warnings,
                      mode: 'workspace-derived'
                    }
                  ]}
                />
              </h2>
              <p className="mt-1 text-sm text-softform-text-secondary">
                Input cost exposure for Electronics Import sector.
              </p>
            </div>
            <div className="inline-flex items-center rounded-full bg-softform-navy-900/5 px-4 py-1.5 text-xs font-medium text-softform-navy-950">
              Viewing: {commoditySource.selectedSector.name} ({commoditySource.selectedSector.geography})
            </div>
          </div>

          {/* High Relevance Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-softform-navy-900">
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
                    className="softform-card rounded-2xl p-6 flex flex-col justify-between border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-medium text-softform-navy-900">{item.commodity}</span>
                        <span
                          className={clsx(
                            'flex shrink-0 items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider',
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

                      <div className="text-3xl font-bold text-softform-navy-950 tracking-tight mb-2">
                        {displayVal}
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-softform-navy-950/5">
                      <span className="block text-[10px] font-medium uppercase tracking-wider text-softform-text-muted mb-1">
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
            <h3 className="text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
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
                    className="rounded-xl border border-white/50 bg-white/30 p-4 flex items-center justify-between opacity-80 hover:scale-[1.005] hover:border-softform-teal-500/10 transition-all duration-150"
                  >
                    <div>
                      <span className="font-medium text-xs text-softform-navy-900 block">{item.commodity}</span>
                      <span className="text-[11px] text-softform-text-muted leading-relaxed">
                        {shortSensitivity}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-medium text-softform-navy-950 block">{displayVal}</span>
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
      </MotionReveal>

      {/* Grouped Signals & Status */}
      <MotionReveal>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Signals */}
          <div className="softform-panel rounded-[28px] p-6 lg:col-span-3 space-y-6">
            {marginSignals.length > 0 && (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-softform-navy-950 uppercase tracking-wider">
                  Margin Pressure Signals
                </h3>
                <div className="space-y-3">
                  {marginSignals.map((signal) => (
                    <div
                      key={signal.id}
                      className={clsx(
                        'rounded-xl border p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 bg-white/40 border-white/50 hover:scale-[1.005] transition-all duration-150',
                        signal.severity === 'Caution' && 'border-softform-amber-500/10 bg-softform-amber-500/5',
                      )}
                    >
                      <div>
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <h4 className="text-xs font-medium text-softform-navy-900 uppercase tracking-wider">
                            {signal.label}
                          </h4>
                          <span className="rounded-full bg-softform-amber-200/20 text-softform-amber-700 px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider">
                            {signal.severity}
                          </span>
                        </div>
                        <p className="text-xs text-softform-text-secondary leading-relaxed">
                          {signal.description}
                        </p>
                      </div>
                      <div className="shrink-0 text-[9px] font-medium uppercase tracking-wider text-softform-text-muted bg-softform-navy-900/5 rounded px-2 py-1">
                        Area: {signal.affectedArea}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Watch Signals */}
            {((commoditySource.watchSignals && commoditySource.watchSignals.length > 0) || (insights?.commodities?.supportingInsights && insights.commodities.supportingInsights.length > 0)) && (
              <div className="border-t border-softform-navy-950/5 pt-6">
                <h3 className="mb-3 text-sm font-semibold text-softform-navy-950 uppercase tracking-wider">
                  Commodity Watch Signals
                </h3>
                <div className="space-y-3">
                  {commoditySource.watchSignals.map((signal) => (
                    <div
                      key={signal.id}
                      className="rounded-xl border border-white/50 bg-white/40 p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 hover:scale-[1.005] transition-all duration-150"
                    >
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-xs font-medium text-softform-navy-900 uppercase tracking-wider">
                            {signal.title}
                          </h4>
                          <span className="rounded-full bg-softform-navy-900/5 text-softform-text-secondary px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider">
                            {signal.severity}
                          </span>
                        </div>
                        <p className="text-xs text-softform-text-secondary leading-relaxed">
                          {signal.description.replace('Monitor copper and steel price trends if sourcing raw components or casings. ', '')}
                        </p>
                      </div>
                      <div className="shrink-0 text-[9px] font-medium uppercase tracking-wider text-softform-text-muted bg-softform-navy-900/5 rounded px-2 py-1">
                        Area: {signal.affectedArea}
                      </div>
                    </div>
                  ))}
                  {insights?.commodities?.supportingInsights && insights.commodities.supportingInsights.map((insight) => (
                    <div
                      key={insight.id}
                      className="rounded-xl border border-white/50 bg-white/40 p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 hover:scale-[1.005] transition-all duration-150"
                    >
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-xs font-medium text-softform-navy-900 uppercase tracking-wider">
                            {insight.title}
                          </h4>
                          <span className="rounded-full bg-softform-navy-900/5 text-softform-text-secondary px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider">
                            {insight.severity}
                          </span>
                        </div>
                        <p className="text-xs text-softform-text-secondary leading-relaxed">
                          {insight.description}
                        </p>
                      </div>
                      <div className="shrink-0 text-[9px] font-medium uppercase tracking-wider text-softform-text-muted bg-softform-navy-900/5 rounded px-2 py-1">
                        Area: Sourcing Risk
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </MotionReveal>
    </MotionStagger>
  )
}
