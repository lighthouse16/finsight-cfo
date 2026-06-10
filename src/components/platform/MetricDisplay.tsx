import { type ReactNode } from 'react'

interface TrendType {
  value: string | number
  isPositive: boolean
}

interface MetricDisplayProps {
  label: string
  value: string | number
  unit?: string
  trend?: TrendType
  description?: string
  className?: string
  icon?: ReactNode
}

export default function MetricDisplay({
  label,
  value,
  unit,
  trend,
  description,
  className = '',
  icon,
}: MetricDisplayProps) {
  return (
    <div className={`flex flex-col justify-between p-1 ${className}`}>
      <div>
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-softform-text-secondary">
            {label}
          </span>
          {icon && <span className="text-softform-text-muted">{icon}</span>}
        </div>
        <div className="mt-2 flex items-baseline gap-1.5">
          {unit && (
            <span className="text-sm font-medium text-softform-text-secondary">
              {unit}
            </span>
          )}
          <span className="text-2xl sm:text-3xl font-bold tracking-tight text-softform-navy-950 tabular-finance">
            {value}
          </span>
        </div>
      </div>
      {(trend || description) && (
        <div className="mt-3 flex items-center justify-between gap-2 border-t border-softform-text-muted/5 pt-2">
          {trend && (
            <span
              className={`flex items-center gap-0.5 text-xs font-medium ${
                trend.isPositive
                  ? 'text-emerald-soft'
                  : 'text-amber-500'
              }`}
            >
              <span>{trend.isPositive ? '▲' : '▼'}</span>
              <span className="tabular-finance">{trend.value}</span>
            </span>
          )}
          {description && (
            <span className="text-xs text-softform-text-secondary line-clamp-1">
              {description}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
