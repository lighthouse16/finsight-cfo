"""
Tests for Provider Integration Hardening v1 — Market Watch provider adapters.

Covers:
1. FixtureMarketDataAdapter returns fixture-backed results with no network
2. WorkspaceDerivedAdapter returns workspace-derived results
3. MissingProviderAdapter returns unavailable results
4. Provider status fields are present and correct
5. Missing provider does not crash
6. Source registry compatibility (get_adapter / get_adapter_provider_name)
7. build_provenance includes providerAdapter and providerIntegration
8. Forbidden wording absent
"""

import asyncio
import pytest
from app.services.market_watch.provider_adapters import (
    FixtureMarketDataAdapter,
    WorkspaceDerivedAdapter,
    MissingProviderAdapter,
    collect_adapter_warnings,
)
from app.services.market_watch.source_registry import (
    build_provenance,
    get_adapter,
    get_adapter_provider_name,
)

FORBIDDEN = [
    "approved", "rejected", "lender approved", "final offer",
    "guaranteed", "formal underwriting", "automated credit decision",
    "approval probability", "predicted default", "bank verified",
    "realtime", "arbitrage profit", "risk-free",
]


# -----------------------------------------------------------------------
# Helper — run a single async coroutine synchronously
# -----------------------------------------------------------------------


def _fetch(adapter):
    return asyncio.run(adapter.fetch())


# -----------------------------------------------------------------------
# 1. FixtureMarketDataAdapter
# -----------------------------------------------------------------------


def test_fixture_adapter_returns_fixture_backed():
    adapter = FixtureMarketDataAdapter(
        provider_key="IHS Markit",
        source_key="industry_health_v1",
        category="ihs_sector_benchmark",
    )
    result = _fetch(adapter)

    assert result is not None
    assert result["sourceKey"] == "industry_health_v1"
    assert result["status"]["mode"] == "fixture"
    assert result["status"]["providerName"] == "IHS Markit"
    assert result["status"]["providerKey"] == "industry_health_v1"
    assert result["status"]["confidence"] is not None
    assert result["status"]["freshness"] is not None
    assert result["status"]["warnings"] is not None
    assert result.get("error") is None


def test_fixture_adapter_unknown_source_key():
    adapter = FixtureMarketDataAdapter(
        provider_key="Unknown Provider",
        source_key="does_not_exist",
        category="ihs_sector_benchmark",
    )
    result = _fetch(adapter)

    assert result is not None
    assert result["status"]["mode"] == "unavailable"
    assert result["error"] is not None
    assert "not found" in result["error"].lower() or "not registered" in result["error"].lower()


def test_fixture_adapter_includes_caveat():
    adapter = FixtureMarketDataAdapter(
        provider_key="ChinaData.live",
        source_key="cross_border_funding_context_v1",
        category="china_data_macro_sector",
    )
    result = _fetch(adapter)

    assert result["status"]["caveat"] is not None
    assert "fixture" in result["status"]["caveat"].lower() or "pending" in result["status"]["caveat"].lower()


# -----------------------------------------------------------------------
# 2. WorkspaceDerivedAdapter
# -----------------------------------------------------------------------


def test_workspace_derived_adapter_returns_workspace_derived():
    adapter = WorkspaceDerivedAdapter(
        provider_key="FinSight CFO Market Watch",
        source_key="timing_signal_v1",
        category="hibor_hk_rates",
    )
    result = _fetch(adapter)

    assert result is not None
    assert result["sourceKey"] == "timing_signal_v1"
    assert result["status"]["mode"] == "workspace_derived"
    assert result["status"]["providerName"] == "FinSight CFO Market Watch"
    assert result.get("error") is None


def test_workspace_derived_adapter_unknown_key():
    adapter = WorkspaceDerivedAdapter(
        provider_key="Unknown",
        source_key="nonexistent_source",
        category="fx_reference",
    )
    result = _fetch(adapter)

    assert result is not None
    assert result["status"]["mode"] == "unavailable"
    assert result["error"] is not None


# -----------------------------------------------------------------------
# 3. MissingProviderAdapter
# -----------------------------------------------------------------------


def test_missing_provider_adapter_returns_unavailable():
    adapter = MissingProviderAdapter(
        provider_key="CME FedWatch",
        source_key="fedwatch_rate_expectation",
        category="fedwatch_rate_expectation",
    )
    result = _fetch(adapter)

    assert result is not None
    assert result["status"]["mode"] == "unavailable"
    assert result["status"]["providerName"] == "CME FedWatch"
    assert result["error"] is not None
    assert "not connected" in result["error"].lower()


def test_missing_provider_does_not_crash():
    adapter = MissingProviderAdapter(
        provider_key="Any Provider",
        source_key="any_key_123",
        category="fx_reference",
    )
    result = _fetch(adapter)

    assert result is not None
    assert isinstance(result, dict)
    assert "status" in result
    assert "sourceKey" in result


# -----------------------------------------------------------------------
# 4. Provider status fields are present
# -----------------------------------------------------------------------


@pytest.mark.parametrize("adapter_cls, source_key, expected_mode", [
    (FixtureMarketDataAdapter, "industry_health_v1", "fixture"),
    (FixtureMarketDataAdapter, "cross_border_funding_context_v1", "fixture"),
    (WorkspaceDerivedAdapter, "timing_signal_v1", "workspace_derived"),
    (WorkspaceDerivedAdapter, "funding_channel_ranking_v1", "workspace_derived"),
    (WorkspaceDerivedAdapter, "red_flags_macro_summary_v1", "workspace_derived"),
    (MissingProviderAdapter, "fedwatch_not_yet_connected", "unavailable"),
])
def test_provider_status_fields(adapter_cls, source_key, expected_mode):
    adapter = adapter_cls(
        provider_key="Test Provider",
        source_key=source_key,
        category="fx_reference",
    )
    result = _fetch(adapter)

    status = result["status"]
    assert "providerName" in status
    assert "providerKey" in status
    assert "mode" in status
    assert "asOf" in status
    assert "freshness" in status
    assert "caveat" in status or status["mode"] == "unavailable"
    assert "warnings" in status
    assert "confidence" in status

    assert status["mode"] == expected_mode
    assert isinstance(status["warnings"], list)


# -----------------------------------------------------------------------
# 5. Provider status fields are typed correctly
# -----------------------------------------------------------------------


def test_provider_status_is_typed():
    adapter = FixtureMarketDataAdapter(
        provider_key="Test",
        source_key="industry_health_v1",
        category="ihs_sector_benchmark",
    )
    result = _fetch(adapter)
    status = result["status"]

    assert isinstance(status["providerName"], str)
    assert isinstance(status["providerKey"], str)
    assert isinstance(status["mode"], str)
    assert isinstance(status["freshness"], str)
    assert isinstance(status["warnings"], list)
    assert isinstance(status["confidence"], str)


# -----------------------------------------------------------------------
# 6. Source registry compatibility (get_adapter / get_adapter_provider_name)
# -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_key, expected_adapter",
    [
        ("rates_liquidity_v1", "provider-backed"),
        ("fx_gba_v1", "provider-backed"),
        ("timing_signal_v1", "WorkspaceDerivedAdapter"),
        ("funding_channel_ranking_v1", "WorkspaceDerivedAdapter"),
        ("red_flags_macro_summary_v1", "WorkspaceDerivedAdapter"),
        ("industry_health_v1", "FixtureMarketDataAdapter"),
        ("cross_border_funding_context_v1", "FixtureMarketDataAdapter"),
        ("commodities_v1", "FixtureMarketDataAdapter"),
        ("sector_benchmarks_v1", "FixtureMarketDataAdapter"),
    ],
)
def test_get_adapter(source_key, expected_adapter):
    assert get_adapter(source_key) == expected_adapter


def test_get_adapter_unknown():
    assert get_adapter("nonexistent_source") == "MissingProviderAdapter"


@pytest.mark.parametrize(
    "source_key, expected_provider",
    [
        ("rates_liquidity_v1", "HKAB / HKMA"),
        ("fx_gba_v1", "Frankfurter"),
        ("industry_health_v1", "FinSight CFO Market Watch"),
    ],
)
def test_get_adapter_provider_name(source_key, expected_provider):
    assert get_adapter_provider_name(source_key) == expected_provider


def test_get_adapter_provider_name_unknown():
    assert get_adapter_provider_name("nonexistent") == "Provider integration pending"


# -----------------------------------------------------------------------
# 7. build_provenance includes providerAdapter and providerIntegration
# -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_key, expected_adapter",
    [
        ("timing_signal_v1", "WorkspaceDerivedAdapter"),
        ("industry_health_v1", "FixtureMarketDataAdapter"),
        ("cross_border_funding_context_v1", "FixtureMarketDataAdapter"),
        ("red_flags_macro_summary_v1", "WorkspaceDerivedAdapter"),
        ("rates_liquidity_v1", "provider-backed"),
        ("fx_gba_v1", "provider-backed"),
    ],
)
def test_build_provenance_includes_provider_adapter(source_key, expected_adapter):
    result = build_provenance(source_key)
    assert result.get("providerAdapter") == expected_adapter


@pytest.mark.parametrize(
    "source_key, expected_integration",
    [
        ("rates_liquidity_v1", "HKAB / HKMA"),
        ("fx_gba_v1", "Frankfurter"),
        ("timing_signal_v1", "FinSight CFO Market Watch"),
        ("industry_health_v1", "FinSight CFO Market Watch"),
    ],
)
def test_build_provenance_includes_provider_integration(source_key, expected_integration):
    result = build_provenance(source_key)
    assert result.get("providerIntegration") == expected_integration


def test_build_provenance_unknown_source_key():
    result = build_provenance("unknown_source")
    assert result["providerAdapter"] == "MissingProviderAdapter"
    assert "pending" in (result.get("providerIntegration") or "")


# -----------------------------------------------------------------------
# 8. No forbidden wording in adapters
# -----------------------------------------------------------------------


@pytest.mark.parametrize("word", FORBIDDEN)
def test_forbidden_word_absent_from_provider_adapters(word):
    """Scan the provider_adapters source for forbidden wording."""
    import inspect
    from app.services.market_watch import provider_adapters as mod
    source = inspect.getsource(mod)
    assert word.lower() not in source.lower(), (
        f"Forbidden word '{word}' found in provider_adapters.py"
    )


@pytest.mark.parametrize("word", FORBIDDEN)
def test_forbidden_word_absent_from_source_registry(word):
    """Scan the source_registry source for forbidden wording."""
    import inspect
    from app.services.market_watch import source_registry as mod
    source = inspect.getsource(mod)
    assert word.lower() not in source.lower(), (
        f"Forbidden word '{word}' found in source_registry.py"
    )


# -----------------------------------------------------------------------
# 9. collect_adapter_warnings dedup
# -----------------------------------------------------------------------


def test_collect_adapter_warnings_no_duplicates():
    adapters = [
        FixtureMarketDataAdapter("IHS", "industry_health_v1", "ihs_sector_benchmark"),
        FixtureMarketDataAdapter("ChinaData.live", "cross_border_funding_context_v1", "china_data_macro_sector"),
    ]
    warnings = asyncio.run(collect_adapter_warnings(adapters))
    # Should have at least some warnings and no duplicates
    assert len(warnings) > 0
    assert len(warnings) == len(set(warnings))


# -----------------------------------------------------------------------
# 10. All registered Phase 2 sources map to expected adapters
# -----------------------------------------------------------------------


PHASE_2_PROVIDER_KEYS = {
    "timing_signal_v1",
    "industry_health_v1",
    "funding_channel_ranking_v1",
    "cross_border_funding_context_v1",
    "red_flags_macro_summary_v1",
}


def test_every_phase_2_source_maps_to_adapter():
    for key in PHASE_2_PROVIDER_KEYS:
        adapter = get_adapter(key)
        assert adapter in ("WorkspaceDerivedAdapter", "FixtureMarketDataAdapter", "provider-backed"), (
            f"{key} maps to unexpected adapter '{adapter}'"
        )


def test_every_phase_2_source_has_provider_name():
    for key in PHASE_2_PROVIDER_KEYS:
        name = get_adapter_provider_name(key)
        assert name, f"{key} has no provider name"
        assert name != "Provider integration pending"
