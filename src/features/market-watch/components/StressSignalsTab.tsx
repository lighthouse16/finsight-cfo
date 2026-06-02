import { AlertTriangle, TrendingDown } from 'lucide-react'
import { StressScenario } from '../types'
import clsx from 'clsx'

type StressSignalsTabProps = {
  scenarios: StressScenario[]
}

export default function StressSignalsTab({ scenarios }: StressSignalsTabProps) {
  return (
    <div className="space-y-6">
      <div className="softform-panel rounded-[28px] p-6 sm:p-8">
        <h2 className="mb-2 text-xl font-bold text-softform-navy-950">
          Stress Scenarios
        </h2>
        <p className="mb-8 text-sm leading-relaxed text-softform-text-primary">
          Anticipate how extreme market movements could impact your financial health.
          Connect your company financials to generate real impact assessments.
        </p>

        <div className="grid gap-6 lg:grid-cols-3">
          {scenarios.map((scenario) => (
            <div
              key={scenario.id}
              className="softform-card flex flex-col justify-between rounded-2xl border-l-4 border-l-softform-amber-400 p-5"
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
                <div className="flex items-center justify-center gap-1.5 rounded-full bg-softform-amber-500/5 border border-softform-amber-200/20 py-2 text-xs font-semibold text-softform-amber-600 shadow-[inset_0_1px_2px_rgba(217,168,63,0.05)]">
                  <span className="h-1.5 w-1.5 rounded-full bg-softform-amber-500 animate-pulse" />
                  <span>Connect Financial Health</span>
                </div>
              </div>
            </div>
          ))}
        </div>
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
