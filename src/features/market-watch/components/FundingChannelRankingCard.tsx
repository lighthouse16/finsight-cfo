import { Info, TrendingUp, ArrowRight } from 'lucide-react'
import clsx from 'clsx'
import { FundingChannelRankingResponse } from '../types'
import SourceInfoTooltip from './SourceInfoTooltip'

type FundingChannelRankingCardProps = {
  ranking: FundingChannelRankingResponse | null
}

const fitBandStyles: Record<string, string> = {
  strong_fit: 'border-emerald-200/80 bg-emerald-50/80 text-emerald-800',
  moderate_fit: 'border-blue-200/80 bg-blue-50/80 text-blue-800',
  watch_fit: 'border-softform-amber-200/80 bg-softform-amber-50/80 text-softform-amber-800',
}

const rankingBandLabels: Record<string, { label: string; description: string }> = {
  working_capital_priority: {
    label: 'Working Capital Priority',
    description: 'Short-term liquidity and working-capital channels rank highest.',
  },
  trade_cycle_priority: {
    label: 'Trade Cycle Priority',
    description: 'Receivables and trade-related channels are most relevant.',
  },
  balance_sheet_review: {
    label: 'Balance Sheet Review',
    description: 'Term structures may be considered after balance-sheet review.',
  },
  risk_context_priority: {
    label: 'Risk Context Priority',
    description: 'Risk management or hedging instruments are contextually relevant.',
  },
}

function formatRankingBand(band: string): string {
  return band.replace(/_/g, ' ')
}

export default function FundingChannelRankingCard({ ranking }: FundingChannelRankingCardProps) {
  if (!ranking) return null

  const rankingInfo = rankingBandLabels[ranking.rankingBand] ?? {
    label: formatRankingBand(ranking.rankingBand),
    description: '',
  }
  const topChannel = ranking.channels.find(c => c.key === ranking.topChannelKey)

  return (
    <div className="softform-panel overflow-hidden rounded-[28px] border border-softform-navy-950/10 bg-white/85 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.08)] sm:p-8">
      {/* Header row */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-softform-navy-950/10 bg-softform-navy-950/[0.03] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-softform-navy-700">
          Funding Channel Ranking v1
        </span>
        <span className="rounded-full border border-softform-navy-950/10 bg-white px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.14em] text-softform-text-muted">
          Context-only
        </span>
        <SourceInfoTooltip
          title="Funding channel provenance"
          sources={[
            {
              label: ranking.provenance.provider,
              mode: 'workspace-derived',
              freshness: ranking.provenance.freshness,
            },
            {
              label: ranking.provenance.asOf ? `As of ${ranking.provenance.asOf}` : 'As-of date unavailable',
              mode: 'workspace-derived',
              freshness: ranking.provenance.freshness,
            },
            {
              label: ranking.source.provider,
              mode: 'fixture-backed',
              freshness: ranking.source.freshness,
            },
          ]}
        />
      </div>

      {/* Ranking band + top channel summary */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <h3 className="text-xl font-semibold tracking-[-0.03em] text-softform-navy-950">
            {rankingInfo.label}
          </h3>
          {rankingInfo.description && (
            <p className="mt-1 text-sm leading-6 text-softform-text-primary">
              {rankingInfo.description}
            </p>
          )}
          <p className="mt-2 text-sm leading-6 text-softform-text-primary">
            {ranking.explanation}
          </p>
        </div>

        {topChannel && (
          <div className="rounded-2xl border border-softform-navy-950/10 bg-softform-navy-950/[0.025] p-4 text-sm md:w-64">
            <div className="flex items-start gap-2">
              <TrendingUp size={16} className="mt-0.5 shrink-0 text-softform-teal-deep" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
                  Top candidate
                </p>
                <p className="mt-0.5 font-semibold text-softform-navy-950">
                  {topChannel.label}
                </p>
                <span className={clsx('mt-1 inline-block rounded-full border px-2 py-0.5 text-[10px] font-semibold capitalize', fitBandStyles[topChannel.fitBand])}>
                  {formatRankingBand(topChannel.fitBand)}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Channel list */}
      {ranking.channels.length > 0 && (
        <div className="mt-6 space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
            Candidate channels
          </h4>
          {ranking.channels.map((ch) => (
            <div
              key={ch.key}
              className="rounded-2xl border border-softform-navy-950/10 bg-white/70 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_14px_40px_rgba(15,23,42,0.08)]"
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-softform-navy-950/10 text-[10px] font-bold text-softform-navy-700 shrink-0">
                      {ch.rank}
                    </span>
                    <span className="text-sm font-semibold text-softform-navy-950">
                      {ch.label}
                    </span>
                    <span className={clsx('rounded-full border px-2 py-0.5 text-[10px] font-semibold capitalize', fitBandStyles[ch.fitBand])}>
                      {formatRankingBand(ch.fitBand)}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-softform-text-primary">
                    <span className="font-medium text-softform-navy-950">Use case:</span>{' '}
                    {ch.useCase}
                  </p>
                  <p className="mt-1 text-xs leading-5 text-softform-text-primary">
                    {ch.rationale}
                  </p>
                  {ch.supportingSignals.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {ch.supportingSignals.map((sig, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 rounded-full border border-softform-navy-950/10 bg-softform-mist-50/60 px-2 py-0.5 text-[9px] font-medium text-softform-text-secondary"
                        >
                          <ArrowRight size={8} className="text-softform-teal-deep" />
                          {sig}
                        </span>
                      ))}
                    </div>
                  )}
                  {ch.constraints.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {ch.constraints.map((c, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 rounded-full border border-softform-amber-200/60 bg-softform-amber-50/50 px-2 py-0.5 text-[9px] font-medium text-softform-amber-800"
                        >
                          <Info size={8} />
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Context components */}
      {ranking.components.length > 0 && (
        <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {ranking.components.map((comp, idx) => (
            <div key={idx} className="rounded-xl border border-softform-navy-950/10 bg-softform-mist-50/50 px-3 py-2">
              <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
                {comp.label}
              </p>
              <p className="mt-0.5 text-[11px] font-medium capitalize text-softform-navy-950">
                {formatRankingBand(comp.band)}
              </p>
              <p className="mt-0.5 text-[10px] leading-relaxed text-softform-text-secondary">
                {comp.explanation}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Warning banner */}
      {ranking.warnings.length > 0 && (
        <div className="mt-4 rounded-2xl border border-softform-amber-200/80 bg-softform-amber-50/60 px-4 py-3 text-xs leading-5 text-softform-amber-900">
          {ranking.warnings.map((w, i) => (
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
          <p>{ranking.disclaimer}</p>
        </div>
      </div>
    </div>
  )
}
