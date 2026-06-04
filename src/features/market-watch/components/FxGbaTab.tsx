import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { ExposureNote, FxPair, GbaFundingSignal, CompanyProfile } from '../types'
import { FxSourceInfo } from '../MarketWatchPage'
import clsx from 'clsx'
import { MarketWatchInsightSet } from '../insights/types'
import LoadingState from './LoadingState'
import SourceInfoTooltip from './SourceInfoTooltip'
import MotionStagger from './MotionStagger'
import MotionReveal from './MotionReveal'

type FxGbaTabProps = {
  fxPairs: FxPair[]
  gbaSignals: GbaFundingSignal[]
  exposureNotes?: ExposureNote[]
  fxSource?: FxSourceInfo | null
  profile?: CompanyProfile | null
  insights?: MarketWatchInsightSet
  loading?: boolean
}

export default function FxGbaTab({
  fxPairs,
  gbaSignals,
  fxSource,
  profile,
  insights,
  loading,
}: FxGbaTabProps) {

  if (loading) {
    return (
      <div className="space-y-8">
        {/* FX Reference Rates Loading */}
        <div className="space-y-4">
          <div className="h-6 w-44 bg-softform-navy-950/5 rounded animate-pulse" />
          <div className="grid gap-6 grid-cols-1 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <LoadingState key={i} variant="card" label="Fetching rates..." lines={2} />
            ))}
          </div>
        </div>
        
        {/* Company FX Exposure Loading */}
        <LoadingState variant="row" label="Analyzing currency exposure..." />

        {/* Cross-border Insights Loading */}
        <div className="space-y-4">
          <div className="h-6 w-48 bg-softform-navy-950/5 rounded animate-pulse" />
          <div className="grid gap-6 grid-cols-1 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <LoadingState key={i} variant="card" label="Mapping cross-border context..." lines={3} />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <MotionStagger className="space-y-8">
      {/* 1. FX Reference Rates */}
      <MotionReveal>
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-softform-navy-950 border-b border-softform-navy-950/5 pb-2 flex items-center gap-2">
            <span>FX Reference Rates</span>
            {fxSource && (
              <SourceInfoTooltip
                title="FX Reference Rates Sourcing"
                sources={[
                  {
                    label: fxSource.label,
                    asOf: fxSource.asOf,
                    freshness: fxSource.freshness,
                    warnings: fxSource.warnings,
                    mode: fxSource.label.toLowerCase().includes('fallback') ? 'local-fallback' : 'provider-backed'
                  }
                ]}
              />
            )}
          </h2>
          <div className="grid gap-6 grid-cols-1 sm:grid-cols-3">
            {fxPairs.map((pair, idx) => {
              let helperLabel = 'Reference Rate'
              const pairName = pair.pair.toUpperCase()
              if (pairName.includes('USD/HKD')) helperLabel = 'Base reference'
              else if (pairName.includes('CNY/HKD')) helperLabel = 'Cross rate'
              else if (pairName.includes('USD/CNY')) helperLabel = 'Peg reference'

              return (
                <div
                  key={idx}
                  className="softform-card flex flex-col rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-[11px] font-medium text-softform-text-secondary uppercase tracking-wider">
                      {pair.pair}
                    </span>
                    <span className="text-[10px] font-semibold text-softform-text-muted uppercase tracking-wider">
                      {helperLabel}
                    </span>
                  </div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="tabular-finance text-3xl font-bold tracking-tight text-softform-navy-950">
                      {pair.rate}
                    </span>
                    <span
                      className={clsx(
                        'flex h-6 w-6 items-center justify-center rounded-full shrink-0 ml-3',
                        pair.trend === 'up' && 'bg-red-500/10 text-red-600',
                        pair.trend === 'down' &&
                          'bg-softform-emerald-soft/10 text-softform-emerald-soft',
                        pair.trend === 'flat' &&
                          'bg-softform-text-muted/10 text-softform-text-secondary',
                      )}
                    >
                      {pair.trend === 'up' && <ArrowUpRight size={14} />}
                      {pair.trend === 'down' && <ArrowDownRight size={14} />}
                      {pair.trend === 'flat' && <ArrowRight size={14} />}
                    </span>
                  </div>
                  <div className="mt-auto text-xs font-normal leading-relaxed text-softform-text-secondary">
                    {pair.context}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </MotionReveal>

      {/* 2. Company FX Exposure */}
      <MotionReveal>
        <div className="softform-panel rounded-[24px] p-6 bg-white/45 backdrop-blur-md border border-white/60 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-softform-teal-500/10 hover:shadow-floating-panel transition-all duration-200">
          <div className="space-y-1 max-w-md">
            <h3 className="text-sm font-semibold text-softform-navy-950">
              Company FX Exposure
            </h3>
            <p className="text-xs text-softform-text-secondary leading-relaxed">
              FX rates are provider-backed. Exposure percentages are workspace-derived.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-x-8 gap-y-4">
            <div>
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                CNY Supplier Payables
              </span>
              <span className="text-base font-bold text-softform-navy-950 tabular-finance">
                {profile ? `${profile.cnySupplierPayablesPercent}%` : '38%'}
              </span>
            </div>
            <div className="h-8 w-px bg-softform-navy-950/10 hidden md:block" />
            <div>
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                USD Import Costs
              </span>
              <span className="text-base font-bold text-softform-navy-950 tabular-finance">
                {profile ? `${profile.usdImportCostPercent}%` : '72%'}
              </span>
            </div>
            <div className="h-8 w-px bg-softform-navy-950/10 hidden md:block" />
            <div>
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider">
                Supplier Contracts
              </span>
              <span className="text-[10px] font-medium text-purple-700 bg-purple-500/10 rounded px-2.5 py-0.5 block mt-0.5 uppercase tracking-wider">
                company records required
              </span>
            </div>
          </div>
        </div>
      </MotionReveal>

      {/* 3. Cross-Border & GBA Insights */}
      <MotionReveal>
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-softform-navy-950 border-b border-softform-navy-950/5 pb-2">
            Cross-Border & GBA Insights
          </h2>
          
          {/* Core Exposure Insights */}
          <div className="grid gap-6 grid-cols-1 md:grid-cols-3">
            <div className="softform-card rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200 bg-white/30">
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider mb-2">
                CNY Payable Exposure
              </span>
              <p className="text-xs text-softform-text-secondary leading-relaxed">
                {profile ? `${profile.cnySupplierPayablesPercent}%` : '38%'} of supplier payables are CNY-linked. Review pricing terms when supplier contracts are connected.
              </p>
            </div>
            
            <div className="softform-card rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200 bg-white/30">
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider mb-2">
                USD Import-Cost Base
              </span>
              <p className="text-xs text-softform-text-secondary leading-relaxed">
                {profile ? `${profile.usdImportCostPercent}%` : '72%'} of import costs are USD-linked. Monitor landed-cost sensitivity.
              </p>
            </div>

            <div className="softform-card rounded-[24px] p-5 border border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200 bg-white/30">
              <span className="text-[10px] uppercase font-semibold text-softform-text-muted block tracking-wider mb-2">
                Funding Context
              </span>
              <p className="text-xs text-softform-text-secondary leading-relaxed">
                Cross-border funding context requires facility terms before impact can be quantified.
              </p>
            </div>
          </div>

          {/* Dynamic GBA Signals */}
          {((gbaSignals && gbaSignals.length > 0) || (insights?.fx?.watchSignals && insights.fx.watchSignals.length > 0)) && (
            <div className="mt-6 space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-softform-navy-900">
                Active GBA Watch Signals
              </h3>
              <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
                {/* Render insights.fx.watchSignals */}
                {insights?.fx?.watchSignals && insights.fx.watchSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="rounded-2xl border border-white/50 bg-white/40 p-5 shadow-sm hover:scale-[1.005] hover:border-softform-teal-500/10 hover:shadow-floating-panel transition-all duration-150"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-softform-navy-950">
                        {signal.title}
                      </h4>
                      <span
                        className={clsx(
                          'rounded-full px-2.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
                          signal.severity === 'Positive'
                            ? 'bg-softform-emerald-soft/10 text-emerald-700'
                            : signal.severity === 'Caution'
                            ? 'bg-softform-amber-200/20 text-softform-amber-700'
                            : signal.severity === 'High'
                            ? 'bg-red-500/10 text-red-700'
                            : 'bg-softform-navy-900/5 text-softform-text-secondary',
                        )}
                      >
                        {signal.severity}
                      </span>
                    </div>
                    <p className="text-xs text-softform-text-secondary leading-relaxed">
                      {signal.description}
                    </p>
                  </div>
                ))}

                {/* Render gbaSignals */}
                {gbaSignals && gbaSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="rounded-2xl border border-white/50 bg-white/40 p-5 shadow-sm hover:scale-[1.005] hover:border-softform-teal-500/10 hover:shadow-floating-panel transition-all duration-150"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-softform-teal-deep">
                        {signal.title}
                      </h4>
                      <span
                        className={clsx(
                          'rounded-full px-2.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
                          signal.severity === 'Positive'
                            ? 'bg-softform-emerald-soft/10 text-emerald-700'
                            : signal.severity === 'Caution'
                            ? 'bg-softform-amber-200/20 text-softform-amber-700'
                            : 'bg-softform-navy-900/5 text-softform-text-secondary',
                        )}
                      >
                        {signal.severity}
                      </span>
                    </div>
                    <p className="text-xs text-softform-text-secondary leading-relaxed">
                      {signal.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </MotionReveal>
    </MotionStagger>
  )
}
