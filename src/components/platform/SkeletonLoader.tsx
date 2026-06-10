interface SkeletonLoaderProps {
  variant?: 'card' | 'metric' | 'row' | 'text'
  count?: number
  className?: string
}

export default function SkeletonLoader({
  variant = 'card',
  count = 1,
  className = '',
}: SkeletonLoaderProps) {
  const renderSkeleton = (index: number) => {
    switch (variant) {
      case 'metric':
        return (
          <div
            key={index}
            className="softform-card rounded-[22px] p-5 space-y-3 softform-skeleton"
          >
            <div className="h-3 w-1/3 bg-softform-text-muted/10 rounded" />
            <div className="h-8 w-2/3 bg-softform-text-muted/20 rounded" />
            <div className="h-3 w-1/2 bg-softform-text-muted/10 rounded" />
          </div>
        )
      case 'row':
        return (
          <div
            key={index}
            className="flex items-center justify-between p-4 bg-white/40 rounded-xl softform-skeleton"
          >
            <div className="flex items-center gap-3 w-full">
              <div className="h-8 w-8 rounded-full bg-softform-text-muted/20 shrink-0" />
              <div className="space-y-2 w-full">
                <div className="h-3 w-1/4 bg-softform-text-muted/20 rounded" />
                <div className="h-2 w-1/2 bg-softform-text-muted/10 rounded" />
              </div>
            </div>
            <div className="h-6 w-16 bg-softform-text-muted/20 rounded-full shrink-0" />
          </div>
        )
      case 'text':
        return (
          <div key={index} className="space-y-2.5 softform-skeleton">
            <div className="h-3 w-full bg-softform-text-muted/10 rounded" />
            <div className="h-3 w-5/6 bg-softform-text-muted/10 rounded" />
            <div className="h-3 w-2/3 bg-softform-text-muted/10 rounded" />
          </div>
        )
      case 'card':
      default:
        return (
          <div
            key={index}
            className="softform-card rounded-[26px] p-6 space-y-4 softform-skeleton min-h-[140px]"
          >
            <div className="h-4 w-1/4 bg-softform-text-muted/20 rounded" />
            <div className="space-y-2">
              <div className="h-3 w-full bg-softform-text-muted/10 rounded" />
              <div className="h-3 w-5/6 bg-softform-text-muted/10 rounded" />
            </div>
            <div className="h-6 w-20 bg-softform-text-muted/15 rounded-full" />
          </div>
        )
    }
  }

  if (count > 1) {
    return (
      <div className={`space-y-4 ${className}`}>
        {Array.from({ length: count }).map((_, i) => renderSkeleton(i))}
      </div>
    )
  }

  return <div className={className}>{renderSkeleton(0)}</div>
}
