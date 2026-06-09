"""Source Registry for Market Watch.

Defines normalized source metadata for all Market Watch data sources,
providing a single source of truth for provenance, freshness, mode,
and caveats. Services should use ``build_provenance()`` instead of
inline source metadata construction.

Modes
-----
- **provider-backed**: Connected to a real external provider API/feed
- **workspace-derived**: Derived from workspace/company context data
- **fixture-backed**: Uses seed/fixture data (no real provider yet)
- **fallback**: Uses degraded/fallback data (e.g., stale cache, derived)
- **missing/unavailable**: Source is not available
"""

from datetime import datetime
from typing import Any, Optional, TypedDict

# ── Type aliases ────────────────────────────────────────────────────

SourceMode = str
"""One of: provider-backed, workspace-derived, fixture-backed, fallback, missing/unavailable"""

SourceConfidence = str
"""One of: high, medium, low, unavailable"""


# ── Registry entry type ─────────────────────────────────────────────

class SourceRegistryEntry(TypedDict, total=False):
    sourceKey: str
    label: str
    mode: SourceMode
    freshness: str
    asOf: Optional[str]
    caveat: Optional[str]
    provider: Optional[str]
    confidence: SourceConfidence


# ── In-memory registry ──────────────────────────────────────────────

_REGISTRY: dict[str, SourceRegistryEntry] = {}


def _register(entry: SourceRegistryEntry) -> None:
    _REGISTRY[entry["sourceKey"]] = entry


def get_source(source_key: str) -> Optional[SourceRegistryEntry]:
    """Look up a source entry by key. Returns None if not found."""
    return _REGISTRY.get(source_key)


def build_provenance(
    source_key: str,
    as_of: Optional[str] = None,
    provider_override: Optional[str] = None,
    freshness_override: Optional[str] = None,
) -> dict[str, Optional[str]]:
    """Build a standard provenance dict matching response-model shapes.

    Returns keys: ``source``, ``provider``, ``asOf``, ``freshness``,
    ``providerAdapter``, ``providerIntegration``.
    All values are ``str | None`` so the caller can unpack with ``**``
    into any provenance model.

    ``providerAdapter`` is the recommended adapter class name from
    :func:`get_adapter`.  ``providerIntegration`` is the recommended
    provider name from :func:`get_adapter_provider_name`.

    Override parameters let callers pass dynamic values from upstream
    responses while falling back to registry defaults.
    """
    entry = _REGISTRY.get(source_key)
    if entry is None:
        return {
            "source": source_key,
            "provider": provider_override or "Unknown",
            "asOf": as_of,
            "freshness": freshness_override or "Workspace",
            "providerAdapter": "MissingProviderAdapter",
            "providerIntegration": "Provider integration pending",
        }
    return {
        "source": entry["sourceKey"],
        "provider": provider_override or entry.get("provider") or "FinSight CFO Market Watch",
        "asOf": as_of or entry.get("asOf"),
        "freshness": freshness_override or entry["freshness"],
        "providerAdapter": get_adapter(source_key),
        "providerIntegration": get_adapter_provider_name(source_key),
    }


# ═══════════════════════════════════════════════════════════════════
#  Registered sources
# ═══════════════════════════════════════════════════════════════════

# ── Phase 2: context-only signals ──────────────────────────────────

_register(SourceRegistryEntry(
    sourceKey="timing_signal_v1",
    label="Golden Timing Index v1",
    mode="workspace-derived",
    freshness="Daily",
    caveat=(
        "Timing signal is derived from HKAB/HKMA rate data and "
        "fixture-based calendar rules. CME FedWatch integration pending."
    ),
    provider="FinSight CFO Market Watch",
    confidence="medium",
))

_register(SourceRegistryEntry(
    sourceKey="industry_health_v1",
    label="Industry Health Context v1",
    mode="fixture-backed",
    freshness="Monthly",
    caveat=(
        "Industry health uses fixture/workspace-derived sector benchmarks. "
        "ChinaData.live/IHS integration pending."
    ),
    provider="FinSight CFO Market Watch",
    confidence="low",
))

_register(SourceRegistryEntry(
    sourceKey="funding_channel_ranking_v1",
    label="Funding Channel Ranking v1",
    mode="workspace-derived",
    freshness="Workspace",
    caveat=(
        "Funding channel ranking uses workspace-derived company context "
        "and fixture industry data. No real lender product catalog scraping."
    ),
    provider="FinSight CFO Market Watch",
    confidence="low",
))

_register(SourceRegistryEntry(
    sourceKey="cross_border_funding_context_v1",
    label="Cross-border Funding Context v1",
    mode="fixture-backed",
    freshness="Workspace",
    caveat=(
        "Cross-border funding context is fixture/workspace-derived. "
        "LPR reference is a fixture placeholder; LPR provider integration pending."
    ),
    provider="FinSight CFO Market Watch",
    confidence="low",
))

_register(SourceRegistryEntry(
    sourceKey="red_flags_macro_summary_v1",
    label="Red Flags & Macro Risk Summary v1",
    mode="workspace-derived",
    freshness="Workspace",
    caveat=(
        "Red Flags summary consolidates workspace-derived Phase 2 signals. "
        "CME FedWatch and ChinaData.live/IHS provider integrations pending."
    ),
    provider="FinSight CFO Market Watch",
    confidence="low",
))

# ── Provider-backed sources ─────────────────────────────────────────

_register(SourceRegistryEntry(
    sourceKey="rates_liquidity_v1",
    label="HKMA Rates & Liquidity",
    mode="provider-backed",
    freshness="Daily",
    caveat=None,
    provider="HKAB / HKMA",
    confidence="high",
))

_register(SourceRegistryEntry(
    sourceKey="fx_gba_v1",
    label="FX & GBA (Frankfurter)",
    mode="provider-backed",
    freshness="Daily",
    caveat=None,
    provider="Frankfurter",
    confidence="high",
))

_register(SourceRegistryEntry(
    sourceKey="commodities_v1",
    label="Commodities",
    mode="fixture-backed",
    freshness="Monthly",
    caveat=(
        "Commodity provider is not configured or unavailable. "
        "Showing workspace seed data."
    ),
    provider="Fixture / Alpha Vantage (pending)",
    confidence="low",
))

_register(SourceRegistryEntry(
    sourceKey="sector_benchmarks_v1",
    label="Sector Benchmarks",
    mode="fixture-backed",
    freshness="Monthly",
    caveat=(
        "Sector benchmarks are fixture/workspace-derived. "
        "C&SD / data.gov.hk integration pending."
    ),
    provider="Fixture",
    confidence="low",
))


# ── Convenience helpers ─────────────────────────────────────────────


def get_mode_label(source_key: str) -> str:
    """Map a source key to a user-facing mode label for tooltips.

    Returns one of: ``provider-backed``, ``workspace-derived``,
    ``fixture-backed``, ``fallback``.
    """
    entry = _REGISTRY.get(source_key)
    if entry is None:
        return "workspace-derived"
    mode = entry["mode"]
    if mode == "provider-backed":
        return "provider-backed"
    if mode == "fixture-backed":
        return "fixture-backed"
    return "workspace-derived"


def get_caveat(source_key: str) -> Optional[str]:
    """Return the caveat text for a source key, or None."""
    entry = _REGISTRY.get(source_key)
    if entry is None:
        return None
    return entry.get("caveat")


def get_disclaimer_base(source_key: str) -> str:
    """Build a short context-only disclaimer prefix for the source."""
    entry = _REGISTRY.get(source_key)
    if entry is None:
        return "Context only. Not a financing instruction."
    label = entry["label"]
    mode = entry["mode"]
    if mode == "provider-backed":
        return f"{label} is provider-backed. Not a financing instruction."
    if mode == "fixture-backed":
        return (
            f"{label} is fixture/workspace-derived. "
            "Production provider integration pending."
        )
    return (
        f"{label} is context-only for planning support. "
        "Not a financing instruction."
    )


def get_adapter(source_key: str) -> str:
    """Return the recommended provider adapter class name for a source key.

    Returns one of:
    - ``FixtureMarketDataAdapter`` — fixture-backed sources
    - ``WorkspaceDerivedAdapter`` — workspace-derived sources
    - ``MissingProviderAdapter`` — unavailable sources
    - ``provider-backed`` — sources with a live provider connection

    This lets services self-describe their provider integration status
    without importing adapter classes directly.
    """
    entry = _REGISTRY.get(source_key)
    if entry is None:
        return "MissingProviderAdapter"
    mode = entry["mode"]
    if mode == "provider-backed":
        return "provider-backed"
    if mode == "fixture-backed":
        return "FixtureMarketDataAdapter"
    return "WorkspaceDerivedAdapter"


def get_adapter_provider_name(source_key: str) -> str:
    """Return the recommended provider name for a source key.

    Returns the provider field from the registry, or a fallback string
    describing the integration mode.
    """
    entry = _REGISTRY.get(source_key)
    if entry is None:
        return "Provider integration pending"
    provider = entry.get("provider")
    if provider:
        return provider
    return "Provider integration pending"

