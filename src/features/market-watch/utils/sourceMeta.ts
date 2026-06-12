/**
 * Source Metadata Helpers (frontend-side).
 *
 * Mirrors the backend source registry so that frontend cards can
 * consistently determine source mode labels, caveats, and disclaimers
 * without hard-coding strings in each card.
 *
 * Modes recognised:
 * - live                    → green "Live public feed"
 * - provider_configured     → green "Provider configured"
 * - provider_not_configured → red "Provider not configured"
 * - workspace_derived       → muted "Workspace-derived estimate"
 * - fixture                 → amber "Fixture fallback"
 * - unavailable             → red "Unavailable"
 */

export type SourceMode =
  | 'live'
  | 'provider_configured'
  | 'provider_not_configured'
  | 'workspace_derived'
  | 'fixture'
  | 'unavailable'
  | 'provider-backed'
  | 'workspace-derived'
  | 'fixture-backed'
  | 'local-fallback'

/** Matches the backend SourceRegistryEntry shape. */
export interface SourceMeta {
  sourceKey: string
  label: string
  mode: SourceMode
  freshness: string
  caveat?: string | null
  provider?: string | null
}

// ── Registry ──────────────────────────────────────────────────────

const _REGISTRY: Record<string, SourceMeta> = {}

function _register(entry: SourceMeta): void {
  _REGISTRY[entry.sourceKey] = entry
}

/** Look up a source entry by key. Returns undefined if not found. */
export function getSourceMeta(sourceKey: string): SourceMeta | undefined {
  return _REGISTRY[sourceKey]
}

/** Resolve the user-facing mode label for tooltip rendering. */
export function resolveSourceModeLabel(sourceKey: string): SourceMeta['mode'] {
  const entry = _REGISTRY[sourceKey]
  if (!entry) return 'workspace_derived'
  return entry.mode
}

// ═══════════════════════════════════════════════════════════════════
//  Registered entries (mirrors backend source_registry.py)
// ═══════════════════════════════════════════════════════════════════

// Phase 2: context-only signals
_register({
  sourceKey: 'timing_signal_v1',
  label: 'Golden Timing Index v1',
  mode: 'workspace_derived',
  freshness: 'Daily',
  caveat: 'Timing signal is derived from HKAB/HKMA rate data and fixture-based calendar rules. CME FedWatch integration pending.',
  provider: 'FinSight CFO Market Watch',
})

_register({
  sourceKey: 'industry_health_v1',
  label: 'Industry Health Context v1',
  mode: 'fixture',
  freshness: 'Monthly',
  caveat: 'Industry health uses fixture/workspace-derived sector benchmarks. ChinaData.live/IHS integration pending.',
  provider: 'FinSight CFO Market Watch',
})

_register({
  sourceKey: 'funding_channel_ranking_v1',
  label: 'Funding Channel Ranking v1',
  mode: 'workspace_derived',
  freshness: 'Workspace',
  caveat: 'Funding channel ranking uses workspace-derived company context and fixture industry data. No real lender product catalog scraping.',
  provider: 'FinSight CFO Market Watch',
})

_register({
  sourceKey: 'cross_border_funding_context_v1',
  label: 'Cross-border Funding Context v1',
  mode: 'fixture',
  freshness: 'Workspace',
  caveat: 'Cross-border funding context is fixture/workspace-derived. LPR reference is a fixture placeholder; LPR provider integration pending.',
  provider: 'FinSight CFO Market Watch',
})

_register({
  sourceKey: 'red_flags_macro_summary_v1',
  label: 'Red Flags & Macro Risk Summary v1',
  mode: 'workspace_derived',
  freshness: 'Workspace',
  caveat: 'Red Flags summary consolidates workspace-derived Phase 2 signals. CME FedWatch and ChinaData.live/IHS provider integrations pending.',
  provider: 'FinSight CFO Market Watch',
})

// Provider-backed sources
_register({
  sourceKey: 'rates_liquidity_v1',
  label: 'HKMA Rates & Liquidity',
  mode: 'live',
  freshness: 'Daily',
  provider: 'HKAB / HKMA',
})

_register({
  sourceKey: 'fx_gba_v1',
  label: 'FX & GBA (Frankfurter)',
  mode: 'live',
  freshness: 'Daily',
  provider: 'Frankfurter',
})

_register({
  sourceKey: 'commodities_v1',
  label: 'Commodities',
  mode: 'fixture',
  freshness: 'Monthly',
  caveat: 'Commodity provider is not configured or unavailable. Showing workspace seed data.',
  provider: 'Fixture / Alpha Vantage (pending)',
})

_register({
  sourceKey: 'sector_benchmarks_v1',
  label: 'Sector Benchmarks',
  mode: 'fixture',
  freshness: 'Monthly',
  caveat: 'Sector benchmarks are fixture/workspace-derived. C&SD / data.gov.hk integration pending.',
  provider: 'Fixture',
})

/**
 * Build a SourceItem[] (for SourceInfoTooltip) from a provenance object
 * returned by any Market Watch API endpoint.
 *
 * The provenance object should have shape:
 *   { source, provider, asOf?, freshness? }
 */
export function buildSourceItems(
  provenance: { source?: string; provider?: string; asOf?: string | null; freshness?: string },
  additionalLabel?: string,
): Array<{ label: string; mode: SourceMeta['mode']; asOf?: string | null; freshness?: string; warnings?: string[] }> {
  const items: Array<{
    label: string
    mode: SourceMeta['mode']
    asOf?: string | null
    freshness?: string
    warnings?: string[]
  }> = []

  if (!provenance) {
    items.push({ label: 'Unknown source', mode: 'workspace_derived' })
    return items
  }

  const sourceKey = provenance.source ?? ''
  const meta = getSourceMeta(sourceKey)
  const mode = meta?.mode ?? 'workspace_derived'

  // Provider line
  items.push({
    label: provenance.provider ?? meta?.provider ?? 'FinSight CFO Market Watch',
    mode,
    freshness: provenance.freshness ?? meta?.freshness,
  })

  // As-of line
  if (provenance.asOf) {
    items.push({
      label: `As of ${provenance.asOf}`,
      mode: 'workspace_derived',
      freshness: provenance.freshness ?? meta?.freshness,
    })
  } else {
    items.push({
      label: 'As-of date unavailable',
      mode: 'workspace_derived',
      freshness: provenance.freshness ?? meta?.freshness,
    })
  }

  // Caveat as warning if present
  if (meta?.caveat) {
    items.push({
      label: additionalLabel ?? meta.label,
      mode,
      warnings: [meta.caveat],
    })
  }

  return items
}
