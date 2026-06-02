import { AlertTriangle, TrendingDown } from 'lucide-react'
import { StressScenario, StressSourceInfo, CompanyProfile } from '../types'
import clsx from 'clsx'

type StressSignalsTabProps = {
  scenarios: StressScenario[]
  stressSource: StressSourceInfo | null
  profile?: CompanyProfile | null
}

export default function StressSignalsTab({
  scenarios,
  stressSource,
  profile,
}: StressSignalsTabProps) {
  if (!stressSource) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm font-medium text-softform-text-muted">
          Loading stress signals intelligence...
        </div>
      </div>
    )
  }

  const seedFallback =
    stressSource.isFallback ||
    stressSource.warnings.some(
      (w) =>
        w.toLowerCase().includes('backend unavailable') ||
        w.toLowerCase().includes('seed data') ||
        w.toLowerCase().includes('fixture-backed'),
    )

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

  return (
    <div className="space-y-6">
      {/* Source & freshness banner */}
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
          <span className="font-semibold">{stressSource.label}</span>
        </span>
        {stressSource.asOf && (
          <span className="flex items-center gap-1.5">
            <span className="opacity-60">As of:</span>
            <span className="font-semibold">{stressSource.asOf}</span>
          </span>
        )}
        <span className="text-xs opacity-50">{stressSource.freshness}</span>
      </div>

      {/* Warnings Banner */}
      {stressSource.warnings && stressSource.warnings.length > 0 && (
        <div
          className={clsx(
            'rounded-2xl border px-5 py-3 text-xs leading-relaxed',
            seedFallback
              ? 'border-softform-amber-200/60 bg-softform-amber-200/10 text-softform-amber-800'
              : 'border-blue-200/60 bg-blue-50/60 text-softform-text-secondary',
          )}
        >
          {stressSource.warnings.map((w, idx) => (
            <p key={idx} className={idx > 0 ? 'mt-1 opacity-70' : ''}>
              {w}
            </p>
          ))}
        </div>
      )}

      {/* Main panel */}
      <div className="softform-panel rounded-[28px] p-6 sm:p-8">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-bold text-softform-navy-950">
              Stress Scenarios
            </h2>
            <p className="mt-1 text-sm text-softform-text-secondary">
              {stressSource.workspaceContext.description}
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <div className="inline-flex flex-col items-end gap-1">
              <div className="inline-flex items-center rounded-full bg-softform-navy-900/5 px-4 py-2 text-sm font-semibold text-softform-navy-950">
                Viewing: {stressSource.workspaceContext.companyLabel}
              </div>
              {stressSource.workspaceContext.geography && (
                <span className="text-[10px] text-softform-text-muted font-mono uppercase tracking-wider pr-2">
                  Geography: {stressSource.workspaceContext.geography}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {scenarios.map((scenario) => (
            <div
              key={scenario.id}
              className="softform-card flex flex-col justify-between rounded-2xl border-l-4 border-l-softform-amber-400 p-6"
            >
              <div>
                <div className="mb-3 flex items-start justify-between">
                  <h3 className="font-bold text-softform-navy-900">
                    {scenario.title}
                  </h3>
                  <div
                    className={clsx(
                      'flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
                      scenario.severity === 'High'
                        ? 'bg-red-500/10 text-red-700'
                        : 'bg-softform-amber-200/20 text-softform-amber-700',
                    )}
                  >
                    <AlertTriangle size={12} strokeWidth={2.5} />
                    <span>{scenario.severity}</span>
                  </div>
                </div>

                <p className="mb-4 text-sm leading-relaxed text-softform-text-secondary">
                  {scenario.description}
                </p>

                <div className="mb-4 rounded-xl border border-softform-teal-500/20 bg-softform-teal-500/5 p-3">
                  <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-softform-teal-deep">
                    CFO Question
                  </div>
                  <div className="text-sm font-medium text-softform-navy-900">
                    "{scenario.cfoQuestion}"
                  </div>
                </div>
              </div>

              <div className="mt-auto border-t border-softform-text-muted/10 pt-4">
                <div className="mb-3 flex items-center justify-between text-xs font-semibold text-softform-navy-950">
                  <span className="text-softform-text-muted uppercase tracking-wider">Affected Area</span>
                  <span className="flex items-center gap-1 text-softform-amber-600">
                    {scenario.impactDirection === 'Negative' && <TrendingDown size={14} />}
                    {scenario.affectedArea}
                  </span>
                </div>
                {(() => {
                  const status = getScenarioDataStatus(scenario)
                  const isConnected = status === 'Data Connected'
                  const isContext = status === 'Context Only'
                  return (
                    <div className={clsx(
                      "flex items-center justify-center gap-1.5 rounded-full py-2 text-xs font-semibold shadow-[inset_0_1px_2px_rgba(8,17,31,0.05)] border",
                      isConnected
                        ? "bg-softform-emerald-soft/5 border-softform-emerald-soft/20 text-emerald-700"
                        : isContext
                        ? "bg-softform-navy-900/5 border-softform-navy-900/10 text-softform-text-secondary"
                        : "bg-softform-amber-500/5 border-softform-amber-200/20 text-softform-amber-600"
                    )}>
                      <span className={clsx(
                        "h-1.5 w-1.5 rounded-full",
                        isConnected ? "bg-softform-emerald-soft" : isContext ? "bg-softform-text-muted" : "bg-softform-amber-500 animate-pulse"
                      )} />
                      <span>{status}</span>
                    </div>
                  )
                })()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grouped Signals & Status */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 columns: Required Data & Watch Signals */}
        <div className="softform-panel rounded-[28px] p-6 sm:p-8 lg:col-span-2 space-y-6">
          {/* Required Data Checklist */}
          <div>
            <h3 className="mb-2 text-base font-bold text-softform-navy-950">
              Required Workspace Data
            </h3>
            <p className="mb-4 text-xs leading-relaxed text-softform-text-secondary">
              The following financial records are required before scenario impacts can be fully quantified.
            </p>
            <div className="grid gap-6 sm:grid-cols-2">
              {stressSource.requiredData.map((dataItem) => {
                const profileRecord = profile?.connectedRecords.find(r => r.id === dataItem.id)
                const isConnected = profileRecord ? profileRecord.status === 'connected' : (dataItem.status !== 'requires_company_data')
                const isPartial = profileRecord ? profileRecord.status === 'partial' : false

                return (
                  <div
                    key={dataItem.id}
                    className="rounded-xl border border-white/50 bg-white/40 p-6 shadow-sm flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                        <h4 className="text-sm font-bold text-softform-navy-900">
                          {dataItem.label}
                        </h4>
                        <span
                          className={clsx(
                            'rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider shrink-0',
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
                            : 'Requires company data'}
                        </span>
                      </div>
                      <p className="text-xs text-softform-text-secondary leading-relaxed">
                        {dataItem.description}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Watch Signals */}
          {stressSource.watchSignals && stressSource.watchSignals.length > 0 && (
            <div className="border-t border-softform-text-muted/10 pt-6">
              <h3 className="mb-4 text-base font-bold text-softform-navy-950">
                Stress Watch Signals
              </h3>
              <div className="space-y-4">
                {stressSource.watchSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="rounded-xl border border-softform-amber-500/10 bg-softform-amber-500/5 p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-bold text-softform-navy-900">
                          {signal.title}
                        </h4>
                        <span className="rounded-full bg-softform-amber-200/20 text-softform-amber-700 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider">
                          {signal.severity}
                        </span>
                      </div>
                      <p className="text-xs text-softform-text-secondary leading-relaxed">
                        {signal.description}
                      </p>
                    </div>
                    <div className="shrink-0 text-[10px] font-semibold text-softform-text-muted bg-softform-navy-900/5 rounded-md px-2 py-1">
                      Area: {signal.affectedArea}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column: Integration Status sidebar */}
        <div className="softform-navy-card rounded-[28px] p-6 sm:p-8 text-white flex flex-col justify-between">
          <div>
            <h3 className="mb-4 text-base font-bold">Integration Status</h3>
            <p className="mb-6 text-xs leading-relaxed text-white/80">
              Connection health for stress signal engine and company financial integration.
            </p>
            <div className="space-y-3">
              {stressSource.sourceStatus.map((src) => (
                <div
                  key={src.id}
                  className="flex items-center justify-between rounded-lg bg-white/5 p-2 text-xs border border-white/5"
                >
                  <span className="font-medium text-white/90">{src.label}</span>
                  <span
                    className={clsx(
                      'rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider',
                      src.status.toLowerCase() === 'connected' &&
                        'bg-softform-emerald-soft/20 text-softform-emerald-soft',
                      (src.status.toLowerCase() === 'seed_data' ||
                        src.status.toLowerCase() === 'seed data') &&
                        'bg-blue-500/20 text-blue-300',
                      src.status.toLowerCase() === 'requires_backend' &&
                        'bg-softform-amber-500/20 text-softform-amber-300',
                      (src.status.toLowerCase() === 'requires_company_data' ||
                        src.status.toLowerCase() === 'requires company data') &&
                        'bg-purple-500/20 text-purple-300',
                    )}
                  >
                    {src.status.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-6 text-[10px] text-white/40 italic leading-relaxed">
            *Scenario framing represents context-only scenario. Pending financial records before impact can be quantified.
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          {profile ? (
            `Your HKD ${profile.floatingRateDebtHkd.toLocaleString()} floating-rate facility is sensitive to interest rate shock. Ensure your debt schedule remains integrated and consult your banker regarding hedging options for the monthly HKD ${profile.monthlyDebtServiceHkd.toLocaleString()} debt service.`
          ) : (
            'Use this context alongside treasury policy and advisor review before making cross-border funding decisions. Connect company financials to quantify impact.'
          )}
        </p>
      </div>
    </div>
  )
}
