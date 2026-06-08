import { CalendarClock, Info, Landmark, LineChart, Waves } from 'lucide-react'
import clsx from 'clsx'
import { TimingSignalResponse } from '../types'
import SourceInfoTooltip from './SourceInfoTooltip'

type TimingSignalCardProps = {
  signal: TimingSignalResponse | null
}

const bandStyles: Record<string, string> = {
  favorable: 'border-emerald-200/80 bg-emerald-50/80 text-emerald-800',
  neutral: 'border-blue-200/80 bg-blue-50/80 text-blue-800',
  cautious: 'border-softform-amber-200/80 bg-softform-amber-50/80 text-softform-amber-800',
  easing: 'border-emerald-200/80 bg-emerald-50/80 text-emerald-800',
  stable: 'border-blue-200/80 bg-blue-50/80 text-blue-800',
  tightening: 'border-softform-amber-200/80 bg-softform-amber-50/80 text-softform-amber-800',
  unavailable: 'border-slate-200/80 bg-slate-50/80 text-slate-700',
  none: 'border-blue-200/80 bg-blue-50/80 text-blue-800',
  month_end: 'border-softform-amber-200/80 bg-softform-amber-50/80 text-softform-amber-800',
  half_year_end: 'border-softform-amber-200/80 bg-softform-amber-50/80 text-softform-amber-800',
  year_end: 'border-softform-amber-200/80 bg-softform-amber-50/80 text-softform-amber-800',
}

const icons = [Landmark, LineChart, Waves, CalendarClock]

function formatLabel(value: string) {
  return value.replace(/_/g, ' ')
}

export default function TimingSignalCard({ signal }: TimingSignalCardProps) {
  if (!signal) return null

  return (
    <div className="softform-panel overflow-hidden rounded-[28px] border border-softform-navy-950/10 bg-white/85 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.08)] sm:p-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-2xl">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-softform-navy-950/10 bg-softform-navy-950/[0.03] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-softform-navy-700">
              Golden Timing Index v1
            </span>
            <SourceInfoTooltip
              title="Timing signal provenance"
              sources={[
                {
                  label: signal.provenance.provider,
                  mode: 'provider-backed',
                  freshness: signal.provenance.freshness,
                },
                {
                  label: signal.provenance.asOf ? `As of ${signal.provenance.asOf}` : 'As-of date unavailable',
                  mode: 'workspace-derived',
                  freshness: signal.provenance.freshness,
                },
              ]}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-2xl font-semibold tracking-[-0.03em] text-softform-navy-950">
              Market timing context is{' '}
              <span className="capitalize">{formatLabel(signal.goldenTimingBand)}</span>
            </h3>
            <span className={clsx('rounded-full border px-3 py-1 text-xs font-semibold capitalize', bandStyles[signal.goldenTimingBand])}>
              {formatLabel(signal.goldenTimingBand)}
            </span>
          </div>
          <p className="mt-3 text-sm leading-6 text-softform-text-primary">
            {signal.explanation}
          </p>
        </div>

        <div className="rounded-2xl border border-softform-navy-950/10 bg-softform-navy-950/[0.025] p-4 text-sm text-softform-navy-800 lg:w-72">
          <div className="flex items-start gap-2">
            <Info size={16} className="mt-0.5 shrink-0 text-softform-amber-600" />
            <p>{signal.disclaimer}</p>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {signal.components.map((component, index) => {
          const Icon = icons[index] ?? Info
          return (
            <div key={`${component.label}-${index}`} className="rounded-2xl border border-softform-navy-950/10 bg-white/70 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_14px_40px_rgba(15,23,42,0.08)]">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-softform-navy-950">
                  <Icon size={16} className="text-softform-amber-600" />
                  {component.label}
                </div>
                <span className={clsx('rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize', bandStyles[component.band] ?? bandStyles.unavailable)}>
                  {formatLabel(component.band)}
                </span>
              </div>
              {component.value && (
                <div className="mb-2 text-xl font-semibold tracking-[-0.03em] text-softform-navy-950">
                  {formatLabel(component.value)}
                </div>
              )}
              <p className="text-xs leading-5 text-softform-text-primary">
                {component.explanation}
              </p>
            </div>
          )
        })}
      </div>

      {signal.warnings.length > 0 && (
        <div className="mt-4 rounded-2xl border border-softform-amber-200/80 bg-softform-amber-50/60 px-4 py-3 text-xs leading-5 text-softform-amber-900">
          {signal.warnings[0]}
        </div>
      )}
    </div>
  )
}
