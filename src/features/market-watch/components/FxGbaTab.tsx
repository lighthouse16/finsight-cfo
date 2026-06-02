import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { ExposureNote, FxPair, GbaFundingSignal } from '../types'
import { FxSourceInfo } from '../MarketWatchPage'
import clsx from 'clsx'

type FxGbaTabProps = {
  fxPairs: FxPair[]
  gbaSignals: GbaFundingSignal[]
  exposureNotes?: ExposureNote[]
  fxSource?: FxSourceInfo | null
}

export default function FxGbaTab({
  fxPairs,
  gbaSignals,
  exposureNotes = [],
  fxSource,
}: FxGbaTabProps) {
  const seedFallback = fxSource?.warnings.some(
    (w) =>
      w.includes('Backend unavailable') ||
      w.includes('seed data') ||
      w.includes('fixture-backed'),
  )

  return (
    <div className="space-y-8">
      {/* Source & freshness banner */}
      {fxSource && (
        <div
          className={clsx(
            'flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl px-5 py-3 text-xs font-medium',
            seedFallback
              ? 'bg-softform-amber-200/20 text-softform-amber-700'
              : 'bg-blue-50/70 text-softform-text-secondary',
          )}
        >
          <span className="flex items-center gap-1.5">
            <span className="opacity-60">Source:</span>
            <span className="font-semibold">{fxSource.label}</span>
          </span>
          {fxSource.asOf && (
            <span className="flex items-center gap-1.5">
              <span className="opacity-60">As of:</span>
              <span className="font-semibold">{fxSource.asOf}</span>
            </span>
          )}
          <span className="text-xs opacity-50">Workspace</span>
        </div>
      )}

      {/* Warnings / Seed Fallback message */}
      {fxSource?.warnings && fxSource.warnings.length > 0 && (
        <div
          className={clsx(
            'rounded-2xl border px-5 py-3 text-xs leading-relaxed',
            seedFallback
              ? 'border-softform-amber-200/60 bg-softform-amber-200/10 text-softform-amber-800'
              : 'border-blue-200/60 bg-blue-50/60 text-softform-text-secondary',
          )}
        >
          {fxSource.warnings.map((w, idx) => (
            <p key={idx} className={idx > 0 ? 'mt-1 opacity-70' : ''}>
              {w}
            </p>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <div className="softform-panel rounded-[28px] p-6 sm:p-8">
            <h2 className="mb-6 text-xl font-bold text-softform-navy-950">
              Currency Context
            </h2>
            <div className="flex flex-col gap-4">
              {fxPairs.map((pair, idx) => (
                <div
                  key={idx}
                  className="flex flex-col gap-2 rounded-2xl border border-white/60 bg-[linear-gradient(145deg,rgba(255,255,255,0.7),rgba(234,247,244,0.5))] p-4 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-softform-navy-900">
                      {pair.pair}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="tabular-finance font-bold text-softform-navy-950">
                        {pair.rate}
                      </span>
                      <span
                        className={clsx(
                          'flex h-6 w-6 items-center justify-center rounded-full',
                          pair.trend === 'up' && 'bg-red-500/10 text-red-600',
                          pair.trend === 'down' &&
                            'bg-softform-emerald-soft/10 text-softform-emerald-soft',
                          pair.trend === 'flat' &&
                            'bg-softform-text-muted/10 text-softform-text-secondary',
                        )}
                      >
                        {pair.trend === 'up' && <ArrowUpRight size={14} />}
                        {pair.trend === 'down' && <ArrowDownRight size={14} />}
                        {pair.trend === 'flat' && <ArrowRight size={14} />}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs font-medium text-softform-text-muted">
                    {pair.context}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="softform-panel rounded-[28px] p-6 sm:p-8">
            <h3 className="mb-4 text-lg font-bold text-softform-navy-950">
              GBA Watch Signals
            </h3>
            <div className="flex flex-col gap-3">
              {exposureNotes.map((note) => (
                <div
                  key={note.id}
                  className="rounded-xl bg-white/40 border border-white/50 p-4 shadow-sm"
                >
                  <span className="inline-block rounded-full bg-softform-navy-900/5 px-2.5 py-0.5 text-xs font-semibold text-softform-text-secondary mb-2">
                    {note.category}
                  </span>
                  <p className="text-xs text-softform-text-primary leading-relaxed">
                    {note.note}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="softform-card rounded-[28px] p-6 sm:p-8">
            <h2 className="mb-4 text-xl font-bold text-softform-navy-950">
              Cross-Border Funding Context
            </h2>
            <p className="mb-6 text-sm leading-relaxed text-softform-text-primary">
              Monitor the spread between onshore and offshore rates to identify
              opportunities for cross-border treasury pooling or strategic entity
              borrowing.
            </p>

            <div className="space-y-4">
              {gbaSignals.length === 0 ? (
                <div className="rounded-2xl border border-blue-200/60 bg-blue-50/60 p-4 text-sm text-softform-text-secondary">
                  Cross-border funding context will activate after FX provider and
                  LPR source are connected.
                </div>
              ) : (
                gbaSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="rounded-2xl border border-softform-teal-500/10 bg-softform-teal-500/5 p-4"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <h4 className="text-sm font-bold text-softform-teal-deep">
                        {signal.title}
                      </h4>
                      <span
                        className={clsx(
                          'rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
                          signal.severity === 'Positive'
                            ? 'bg-softform-emerald-soft/10 text-emerald-700'
                            : 'bg-softform-amber-200/20 text-softform-amber-700',
                        )}
                      >
                        {signal.severity}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed text-softform-navy-900">
                      {signal.description}
                    </p>
                  </div>
                ))
              )}
            </div>

            <div className="mt-6 rounded-xl bg-softform-navy-900/5 p-4 text-xs font-medium leading-relaxed text-softform-text-muted">
              <strong className="block text-softform-navy-900 mb-1">
                Important Watch Signal:
              </strong>
              This is a contextual indicator. Use this context alongside treasury policy and advisor review before making cross-border funding decisions.
            </div>
          </div>

          <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
            <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
              CFO Takeaway
            </h4>
            <p className="text-xs text-softform-text-secondary leading-relaxed">
              Use this context alongside uploaded financial records before lender
              conversations. Connect company financials to quantify impact.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
