import { Info } from 'lucide-react'
import clsx from 'clsx'

export type SourceItem = {
  label: string
  asOf?: string | null
  freshness?: string
  warnings?: string[]
  mode?: 'provider-backed' | 'workspace-derived' | 'fixture-backed' | 'local-fallback' | 'unavailable'
}

type SourceInfoTooltipProps = {
  title?: string
  sources: SourceItem[]
  ariaLabel?: string
}

export default function SourceInfoTooltip({ title = "Source Provenance", sources, ariaLabel }: SourceInfoTooltipProps) {
  return (
    <span className="group relative inline-flex align-middle ml-1.5 select-none">
      <button
        type="button"
        aria-label={ariaLabel || title}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-white/70 bg-white/55 text-softform-text-muted shadow-[0_6px_18px_rgba(8,17,31,0.07)] backdrop-blur-xl transition-all duration-200 hover:-translate-y-0.5 hover:border-white hover:bg-white/80 hover:text-softform-navy-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-softform-teal/40 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent"
      >
        <Info className="h-2.5 w-2.5" aria-hidden="true" strokeWidth={2.4} />
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 w-72 -translate-x-1/2 rounded-[18px] border border-white/70 bg-white/95 p-4 text-left text-xs font-normal leading-normal text-softform-navy-900 opacity-0 shadow-floating-panel backdrop-blur-xl transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:translate-y-0 group-focus-within:opacity-100 sm:left-0 sm:translate-x-0"
      >
        <div className="font-semibold text-softform-navy-950 border-b border-softform-navy-950/5 pb-1.5 mb-2">
          {title}
        </div>
        <div className="space-y-3">
          {sources.map((src, idx) => {
            const hasWarnings = src.warnings && src.warnings.length > 0
            
            // Map mode to label and styling
            let modeBadge = ''
            let modeBg = ''
            if (src.mode === 'provider-backed') {
              modeBadge = 'Workspace-derived' // Using user-facing wording: "Workspace-derived"
              modeBg = 'bg-emerald-500/10 text-emerald-700'
            } else if (src.mode === 'workspace-derived') {
              modeBadge = 'Workspace-derived'
              modeBg = 'bg-softform-navy-900/10 text-softform-text-secondary'
            } else if (src.mode === 'fixture-backed') {
              modeBadge = 'Context-only'
              modeBg = 'bg-amber-500/10 text-amber-800'
            } else if (src.mode === 'local-fallback') {
              modeBadge = 'Source pending'
              modeBg = 'bg-amber-500/20 text-amber-900'
            } else if (src.mode === 'unavailable') {
              modeBadge = 'Unavailable'
              modeBg = 'bg-red-500/10 text-red-700'
            }

            return (
              <div key={idx} className="space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-softform-navy-950 min-w-0 break-words">
                    {src.label}
                  </span>
                  {modeBadge && (
                    <span className={clsx("shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider", modeBg)}>
                      {modeBadge}
                    </span>
                  )}
                </div>
                <div className="text-[10px] text-softform-text-muted">
                  {src.asOf && `As of ${src.asOf}`}
                  {src.asOf && src.freshness && ` · `}
                  {src.freshness && `${src.freshness}`}
                </div>
                {hasWarnings && (
                  <div className="text-[9px] leading-relaxed text-amber-800 bg-amber-500/5 rounded p-1.5 mt-1">
                    {src.warnings!.map((w, wIdx) => (
                      <span key={wIdx} className="block">
                        • {w}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </span>
    </span>
  )
}
