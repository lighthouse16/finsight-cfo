import clsx from 'clsx'
import { Database, Link2, Plug, Server } from 'lucide-react'
import { SourceStatus, SourceStatusItem } from '../types'

const statusConfig: Record<
  SourceStatus,
  { icon: React.ElementType; colorClass: string; bgClass: string }
> = {
  'Ready for connector': {
    icon: Plug,
    colorClass: 'text-emerald-700',
    bgClass: 'bg-softform-emerald-soft/10',
  },
  'Seed data': {
    icon: Database,
    colorClass: 'text-softform-navy-950/70',
    bgClass: 'bg-softform-navy-900/5',
  },
  'Requires backend': {
    icon: Server,
    colorClass: 'text-softform-amber-700',
    bgClass: 'bg-softform-amber-200/20',
  },
  'Requires company data': {
    icon: Link2,
    colorClass: 'text-softform-navy-800',
    bgClass: 'bg-softform-navy-900/10',
  },
}

type SourceStatusPanelProps = {
  sources: SourceStatusItem[]
}

export default function SourceStatusPanel({ sources }: SourceStatusPanelProps) {
  return (
    <div className="softform-card rounded-[24px] p-6">
      <h3 className="mb-4 text-sm font-semibold text-softform-navy-900 uppercase tracking-wider">
        Integration Readiness
      </h3>
      <div className="flex flex-col gap-4">
        {sources.map((item, i) => {
          const config = statusConfig[item.status]
          const Icon = config.icon
          return (
            <div
              key={i}
              className="flex items-center justify-between border-b border-softform-text-muted/5 pb-3 last:border-0 last:pb-0"
            >
              <span className="text-sm font-medium text-softform-text-secondary">
                {item.label}
              </span>
              <div
                className={clsx(
                  'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold',
                  config.colorClass,
                  config.bgClass,
                )}
              >
                <Icon size={12} strokeWidth={2} />
                <span>{item.status}</span>
              </div>
            </div>
          )
        })}
      </div>
      <div className="mt-5 rounded-xl bg-softform-navy-900/5 p-4 text-xs leading-relaxed text-softform-text-muted">
        This workspace uses typed UI seed data to demonstrate structure without
        claiming live connectivity. The api abstraction layer is prepared for
        future backend swap.
      </div>
    </div>
  )
}
