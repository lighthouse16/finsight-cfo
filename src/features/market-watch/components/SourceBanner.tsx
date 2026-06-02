import clsx from 'clsx'

type SourceBannerProps = {
  source: {
    label: string
    asOf: string | null
    freshness?: string
    warnings?: string[]
  }
  compact?: boolean
}

export default function SourceBanner({ source, compact = false }: SourceBannerProps) {
  const hasWarnings = source.warnings && source.warnings.length > 0
  const isWorkspace = source.freshness?.toLowerCase() === 'workspace' || 
                      source.label.toLowerCase().includes('workspace') ||
                      source.label.toLowerCase().includes('seed')
  
  if (compact) {
    return (
      <div className={clsx(
        'inline-flex items-center gap-3 rounded-xl px-3 py-1.5 text-[11px] font-medium',
        isWorkspace ? 'bg-softform-amber-200/15 text-softform-amber-800' : 'bg-blue-50/60 text-softform-text-secondary'
      )}>
        <span className="opacity-60">Source:</span>
        <span className="font-semibold">{source.label}</span>
        {source.asOf && (
          <>
            <span className="opacity-40">•</span>
            <span className="opacity-70">{source.asOf}</span>
          </>
        )}
        {source.freshness && (
          <>
            <span className="opacity-40">•</span>
            <span className="opacity-70">{source.freshness}</span>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className={clsx(
        'flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl px-5 py-3 text-xs font-medium',
        isWorkspace ? 'bg-softform-amber-200/20 text-softform-amber-700' : 'bg-blue-50/70 text-softform-text-secondary'
      )}>
        <span className="flex items-center gap-1.5">
          <span className="opacity-60">Source:</span>
          <span className="font-semibold">{source.label}</span>
        </span>
        
        {source.asOf ? (
          <span className="flex items-center gap-1.5">
            <span className="opacity-60">As of:</span>
            <span className="font-semibold">{source.asOf}</span>
          </span>
        ) : source.label.toLowerCase().includes('unavailable') || source.label.toLowerCase().includes('fallback') ? (
          <span className="font-semibold text-softform-amber-800">
            Backend unavailable
          </span>
        ) : null}
        
        {source.freshness && (
          <span className="text-xs opacity-50">{source.freshness}</span>
        )}
      </div>

      {hasWarnings && (
        <div className={clsx(
          'rounded-2xl border px-5 py-3 text-xs leading-relaxed',
          isWorkspace 
            ? 'border-softform-amber-200/60 bg-softform-amber-200/10 text-softform-amber-800'
            : 'border-blue-200/60 bg-blue-50/60 text-softform-text-secondary'
        )}>
          {source.warnings!.map((w, idx) => (
            <p key={idx} className={idx > 0 ? 'mt-1 opacity-70' : ''}>
              {w}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
