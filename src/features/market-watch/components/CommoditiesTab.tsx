import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { CommodityExposure, CommoditySourceInfo } from '../types'
import clsx from 'clsx'

type CommoditiesTabProps = {
  commodities: CommodityExposure[]
  commoditySource: CommoditySourceInfo | null
}

export default function CommoditiesTab({
  commodities,
  commoditySource,
}: CommoditiesTabProps) {
  if (!commoditySource) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm font-medium text-softform-text-muted">
          Loading commodities intelligence...
        </div>
      </div>
    )
  }

  const seedFallback =
    commoditySource.isFallback ||
    commoditySource.warnings.some(
      (w) =>
        w.includes('Backend unavailable') ||
        w.includes('seed data') ||
        w.includes('fixture-backed'),
    )

  return (
    <div className="space-y-6">
      {/* Source & freshness banner */}
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
          <span className="font-semibold">{commoditySource.label}</span>
        </span>
        {commoditySource.asOf && (
          <span className="flex items-center gap-1.5">
            <span className="opacity-60">As of:</span>
            <span className="font-semibold">{commoditySource.asOf}</span>
          </span>
        )}
        <span className="text-xs opacity-50">{commoditySource.freshness}</span>
      </div>

      {/* Warnings Banner */}
      {commoditySource.warnings && commoditySource.warnings.length > 0 && (
        <div
          className={clsx(
            'rounded-2xl border px-5 py-3 text-xs leading-relaxed',
            seedFallback
              ? 'border-softform-amber-200/60 bg-softform-amber-200/10 text-softform-amber-800'
              : 'border-blue-200/60 bg-blue-50/60 text-softform-text-secondary',
          )}
        >
          {commoditySource.warnings.map((w, idx) => (
            <p key={idx} className={idx > 0 ? 'mt-1 opacity-70' : ''}>
              {w}
            </p>
          ))}
        </div>
      )}

      {/* Main panel */}
      <div className="softform-panel rounded-[28px] p-6 sm:p-8">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-bold text-softform-navy-950">
              Commodity & Input Cost Pressure
            </h2>
            <p className="mt-1 text-sm text-softform-text-secondary">
              {commoditySource.selectedSector.description}
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <div className="inline-flex flex-col items-end gap-1">
              <div className="inline-flex items-center rounded-full bg-softform-navy-900/5 px-4 py-2 text-sm font-semibold text-softform-navy-950">
                Viewing: {commoditySource.selectedSector.name} ({commoditySource.selectedSector.geography})
              </div>
              {commoditySource.selectedSector.code && (
                <span className="text-[10px] text-softform-text-muted font-mono uppercase tracking-wider pr-2">
                  Code: {commoditySource.selectedSector.code}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {commodities.map((item, idx) => (
            <div
              key={idx}
              className="softform-card flex flex-col justify-between rounded-2xl p-5"
            >
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-softform-navy-900">
                    {item.commodity}
                  </h3>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {item.affectedSectors.map((sector) => (
                      <span
                        key={sector}
                        className="rounded-full bg-softform-navy-900/5 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-softform-text-secondary"
                      >
                        {sector}
                      </span>
                    ))}
                  </div>
                </div>
                <div
                  className={clsx(
                    'flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
                    item.priceTrend === 'up' && 'bg-red-500/10 text-red-700',
                    item.priceTrend === 'down' &&
                      'bg-softform-emerald-soft/10 text-emerald-700',
                    item.priceTrend === 'flat' &&
                      'bg-softform-text-muted/10 text-softform-text-secondary',
                  )}
                >
                  {item.priceTrend === 'up' && <ArrowUpRight size={14} />}
                  {item.priceTrend === 'down' && <ArrowDownRight size={14} />}
                  {item.priceTrend === 'flat' && <ArrowRight size={14} />}
                  <span>{item.displayValue || (item.yoyChange ? `${item.yoyChange} YoY` : '')}</span>
                </div>
              </div>

              <div className="rounded-xl border border-softform-text-muted/10 bg-white/40 p-3 text-sm text-softform-navy-900">
                <span className="block text-xs font-semibold text-softform-text-muted mb-1">
                  Margin Sensitivity:
                </span>
                {item.marginSensitivity}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grouped Signals & Status */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Signals */}
        <div className="softform-panel rounded-[28px] p-6 sm:p-8 lg:col-span-2 space-y-6">
          {/* Margin Pressure Signals */}
          {commoditySource.marginPressureSignal && commoditySource.marginPressureSignal.length > 0 && (
            <div>
              <h3 className="mb-4 text-base font-bold text-softform-navy-950">
                Margin Pressure Signals
              </h3>
              <div className="space-y-4">
                {commoditySource.marginPressureSignal.map((signal) => (
                  <div
                    key={signal.id}
                    className={clsx(
                      'rounded-xl border p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4',
                      signal.severity === 'Positive'
                        ? 'border-softform-teal-500/10 bg-softform-teal-500/5'
                        : signal.severity === 'Caution'
                        ? 'border-softform-amber-500/10 bg-softform-amber-500/5'
                        : 'border-white/50 bg-white/40',
                    )}
                  >
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <h4 className="text-sm font-bold text-softform-navy-900">
                          {signal.label}
                        </h4>
                        <span
                          className={clsx(
                            'rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
                            signal.severity === 'Positive'
                              ? 'bg-softform-emerald-soft/10 text-emerald-700'
                              : signal.severity === 'Caution'
                              ? 'bg-softform-amber-200/20 text-softform-amber-700'
                              : 'bg-softform-navy-900/5 text-softform-text-secondary',
                          )}
                        >
                          {signal.severity}
                        </span>
                        {signal.requiresCompanyData && (
                          <span className="rounded-full bg-purple-100 text-purple-700 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                            Requires Company Data
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-softform-text-secondary leading-relaxed">
                        {signal.description}
                      </p>
                    </div>
                    <div className="shrink-0 text-[10px] font-semibold text-softform-text-muted bg-softform-navy-900/5 rounded-md px-2 py-1">
                      Area: {signal.affectedArea}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Watch Signals */}
          {commoditySource.watchSignals && commoditySource.watchSignals.length > 0 && (
            <div>
              <h3 className="mb-4 text-base font-bold text-softform-navy-950">
                Commodity Watch Signals
              </h3>
              <div className="space-y-4">
                {commoditySource.watchSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className={clsx(
                      'rounded-xl border p-4 shadow-sm flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4',
                      signal.severity === 'Positive'
                        ? 'border-softform-teal-500/10 bg-softform-teal-500/5'
                        : signal.severity === 'Caution'
                        ? 'border-softform-amber-500/10 bg-softform-amber-500/5'
                        : 'border-white/50 bg-white/40',
                    )}
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-bold text-softform-navy-900">
                          {signal.title}
                        </h4>
                        <span
                          className={clsx(
                            'rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
                            signal.severity === 'Positive'
                              ? 'bg-softform-emerald-soft/10 text-emerald-700'
                              : signal.severity === 'Caution'
                              ? 'bg-softform-amber-200/20 text-softform-amber-700'
                              : 'bg-softform-navy-900/5 text-softform-text-secondary',
                          )}
                        >
                          {signal.severity}
                        </span>
                      </div>
                      <p className="text-xs text-softform-text-secondary leading-relaxed">
                        {signal.description}
                      </p>
                    </div>
                    <div className="shrink-0 text-[10px] font-semibold text-softform-text-muted bg-softform-navy-900/5 rounded-md px-2 py-1">
                      Area: {signal.affectedArea}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Integration Status */}
        <div className="softform-navy-card rounded-[28px] p-6 sm:p-8 text-white flex flex-col justify-between">
          <div>
            <h3 className="mb-4 text-base font-bold">Integration Status</h3>
            <p className="mb-6 text-xs leading-relaxed text-white/80">
              Connection health for commodity and cost-pressure data sources.
            </p>
            <div className="space-y-3">
              {commoditySource.sourceStatus.map((src) => (
                <div
                  key={src.id}
                  className="flex items-center justify-between rounded-lg bg-white/5 p-2 text-xs border border-white/5"
                >
                  <span className="font-medium text-white/90">{src.label}</span>
                  <span
                    className={clsx(
                      'rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider',
                      src.status.toLowerCase() === 'connected' &&
                        'bg-softform-emerald-soft/20 text-softform-emerald-soft',
                      (src.status.toLowerCase() === 'seed_data' ||
                        src.status.toLowerCase() === 'seed data') &&
                        'bg-blue-500/20 text-blue-300',
                      src.status.toLowerCase() === 'requires_backend' &&
                        'bg-softform-amber-500/20 text-softform-amber-300',
                      (src.status.toLowerCase() === 'requires_company_data' ||
                        src.status.toLowerCase() === 'requires company data') &&
                        'bg-purple-500/20 text-purple-300',
                    )}
                  >
                    {src.status.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-6 text-[10px] text-white/40 italic">
            *Sector-level commodity inputs and freight indexes represent context only. Company-specific margin impact requires company records.
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-softform-teal-500/10 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-softform-teal-deep mb-1">
          CFO Takeaway
        </h4>
        <p className="text-xs text-softform-text-secondary leading-relaxed">
          Use this context alongside treasury policy and advisor review before
          making cross-border funding decisions. Connect company financials to
          quantify impact.
        </p>
      </div>
    </div>
  )
}
