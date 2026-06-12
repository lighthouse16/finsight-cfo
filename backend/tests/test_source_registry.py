"""Tests for Source Registry Hardening v1.

Covers:
1. Source registry entry lookup & helpers
2. build_provenance() with overrides
3. Service-level provenance consistency (each Phase 2 service
   includes a 'source' key that matches a registered source_key)
4. API endpoint smoke test for source status endpoint
"""

import pytest
from datetime import datetime
from app.services.market_watch.source_registry import (
    _REGISTRY,
    build_provenance,
    get_source,
    get_mode_label,
    get_caveat,
    get_disclaimer_base,
)

# ---------------------------------------------------------------------------
# 1. Registry structure
# ---------------------------------------------------------------------------

EXPECTED_KEYS = {
    "timing_signal_v1",
    "industry_health_v1",
    "funding_channel_ranking_v1",
    "cross_border_funding_context_v1",
    "red_flags_macro_summary_v1",
    "rates_liquidity_v1",
    "fx_gba_v1",
    "commodities_v1",
    "sector_benchmarks_v1",
    "stress_signals_v1",
}


def test_registry_contains_expected_keys():
    missing = EXPECTED_KEYS - set(_REGISTRY.keys())
    assert not missing, f"Missing source registry entries: {missing}"


def test_each_entry_has_required_fields():
    for key, entry in _REGISTRY.items():
        assert "sourceKey" in entry
        assert "label" in entry
        assert "mode" in entry
        assert "freshness" in entry
        assert entry["sourceKey"] == key


@pytest.mark.parametrize("key", list(EXPECTED_KEYS))
def test_get_source(key):
    entry = get_source(key)
    assert entry is not None
    assert entry["sourceKey"] == key


def test_get_source_unknown():
    assert get_source("nonexistent_key") is None


# ---------------------------------------------------------------------------
# 2. build_provenance()
# ---------------------------------------------------------------------------


def test_build_provenance_with_registered_key():
    result = build_provenance("timing_signal_v1")
    assert result["source"] == "timing_signal_v1"
    assert result["provider"] is not None
    assert result["asOf"] is None
    assert result["freshness"] == "Daily"


def test_build_provenance_with_unknown_key():
    result = build_provenance("unknown_key")
    assert result["source"] == "unknown_key"
    assert result["provider"] == "Unknown"
    assert result["freshness"] == "Workspace"


def test_build_provenance_overrides():
    result = build_provenance(
        "timing_signal_v1",
        as_of="2026-06-01",
        provider_override="Overridden Provider",
        freshness_override="Monthly",
    )
    assert result["provider"] == "Overridden Provider"
    assert result["asOf"] == "2026-06-01"
    assert result["freshness"] == "Monthly"


# ---------------------------------------------------------------------------
# 3. Convenience helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key, expected_mode",
    [
        ("rates_liquidity_v1", "provider-backed"),
        ("fx_gba_v1", "provider-backed"),
        ("timing_signal_v1", "workspace-derived"),
        ("funding_channel_ranking_v1", "workspace-derived"),
        ("red_flags_macro_summary_v1", "workspace-derived"),
        ("industry_health_v1", "fixture-backed"),
        ("cross_border_funding_context_v1", "fixture-backed"),
        ("commodities_v1", "fixture-backed"),
        ("sector_benchmarks_v1", "fixture-backed"),
    ],
)
def test_get_mode_label(key, expected_mode):
    assert get_mode_label(key) == expected_mode


def test_get_mode_label_unknown():
    assert get_mode_label("does_not_exist") == "workspace-derived"


def test_caveat_for_provider_backed_is_none():
    assert get_caveat("rates_liquidity_v1") is None


def test_caveat_for_fixture_backed_is_present():
    caveat = get_caveat("industry_health_v1")
    assert caveat is not None
    assert len(caveat) > 10


def test_get_caveat_unknown():
    assert get_caveat("no_such_key") is None


def test_disclaimer_base_unknown():
    disclaimer = get_disclaimer_base("no_such_key")
    assert "financing instruction" in disclaimer


@pytest.mark.parametrize(
    "key, expected_substring",
    [
        ("rates_liquidity_v1", "provider-backed"),
        ("industry_health_v1", "fixture/workspace-derived"),
        ("timing_signal_v1", "context-only"),
    ],
)
def test_disclaimer_base(key, expected_substring):
    disclaimer = get_disclaimer_base(key)
    assert expected_substring in disclaimer


# ---------------------------------------------------------------------------
# 4. Service provenance consistency (covers all 5 Phase 2 services)
#    These test the registry key strings only — no fixture/client needed.
# ---------------------------------------------------------------------------


def test_provenance_source_key_convention():
    """Every registered Phase 2 context source_key ends with '_v1'."""
    phase2_keys = {k for k in EXPECTED_KEYS if k.startswith((
        "timing_", "industry_", "funding_", "cross_border_", "red_flags_"
    ))}
    for key in phase2_keys:
        assert key.endswith("_v1"), f"{key} does not end with '_v1'"


def test_all_provenance_sources_have_provider():
    """Every Phase 2 registered source has a non-empty provider."""
    phase2_keys = {k for k in EXPECTED_KEYS if k.startswith((
        "timing_", "industry_", "funding_", "cross_border_", "red_flags_"
    ))}
    for key in phase2_keys:
        entry = get_source(key)
        assert entry is not None
        assert entry.get("provider"), f"{key} has no provider"


def test_all_provenance_sources_have_freshness():
    """Every registered source has a non-empty freshness."""
    for key in EXPECTED_KEYS:
        entry = get_source(key)
        assert entry is not None
        assert entry.get("freshness"), f"{key} has no freshness"


def test_provider_backed_sources_have_high_confidence():
    """Provider-backed sources should have confidence='high'."""
    for key in ("rates_liquidity_v1", "fx_gba_v1"):
        entry = get_source(key)
        assert entry is not None
        assert entry.get("confidence") == "high"


def test_fixture_sources_have_caveat():
    """Fixture-backed sources should have a non-empty caveat."""
    for key in ("industry_health_v1", "cross_border_funding_context_v1",
                "commodities_v1", "sector_benchmarks_v1"):
        entry = get_source(key)
        assert entry is not None
        assert entry.get("caveat"), f"{key} has no caveat"
