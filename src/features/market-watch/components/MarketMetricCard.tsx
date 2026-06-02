import clsx from 'clsx'
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react'
import { MarketMetric, SignalSeverity } from '../types'

const severityConfig: Record<
  SignalSeverity,
  { icon: React.ElementType; colorClass: string; bgClass: string }
> = {
  High: {
    icon: AlertCircle,
    colorClass: 'text-red-800/70',
    bgClass: 'bg-red-500/7',
  },
  Caution: {
    icon: AlertTriangle,
    colorClass: 'text-softform-amber-700/80',
    bgClass: 'bg-softform-amber-200/16',
  },
  Positive: {
    icon: CheckCircle2,
    colorClass: 'text-emerald-800/70',
    bgClass: 'bg-softform-emerald-soft/10',
  },
  Neutral: {
    icon: Info,
    colorClass: 'text-softform-teal-deep/75',
    bgClass: 'bg-softform-teal-500/8',
  },
}

type MarketMetricCardProps = {
  metric: MarketMetric
}

function MotifSlot({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-10 w-full items-center justify-center rounded-2xl bg-white/32 px-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.55)] ring-1 ring-white/45">
      {children}
    </div>
  )
}

function MetricMotif({ id }: { id: MarketMetric['id'] }) {
  if (id === 'funding-conditions') {
    return (
      <MotifSlot>
        <div className="flex h-6 items-end gap-1.5" aria-hidden="true">
          {[16, 22, 14, 19, 12].map((height, index) => (
            <span
              key={`${height}-${index}`}
              className={clsx(
                'w-6 rounded-full shadow-[inset_0_1px_0_rgba(255,255,255,0.7)] sm:w-7',
                index < 2
                  ? 'bg-softform-teal-500/38'
                  : index === 2
                    ? 'bg-softform-amber-300/54'
                    : 'bg-softform-navy-900/14',
              )}
              style={{ height }}
            />
          ))}
        </div>
      </MotifSlot>
    )
  }

  if (id === 'rate-pressure') {
    return (
      <MotifSlot>
        <svg
          className="h-7 w-[132px] overflow-visible"
          viewBox="0 0 132 28"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M5 21C24 21 30 16 45 17C61 18 66 11 81 13C98 15 105 8 127 7"
            stroke="rgba(180,83,9,0.38)"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M119 6.8H127.5V15.2"
            stroke="rgba(180,83,9,0.38)"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </MotifSlot>
    )
  }

  if (id === 'sector-health') {
    return (
      <MotifSlot>
        <div className="w-full max-w-[148px] space-y-2" aria-hidden="true">
          <div className="h-2 overflow-hidden rounded-full bg-white/52 shadow-[inset_0_1px_3px_rgba(8,17,31,0.08)]">
            <div className="h-full w-[62%] rounded-full bg-softform-teal-500/46" />
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/52 shadow-[inset_0_1px_3px_rgba(8,17,31,0.08)]">
            <div className="h-full w-[38%] rounded-full bg-softform-amber-300/58" />
          </div>
        </div>
      </MotifSlot>
    )
  }

  return (
    <MotifSlot>
      <div className="flex items-center gap-1.5" aria-hidden="true">
        {['HKD', 'CNY', 'USD'].map((pair) => (
          <span
            key={pair}
            className={clsx(
              'rounded-full border border-white/65 px-2 py-0.5 text-[10px] font-bold tracking-wide shadow-[0_6px_14px_rgba(8,17,31,0.05)]',
              pair === 'CNY'
                ? 'bg-softform-amber-200/32 text-softform-amber-700/90'
                : 'bg-white/55 text-softform-text-secondary/85',
            )}
          >
            {pair}
          </span>
        ))}
      </div>
    </MotifSlot>
  )
}

export default function MarketMetricCard({ metric }: MarketMetricCardProps) {
  const config = severityConfig[metric.severity]
  const Icon = config.icon

  return (
    <div className="softform-card hover-lift relative flex min-h-[218px] flex-col overflow-hidden rounded-[24px] p-5">
      <div className="pointer-events-none absolute -right-10 -top-12 h-28 w-28 rounded-full bg-softform-teal-500/8 blur-2xl" />

      <div className="relative mb-4 flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-softform-text-secondary">
          {metric.label}
        </h3>
        <div
          className={clsx(
            'inline-flex h-5 items-center gap-1 rounded-full px-2 text-[9px] font-bold uppercase tracking-[0.12em]',
            config.colorClass,
            config.bgClass,
          )}
          title={`Severity: ${metric.severity}`}
        >
          <Icon size={9} strokeWidth={2.4} />
          <span>{metric.severity}</span>
        </div>
      </div>

      <div className="relative mb-3">
        <div className="tabular-finance text-[1.9rem] font-bold leading-none tracking-tight text-softform-navy-950 sm:text-[2rem]">
          {metric.value}
        </div>
      </div>

      <p className="relative mb-3 min-h-[2.25rem] text-sm leading-snug text-softform-text-primary">
        {metric.interpretation}
      </p>

      <div className="relative mb-4">
        <MetricMotif id={metric.id} />
      </div>

      <div className="relative mt-auto flex items-center justify-between gap-3 border-t border-softform-text-muted/10 pt-3 text-xs font-medium text-softform-text-muted">
        <span className="truncate font-semibold text-softform-navy-950/70">
          {metric.source}
        </span>
        <span
          className={clsx(
            'inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold',
            metric.freshness === 'Daily'
              ? 'bg-softform-teal-500/10 text-softform-teal-deep'
              : 'bg-softform-navy-900/5 text-softform-text-secondary',
          )}
        >
          <span
            className={clsx(
              'inline-block h-1.5 w-1.5 rounded-full',
              metric.freshness === 'Daily'
                ? 'bg-softform-teal-500'
                : 'bg-softform-text-muted/60',
            )}
          />
          {metric.freshness}
        </span>
      </div>
    </div>
  )
}
