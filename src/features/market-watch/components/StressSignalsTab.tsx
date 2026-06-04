import { AlertTriangle, TrendingDown } from 'lucide-react'
import { StressScenario, StressSourceInfo, CompanyProfile } from '../types'
import clsx from 'clsx'
import SourceInfoTooltip from './SourceInfoTooltip'
import { MarketWatchInsightSet } from '../insights/types'
import LoadingState from './LoadingState'
import MotionStagger from './MotionStagger'
import MotionReveal from './MotionReveal'

type StressSignalsTabProps = {
  scenarios: StressScenario[]
  stressSource: StressSourceInfo | null
  profile?: CompanyProfile | null
  insights?: MarketWatchInsightSet
  loading?: boolean
}

export default function StressSignalsTab({
  scenarios,
  stressSource,
  profile,
  insights,
  loading,
}: StressSignalsTabProps) {

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="softform-panel rounded-[28px] p-8">
          <div className="grid gap-6 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <LoadingState key={i} variant="card" label="Preparing scenario context..." lines={3} />
            ))}
          </div>
        </div>
        <LoadingState variant="card" label="Checking required workspace data..." lines={2} />
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <LoadingState variant="card" label="Preparing stress watch signals..." lines={3} />
          </div>
          <LoadingState variant="card" label="Checking connections..." lines={3} />
        </div>
      </div>
    )
  }

  if (!stressSource) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm font-medium text-softform-text-muted">
          Loading stress signals intelligence...
        </div>
      </div>
    )
  }

  const getScenarioDataStatus = (scen: StressScenario) => {
    if (!profile) return scen.requiredDataStatus || 'Requires company financials'
    const ids = scen.requiredDataIds || []
    if (ids.length === 0) return 'Context Only'
    const records = ids.map(id => profile.connectedRecords.find(r => r.id === id))
    const allConnected = records.every(r => r && r.status === 'connected')
    const anyConnected = records.some(r => r && r.status === 'connected')
    if (allConnected) return 'Data Connected'
    if (anyConnected) return 'Partial Data'
    return 'Requires company financials'
  }

  const getScenarioImplication = (scenId: string): string => {
    const idLower = scenId.toLowerCase()
    if (idLower.includes('rate') || idLower.includes('stress-1') || idLower.includes('150')) {
      return "Review whether operating cashflow has enough buffer under this rate-shock context."
    }
    if (idLower.includes('receivables') || idLower.includes('delay') || idLower.includes('stress-2') || idLower.includes('15')) {
      return "Review whether credit facilities and collections buffer a 15-day stretch."
    }
    if (idLower.includes('fx') || idLower.includes('cny') || idLower.includes('depreciation') || idLower.includes('volatility')) {
      return "Review whether import payables conversion margins are protected."
    }
    if (idLower.includes('commodity') || idLower.includes('squeeze') || idLower.includes('input') || idLower.includes('raw')) {
      return "Review whether supplier/customer terms would absorb this input-cost context."
    }
    if (idLower.includes('liquidity')) {
      return "Review revolving facility commit status during interbank rate spikes."
    }
    return "Review potential cashflow volatility before impact can be quantified."
  }

  // Split scenarios into priority vs secondary
  const priorityIds = ['rate-shock-150', 'receivables-delay-15', 'fx-volatility-5']
  
  const mappedScenarios = scenarios.map(scen => {
    const finalScen = { ...scen }
    if (scen.title === 'Rate Shock (+150 bps)') {
      finalScen.title = 'Rate sensitivity scenario'
    }
    if (!insights?.stress) return finalScen
    const allStressInsights = [
      ...(insights.stress.watchSignals || []),
      ...(insights.stress.supportingInsights || [])
    ]
    const matched = allStressInsights.find(i => {
      const title = i.title.toLowerCase()
      const sTitle = finalScen.title.toLowerCase()
      return (title.includes('rate') && sTitle.includes('rate')) ||
             (title.includes('receivables') && sTitle.includes('receivables')) ||
             (title.includes('cny') && sTitle.includes('cny')) ||
             (title.includes('depreciation') && sTitle.includes('depreciation')) ||
             (title.includes('commodity') && sTitle.includes('commodity')) ||
             (title.includes('liquidity') && sTitle.includes('liquidity'))
    })
    if (matched) {
      return {
        ...finalScen,
        severity: matched.severity,
        description: matched.description
      }
    }
    return finalScen
  })

  const sortedPriorityScenarios = [
    mappedScenarios.find(s => s.id.includes('rate') || s.id.includes('150')),
    mappedScenarios.find(s => s.id.includes('receivables') || s.id.includes('delay')),
    mappedScenarios.find(s => s.id.includes('fx') || s.id.includes('cny') || s.id.includes('depreciation')),
  ].filter(Boolean) as StressScenario[]

  const secondaryScenarios = mappedScenarios.filter(s => {
    const isPriority = priorityIds.includes(s.id) || 
                       s.id.includes('rate') || 
                       s.id.includes('receivables') || 
                       s.id.includes('fx')
    return !isPriority
  })

  return (
    <MotionStagger className="space-y-8">
      {/* 2. Top priority scenarios first */}
      <MotionReveal>
        <div className="softform-panel rounded-[28px] p-8">
          <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-softform-navy-950/5 pb-4">
            <div>
              <h2 className="text-xl font-semibold text-softform-navy-950 flex items-center gap-2">
                <span>Stress Scenarios</span>
                <SourceInfoTooltip
                  title="Stress Scenarios Sourcing"
                  sources={[
                    {
                      label: stressSource.label,
                      asOf: stressSource.asOf,
                      freshness: stressSource.freshness,
                      warnings: stressSource.warnings,
                      mode: 'workspace-derived'
                    }
                  ]}
                />
              </h2>
              <p className="mt-1 text-sm text-softform-text-secondary">
                Placeholder stress scenarios. Connect company records to analyze exposures.
              </p>
            </div>
            <div className="inline-flex items-center rounded-full bg-softform-navy-900/5 px-4 py-1.5 text-xs font-medium text-softform-navy-950">
              Context: {stressSource.workspaceContext.companyLabel}
            </div>
          </div>

          {/* Priority Grid */}
          <div className="grid gap-6 md:grid-cols-3">
            {sortedPriorityScenarios.map((scenario) => {
              const status = getScenarioDataStatus(scenario)
              const isConnected = status === 'Data Connected'
              const isContext = status === 'Context Only'
              
              return (
                <div
                  key={scenario.id}
                  className="softform-card flex flex-col justify-between rounded-2xl border-l-4 border-l-softform-amber-400 p-6 border-transparent hover:border-softform-teal-500/10 hover:shadow-floating-panel hover:-translate-y-0.5 transition-all duration-200"
                >
                  <div>
                    <div className="mb-3 flex items-start justify-between">
                      <h3 className="font-medium text-softform-navy-900 text-sm">
                        {scenario.title}
                      </h3>
                      <div
                        className={clsx(
                          'flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider',
                          scenario.severity === 'High'
                            ? 'bg-red-500/10 text-red-700'
                            : 'bg-softform-amber-200/20 text-softform-amber-700',
                        )}
                      >
                        <AlertTriangle size={10} strokeWidth={2.5} />
                        <span>{scenario.severity}</span>
                      </div>
                    </div>

                    <p className="mb-4 text-xs leading-relaxed text-softform-text-secondary">
                      {scenario.description || getScenarioImplication(scenario.id)}
                    </p>
                  </div>

                  <div className="border-t border-softform-navy-950/5 pt-4 space-y-3">
                    <div className="flex items-center justify-between text-xs font-medium text-softform-navy-950">
                      <span className="text-softform-text-muted uppercase tracking-wider text-[9px]">Affected Area</span>
                      <span className="flex items-center gap-1 text-softform-amber-600 text-[10px]">
                        {scenario.impactDirection === 'Negative' && <TrendingDown size={12} />}
                        {scenario.affectedArea.replace('Ratio (DSCR)', '')}
                      </span>
                    </div>

                    <div className={clsx(
                      "flex items-center justify-center gap-1.5 rounded-lg py-1 text-xs font-medium border shadow-[inset_0_1px_2px_rgba(8,17,31,0.02)]",
                      isConnected
                        ? "bg-softform-emerald-soft/5 border-softform-emerald-soft/20 text-emerald-700"
                        : isContext
                        ? "bg-softform-navy-900/5 border-softform-navy-900/10 text-softform-text-secondary"
                        : "bg-softform-amber-500/5 border-softform-amber-200/20 text-softform-amber-600"
                    )}>
                      <span className={clsx(
                        "h-1.5 w-1.5 rounded-full",
                        isConnected ? "bg-softform-emerald-soft" : isContext ? "bg-softform-text-muted" : "bg-softform-amber-500"
                      )} />
                      <span className="text-[9px] uppercase tracking-wider">{status}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Secondary Scenarios Section */}
          {secondaryScenarios.length > 0 && (
            <div className="mt-8 pt-6 border-t border-softform-navy-950/5 space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
                Additional Scenarios
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                {secondaryScenarios.map((scenario) => {
                  const status = getScenarioDataStatus(scenario)
                  
                  return (
                    <div
                      key={scenario.id}
                      className="rounded-xl border border-white/50 bg-white/30 p-4 flex items-center justify-between opacity-85 hover:scale-[1.005] hover:border-softform-teal-500/10 hover:shadow-sm transition-all duration-150"
                    >
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-xs text-softform-navy-900 block">{scenario.title}</span>
                          <span className="rounded-full bg-softform-navy-900/5 px-2 py-0.5 text-[8px] font-medium uppercase tracking-wider text-softform-text-secondary">
                            {scenario.severity}
                          </span>
                        </div>
                        <span className="text-[11px] text-softform-text-muted leading-relaxed">
                          {scenario.description || getScenarioImplication(scenario.id)}
                        </span>
                      </div>
                      <div className="text-right shrink-0 ml-3">
                        <span className="text-[10px] font-medium text-softform-text-muted block uppercase tracking-wider">
                          {status === 'Data Connected' ? 'Connected' : status === 'Context Only' ? 'Context' : 'Required'}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </MotionReveal>

      {/* 3. Required workspace data second */}
      <MotionReveal>
        <div className="softform-panel rounded-[28px] p-8">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-softform-navy-950">
            Required Workspace Data
          </h3>
          <p className="mb-4 text-xs leading-relaxed text-softform-text-secondary">
            The following financial records are required before scenario impacts can be fully quantified.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {stressSource.requiredData.map((dataItem) => {
              const profileRecord = profile?.connectedRecords.find(r => r.id === dataItem.id)
              const isConnected = profileRecord ? profileRecord.status === 'connected' : (dataItem.status !== 'requires_company_data')
              const isPartial = profileRecord ? profileRecord.status === 'partial' : false

              return (
                <div
                  key={dataItem.id}
                  className="flex items-center justify-between rounded-xl border border-softform-navy-950/5 bg-white/40 px-4 py-2.5 shadow-sm hover:scale-[1.005] hover:border-softform-teal-500/10 transition-all duration-150"
                >
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-softform-navy-900">{dataItem.label}</span>
                    <span className="text-[10px] text-softform-text-muted">{dataItem.description}</span>
                  </div>
                  <span
                    className={clsx(
                      'rounded px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider shrink-0 ml-3',
                      isConnected
                        ? 'bg-softform-emerald-soft/10 text-emerald-700'
                        : isPartial
                        ? 'bg-softform-amber-200/20 text-softform-amber-700'
                        : 'bg-purple-100 text-purple-700',
                    )}
                  >
                    {isConnected
                      ? 'Connected'
                      : isPartial
                      ? 'Partial'
                      : 'Required'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </MotionReveal>

      {/* 4. Watch Signals */}
      <MotionReveal>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Watch Signals */}
          <div className="softform-panel rounded-[28px] p-6 lg:col-span-3 space-y-4">
            <h3 className="text-sm font-semibold text-softform-navy-950 uppercase tracking-wider">
              Stress Watch Signals
            </h3>
            {stressSource.watchSignals && stressSource.watchSignals.length > 0 && (
              <div className="space-y-3">
                {stressSource.watchSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="rounded-xl border border-softform-amber-500/10 bg-softform-amber-500/5 p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 hover:scale-[1.005] transition-all duration-150"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-xs font-medium text-softform-navy-900 uppercase tracking-wider">
                          {signal.title}
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
            )}
          </div>
        </div>
      </MotionReveal>
    </MotionStagger>
  )
}
