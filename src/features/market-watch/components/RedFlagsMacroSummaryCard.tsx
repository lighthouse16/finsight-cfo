import {
  AlertTriangle,
  ShieldAlert,
  Info,
  Minus,
  ChevronRight,
} from 'lucide-react'
import { type RedFlagsMacroSummaryResponse } from '../types'
import SourceInfoTooltip from './SourceInfoTooltip'
import MotionReveal from './MotionReveal'

type Props = {
  summary: RedFlagsMacroSummaryResponse | null
}

const SEVERITY_CONFIG: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  stressed: {
    bg: 'bg-red-500/5',
    border: 'border-red-500/20',
    text: 'text-red-700',
    icon: 'text-red-600',
  },
  elevated: {
    bg: 'bg-softform-amber-500/5',
    border: 'border-softform-amber-500/20',
    text: 'text-softform-amber-800',
    icon: 'text-softform-amber-600',
  },
  moderate: {
    bg: 'bg-amber-50',
    border: 'border-amber-200/60',
    text: 'text-amber-800',
    icon: 'text-amber-600',
  },
  low: {
    bg: 'bg-blue-50/50',
    border: 'border-blue-100',
    text: 'text-blue-700',
    icon: 'text-blue-500',
  },
  unavailable: {
    bg: 'bg-gray-50/50',
    border: 'border-gray-200/50',
    text: 'text-gray-500',
    icon: 'text-gray-400',
  },
}

const BAND_CONFIG: Record<string, { bg: string; text: string; label: string; dot: string }> = {
  stressed: {
    bg: 'bg-red-500/10',
    text: 'text-red-800',
    label: 'Stressed',
    dot: 'bg-red-500',
  },
  elevated: {
    bg: 'bg-softform-amber-500/10',
    text: 'text-softform-amber-800',
    label: 'Elevated',
    dot: 'bg-softform-amber-500',
  },
  watch: {
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    label: 'Watch',
    dot: 'bg-amber-500',
  },
  clear: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-800',
    label: 'Clear',
    dot: 'bg-emerald-500',
  },
  unavailable: {
    bg: 'bg-gray-50',
    text: 'text-gray-500',
    label: 'Unavailable',
    dot: 'bg-gray-400',
  },
}

export default function RedFlagsMacroSummaryCard({ summary }: Props) {
  if (!summary) {
    return (
      <div className="softform-panel rounded-[28px] p-6 sm:p-8">
        <div className="flex items-center justify-center min-h-[120px]">
          <p className="text-sm text-softform-text-muted">
            Red Flags summary is loading…
          </p>
        </div>
      </div>
    )
  }

  // Sort red flags by severity for display
  const severityOrder: Record<string, number> = {
    stressed: 0,
    elevated: 1,
    moderate: 2,
    low: 3,
    unavailable: 4,
  }
  const sortedFlags = [...summary.redFlags].sort(
    (a, b) => (severityOrder[a.severity] ?? 5) - (severityOrder[b.severity] ?? 5),
  )

  return (
    <div className="softform-panel rounded-[28px] p-6 sm:p-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="flex items-center gap-2">
          <AlertTriangle size={20} className="text-softform-navy-950/70" />
          <h2 className="text-xl font-semibold text-softform-navy-950">
            Red Flags &amp; Macro Risk Summary
          </h2>
          <SourceInfoTooltip
            title="Red Flags & Macro Risk Summary v1"
            sources={[
              { label: 'Golden Timing Index v1', mode: 'workspace-derived', freshness: 'Daily' },
              { label: 'Industry Health Context v1', mode: 'workspace-derived', freshness: 'Workspace' },
              { label: 'Funding Channel Ranking v1', mode: 'workspace-derived', freshness: 'Workspace' },
              { label: 'Cross-border Funding Context v1', mode: 'workspace-derived', freshness: 'Workspace' },
            ]}
          />
        </div>

        {/* Summary Band Badge */}
        <div
          className={`shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide ${
            BAND_CONFIG[summary.summaryBand]?.bg ?? 'bg-gray-50'
          } ${BAND_CONFIG[summary.summaryBand]?.text ?? 'text-gray-500'}`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              BAND_CONFIG[summary.summaryBand]?.dot ?? 'bg-gray-400'
            }`}
          />
          {BAND_CONFIG[summary.summaryBand]?.label ?? 'Unknown'}
        </div>
      </div>

      {/* Headline */}
      <p className="text-sm text-softform-navy-950/70 mb-5 leading-relaxed">
        {summary.headline}
        {'. '}
        This is a context-only summary; it consolidates market-watch signals and
        is not a credit decision, underwriting assessment, or lending recommendation.
      </p>

      {/* Red Flags grouped by severity */}
      {sortedFlags.length > 0 && (
        <div className="space-y-3 mb-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-softform-navy-950/60">
            Red Flags ({summary.redFlags.length})
          </h3>
          {sortedFlags.map((flag) => {
            const sevCfg = SEVERITY_CONFIG[flag.severity] ?? SEVERITY_CONFIG.unavailable
            const IconComponent = flag.severity === 'stressed'
              ? ShieldAlert
              : flag.severity === 'elevated'
              ? AlertTriangle
              : flag.severity === 'moderate' || flag.severity === 'low'
              ? Info
              : Minus
            return (
              <MotionReveal key={flag.flagKey}>
                <div
                  className={`rounded-2xl border ${sevCfg.border} ${sevCfg.bg} p-4 transition-all duration-150 hover:scale-[1.005]`}
                >
                  <div className="flex items-start gap-3">
                    <IconComponent
                      size={16}
                      className={`shrink-0 mt-0.5 ${sevCfg.icon}`}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className={`text-sm font-semibold ${sevCfg.text}`}>
                          {flag.label}
                        </h4>
                        <span
                          className={`inline-block text-[10px] leading-none font-medium px-1.5 py-0.5 rounded-full capitalize ${
                            sevCfg.bg
                          } ${sevCfg.text} border ${sevCfg.border}`}
                        >
                          {flag.severity}
                        </span>
                        <span className="text-[10px] leading-none text-softform-navy-950/40 capitalize">
                          {flag.category.replace('_', ' & ')}
                        </span>
                      </div>

                      {/* Signal */}
                      <p className="text-xs text-softform-navy-950/70 mt-1 line-clamp-2">
                        {flag.signal}
                      </p>

                      {/* Rationale */}
                      <p className="text-xs text-softform-navy-950/50 mt-1 line-clamp-3">
                        {flag.rationale}
                      </p>

                      {/* Suggested action */}
                      <div className="mt-2 flex items-start gap-1.5 text-xs">
                        <ChevronRight size={12} className="shrink-0 mt-0.5 text-softform-navy-950/40" />
                        <span className="text-softform-navy-950/70">
                          {flag.suggestedReviewAction}
                        </span>
                      </div>

                      {/* Supporting signals */}
                      {flag.supportingSignals.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {flag.supportingSignals.map((signal, i) => (
                            <span
                              key={i}
                              className="inline-block text-[10px] leading-none px-1.5 py-0.5 rounded-full bg-softform-navy-950/5 text-softform-navy-950/50"
                            >
                              {signal}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </MotionReveal>
            )
          })}
        </div>
      )}

      {/* Mitigants */}
      {summary.mitigants.length > 0 && (
        <div className="mb-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-softform-navy-950/60 mb-2">
            Mitigating Considerations
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {summary.mitigants.map((mitigant, i) => (
              <div
                key={i}
                className="rounded-xl border border-emerald-200/50 bg-emerald-50/50 p-3"
              >
                <p className="text-xs font-medium text-emerald-800 mb-0.5">
                  {mitigant.label}
                </p>
                <p className="text-[11px] text-emerald-700/70 leading-relaxed">
                  {mitigant.rationale}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Component breakdown */}
      {summary.components.length > 0 && (
        <div className="mb-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-softform-navy-950/60 mb-2">
            Component Breakdown
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {summary.components.map((comp, i) => (
              <div
                key={i}
                className="rounded-xl border border-softform-navy-950/10 p-3 bg-white/40"
              >
                <p className="text-[11px] font-medium text-softform-navy-950 truncate">
                  {comp.label}
                </p>
                <p className="text-xs text-softform-navy-950/60 mt-0.5 truncate">
                  {comp.value ?? '—'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer: provenance + warnings + disclaimer */}
      <div className="pt-4 border-t border-softform-navy-950/5 space-y-2">
        {/* Provenance */}
        <div className="flex items-center gap-2 text-[11px] text-softform-navy-950/40">
          <span>Source: {summary.provenance.source}</span>
          <span className="h-3 w-px bg-softform-navy-950/10" />
          <span>Provider: {summary.provenance.provider}</span>
          {summary.provenance.freshness && (
            <>
              <span className="h-3 w-px bg-softform-navy-950/10" />
              <span>Freshness: {summary.provenance.freshness}</span>
            </>
          )}
        </div>

        {/* Warnings */}
        {summary.warnings.length > 0 && (
          <div className="space-y-1">
            {summary.warnings.map((w, i) => (
              <p key={i} className="text-[11px] text-softform-amber-700/70 flex items-start gap-1">
                <Info size={10} className="shrink-0 mt-0.5 text-softform-amber-500" />
                {w}
              </p>
            ))}
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-[10px] text-softform-navy-950/40 leading-relaxed italic">
          {summary.disclaimer}
        </p>
      </div>
    </div>
  )
}
