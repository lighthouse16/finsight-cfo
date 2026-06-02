import clsx from 'clsx'
import { SectorBenchmarkItem, SectorSourceInfo } from '../types'
import SoftBarChart from './SoftBarChart'

type SectorBenchmarksTabProps = {
  benchmarks: SectorBenchmarkItem[]
  sectorSource: SectorSourceInfo | null
}

export default function SectorBenchmarksTab({
  benchmarks,
  sectorSource,
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

  const seedFallback =
    sectorSource.isFallback ||
    sectorSource.warnings.some(
      (w) =>
        w.includes('Backend unavailable') ||
        w.includes('seed data') ||
        w.includes('fixture-backed'),
    )

  const selectedSector = sectorSource.selectedSector
  const sectorHealth = sectorSource.sectorHealth
  const watchSignals = sectorSource.watchSignals
  const sourceStatus = sectorSource.sourceStatus

  return (
    <div className="space-y-8">
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
          <span className="font-semibold">{sectorSource.label}</span>
        </span>
        {sectorSource.asOf && (
          <span className="flex items-center gap-1.5">
            <span className="opacity-60">As of:</span>
            <span className="font-semibold">{sectorSource.asOf}</span>
          </span>
        )}
        <span className="text-xs opacity-50">{sectorSource.freshness}</span>
      </div>

      {/* Warnings Banner */}
      {sectorSource.warnings && sectorSource.warnings.length > 0 && (
        <div
          className={clsx(
            'rounded-2xl border px-5 py-3 text-xs leading-relaxed',
            seedFallback
              ? 'border-softform-amber-200/60 bg-softform-amber-200/10 text-softform-amber-800'
              : 'border-blue-200/60 bg-blue-50/60 text-softform-text-secondary',
          )}
        >
          {sectorSource.warnings.map((w, idx) => (
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
            <div className="grid gap-4 sm:grid-cols-2">
              {benchmarks.map((benchmark) => (
                <div
                  key={benchmark.id}
                  className="rounded-2xl border border-white/50 bg-[linear-gradient(145deg,rgba(255,255,255,0.7),rgba(234,247,244,0.5))] p-4 shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-softform-text-muted">
                        {benchmark.label}
                      </span>
                      <span
                        className={clsx(
                          'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider',
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
                    <div className="text-2xl font-bold text-softform-navy-950 tracking-tight mb-2">
                      {benchmark.displayValue}
                    </div>
                    <div className="text-[10px] italic text-softform-text-muted mb-2">
                      {benchmark.comparison}
                    </div>
                  </div>
                  <p className="text-xs text-softform-text-secondary leading-relaxed border-t border-softform-text-muted/5 pt-2">
                    {benchmark.context}
                  </p>
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
            {watchSignals.map((signal) => (
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
                <div className="shrink-0 text-[10px] font-semibold text-softform-text-muted bg-softform-navy-900/5 rounded-md px-2 py-1">
                  Area: {signal.affectedArea}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Source status list */}
        <div className="softform-navy-card rounded-[28px] p-6 sm:p-8 text-white flex flex-col justify-between">
          <div>
            <h3 className="mb-4 text-base font-bold">Integration Status</h3>
            <p className="mb-6 text-xs leading-relaxed text-white/80">
              Connection health for metrics and benchmark data sources.
            </p>
            <div className="space-y-3">
              {sourceStatus.map((src) => (
                <div
                  key={src.id}
                  className="flex items-center justify-between rounded-lg bg-white/5 p-2 text-xs border border-white/5"
                >
                  <span className="font-medium text-white/90">{src.label}</span>
                  <span
                    className={clsx(
                      'rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider',
                      src.status === 'connected' &&
                        'bg-softform-emerald-soft/20 text-softform-emerald-soft',
                      src.status === 'seed_data' && 'bg-blue-500/20 text-blue-300',
                      src.status === 'requires_backend' &&
                        'bg-softform-amber-500/20 text-softform-amber-300',
                      src.status === 'requires_company_data' &&
                        'bg-purple-500/20 text-purple-300',
                    )}
                  >
                    {src.status.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-6 text-[10px] text-white/40 italic">
            *Regional averages and benchmarks represent contextual indicators.
            Regional averages may vary.
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
              value: 75,
              displayValue: '45d / 38d',
              colorClass: 'bg-softform-amber-400',
            },
            {
              label: 'Your DPO vs Sector',
              value: 40,
              displayValue: '30d / 45d',
              colorClass: 'bg-softform-amber-400',
            },
            {
              label: 'Margin vs Sector',
              value: 85,
              displayValue: '18% / 15%',
              colorClass: 'bg-softform-teal-500',
            },
          ]}
        />
        <p className="mt-4 text-xs italic text-softform-text-muted">
          *Note: Requires company financials connection to generate real
          comparative metrics. Using UI seed values.
        </p>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          Use this context alongside treasury policy and advisor review before
          making cross-border funding decisions. Connect company financials to
          quantify impact.
        </p>
      </div>
    </div>
  )
}
