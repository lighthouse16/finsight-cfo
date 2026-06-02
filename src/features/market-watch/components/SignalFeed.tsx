import clsx from 'clsx'
import { Activity, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { SignalFeedItem, SignalSeverity } from '../types'

const severityConfig: Record<
  SignalSeverity,
  { icon: React.ElementType; colorClass: string; bgClass: string }
> = {
  High: {
    icon: AlertCircle,
    colorClass: 'text-red-700',
    bgClass: 'bg-red-500/10',
  },
  Caution: {
    icon: AlertTriangle,
    colorClass: 'text-softform-amber-700',
    bgClass: 'bg-softform-amber-200/20',
  },
  Positive: {
    icon: Activity,
    colorClass: 'text-emerald-700',
    bgClass: 'bg-softform-emerald-soft/10',
  },
  Neutral: {
    icon: Info,
    colorClass: 'text-softform-teal-deep',
    bgClass: 'bg-softform-teal-500/10',
  },
}

type SignalFeedProps = {
  signals: SignalFeedItem[]
}

export default function SignalFeed({ signals }: SignalFeedProps) {
  return (
    <div className="softform-card rounded-[24px] p-1">
      <div className="flex flex-col">
        {signals.map((signal, idx) => {
          const config = severityConfig[signal.severity]
          const Icon = config.icon

          return (
            <div
              key={signal.id}
              className={clsx(
                'group p-4 transition-colors hover:bg-white/40',
                idx !== 0 && 'border-t border-softform-text-muted/10',
                idx === 0 && 'rounded-t-[20px]',
                idx === signals.length - 1 && 'rounded-b-[20px]',
              )}
            >
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-softform-navy-900/5 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-softform-text-secondary">
                    {signal.category}
                  </span>
                  <span className="text-xs text-softform-text-muted/70">
                    {signal.timestamp}
                  </span>
                </div>
                <div
                  className={clsx(
                    'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
                    config.colorClass,
                    config.bgClass,
                  )}
                >
                  <Icon size={12} strokeWidth={2.5} />
                  <span>{signal.severity}</span>
                </div>
              </div>

              <h4 className="mb-1.5 text-base font-semibold text-softform-navy-950">
                {signal.title}
              </h4>
              <p className="mb-3 text-sm leading-relaxed text-softform-text-secondary">
                {signal.description}
              </p>

              <div className="rounded-xl border border-softform-teal-500/10 bg-[linear-gradient(145deg,rgba(255,255,255,0.4),rgba(234,247,244,0.3))] p-3">
                <div className="mb-1 text-[11px] font-bold uppercase tracking-wider text-softform-teal-deep">
                  CFO Interpretation Context
                </div>
                <p className="text-sm font-medium text-softform-navy-900">
                  {signal.cfoQuestion}
                </p>
                <div className="mt-2 text-[11px] font-medium text-softform-text-muted">
                  Affected area: {signal.affectedArea}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
