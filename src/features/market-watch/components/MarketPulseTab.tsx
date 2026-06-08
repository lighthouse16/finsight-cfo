import { AlertCircle, ArrowUpRight, ShieldAlert, Zap } from 'lucide-react'
import { MarketSignal, SourceStatusItem, CompanyProfile, TimingSignalResponse, FundingChannelRankingResponse } from '../types'
import { MarketWatchInsightSet } from '../insights/types'
import LoadingState from './LoadingState'
import SourceInfoTooltip from './SourceInfoTooltip'

import MotionStagger from './MotionStagger'
import MotionReveal from './MotionReveal'
import TimingSignalCard from './TimingSignalCard'
import FundingChannelRankingCard from './FundingChannelRankingCard'

type MarketPulseTabProps = {
  signals: MarketSignal[]
  sources: SourceStatusItem[]
  profile?: CompanyProfile | null
  insights?: MarketWatchInsightSet
  loading?: boolean
  timingSignal?: TimingSignalResponse | null
  fundingChannelRanking?: FundingChannelRankingResponse | null
}

export default function MarketPulseTab({
  sources: _sources,
  profile,
  insights,
  loading,
  timingSignal,
  fundingChannelRanking,
}: MarketPulseTabProps) {
  // if loading, show contextual loading placeholders
  if (loading) {
    return (
      <div className="space-y-6">
        {/* What Needs Attention Now — loading placeholder */}
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h2 className="mb-4 text-xl font-semibold text-softform-navy-950 flex items-center gap-2">
            <AlertCircle size={20} className="text-softform-amber-500" />
            What Needs Attention Now
          </h2>
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <LoadingState key={i} variant="row" label="Preparing context..." />
            ))}
          </div>
        </div>

        {/* Latest Signals — loading */}
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h3 className="mb-4 text-base font-semibold text-softform-navy-950 uppercase tracking-wider">
            Latest Signals
          </h3>
          <ul className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <li key={i}>
                <LoadingState variant="compact" label="Checking source freshness..." />
              </li>
            ))}
          </ul>
        </div>
      </div>
    )
  }

  // Derive latest signals from rules engine
  const derivedLatestSignals = insights
    ? [
        ...(insights.rates.watchSignals || []),
        ...(insights.sector.watchSignals || []),
        ...(insights.fx.watchSignals || []),
        ...(insights.commodities.watchSignals || []),
        ...(insights.stress.watchSignals || []),
        ...(insights.rates.supportingInsights || []),
        ...(insights.sector.supportingInsights || []),
        ...(insights.commodities.supportingInsights || []),
        ...(insights.stress.supportingInsights || [])
      ].slice(0, 5)
    : [];

  return (
    <MotionStagger className="space-y-6">
      <MotionReveal>
        <TimingSignalCard signal={timingSignal ?? null} />
      </MotionReveal>

      <MotionReveal>
        <FundingChannelRankingCard ranking={fundingChannelRanking ?? null} />
      </MotionReveal>

      {/* What Needs Attention Now Section */}
      <MotionReveal>
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h2 className="mb-4 text-xl font-semibold text-softform-navy-950 flex items-center gap-2">
            <AlertCircle size={20} className="text-softform-amber-500" />
            <span>What Needs Attention Now</span>
            <SourceInfoTooltip
              title="Market Pulse Coverage"
              sources={[
                { label: 'HKAB / HKMA public rates', mode: 'provider-backed', freshness: 'Daily' },
                { label: 'Frankfurter FX reference rates', mode: 'provider-backed', freshness: 'Daily' },
                { label: 'Sector benchmark models', mode: 'workspace-derived', freshness: 'Monthly' },
                { label: 'Commodity price index', mode: 'workspace-derived', freshness: 'Monthly' },
                { label: 'Stress testing scenarios', mode: 'workspace-derived', freshness: 'Workspace' },
              ]}
            />
          </h2>
          
          <div className="space-y-4">
            {insights?.executivePriorities && insights.executivePriorities.length > 0 ? (
              insights.executivePriorities.slice(0, 3).map((item) => {
                const isHigh = item.severity === 'High'
                const isCaution = item.severity === 'Caution'
                const isPositive = item.severity === 'Positive'
                
                const bgClass = isHigh 
                  ? 'bg-red-500/5 border-red-500/10' 
                  : isCaution 
                  ? 'bg-softform-amber-500/5 border-softform-amber-500/10' 
                  : isPositive
                  ? 'bg-softform-emerald-soft/5 border-softform-emerald-soft/10'
                  : 'bg-blue-50/70 border-blue-100'
                  
                const textClass = isHigh 
                  ? 'text-red-800' 
                  : isCaution 
                  ? 'text-softform-amber-800' 
                  : isPositive
                  ? 'text-emerald-800'
                  : 'text-blue-800'
                  
                const iconColor = isHigh 
                  ? 'text-red-600' 
                  : isCaution 
                  ? 'text-softform-amber-600' 
                  : isPositive
                  ? 'text-emerald-600'
                  : 'text-blue-600'

                const IconComponent = isHigh ? ShieldAlert : isCaution ? Zap : ArrowUpRight

                return (
                  <div key={item.id} className={`flex items-start gap-3 rounded-2xl border p-4 ${bgClass} hover:scale-[1.005] transition-all duration-150`}>
                    <IconComponent size={18} className={`${iconColor} shrink-0 mt-0.5`} />
                    <div>
                      <h4 className={`text-xs font-medium tracking-wider ${textClass}`}>
                        {item.title}
                      </h4>
                      <p className="text-sm font-normal text-softform-navy-950 mt-0.5">
                        {item.description}
                      </p>
                    </div>
                  </div>
                )
              })
            ) : profile ? (
              <>
                <div className="flex items-start gap-3 rounded-2xl bg-red-500/5 border border-red-500/10 p-4 hover:scale-[1.005] transition-all duration-150">
                  <ShieldAlert size={18} className="text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-medium tracking-wider text-red-800">
                      Floating-rate Exposure
                    </h4>
                    <p className="text-sm font-normal text-softform-navy-950 mt-0.5">
                      HKD 6.5M facility remains sensitive to HIBOR movement.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 rounded-2xl bg-softform-amber-500/5 border border-softform-amber-500/10 p-4 hover:scale-[1.005] transition-all duration-150">
                  <Zap size={18} className="text-softform-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-medium tracking-wider text-softform-amber-800">
                      Receivables Stretch
                    </h4>
                    <p className="text-sm font-normal text-softform-navy-950 mt-0.5">
                      DSO 52d vs 45d benchmark, creating working-capital pressure.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 rounded-2xl bg-blue-50/70 border border-blue-100 p-4 hover:scale-[1.005] transition-all duration-150">
                  <ArrowUpRight size={18} className="text-blue-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-medium tracking-wider text-blue-800">
                      FX/Input-cost Exposure
                    </h4>
                    <p className="text-sm font-normal text-softform-navy-950 mt-0.5">
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
      </MotionReveal>

      {/* Latest Signals */}
      <MotionReveal>
        <div className="softform-panel rounded-[28px] p-6 sm:p-8">
          <h3 className="mb-4 text-base font-semibold text-softform-navy-950 uppercase tracking-wider">
            Latest Signals
          </h3>
          <ul className="space-y-3 text-sm text-softform-navy-900">
            {derivedLatestSignals.length > 0 ? (
              derivedLatestSignals.map((item) => {
                const bulletBg = item.severity === 'High'
                  ? 'bg-red-500'
                  : item.severity === 'Caution'
                  ? 'bg-softform-amber-500'
                  : item.severity === 'Positive'
                  ? 'bg-softform-emerald-soft'
                  : 'bg-blue-500'
                return (
                  <li key={item.id} className="flex items-start gap-2 border-b border-softform-navy-950/5 pb-2.5 last:border-b-0 last:pb-0 hover:pl-1 transition-all duration-150">
                    <span className={`h-1.5 w-1.5 rounded-full shrink-0 mt-2 ${bulletBg}`} />
                    <span>
                      <strong className="text-softform-navy-950 font-medium">{item.title}</strong>: {item.description}
                    </span>
                  </li>
                )
              })
            ) : (
              <>
                <li className="flex items-center gap-2 border-b border-softform-navy-950/5 pb-2.5 hover:pl-1 transition-all duration-150">
                  <span className="h-1.5 w-1.5 rounded-full bg-softform-amber-500 shrink-0" />
                  <span>HIBOR remains relevant to HKD 6.5M facility.</span>
                </li>
                <li className="flex items-center gap-2 border-b border-softform-navy-950/5 pb-2.5 hover:pl-1 transition-all duration-150">
                  <span className="h-1.5 w-1.5 rounded-full bg-softform-amber-500 shrink-0" />
                  <span>DSO remains above sector benchmark.</span>
                </li>
                <li className="flex items-center gap-2 hover:pl-1 transition-all duration-150">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
                  <span>Copper and energy costs remain input-cost watch items.</span>
                </li>
              </>
            )}
          </ul>
        </div>
      </MotionReveal>
    </MotionStagger>
  )
}
