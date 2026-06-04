import clsx from 'clsx'

type LoadingStateProps = {
  label: string
  description?: string
  variant?: 'card' | 'row' | 'banner' | 'compact'
  className?: string
  lines?: number
}

const SkeletonBar = ({ className }: { className?: string }) => (
  <div
    className={clsx('rounded bg-softform-text-muted/7 animate-pulse', className)}
  />
)

export default function LoadingState({
  label,
  description,
  variant = 'card',
  className,
  lines = 2,
}: LoadingStateProps) {
  if (variant === 'row') {
    return (
      <div className={clsx('flex items-center gap-3 py-3', className)}>
        <SkeletonBar className="h-4 w-4 shrink-0 rounded-full" />
        <div className="min-w-0 flex-1 space-y-1.5">
          <SkeletonBar className="h-3 w-48" />
          {description && <SkeletonBar className="h-2.5 w-32" />}
        </div>
        <span className="shrink-0 text-[10px] font-medium text-softform-text-muted/40">
          {label}
        </span>
      </div>
    )
  }

  if (variant === 'banner') {
    return (
      <div
        className={clsx(
          'flex items-center gap-3 rounded-2xl border border-softform-text-muted/8 bg-softform-text-muted/3 px-5 py-4',
          className,
        )}
      >
        <SkeletonBar className="h-3 w-3 shrink-0 rounded-full" />
        <span className="text-xs font-medium text-softform-text-muted/40">
          {label}
        </span>
      </div>
    )
  }

  if (variant === 'compact') {
    return (
      <div className={clsx('flex items-center gap-2', className)}>
        <SkeletonBar className="h-2.5 w-2.5 shrink-0 rounded-full" />
        <span className="text-xs text-softform-text-muted/40">{label}</span>
      </div>
    )
  }

  // default: card variant
  return (
    <div
      className={clsx(
        'softform-card flex flex-col gap-3 rounded-[24px] p-5',
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <SkeletonBar className="h-3 w-24" />
        <SkeletonBar className="h-3 w-16 rounded-full" />
      </div>
      <SkeletonBar className="h-7 w-40" />
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonBar
          key={i}
          className={i === lines - 1 ? 'h-3 w-2/3' : 'h-3 w-full'}
        />
      ))}
      {description && (
        <span className="mt-auto text-[10px] font-medium text-softform-text-muted/40">
          {description}
        </span>
      )}
    </div>
  )
}
