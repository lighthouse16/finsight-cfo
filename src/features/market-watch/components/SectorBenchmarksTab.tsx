import clsx from 'clsx'
import { SectorBenchmark } from '../types'
import SoftBarChart from './SoftBarChart'

type SectorBenchmarksTabProps = {
  benchmarks: SectorBenchmark[]
}

export default function SectorBenchmarksTab({
  benchmarks,
}: SectorBenchmarksTabProps) {
  return (
    <div className="space-y-8">
      <div className="softform-panel rounded-[28px] p-6 sm:p-8">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-bold text-softform-navy-950">
              Sector Benchmarks
            </h2>
            <p className="mt-1 text-sm text-softform-text-secondary">
              Compare your operational metrics against seeded industry averages.
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            {/* Visual selector placeholder */}
            <div className="inline-flex items-center rounded-full bg-softform-navy-900/5 px-4 py-2 text-sm font-semibold text-softform-navy-950">
              Viewing: Manufacturing (Export)
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {benchmarks.map((benchmark, idx) => (
            <div
              key={idx}
              className={clsx(
                'softform-card rounded-2xl p-6',
                idx === 0 ? 'border-softform-teal-500/30 ring-1 ring-softform-teal-500/20' : 'opacity-60 grayscale',
              )}
            >
              <h3 className="mb-4 text-lg font-bold text-softform-navy-900">
                {benchmark.sector}
              </h3>

              <div className="mb-6">
                <div className="mb-2 flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
                  <span>Industry Health Score</span>
                  <span>{benchmark.healthScore}/100</span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-white/40 border border-white/20 shadow-[inset_0_1px_2px_rgba(8,17,31,0.05)] backdrop-blur-[2px] overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full transition-all duration-700 ease-out',
                      benchmark.healthScore > 60
                        ? 'bg-[linear-gradient(90deg,rgba(32,169,154,0.6),rgba(32,169,154,0.85))]'
                        : 'bg-[linear-gradient(90deg,rgba(217,168,63,0.6),rgba(217,168,63,0.85))]',
                    )}
                    style={{ width: `${benchmark.healthScore}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 border-t border-softform-text-muted/10 pt-4">
                <div>
                  <div className="mb-1 text-xs font-medium text-softform-text-muted">
                    PMI Context
                  </div>
                  <div className="tabular-finance text-lg font-bold text-softform-navy-950">
                    {benchmark.pmi}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-xs font-medium text-softform-text-muted">
                    Export Growth
                  </div>
                  <div className="tabular-finance text-lg font-bold text-softform-navy-950">
                    {benchmark.exportGrowth}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-xs font-medium text-softform-text-muted">
                    Avg. WC Days
                  </div>
                  <div className="tabular-finance text-lg font-bold text-softform-navy-950">
                    {benchmark.workingCapitalDays}d
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-xs font-medium text-softform-text-muted">
                    Avg. Receivables
                  </div>
                  <div className="tabular-finance text-lg font-bold text-softform-navy-950">
                    {benchmark.receivablesDays}d
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-xl bg-softform-navy-900/5 p-3 text-xs font-medium text-softform-text-secondary">
                Inventory Pressure:{' '}
                <span
                  className={clsx(
                    benchmark.inventoryPressure === 'High'
                      ? 'text-softform-amber-600'
                      : 'text-softform-teal-deep',
                  )}
                >
                  {benchmark.inventoryPressure}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="softform-card rounded-[28px] p-6 sm:p-8">
        <h3 className="mb-4 text-lg font-bold text-softform-navy-950">
          Comparative Performance
        </h3>
        <SoftBarChart
          data={[
            { label: 'Your DSO vs Sector', value: 75, displayValue: '45d / 38d', colorClass: 'bg-softform-amber-400' },
            { label: 'Your DPO vs Sector', value: 40, displayValue: '30d / 45d', colorClass: 'bg-softform-amber-400' },
            { label: 'Margin vs Sector', value: 85, displayValue: '18% / 15%', colorClass: 'bg-softform-teal-500' },
          ]}
        />
        <p className="mt-4 text-xs italic text-softform-text-muted">
          *Note: Requires company financials connection to generate real comparative metrics. Using UI seed values.
        </p>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          Use this context alongside uploaded financial records before lender conversations. Connect company financials to quantify impact.
        </p>
      </div>
    </div>
  )
}
