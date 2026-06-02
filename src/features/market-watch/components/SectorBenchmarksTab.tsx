import clsx from 'clsx'
import { SectorBenchmarkItem, SectorSourceInfo, CompanyProfile } from '../types'
import SoftBarChart from './SoftBarChart'
import SourceBanner from './SourceBanner'
import { MarketWatchInsightSet } from '../insights/types'

type SectorBenchmarksTabProps = {
  benchmarks: SectorBenchmarkItem[]
  sectorSource: SectorSourceInfo | null
  profile?: CompanyProfile | null
  insights?: MarketWatchInsightSet
}

export default function SectorBenchmarksTab({
  benchmarks,
  sectorSource,
  profile,
  insights,
}: SectorBenchmarksTabProps) {
  if (!sectorSource) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm font-medium text-softform-text-muted">
          Loading sector intelligence...
        </div>
      </div>
    )
  }



  const selectedSector = sectorSource.selectedSector
  const sectorHealth = sectorSource.sectorHealth
  const watchSignals = sectorSource.watchSignals
  const sourceStatus = sectorSource.sourceStatus

  return (
    <div className="space-y-8">
      <SourceBanner
        source={{
          label: sectorSource.label,
          asOf: sectorSource.asOf,
          freshness: sectorSource.freshness,
          warnings: sectorSource.warnings,
        }}
      />

      {/* Main panel */}
      <div className="softform-panel rounded-[28px] p-6 sm:p-8">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-bold text-softform-navy-950">
              Sector Benchmarks
            </h2>
            <p className="mt-1 text-sm text-softform-text-secondary">
              {selectedSector.description}
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <div className="inline-flex flex-col items-end gap-1">
              <div className="inline-flex items-center rounded-full bg-softform-navy-900/5 px-4 py-2 text-sm font-semibold text-softform-navy-950">
                Viewing: {selectedSector.name} ({selectedSector.geography})
              </div>
              {selectedSector.code && (
                <span className="text-[10px] text-softform-text-muted font-mono uppercase tracking-wider pr-2">
                  Code: {selectedSector.code}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Health score and health components */}
          <div className="softform-card rounded-2xl p-6 lg:col-span-1 border-softform-teal-500/30 ring-1 ring-softform-teal-500/20">
            <h3 className="mb-4 text-base font-bold text-softform-navy-900">
              Industry Health Score
            </h3>

            <div className="mb-6">
              <div className="mb-2 flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
                <span>{sectorHealth.label}</span>
                <span>
                  {sectorHealth.score !== null
                    ? `${sectorHealth.score}/100`
                    : 'N/A'}
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-white/40 border border-white/20 shadow-[inset_0_1px_2px_rgba(8,17,31,0.05)] backdrop-blur-[2px] overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all duration-700 ease-out',
                    sectorHealth.severity === 'Positive'
                      ? 'bg-[linear-gradient(90deg,rgba(32,169,154,0.6),rgba(32,169,154,0.85))]'
                      : sectorHealth.severity === 'Caution'
                      ? 'bg-[linear-gradient(90deg,rgba(217,168,63,0.6),rgba(217,168,63,0.85))]'
                      : 'bg-[linear-gradient(90deg,rgba(100,116,139,0.6),rgba(100,116,139,0.85))]',
                  )}
                  style={{ width: `${sectorHealth.score ?? 0}%` }}
                />
              </div>
            </div>

            {/* Health components */}
            <div className="space-y-4 border-t border-softform-text-muted/10 pt-4">
              {Object.entries(sectorHealth.components).map(([key, comp]) => {
                if (!comp) return null
                return (
                  <div key={key} className="text-xs">
                    <div className="flex items-center justify-between font-semibold text-softform-navy-900 mb-0.5">
                      <span>{comp.label}</span>
                      <span className="font-mono tabular-nums">
                        {comp.displayValue}
                      </span>
                    </div>
                    <p className="text-[11px] text-softform-text-muted leading-relaxed">
                      {comp.context}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Benchmarks grid */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-base font-bold text-softform-navy-900">
              Benchmark Indicators
            </h3>
            <div className="grid gap-6 sm:grid-cols-2">
              {benchmarks.map((benchmark) => (
                <div
                  key={benchmark.id}
                  className="rounded-2xl border border-white/50 bg-[linear-gradient(145deg,rgba(255,255,255,0.7),rgba(234,247,244,0.5))] p-5 shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-softform-text-secondary">
                        {benchmark.label}
                      </span>
                      <span
                        className={clsx(
                          'rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
                          benchmark.severity === 'Positive'
                            ? 'bg-softform-emerald-soft/10 text-emerald-700'
                            : benchmark.severity === 'Caution'
                            ? 'bg-softform-amber-200/20 text-softform-amber-700'
                            : 'bg-softform-navy-900/5 text-softform-text-secondary',
                        )}
                      >
                        {benchmark.severity}
                      </span>
                    </div>
                    {profile ? (
                      <div className="mb-2 flex items-baseline justify-between border-b border-softform-navy-950/5 pb-2">
                        <div>
                          <p className="text-[9px] uppercase font-bold text-softform-teal-deep tracking-wider">Company</p>
                          <div className="text-2xl font-extrabold text-softform-navy-950 tracking-tight">
                            {benchmark.id === 'dso' && `${profile.dsoDays}d`}
                            {benchmark.id === 'dio' && `${profile.inventoryDays}d`}
                            {benchmark.id === 'dpo' && `${profile.dpoDays}d`}
                            {benchmark.id === 'gross-margin' && `${profile.grossMarginPercent}%`}
                            {benchmark.id === 'documentation-readiness' && '85%'}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-[9px] uppercase font-bold text-softform-text-muted tracking-wider">Sector</p>
                          <div className="text-sm font-bold text-softform-text-secondary">
                            {benchmark.id === 'dso' && '45d'}
                            {benchmark.id === 'dio' && '60d'}
                            {benchmark.id === 'dpo' && '50d'}
                            {benchmark.id === 'gross-margin' && '18.5%'}
                            {benchmark.id === 'documentation-readiness' && '90%'}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="text-xl font-bold text-softform-navy-950 tracking-tight mb-1">
                          {benchmark.displayValue}
                        </div>
                        <div className="text-[9px] italic text-softform-text-muted mb-2 border-b border-softform-navy-950/5 pb-2">
                          {benchmark.comparison}
                        </div>
                      </>
                    )}
                  </div>
                  {(() => {
                    let shortContext = benchmark.context
                    if (insights?.sector) {
                      const allSecInsights = [
                        ...(insights.sector.watchSignals || []),
                        ...(insights.sector.supportingInsights || [])
                      ]
                      const matched = allSecInsights.find(
                        (i) => i.metricRefs.includes(benchmark.id === 'dso' ? 'dsoDays' : benchmark.id === 'dio' ? 'inventoryDays' : benchmark.id === 'dpo' ? 'dpoDays' : benchmark.id === 'gross-margin' ? 'grossMarginPercent' : '')
                      )
                      if (matched) {
                        shortContext = matched.description
                      } else if (benchmark.id === 'documentation-readiness') {
                        const docReady = allSecInsights.find(i => i.id === 'sector-doc-readiness')
                        if (docReady) shortContext = docReady.description
                      }
                    } else {
                      if (benchmark.id === 'dso') {
                        shortContext = "Receivables cycle slightly elevated. Maintain collection discipline."
                      } else if (benchmark.id === 'dio') {
                        shortContext = "Inventory turnaround stable. Monitor storage and holding costs."
                      } else if (benchmark.id === 'dpo') {
                        shortContext = "Leverage supplier payment terms to match receivables cycles."
                      } else if (benchmark.id === 'gross-margin') {
                        shortContext = "Input cost pressure watch on raw components."
                      } else if (benchmark.id === 'documentation-readiness') {
                        shortContext = "Invoice records complete; declarations pending final review."
                      }
                    }
                    return (
                      <p className="text-xs text-softform-text-secondary leading-relaxed opacity-95">
                        {shortContext}
                      </p>
                    )
                  })()}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Comparative analysis and signals */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Signals */}
        <div className="softform-panel rounded-[28px] p-6 sm:p-8 lg:col-span-2">
          <h3 className="mb-4 text-base font-bold text-softform-navy-950">
            Sector Watch Signals
          </h3>
          <div className="space-y-4">
            {(insights?.sector?.watchSignals && insights.sector.watchSignals.length > 0
              ? insights.sector.watchSignals
              : watchSignals
            ).map((signal) => (
              <div
                key={signal.id}
                className={clsx(
                  'rounded-xl border p-4 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2',
                  signal.severity === 'Positive'
                    ? 'border-softform-teal-500/10 bg-softform-teal-500/5'
                    : signal.severity === 'Caution'
                    ? 'border-softform-amber-500/10 bg-softform-amber-500/5'
                    : 'border-white/50 bg-white/40',
                )}
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-sm font-bold text-softform-navy-900">
                      {signal.title}
                    </h4>
                    <span
                      className={clsx(
                        'rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
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
                {'affectedArea' in signal && signal.affectedArea && (
                  <div className="shrink-0 text-[10px] font-semibold text-softform-text-muted bg-softform-navy-900/5 rounded-md px-2 py-1">
                    Area: {signal.affectedArea}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Source status list */}
        <div className="softform-card rounded-[28px] p-6 flex flex-col justify-between text-softform-navy-950">
          <div>
            <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-softform-navy-900">Integration Status</h3>
            <p className="mb-4 text-xs leading-relaxed text-softform-text-secondary">
              Connection health for metrics and benchmark data sources.
            </p>
            <div className="space-y-2">
              {sourceStatus.map((src) => (
                <div
                  key={src.id}
                  className="flex items-center justify-between rounded-lg bg-softform-navy-900/5 p-2 text-xs border border-softform-navy-950/5"
                >
                  <span className="font-semibold text-softform-navy-900">{src.label}</span>
                  <span
                    className={clsx(
                      'rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider',
                      src.status === 'connected' &&
                        'bg-softform-emerald-soft/10 text-emerald-700',
                      src.status === 'seed_data' && 'bg-softform-navy-900/10 text-softform-text-secondary',
                      src.status === 'requires_backend' &&
                        'bg-softform-amber-200/20 text-softform-amber-700',
                      src.status === 'requires_company_data' &&
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
            *Regional averages and benchmarks represent contextual indicators.
          </div>
        </div>
      </div>

      {/* Comparative Performance Chart */}
      <div className="softform-card rounded-[28px] p-6 sm:p-8">
        <h3 className="mb-4 text-lg font-bold text-softform-navy-950">
          Comparative Performance
        </h3>
        <SoftBarChart
          data={[
            {
              label: 'Your DSO vs Sector',
              value: profile ? Math.min(100, Math.round((45 / profile.dsoDays) * 100)) : 75,
              displayValue: profile ? `${profile.dsoDays}d / 45d` : '45d / 38d',
              colorClass: 'bg-softform-amber-400',
            },
            {
              label: 'Your DPO vs Sector',
              value: profile ? Math.min(100, Math.round((profile.dpoDays / 50) * 100)) : 40,
              displayValue: profile ? `${profile.dpoDays}d / 50d` : '30d / 45d',
              colorClass: 'bg-softform-amber-400',
            },
            {
              label: 'Margin vs Sector',
              value: profile ? Math.min(100, Math.round((profile.grossMarginPercent / 18.5) * 100)) : 85,
              displayValue: profile ? `${profile.grossMarginPercent}% / 18.5%` : '18% / 15%',
              colorClass: 'bg-softform-teal-500',
            },
          ]}
        />
        <p className="mt-4 text-xs italic text-softform-text-muted">
          {profile
            ? '*Note: Comparative metrics are generated using connected company financials.'
            : '*Note: Requires company financials connection to generate real comparative metrics. Using UI seed values.'}
        </p>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          {insights?.sector?.takeaway ? (
            insights.sector.takeaway.description
          ) : profile ? (
            `Your DSO of ${profile.dsoDays} days exceeds the sector average of 45 days. Leverage receivables aging details to shorten collection terms and bridge the HKD ${profile.workingCapitalGapHkd.toLocaleString()} working capital gap.`
          ) : (
            'Use this context alongside treasury policy and advisor review before making cross-border funding decisions. Connect company financials to quantify impact.'
          )}
        </p>
      </div>
    </div>
  )
}
