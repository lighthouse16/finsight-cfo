import { Info, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import { CrossBorderFundingContextResponse } from '../types'
import SourceInfoTooltip from './SourceInfoTooltip'
import { buildSourceItems } from '../utils/sourceMeta'

type CrossBorderFundingContextCardProps = {
  context: CrossBorderFundingContextResponse | null
}

const reviewBandStyles: Record<string, string> = {
  worth_reviewing: 'border-emerald-200/80 bg-emerald-50/80 text-emerald-800',
  monitor: 'border-softform-amber-200/80 bg-softform-amber-50/80 text-softform-amber-700',
  not_priority: 'border-softform-navy-950/10 bg-softform-navy-950/[0.03] text-softform-text-secondary',
  unavailable: 'border-softform-navy-950/10 bg-softform-navy-950/[0.03] text-softform-text-muted',
}

const spreadBandLabels: Record<string, string> = {
  hkd_advantage: 'HKD more expensive',
  rmb_advantage: 'RMB more expensive',
  balanced: 'Balanced',
  unavailable: 'Unavailable',
}

const fxRiskLabels: Record<string, string> = {
  low: 'Low',
  moderate: 'Moderate',
  elevated: 'Elevated',
  unavailable: 'Unavailable',
}

export default function CrossBorderFundingContextCard({
  context,
}: CrossBorderFundingContextCardProps) {
  if (!context) return null

  return (
    <div className="softform-panel overflow-hidden rounded-[28px] border border-softform-navy-950/10 bg-white/85 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.08)] sm:p-8">
      {/* Header row */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-softform-navy-950/10 bg-softform-navy-950/[0.03] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-softform-navy-700">
          Cross-border Funding Context v1
        </span>
        {(() => {
          const mode = (context.provenance?.source_mode || 'fixture') as string;
          let modeBadge = 'Context-only';
          let modeBg = 'bg-white text-softform-text-muted border-softform-navy-950/10';
          if (mode === 'live') {
            modeBadge = 'Live';
            modeBg = 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20';
          } else if (mode === 'provider_configured' || mode === 'provider-backed') {
            modeBadge = 'Provider Configured';
            modeBg = 'bg-teal-500/10 text-teal-700 border-teal-500/20';
          } else if (mode === 'provider_not_configured') {
            modeBadge = 'Provider Not Configured';
            modeBg = 'bg-amber-500/10 text-amber-800 border-amber-500/20';
          } else if (mode === 'workspace_derived' || mode === 'workspace-derived') {
            modeBadge = 'Workspace-derived';
            modeBg = 'bg-softform-navy-900/10 text-softform-text-secondary border-softform-navy-900/20';
          } else if (mode === 'fixture' || mode === 'fixture-backed') {
            modeBadge = 'Context-only';
            modeBg = 'bg-amber-500/10 text-amber-800 border-amber-500/20';
          } else if (mode === 'local-fallback') {
            modeBadge = 'Source pending';
            modeBg = 'bg-amber-500/20 text-amber-900 border-amber-500/30';
          } else if (mode === 'unavailable') {
            modeBadge = 'Unavailable';
            modeBg = 'bg-red-500/10 text-red-700 border-red-500/20';
          }
          return (
            <span className={clsx("rounded-full border px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.14em]", modeBg)}>
              {modeBadge}
            </span>
          );
        })()}
        <SourceInfoTooltip
          title="Cross-border funding provenance"
          sources={buildSourceItems(context.provenance)}
        />
      </div>

      {/* Summary row */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <h3 className="text-xl font-semibold tracking-[-0.03em] text-softform-navy-950">
            {context.baseCurrency}/{context.comparisonCurrency} Funding Context
          </h3>
          <p className="mt-2 text-sm leading-6 text-softform-text-primary">
            {context.explanation}
          </p>
        </div>

        {/* Review signal card */}
        <div className="rounded-2xl border border-softform-navy-950/10 bg-softform-navy-950/[0.025] p-4 text-sm md:w-56">
          <div className="flex items-start gap-2">
            <TrendingUp size={16} className="mt-0.5 shrink-0 text-softform-teal-deep" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
                Review signal
              </p>
              <span
                className={clsx(
                  'mt-1 inline-block rounded-full border px-2.5 py-0.5 text-[10px] font-semibold capitalize',
                  reviewBandStyles[context.crossBorderReviewBand] ??
                    'border-softform-navy-950/10 text-softform-text-muted',
                )}
              >
                {context.crossBorderReviewBand.replace(/_/g, ' ')}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Rate comparison */}
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-softform-navy-950/10 bg-white/70 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_14px_40px_rgba(15,23,42,0.08)]">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
            HKD funding reference
          </p>
          <p className="mt-1 tabular-finance text-2xl font-bold tracking-tight text-softform-navy-950">
            {context.hkdFundingReference.displayValue}
          </p>
          <p className="mt-0.5 text-[11px] font-medium text-softform-text-secondary">
            {context.hkdFundingReference.label}
          </p>
          <p className="mt-1 text-[10px] leading-relaxed text-softform-text-muted">
            {context.hkdFundingReference.source}
          </p>
        </div>
        <div className="rounded-2xl border border-softform-navy-950/10 bg-white/70 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_14px_40px_rgba(15,23,42,0.08)]">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
            RMB funding reference
          </p>
          <p className="mt-1 tabular-finance text-2xl font-bold tracking-tight text-softform-navy-950">
            {context.rmbFundingReference.displayValue}
          </p>
          <p className="mt-0.5 text-[11px] font-medium text-softform-text-secondary">
            {context.rmbFundingReference.label}
          </p>
          <p className="mt-1 text-[10px] leading-relaxed text-softform-text-muted">
            {context.rmbFundingReference.source}
          </p>
        </div>
      </div>

      {/* Spread + bands */}
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        <div className="rounded-xl border border-softform-navy-950/10 bg-softform-mist-50/50 px-3 py-2">
          <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
            Rate spread
          </p>
          <p className="mt-0.5 tabular-finance text-sm font-bold text-softform-navy-950">
            {context.spreadBps !== null && context.spreadBps !== undefined
              ? `${context.spreadBps > 0 ? '+' : ''}${context.spreadBps} bps`
              : 'N/A'}
          </p>
          <p className="mt-0.5 text-[10px] leading-relaxed text-softform-text-secondary">
            {spreadBandLabels[context.spreadBand] ?? context.spreadBand}
          </p>
        </div>
        <div className="rounded-xl border border-softform-navy-950/10 bg-softform-mist-50/50 px-3 py-2">
          <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
            FX risk context
          </p>
          <p className="mt-0.5 text-sm font-bold text-softform-navy-950">
            {fxRiskLabels[context.fxRiskBand] ?? context.fxRiskBand}
          </p>
          <p className="mt-0.5 text-[10px] leading-relaxed text-softform-text-secondary">
            From import/payable exposure
          </p>
        </div>
        <div className="rounded-xl border border-softform-navy-950/10 bg-softform-mist-50/50 px-3 py-2">
          <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
            Review signal
          </p>
          <p className="mt-0.5 text-sm font-bold capitalize text-softform-navy-950">
            {context.crossBorderReviewBand.replace(/_/g, ' ')}
          </p>
          <p className="mt-0.5 text-[10px] leading-relaxed text-softform-text-secondary">
            Combined rate & FX context
          </p>
        </div>
      </div>

      {/* Context components */}
      {context.components.length > 0 && (
        <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {context.components.map((comp, idx) => (
            <div
              key={idx}
              className="rounded-xl border border-softform-navy-950/10 bg-softform-mist-50/50 px-3 py-2"
            >
              <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
                {comp.label}
              </p>
              {comp.value && (
                <p className="mt-0.5 text-[11px] font-medium capitalize text-softform-navy-950">
                  {comp.value}
                </p>
              )}
              <p className="mt-0.5 text-[10px] leading-relaxed text-softform-text-secondary">
                {comp.explanation}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Warning banner */}
      {context.warnings.length > 0 && (
        <div className="mt-4 rounded-2xl border border-softform-amber-200/80 bg-softform-amber-50/60 px-4 py-3 text-xs leading-5 text-softform-amber-900">
          {context.warnings.map((w, i) => (
            <p key={i} className={i > 0 ? 'mt-1' : ''}>
              <span className="font-semibold">•</span> {w}
            </p>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-4 rounded-2xl border border-softform-navy-950/10 bg-softform-navy-950/[0.025] px-4 py-3 text-xs leading-5 text-softform-text-secondary">
        <div className="flex items-start gap-2">
          <Info size={14} className="mt-0.5 shrink-0 text-softform-text-muted" />
          <p>{context.disclaimer}</p>
        </div>
      </div>
    </div>
  )
}
