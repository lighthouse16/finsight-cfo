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
  const labelLower = source.label.toLowerCase()
  const freshnessLower = source.freshness?.toLowerCase() || ''
  
  const isFallback = labelLower.includes('unavailable') || 
                     labelLower.includes('fallback') ||
                     labelLower.includes('offline')
                     
  const isWorkspaceDerived = labelLower.includes('workspace-derived') ||
                             labelLower.includes('workspace derived') ||
                             freshnessLower === 'workspace-derived' ||
                             freshnessLower === 'workspace' ||
                             labelLower.includes('workspace seed') ||
                             labelLower.includes('seed data')
                             
  const isFixture = labelLower.includes('fixture') || 
                    labelLower.includes('mock')
                    
  const isProviderBacked = labelLower.includes('frankfurter') || 
                           labelLower.includes('hkma') || 
                           labelLower.includes('provider') ||
                           freshnessLower === 'daily' ||
                           freshnessLower === 'delayed'

  // Decide styling mode
  let containerBg = 'bg-softform-navy-900/5 text-softform-text-secondary border border-softform-navy-900/10'
  if (isFallback) {
    containerBg = 'bg-amber-500/15 text-amber-900 border border-amber-500/30'
  } else if (isProviderBacked) {
    containerBg = 'bg-emerald-500/5 text-emerald-700 border border-emerald-500/10'
  } else if (isFixture) {
    containerBg = 'bg-amber-500/5 text-amber-800 border border-amber-500/10'
  } else if (isWorkspaceDerived) {
    containerBg = 'bg-softform-navy-900/5 text-softform-text-secondary border border-softform-navy-900/10'
  }

  return (
    <div className="space-y-1">
      <div className={clsx(
        'inline-flex flex-wrap items-center gap-x-2 rounded-lg px-3 py-1 text-[11px] font-semibold',
        containerBg
      )}>
        <span>
          Source: <span className="font-bold">{source.label}</span>
          {source.asOf && ` · As of ${source.asOf}`}
          {source.freshness && ` · ${source.freshness}`}
        </span>
      </div>

      {hasWarnings && !compact && (
        <div className={clsx(
          'text-[10px] leading-relaxed max-w-2xl mt-1 opacity-75 pl-1',
          isFallback ? 'text-amber-800 font-semibold' : 'text-softform-text-muted'
        )}>
          {source.warnings!.map((w, idx) => (
            <span key={idx} className="block">
              {w}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

