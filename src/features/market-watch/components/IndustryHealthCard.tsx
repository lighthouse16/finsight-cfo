import clsx from 'clsx'
import { Factory, Info } from 'lucide-react'
import { IndustryHealthResponse } from '../types'
import SourceInfoTooltip from './SourceInfoTooltip'
import { buildSourceItems } from '../utils/sourceMeta'

const bandStyles: Record<string, string> = {
  resilient: 'border-emerald-400/35 bg-emerald-500/10 text-emerald-800',
  stable: 'border-softform-teal-500/35 bg-softform-teal-500/10 text-softform-navy-900',
  watch: 'border-amber-400/35 bg-amber-400/10 text-amber-800',
  stressed: 'border-rose-400/35 bg-rose-500/10 text-rose-800',
  unavailable: 'border-slate-300/60 bg-slate-100/70 text-slate-600',
}

function labelize(value: string) {
  return value.replace(/_/g, ' ')
}

type IndustryHealthCardProps = {
  industryHealth: IndustryHealthResponse | null
}

export default function IndustryHealthCard({ industryHealth }: IndustryHealthCardProps) {
  if (!industryHealth) return null

  const provenance = industryHealth.provenance ?? industryHealth.source
  const signals = [
    ['Demand', industryHealth.demandSignal],
    ['Margin', industryHealth.marginSignal],
    ['Working capital', industryHealth.workingCapitalSignal],
    ['Benchmark', industryHealth.benchmarkSignal],
  ]

  return (
    <div className="softform-card rounded-[26px] border border-softform-teal-500/25 p-5 sm:p-6 shadow-softform-card">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex items-center gap-2">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-softform-teal-500/10 text-softform-teal-700">
              <Factory size={18} aria-hidden="true" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-softform-navy-950">
                  Industry Health Context v1
                </h3>
                {provenance && (
                  <SourceInfoTooltip
                    title="Industry Health Sourcing"
                    sources={buildSourceItems(provenance, industryHealth.warnings ? undefined : undefined)}
                  />
                )}
              </div>
              <p className="text-xs text-softform-text-muted">
                {industryHealth.sectorName} · context-only sector proxy
              </p>
            </div>
          </div>

          <p className="max-w-4xl text-sm leading-6 text-softform-text-secondary">
            {industryHealth.explanation}
          </p>
        </div>

        <div
          className={clsx(
            'inline-flex shrink-0 items-center justify-center rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em]',
            bandStyles[industryHealth.industryHealthBand] ?? bandStyles.unavailable,
          )}
        >
          {labelize(industryHealth.industryHealthBand)}
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {signals.map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-white/45 bg-white/55 p-4 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
            <div className="text-[11px] font-medium uppercase tracking-[0.16em] text-softform-text-muted">
              {label}
            </div>
            <div className="mt-2 text-sm font-semibold capitalize text-softform-navy-950">
              {labelize(value)}
            </div>
          </div>
        ))}
      </div>

      {industryHealth.components.length > 0 && (
        <div className="mt-5 grid gap-3 lg:grid-cols-2">
          {industryHealth.components.map((component) => (
            <div key={component.signal} className="rounded-2xl bg-softform-navy-900/[0.03] p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-medium text-softform-navy-950">{component.label}</div>
                <div className="text-xs font-semibold capitalize text-softform-text-muted">
                  {labelize(component.band)}
                </div>
              </div>
              {component.value && (
                <div className="mt-1 text-xs font-medium text-softform-teal-700">{component.value}</div>
              )}
              <p className="mt-2 text-xs leading-5 text-softform-text-secondary">
                {component.explanation}
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-5 flex items-start gap-2 rounded-2xl bg-white/45 px-4 py-3 text-xs leading-5 text-softform-text-muted">
        <Info size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
        <span>{industryHealth.disclaimer}</span>
      </div>
    </div>
  )
}
