import clsx from 'clsx'
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react'
import { MarketMetric, SignalSeverity } from '../types'
import { motion, useReducedMotion } from 'framer-motion'

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
  metric?: MarketMetric
  loading?: boolean
  loadingLabel?: string
}

function formatSource(metric: MarketMetric) {
  const source = metric.source.trim()

  if (source.toLowerCase().includes('frankfurter')) {
    return 'Frankfurter · Daily'
  }

  if (source.toLowerCase().includes('hkma')) {
    return metric.freshness === 'Workspace'
      ? 'HKMA · Daily · Workspace-derived'
      : 'HKMA · Daily'
  }

  if (metric.id === 'sector-health') {
    return 'Workspace benchmark · Workspace'
  }

  if (metric.id === 'funding-conditions') {
    return 'Workspace-derived'
  }

  if (source.toLowerCase().includes('workspace')) {
    return 'Workspace-derived'
  }

  return metric.freshness === 'Workspace'
    ? source
    : `${source} · ${metric.freshness}`
}

const SkeletonBar = ({ className }: { className?: string }) => (
  <div
    className={clsx('rounded bg-softform-text-muted/7 animate-pulse', className)}
  />
)

export default function MarketMetricCard({ metric, loading, loadingLabel }: MarketMetricCardProps) {
  const shouldReduceMotion = useReducedMotion()

  if (loading) {
    return (
      <div className="softform-card relative flex min-h-[188px] flex-col overflow-hidden rounded-[24px] p-5 border border-transparent">
        <div className="pointer-events-none absolute -right-10 -top-12 h-28 w-28 rounded-full bg-softform-teal-500/7 blur-2xl" />

        {/* Top row: muted label + Analyzing chip */}
        <div className="relative mb-4 flex items-center justify-between gap-3">
          <SkeletonBar className="h-3 w-28" />
          <div className="inline-flex h-5 shrink-0 items-center rounded-full bg-softform-text-muted/8 px-2">
            <span className="text-[9px] font-medium uppercase tracking-[0.12em] text-softform-text-muted/35 animate-pulse">
              Analyzing
            </span>
          </div>
        </div>

        {/* Main value skeleton */}
        <div className="relative mb-3">
          <SkeletonBar className="h-8 w-44" />
        </div>

        {/* Implication skeleton */}
        <div className="relative mb-5 space-y-1.5">
          <SkeletonBar className="h-3 w-full" />
          <SkeletonBar className="h-3 w-3/4" />
        </div>

        {/* Footer */}
        <div className="relative mt-auto border-t border-softform-text-muted/10 pt-3 text-[10px] font-normal leading-snug text-softform-text-muted/40 animate-pulse">
          {loadingLabel || 'Calculating insights...'}
        </div>
      </div>
    )
  }

  const config = severityConfig[metric!.severity]
  const Icon = config.icon

  return (
    <motion.div
      whileHover={shouldReduceMotion ? {} : {
        y: -4,
        borderColor: 'rgba(32, 169, 154, 0.25)',
        boxShadow: '0 28px 86px rgba(8, 17, 31, 0.16), 0 8px 22px rgba(8, 17, 31, 0.08)',
      }}
      transition={{ duration: 0.14, ease: [0.22, 1, 0.36, 1] }}
      className="softform-card relative flex min-h-[188px] flex-col overflow-hidden rounded-[24px] p-5 border border-transparent transition-all duration-200"
    >
      <div className="pointer-events-none absolute -right-10 -top-12 h-28 w-28 rounded-full bg-softform-teal-500/7 blur-2xl" />

      <div className="relative mb-4 flex items-center justify-between gap-3">
        <h3 className="min-w-0 flex-1 whitespace-nowrap text-[9px] font-medium uppercase leading-none tracking-[0.08em] text-softform-text-muted">
          {metric!.label}
        </h3>
        <div
          className={clsx(
            'inline-flex h-5 shrink-0 items-center gap-1 rounded-full px-2 text-[9px] font-medium uppercase tracking-[0.12em]',
            config.colorClass,
            config.bgClass,
          )}
          title={`Severity: ${metric!.severity}`}
        >
          <Icon size={9} strokeWidth={2.4} />
          <span>{metric!.severity}</span>
        </div>
      </div>

      <div className="relative mb-3">
        <motion.div
          key={metric!.value}
          initial={{ opacity: 0.7 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.16 }}
          className="tabular-finance break-words text-[1.5rem] font-bold leading-[1.08] tracking-tight text-softform-navy-950 sm:text-[1.58rem]"
        >
          {metric!.value}
        </motion.div>
      </div>

      <p className="relative mb-5 line-clamp-2 text-[13px] leading-snug text-softform-text-primary">
        {metric!.interpretation}
      </p>

      <div className="relative mt-auto border-t border-softform-text-muted/10 pt-3 text-[10px] font-normal leading-snug text-softform-text-muted/65">
        <span>{formatSource(metric!)}</span>
      </div>
    </motion.div>
  )
}
