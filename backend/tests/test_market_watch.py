import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_rates_liquidity(monkeypatch):
    # Enable fixture mode to avoid external HKMA calls
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", True)
    
    response = client.get("/api/market-watch/rates-liquidity")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "rates" in data
    assert "liquidityEvents" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert "fetchedAt" in metadata
    assert "freshness" in metadata
    
    # Verify field types
    assert isinstance(data["rates"], list)
    assert isinstance(data["sourceStatus"], list)
    assert isinstance(data["liquidityEvents"], list)

def test_fx_gba(monkeypatch):
    # Mock FrankfurterClient fetch_fx_rates
    async def mock_fetch_fx_rates(self):
        return {
            "usd": {
                "date": "2026-06-02",
                "rates": {"CNY": 6.7626, "HKD": 7.8374}
            },
            "cny": {
                "date": "2026-06-02",
                "rates": {"HKD": 1.1589}
            },
            "is_v2": False
        }
    
    from app.services.market_watch.fx_client import FrankfurterClient
    monkeypatch.setattr(FrankfurterClient, "fetch_fx_rates", mock_fetch_fx_rates)
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", False)

    response = client.get("/api/market-watch/fx-gba")
    assert response.status_code == 200
    data = response.json()
    
    # Verify provider is Frankfurter
    assert data["metadata"]["source"]["provider"] == "Frankfurter"
    assert isinstance(data["metadata"]["warnings"], list)
    
    fx_pairs = data["fxPairs"]
    assert isinstance(fx_pairs, list)
    pairs = [item["pair"] for item in fx_pairs]
    assert "USD/HKD" in pairs
    assert "CNY/HKD" in pairs
    
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [item["status"] for item in source_status]
    assert "connected" in statuses
    
    # Test fallback path
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", True)
    response_fallback = client.get("/api/market-watch/fx-gba")
    assert response_fallback.status_code == 200
    data_fallback = response_fallback.json()
    assert data_fallback["metadata"]["source"]["provider"] == "Fixture"
    assert data_fallback["sourceStatus"][0]["status"] == "seed_data"
    
    response_text_lower = response.text.lower()
    assert "realtime" not in response_text_lower
    assert "source-fresh" not in response_text_lower
    assert "source_fresh" not in response_text_lower


def test_sector_benchmarks():
    # 1. Test default query
    response = client.get("/api/market-watch/sector-benchmarks")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "selectedSector" in data
    assert "sectorHealth" in data
    assert "benchmarks" in data
    assert "watchSignals" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert metadata["source"]["provider"] == "Fixture"
    assert isinstance(metadata["warnings"], list)
    assert len(metadata["warnings"]) > 0
    assert "fixture-backed" in metadata["warnings"][0].lower()
    
    # Verify default sector
    selected_sector = data["selectedSector"]
    assert selected_sector["id"] == "trading-distribution"
    assert selected_sector["name"] == "Trading & Distribution"
    assert selected_sector["geography"] == "HK"
    assert selected_sector["code"] == "HK-SME-TRD"
    
    # Verify benchmarks and watch signals
    benchmarks = data["benchmarks"]
    assert isinstance(benchmarks, list)
    assert len(benchmarks) >= 3
    # Check DSO, DIO, DPO
    labels = [b["label"] for b in benchmarks]
    assert "Days Sales Outstanding" in labels
    assert "Inventory Days" in labels
    assert "Days Payable Outstanding" in labels
    
    watch_signals = data["watchSignals"]
    assert isinstance(watch_signals, list)
    assert len(watch_signals) >= 3
    
    # Verify sourceStatus includes seed_data
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [s["status"] for s in source_status]
    assert "seed_data" in statuses
    
    # Ensure no response text claims realtime/source-fresh/approved/certified
    response_text_lower = response.text.lower()
    assert "realtime" not in response_text_lower
    assert "source-fresh" not in response_text_lower
    assert "source_fresh" not in response_text_lower
    assert "approved" not in response_text_lower
    assert "certified" not in response_text_lower
    
    # 2. Test electronics-import custom query
    response_custom = client.get("/api/market-watch/sector-benchmarks?sector=electronics-import&geography=CN")
    assert response_custom.status_code == 200
    data_custom = response_custom.json()
    
    selected_sector_custom = data_custom["selectedSector"]
    assert selected_sector_custom["id"] == "electronics-import"
    assert selected_sector_custom["name"] == "Electronics Import"
    assert selected_sector_custom["geography"] == "CN"
    assert selected_sector_custom["code"] == "HK-SME-ELC"
    
    # Check that component display value is correctly fetched
    sector_health_custom = data_custom["sectorHealth"]
    assert sector_health_custom["components"]["pmi"]["displayValue"] == "52.4"


def test_commodities():
    # 1. Test default query
    response = client.get("/api/market-watch/commodities")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "selectedSector" in data
    assert "commodityExposures" in data
    assert "marginPressureSignal" in data
    assert "watchSignals" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert metadata["source"]["provider"] == "Fixture"
    assert isinstance(metadata["warnings"], list)
    assert len(metadata["warnings"]) > 0
    assert "fixture-backed" in metadata["warnings"][0].lower() or "not configured" in metadata["warnings"][0].lower()
    
    # Verify default sector
    selected_sector = data["selectedSector"]
    assert selected_sector["id"] == "electronics-import"
    assert selected_sector["name"] == "Electronics Import"
    assert selected_sector["geography"] == "HK"
    assert selected_sector["code"] == "HK-SME-ELEC"
    
    # Verify commodity exposures
    exposures = data["commodityExposures"]
    assert isinstance(exposures, list)
    assert len(exposures) >= 4
    
    commodities = [c["commodity"] for c in exposures]
    assert "Copper (LME)" in commodities
    assert "Steel / Iron Ore" in commodities
    assert "Cotton" in commodities
    assert "Energy / Oil (Brent)" in commodities
    assert "Freight / Logistics" in commodities
    
    # Verify margin pressure signals
    signals = data["marginPressureSignal"]
    assert isinstance(signals, list)
    assert len(signals) == 1
    assert signals[0]["requiresCompanyData"] is True
    
    # Verify sourceStatus includes seed_data
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [s["status"] for s in source_status]
    assert "seed_data" in statuses
    
    # Ensure no response text claims realtime/source-fresh/approved/certified/trading/lender approved
    response_text_lower = response.text.lower()
    assert "realtime" not in response_text_lower
    assert "source-fresh" not in response_text_lower
    assert "source_fresh" not in response_text_lower
    assert "approved" not in response_text_lower
    assert "certified" not in response_text_lower
    assert "trading advice" not in response_text_lower
    assert "investment recommendation" not in response_text_lower

    # 2. Test trading-distribution custom query
    response_custom = client.get("/api/market-watch/commodities?sector=trading-distribution&geography=CN")
    assert response_custom.status_code == 200
    data_custom = response_custom.json()
    
    selected_sector_custom = data_custom["selectedSector"]
    assert selected_sector_custom["id"] == "trading-distribution"
    assert selected_sector_custom["name"] == "Trading & Distribution"
    assert selected_sector_custom["geography"] == "CN"
    assert selected_sector_custom["code"] == "HK-SME-TRD"


def test_stress_signals():
    # 1. Test default query
    response = client.get("/api/market-watch/stress-signals")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "workspaceContext" in data
    assert "scenarios" in data
    assert "requiredData" in data
    assert "watchSignals" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert metadata["source"]["provider"] == "Fixture"
    assert isinstance(metadata["warnings"], list)
    assert len(metadata["warnings"]) > 0
    assert "fixture-backed" in metadata["warnings"][0].lower()
    
    # Verify workspace context
    context = data["workspaceContext"]
    assert context["id"] == "workspace-demo"
    assert context["companyLabel"] == "Workspace Demo Context (Trading & Distribution)"
    assert context["sector"] == "Trading & Distribution"
    assert context["geography"] == "HK"
    
    # Verify scenarios
    scenarios = data["scenarios"]
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 5
    
    titles = [s["title"] for s in scenarios]
    assert "Rate Shock (+150 bps)" in titles
    assert "CNY Depreciation (-5%)" in titles
    assert "Raw Material Input Squeeze (+10%)" in titles
    assert "Receivables Delay (+15 Days)" in titles
    assert "Liquidity Squeeze" in titles
    
    # Verify sourceStatus includes seed_data and requires_company_data
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [s["status"] for s in source_status]
    assert "seed_data" in statuses
    assert "requires_company_data" in statuses
    
    # Ensure no response text claims forbidden phrases
    response_text_lower = response.text.lower()
    assert "predicted default" not in response_text_lower
    assert "approval probability" not in response_text_lower
    assert "lender approved" not in response_text_lower
    assert "guaranteed failure" not in response_text_lower
    assert "credit score impact" not in response_text_lower
    assert "bank verified" not in response_text_lower
    assert "quantified dscr impact" not in response_text_lower
    assert "quantify dscr" not in response_text_lower

    # 2. Test custom query
    response_custom = client.get("/api/market-watch/stress-signals?sector=Logistics")
    assert response_custom.status_code == 200
    data_custom = response_custom.json()
    
    context_custom = data_custom["workspaceContext"]
    assert context_custom["sector"] == "Logistics"


def test_source_status():
    response = client.get("/api/market-watch/source-status")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    sources = data["sources"]
    assert len(sources) == 6
    ids = [s["id"] for s in sources]
    assert "hkma-rates" in ids
    assert "fx-provider" in ids
    assert "commodity-provider" in ids


def test_refresh(monkeypatch):
    # Mock Frankfurter client
    async def mock_fetch_fx_rates(self):
        return {
            "usd": {
                "date": "2026-06-02",
                "rates": {"CNY": 6.7626, "HKD": 7.8374}
            },
            "cny": {
                "date": "2026-06-02",
                "rates": {"HKD": 1.1589}
            },
            "is_v2": False
        }
    from app.services.market_watch.fx_client import FrankfurterClient
    monkeypatch.setattr(FrankfurterClient, "fetch_fx_rates", mock_fetch_fx_rates)
    # Also mock HKMA calls by forcing settings
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", True)

    response = client.post("/api/market-watch/refresh", json={"scope": "all"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["refreshedScope"] == "all"
    assert "sources" in data

    response_single = client.post("/api/market-watch/refresh", json={"scope": "rates-liquidity"})
    assert response_single.status_code == 200
    data_single = response_single.json()
    assert data_single["status"] == "success"
    assert data_single["refreshedScope"] == "rates-liquidity"

    response_fixture = client.post("/api/market-watch/refresh", json={"scope": "sector-benchmarks"})
    assert response_fixture.status_code == 200
    data_fixture = response_fixture.json()
    assert data_fixture["status"] == "success"
    assert "retained" in data_fixture["message"]
def test_company_context():
    response = client.get("/api/market-watch/company-context")
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "exposures" in data
    assert "dataMode" in data
    assert data["profile"]["companyName"] == "Harbour & Finch Trading Ltd."
    assert len(data["exposures"]) > 0

def test_rates_liquidity_normalization(monkeypatch):
    from app.services.market_watch.hkma_client import hkma_client
    from app.services.market_watch.hkab_web_client import hkab_web_client
    from app.services.market_watch.cache import cache
    
    # 1. Verify HKAB fetch failure triggers HKMA fallback sorting and metadata.asOf behavior
    async def mock_fetch_hkab_failed():
        return None

    async def mock_get_hibor_fixing_sorting():
        return [
            {"end_of_day": "2026-05-29", "ir_overnight": 3.02, "ir_1m": 2.61, "ir_3m": 2.83, "ir_6m": 2.97, "ir_12m": 3.18},
            {"end_of_day": "2026-06-02", "ir_overnight": 2.89, "ir_1m": 2.44, "ir_3m": 2.60, "ir_6m": 2.70, "ir_12m": 2.90}
        ]
        
    async def mock_get_honia_sorting():
        return [
            {"end_of_day": "2026-05-29", "ir_overnight": 2.90},
            {"end_of_day": "2026-06-02", "ir_overnight": 2.76}
        ]
        
    async def mock_get_interbank_liquidity():
        return [{
            "end_of_date": "2026-06-02",
            "opening_balance": 53997,
            "closing_balance": 53997,
            "forecast_aggregate_bal_t1": 53947,
            "disc_win_base_rate": 4,
            "interest_payment_issuance_efbn_t1": -50,
            "interest_payment_issuance_efbn_t2": "+0"
        }]

    monkeypatch.setattr(hkab_web_client, "fetch_latest_hibor", mock_fetch_hkab_failed)
    monkeypatch.setattr(hkma_client, "get_hibor_fixing", mock_get_hibor_fixing_sorting)
    monkeypatch.setattr(hkma_client, "get_honia", mock_get_honia_sorting)
    monkeypatch.setattr(hkma_client, "get_interbank_liquidity", mock_get_interbank_liquidity)
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", False)

    cache.delete("rates_liquidity")

    response = client.get("/api/market-watch/rates-liquidity")
    assert response.status_code == 200
    data = response.json()

    # Fallback path assertions
    overnight_rate = next(r for r in data["rates"] if r["id"] == "hibor-o/n")
    assert overnight_rate["value"] == 2.89
    assert overnight_rate["sourceTimestamp"] == "2026-06-02"
    assert overnight_rate["context"] == "HKMA fixing"
    assert data["metadata"]["asOf"] == "2026-06-02"

    # HKAB should show unavailable status, HKMA HIBOR connected
    hkab_status_item = next(item for item in data["sourceStatus"] if item["id"] == "hkab-hibor")
    assert hkab_status_item["status"] == "unavailable"
    hkma_status_item = next(item for item in data["sourceStatus"] if item["id"] == "hkma-hibor")
    assert hkma_status_item["status"] == "connected"

    # 2. Verify cache refresh and HKAB success path behavior
    async def mock_fetch_hkab_success():
        return {
            "source_date": "2026-06-03",
            "rates": {
                "Overnight": 2.05,
                "1 Month": 2.60,
                "3 Months": 2.75,
                "6 Months": 2.91,
                "12 Months": 3.17
            },
            "source_label": "HKAB public HIBOR page"
        }

    async def mock_get_honia_june3():
        return [
            {"end_of_day": "2026-06-03", "ir_overnight": 2.01}
        ]

    # Triggering GET again should serve cached values
    response_cached = client.get("/api/market-watch/rates-liquidity")
    assert response_cached.json()["metadata"]["asOf"] == "2026-06-02"

    # Monkeypatch to HKAB success
    monkeypatch.setattr(hkab_web_client, "fetch_latest_hibor", mock_fetch_hkab_success)
    monkeypatch.setattr(hkma_client, "get_honia", mock_get_honia_june3)

    # Calling refresh should clear the cache and return fresh June 3 values
    response_refresh = client.post("/api/market-watch/refresh", json={"scope": "rates-liquidity"})
    assert response_refresh.status_code == 200
    
    response_fresh = client.get("/api/market-watch/rates-liquidity")
    data_fresh = response_fresh.json()
    assert data_fresh["metadata"]["asOf"] == "2026-06-03"
    
    overnight_fresh = next(r for r in data_fresh["rates"] if r["id"] == "hibor-o/n")
    assert overnight_fresh["value"] == 2.05
    assert overnight_fresh["context"] == "HKAB HIBOR fixing"
    assert overnight_fresh["sourceTimestamp"] == "2026-06-03"

    # HONIA should remain HKMA
    honia_fresh = next(r for r in data_fresh["rates"] if r["id"] == "honia-on")
    assert honia_fresh["context"] == "HKMA HONIA fixing"

    # hkab-hibor connected, hkma-hibor stale (secondary fallback)
    hkab_fresh_status = next(item for item in data_fresh["sourceStatus"] if item["id"] == "hkab-hibor")
    assert hkab_fresh_status["status"] == "connected"
    hkma_fresh_status = next(item for item in data_fresh["sourceStatus"] if item["id"] == "hkma-hibor")
    assert hkma_fresh_status["status"] == "stale"


def test_hkab_web_client_parsing():
    from app.services.market_watch.hkab_web_client import hkab_web_client
    
    mock_html = """
    <h2 class="hibor_section_title">Rates as at 11:15a.m.<br/>Hong Kong Time on 2026-6-3.</h2>
    <div class="general_table_row"><div class="general_table_cell hibor_maturity"><div>Overnight</div></div><div class="general_table_cell last"><div>2.05595</div></div></div>
    <div class="general_table_row"><div class="general_table_cell hibor_maturity"><div>1 Month</div></div><div class="general_table_cell last"><div>2.60000</div></div></div>
    """
    
    result = hkab_web_client.parse_html(mock_html)
    assert result is not None
    assert result["source_date"] == "2026-06-03"
    assert result["rates"]["Overnight"] == 2.05595
    assert result["rates"]["1 Month"] == 2.6
    assert result["source_label"] == "HKAB public HIBOR page"


def test_rates_liquidity_mixed_availability(monkeypatch):
    from app.services.market_watch.hkma_client import hkma_client
    from app.services.market_watch.hkab_web_client import hkab_web_client
    from app.services.market_watch.cache import cache

    # Case A: HKAB success, HONIA unavailable, Liquidity success
    async def mock_fetch_hkab_success():
        return {
            "source_date": "2026-06-03",
            "rates": {
                "Overnight": 2.05,
                "1 Month": 2.60,
                "3 Months": 2.75,
                "6 Months": 2.91,
                "12 Months": 3.17
            },
            "source_label": "HKAB public HIBOR page"
        }

    async def mock_get_honia_empty():
        return []

    async def mock_get_interbank_liquidity_success():
        return [{
            "end_of_date": "2026-06-03",
            "opening_balance": 50000,
            "closing_balance": 51000,
            "forecast_aggregate_bal_t1": 52000,
            "disc_win_base_rate": 4.5,
            "interest_payment_issuance_efbn_t1": 100,
            "interest_payment_issuance_efbn_t2": -100
        }]

    monkeypatch.setattr(hkab_web_client, "fetch_latest_hibor", mock_fetch_hkab_success)
    monkeypatch.setattr(hkma_client, "get_honia", mock_get_honia_empty)
    monkeypatch.setattr(hkma_client, "get_interbank_liquidity", mock_get_interbank_liquidity_success)
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", False)

    cache.delete("rates_liquidity")

    response = client.get("/api/market-watch/rates-liquidity")
    assert response.status_code == 200
    data = response.json()

    # HONIA should not be faked
    rates_ids = [r["id"] for r in data["rates"]]
    assert "honia-on" not in rates_ids

    # sourceStatus for HONIA should be unavailable
    honia_status = next(item for item in data["sourceStatus"] if item["id"] == "hkma-honia")
    assert honia_status["status"] == "unavailable"
    assert "HKMA HONIA data was unavailable from the source response." in data["metadata"]["warnings"]

    # Liquidity should be connected
    liq_status = next(item for item in data["sourceStatus"] if item["id"] == "hkma-liquidity")
    assert liq_status["status"] == "connected"
    assert len(data["liquidityEvents"]) > 0

    # Case B: HKAB success, HONIA success, Liquidity unavailable (missing fields)
    async def mock_get_honia_success():
        return [{"end_of_day": "2026-06-03", "ir_overnight": 2.01}]

    async def mock_get_interbank_liquidity_missing_fields():
        return [{
            "end_of_date": "2026-06-03",
            "opening_balance": 50000,
            # closing_balance is missing
            "forecast_aggregate_bal_t1": 52000,
            "disc_win_base_rate": 4.5
        }]

    monkeypatch.setattr(hkma_client, "get_honia", mock_get_honia_success)
    monkeypatch.setattr(hkma_client, "get_interbank_liquidity", mock_get_interbank_liquidity_missing_fields)

    cache.delete("rates_liquidity")

    response = client.get("/api/market-watch/rates-liquidity")
    assert response.status_code == 200
    data = response.json()

    # Liquidity should be unavailable
    liq_status = next(item for item in data["sourceStatus"] if item["id"] == "hkma-liquidity")
    assert liq_status["status"] == "unavailable"
    assert data["liquidityEvents"] == []
    # Warning should list the expected fields failure
    warnings = data["metadata"]["warnings"]
    assert any("missing expected fields" in w for w in warnings)







def _make_rates_response(rate_value=2.0, change_bps=None, liquidity_value=60000, as_of="2026-06-03"):
    from app.models.market_watch import (
        LiquidityEvent,
        RateSnapshot,
        RatesLiquidityResponse,
        ResponseMetadata,
        SourceInfo,
        SourceStatusItem,
    )

    liquidity_events = [] if liquidity_value is None else [
        LiquidityEvent(
            id="hkma-closing-balance",
            date=as_of,
            event=f"Closing Aggregate Balance: HKD {liquidity_value:,}M",
            impact="Contextual liquidity level",
            severity="Neutral",
        )
    ]
    return RatesLiquidityResponse(
        metadata=ResponseMetadata(
            asOf=as_of,
            fetchedAt="2026-06-03T00:00:00Z",
            freshness="Daily",
            isStale=False,
            source=SourceInfo(provider="HKAB / HKMA", name="HKAB and HKMA Public Data"),
            warnings=[],
        ),
        rates=[
            RateSnapshot(
                id="hibor-1m",
                label="HIBOR 1 Month",
                tenor="1M",
                value=rate_value,
                unit="percent",
                displayValue=f"{rate_value}%",
                changeBasisPoints=change_bps,
                trend="unknown",
                context="HKAB HIBOR fixing",
                sourceTimestamp=as_of,
            )
        ] if rate_value is not None else [],
        liquidityEvents=liquidity_events,
        sourceStatus=[SourceStatusItem(id="hkab-hibor", label="HKAB HIBOR", status="connected", provider="HKAB")],
    )


def test_timing_signal_endpoint_favorable(monkeypatch):
    from app.services.market_watch import timing_signal_service

    async def mock_rates():
        return _make_rates_response(rate_value=2.0, change_bps=-12, liquidity_value=65000)

    monkeypatch.setattr(timing_signal_service, "get_rates_liquidity", mock_rates)
    monkeypatch.setattr(timing_signal_service, "_calendar_red_flag", lambda: ("none", "No flag."))

    response = client.get("/api/market-watch/timing-signal")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "context_only"
    assert data["hiborLevelBand"] == "favorable"
    assert data["hiborTrendSignal"] == "easing"
    assert data["liquidityTimingSignal"] == "favorable"
    assert data["goldenTimingBand"] == "favorable"
    assert data["provenance"]["source"] == "timing_signal_v1"
    assert data["disclaimer"] == "Timing context only. Not a financing instruction."


def test_timing_signal_endpoint_neutral(monkeypatch):
    from app.services.market_watch import timing_signal_service

    async def mock_rates():
        return _make_rates_response(rate_value=2.75, change_bps=0, liquidity_value=45000)

    monkeypatch.setattr(timing_signal_service, "get_rates_liquidity", mock_rates)
    monkeypatch.setattr(timing_signal_service, "_calendar_red_flag", lambda: ("none", "No flag."))

    data = client.get("/api/market-watch/timing-signal").json()
    assert data["hiborLevelBand"] == "neutral"
    assert data["hiborTrendSignal"] == "stable"
    assert data["liquidityTimingSignal"] == "neutral"
    assert data["goldenTimingBand"] == "neutral"


def test_timing_signal_endpoint_cautious(monkeypatch):
    from app.services.market_watch import timing_signal_service

    async def mock_rates():
        return _make_rates_response(rate_value=3.8, change_bps=15, liquidity_value=25000)

    monkeypatch.setattr(timing_signal_service, "get_rates_liquidity", mock_rates)
    monkeypatch.setattr(timing_signal_service, "_calendar_red_flag", lambda: ("none", "No flag."))

    data = client.get("/api/market-watch/timing-signal").json()
    assert data["hiborLevelBand"] == "cautious"
    assert data["hiborTrendSignal"] == "tightening"
    assert data["liquidityTimingSignal"] == "cautious"
    assert data["goldenTimingBand"] == "cautious"


def test_timing_signal_endpoint_unavailable_data(monkeypatch):
    from app.services.market_watch import timing_signal_service

    async def mock_rates():
        return _make_rates_response(rate_value=None, change_bps=None, liquidity_value=None)

    monkeypatch.setattr(timing_signal_service, "get_rates_liquidity", mock_rates)
    monkeypatch.setattr(timing_signal_service, "_calendar_red_flag", lambda: ("none", "No flag."))

    data = client.get("/api/market-watch/timing-signal").json()
    assert data["hiborTrendSignal"] == "unavailable"
    assert data["liquidityTimingSignal"] == "unavailable"
    assert len(data["warnings"]) >= 2


def test_timing_signal_endpoint_calendar_red_flag(monkeypatch):
    from app.services.market_watch import timing_signal_service

    async def mock_rates():
        return _make_rates_response(rate_value=2.1, change_bps=-12, liquidity_value=65000)

    monkeypatch.setattr(timing_signal_service, "get_rates_liquidity", mock_rates)
    monkeypatch.setattr(timing_signal_service, "_calendar_red_flag", lambda: ("year_end", "Year-end calendar window."))

    data = client.get("/api/market-watch/timing-signal").json()
    assert data["calendarRedFlag"] == "year_end"
    assert data["goldenTimingBand"] == "neutral"


def test_timing_signal_safe_wording(monkeypatch):
    from app.services.market_watch import timing_signal_service

    async def mock_rates():
        return _make_rates_response(rate_value=2.75, change_bps=0, liquidity_value=45000)

    monkeypatch.setattr(timing_signal_service, "get_rates_liquidity", mock_rates)
    monkeypatch.setattr(timing_signal_service, "_calendar_red_flag", lambda: ("none", "No flag."))

    response_text = client.get("/api/market-watch/timing-signal").text.lower()
    assert "financing instruction" in response_text
    assert "timing context only" in response_text
    assert "rule-based" in response_text
